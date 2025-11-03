import os

# chroma 不上传数据
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["DISABLE_TELEMETRY"] = "1"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

import json
import logging
import pandas as pd
from typing import Any, Dict, List, Optional

# llama-index & chroma
import chromadb
from llama_index.core import Settings  # 全局
from llama_index.core import Document
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore  # 注意导入路径
from llama_index.llms.ollama import Ollama  # 使用 llama-index 的 Ollama
from llama_index.embeddings.ollama import OllamaEmbedding  # 使用 llama-index 的 Embedding

# langchain (仅用于 prompt)
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

# 日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入高级 RAG 组件
try:
    from hybrid_retriever import HybridRetriever, AdvancedLogRetriever
    from query_optimizer import QueryOptimizer, AdvancedQueryOptimizer
    from reranker import create_reranker, RuleBasedReranker
    ADVANCED_RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"高级 RAG 组件导入失败: {e}")
    logger.info("安装高级 RAG 依赖: pip install rank-bm25")
    ADVANCED_RAG_AVAILABLE = False

# 导入自定义 prompt 模板
try:
    from deepseek_api.prompt_templates import PromptTemplates
    prompt_templates = PromptTemplates()
except ImportError:
    # 如果未安装或找不到模块，使用内置的简单模板
    prompt_templates = None

# 日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopKLogSystem:
    def __init__(
        self,
        log_path: str,
        llm: str,
        embedding_model: str,
        use_advanced_rag: bool = True,  # 是否使用高级 RAG
        retrieval_mode: str = "hybrid",  # 检索模式: "vector", "bm25", "hybrid"
        enable_reranking: bool = True,   # 是否启用重排序
        enable_query_optimization: bool = True,  # 是否启用查询优化
    ) -> None:
        # init models - 使用 llama-index 原生组件
        self.llm = Ollama(
            model=llm, 
            temperature=0.1, 
            request_timeout=600.0,  # 增加超时时间到 10 分钟
            context_window=4096,     # 增加上下文窗口
            num_ctx=4096
        )
        self.embedding_model = OllamaEmbedding(
            model_name=embedding_model,
            request_timeout=300.0    # embedding 超时时间 5 分钟
        )

        # init database
        Settings.llm = self.llm
        Settings.embed_model = self.embedding_model

        self.log_path = log_path
        self.log_index = None
        self.vector_store = None
        self.documents_list = []  # 存储文档列表（用于 BM25）
        
        # 高级 RAG 组件
        self.use_advanced_rag = use_advanced_rag and ADVANCED_RAG_AVAILABLE
        self.retrieval_mode = retrieval_mode
        self.enable_reranking = enable_reranking
        self.enable_query_optimization = enable_query_optimization
        
        self.hybrid_retriever = None
        self.query_optimizer = None
        self.reranker = None
        
        # 构建向量存储
        self._build_vectorstore()
        
        # 初始化高级 RAG 组件
        if self.use_advanced_rag:
            self._init_advanced_rag()
        else:
            logger.info("使用基础 RAG 模式（仅向量检索）")

    # 加载数据并构建索引
    def _build_vectorstore(self):
        vector_store_path = "./data/vector_stores"
        os.makedirs(vector_store_path, exist_ok=True)  # exist_ok=True 目录存在时不报错

        chroma_client = chromadb.PersistentClient(path=vector_store_path)  # chromadb 持久化

        # 检查是否已存在集合
        collection_exists = False
        try:
            existing_collections = chroma_client.list_collections()
            collection_exists = any(c.name == "log_collection" for c in existing_collections)
            if collection_exists:
                logger.info("找到现有向量索引，直接加载...")
        except Exception as e:
            logger.warning(f"检查集合时出错: {e}")
            collection_exists = False

        # ChromaVectorStore 将 collection 与 store 绑定
        # 也是将 Chroma 包装为 llama-index 的接口
        # StorageContext存储上下文， 包含Vector Store、Document Store、Index Store 等
        log_collection = chroma_client.get_or_create_collection("log_collection")

        # 构建 log 库 index
        log_vector_store = ChromaVectorStore(chroma_collection=log_collection)
        log_storage_context = StorageContext.from_defaults(vector_store=log_vector_store)
        
        # 检查集合是否为空
        is_empty = len(log_collection.get(limit=1)["ids"]) == 0
        
        # 只有当集合不存在或为空时才重建索引
        if not collection_exists or is_empty:
            logger.info("向量索引不存在或为空，开始构建...")
            if log_documents := self._load_documents(self.log_path):
                self.log_index = VectorStoreIndex.from_documents(
                    log_documents,
                    storage_context=log_storage_context,
                    show_progress=True,
                )
                logger.info(f"日志库索引构建完成，共 {len(log_documents)} 条日志")
        else:
            # 直接使用现有索引
            self.log_index = VectorStoreIndex.from_vector_store(
                log_vector_store,
            )
            logger.info("成功加载现有向量索引，跳过构建步骤")

    # 加载文档数据
    def _load_documents(self, data_path: str) -> List[Document]:
        if not os.path.exists(data_path):
            logger.warning(f"数据路径不存在: {data_path}")
            return []

        documents = []
        # 同时保存为字典格式（用于 BM25）
        self.documents_list = []
        
        for file in os.listdir(data_path):
            ext = os.path.splitext(file)[1]
            if ext not in [".txt", ".md", ".json", ".jsonl", ".csv"]:
                continue

            file_path = f"{data_path}/{file}"
            try:
                if ext == ".csv":  # utf-8 的 csv
                    # 大型 csv 分块进行读取
                    chunk_size = 1000  # 每次读取1000行
                    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                        for row in chunk.itertuples(index=False):  # 无行号
                            content = str(row).replace("Pandas", " ")
                            documents.append(Document(text=content))
                            # 同时保存为字典（用于高级检索）
                            self.documents_list.append({"text": content})
                else:  # .txt or .md, .json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        doc = Document(text=content)
                        documents.append(doc)
                        self.documents_list.append({"text": content})
            except Exception as e:
                logger.error(f"加载文档失败 {file_path}: {e}")
        
        logger.info(f"文档加载完成：{len(documents)} 条记录")
        return documents
    
    def _init_advanced_rag(self):
        """初始化高级 RAG 组件"""
        logger.info("=" * 60)
        logger.info("初始化高级 RAG 系统")
        logger.info("=" * 60)
        
        try:
            # 1. 初始化混合检索器
            if self.retrieval_mode in ["hybrid", "bm25"]:
                logger.info("🔍 初始化混合检索器（BM25 + 向量）...")
                self.hybrid_retriever = AdvancedLogRetriever(
                    vector_index=self.log_index,
                    documents=self.documents_list,
                    alpha=0.6,  # 60% 向量权重，40% BM25 权重
                    enable_context_expansion=True
                )
                stats = self.hybrid_retriever.get_statistics()
                logger.info(f"   ✓ 混合检索器初始化完成")
                logger.info(f"   - 文档总数: {stats['total_documents']}")
                logger.info(f"   - 日志级别分布: {stats['level_distribution']}")
                logger.info(f"   - 向量/BM25 权重: {stats['alpha']}/{stats['beta']}")
            
            # 2. 初始化查询优化器
            if self.enable_query_optimization:
                logger.info("✨ 初始化查询优化器...")
                self.query_optimizer = AdvancedQueryOptimizer(llm=self.llm)
                logger.info("   ✓ 查询优化器初始化完成（支持同义词扩展、意图识别）")
            
            # 3. 初始化重排序器
            if self.enable_reranking:
                logger.info("🎯 初始化重排序器...")
                self.reranker = create_reranker(
                    reranker_type="diversity",  # 使用多样性重排序
                    diversity_weight=0.3
                )
                logger.info("   ✓ 重排序器初始化完成（基于规则 + 多样性）")
            
            logger.info("=" * 60)
            logger.info("✅ 高级 RAG 系统初始化完成")
            logger.info(f"检索模式: {self.retrieval_mode}")
            logger.info(f"查询优化: {'启用' if self.enable_query_optimization else '禁用'}")
            logger.info(f"重排序: {'启用' if self.enable_reranking else '禁用'}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ 高级 RAG 初始化失败: {e}")
            logger.warning("回退到基础 RAG 模式")
            self.use_advanced_rag = False

        # 检索相关日志

    def retrieve_logs(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        检索相关日志
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件
            
        Returns:
            检索结果列表
        """
        if not self.log_index:
            logger.warning("索引未初始化，尝试重新构建...")
            self._build_vectorstore()
            if not self.log_index:
                logger.error("索引构建失败")
                return []

        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 开始检索日志")
            logger.info(f"原始查询: {query}")
            logger.info(f"目标数量: top_{top_k}")
            logger.info(f"{'='*60}")
            
            # 使用高级 RAG
            if self.use_advanced_rag and self.hybrid_retriever:
                return self._advanced_retrieve(query, top_k, filters)
            else:
                # 回退到基础检索
                return self._basic_retrieve(query, top_k)
                
        except Exception as e:
            logger.error(f"日志检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _basic_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """基础向量检索（原始方法）"""
        logger.info("使用基础向量检索...")
        
        retriever = self.log_index.as_retriever(similarity_top_k=top_k)
        results = retriever.retrieve(query)

        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.text,
                "score": result.score if result.score else 0.5
            })
        
        logger.info(f"✓ 基础检索完成，返回 {len(formatted_results)} 条结果")
        return formatted_results
    
    def _advanced_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """高级检索（混合检索 + 查询优化 + 重排序）"""
        logger.info("🚀 使用高级 RAG 检索...")
        
        # 1. 查询优化
        optimized_query = query
        if self.query_optimizer and self.enable_query_optimization:
            logger.info("📝 步骤 1: 查询优化")
            try:
                opt_result = self.query_optimizer.optimize(query)
                logger.info(f"   - 原始查询: {query}")
                logger.info(f"   - 查询意图: {opt_result.intent}")
                logger.info(f"   - 扩展术语: {opt_result.expanded_terms[:5]}")
                
                # 使用增强后的查询
                optimized_query = self.query_optimizer.enhance_query_for_retrieval(query)
                logger.info(f"   - 优化后查询: {optimized_query}")
                
                # 建议过滤器
                if not filters:
                    filters = self.query_optimizer.suggest_filters(query)
                    if filters:
                        logger.info(f"   - 建议过滤器: {filters}")
            except Exception as e:
                logger.warning(f"查询优化失败: {e}，使用原始查询")
        
        # 2. 混合检索
        logger.info("📚 步骤 2: 混合检索（BM25 + 向量）")
        try:
            # 获取更多候选结果（用于重排序）
            candidate_count = min(top_k * 3, 50)
            
            results = self.hybrid_retriever.retrieve(
                query=optimized_query,
                top_k=candidate_count,
                filters=filters,
                boost_severity=True  # 提升高严重性日志权重
            )
            logger.info(f"   ✓ 检索到 {len(results)} 条候选结果")
            
            # 显示检索统计
            if results:
                sources = [r.source for r in results]
                from collections import Counter
                source_counts = Counter(sources)
                logger.info(f"   - 结果来源: {dict(source_counts)}")
        except Exception as e:
            logger.error(f"混合检索失败: {e}，回退到基础检索")
            return self._basic_retrieve(query, top_k)
        
        # 3. 重排序
        if self.reranker and self.enable_reranking and len(results) > 1:
            logger.info("🎯 步骤 3: 重排序")
            try:
                results = self.reranker.rerank(
                    query=query,  # 使用原始查询进行重排序
                    results=results,
                    top_k=top_k
                )
                logger.info(f"   ✓ 重排序完成，返回 top_{len(results)} 结果")
            except Exception as e:
                logger.warning(f"重排序失败: {e}，跳过重排序")
                results = results[:top_k]
        else:
            results = results[:top_k]
        
        # 4. 格式化结果
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "content": result.content,
                "score": result.score,
                "metadata": {
                    "service": result.metadata.service,
                    "level": result.metadata.level,
                    "error_type": result.metadata.error_type,
                    "component": result.metadata.component,
                    "severity_score": result.metadata.severity_score
                },
                "rank": i + 1
            })
        
        logger.info(f"{'='*60}")
        logger.info(f"✅ 高级检索完成，返回 {len(formatted_results)} 条结果")
        logger.info(f"{'='*60}\n")
        
        return formatted_results

            # LLM 生成响应

    def generate_response(self, query: str, context: Dict, query_type: str = "analysis") -> str:
        """
        使用 LLM 生成响应
        
        Args:
            query: 用户查询
            context: 检索到的日志上下文
            query_type: 查询类型，可选值: analysis, multi_turn, error_classification, performance_analysis, security_analysis
            
        Returns:
            LLM 生成的响应文本
        """
        prompt = self._build_prompt_string(query, context, query_type)  # 构建提示词字符串

        try:
            response = self.llm.complete(prompt)  # 使用 complete 而不是 invoke
            return response.text
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f"生成响应时出错: {str(e)}"

            # 构建 prompt 字符串

    def _build_prompt_string(self, query: str, context: Dict, query_type: str = "analysis") -> str:
        """
        构建提示词字符串
        
        Args:
            query: 用户查询
            context: 检索到的日志上下文
            query_type: 查询类型，可选值: analysis, multi_turn, error_classification, performance_analysis, security_analysis
            
        Returns:
            构建好的提示词
        """
        # 构建日志上下文
        log_context = ""
        for i, log in enumerate(context, 1):
            log_context += f"日志 {i} : {log['content']}\n\n"
        
        # 使用 prompt 模板
        if prompt_templates:
            # 使用专业模板库
            try:
                prompt = prompt_templates.get_template_by_type(
                    query_type=query_type,
                    log_context=log_context,
                    query=query
                )
                return prompt
            except Exception as e:
                logger.error(f"使用模板失败: {e}，回退到内置模板")
        
        # 内置的默认模板（作为备份）
        prompt = f"""
你是一个专业的日志分析专家，擅长从海量日志中发现问题、定位根因、提供解决方案。

你的分析应该：
1. 结构化：使用清晰的段落和标题
2. 数据驱动：引用具体的日志证据
3. 深入：从现象到根因，再到解决方案
4. 可操作：提供具体的修复建议

## 相关历史日志参考:
{log_context}

## 当前需要分析的问题:
{query}

## 分析要求
请按照以下步骤进行分析：

### 第一步：问题识别
从日志中提取关键错误信息、异常模式、性能指标

### 第二步：根因分析
结合日志时间线、错误堆栈、系统状态，推断问题根本原因

### 第三步：影响评估
评估问题的严重程度、影响范围、业务影响

### 第四步：解决方案
提供分层解决方案：
- 紧急修复（立即可执行）
- 短期优化（一周内）
- 长期改进（架构层面）

### 第五步：预防措施
建议监控指标、告警规则、代码规范

## 输出格式要求
请使用 Markdown 格式，包含以下部分：
- **问题摘要**：简明概述问题
- **根因分析**：详细分析问题原因
- **影响范围**：评估影响范围和严重程度
- **解决方案**：分层次提供解决建议
- **预防措施**：防止类似问题再次发生的建议

## Few-shot 示例
<example>
问题：数据库连接池耗尽
日志：HikariPool-1 - Connection is not available, request timed out after 30000ms

分析：
**问题摘要**
系统出现数据库连接池耗尽，导致新请求无法获取连接

**根因分析**
1. 连接泄漏：部分代码未正确关闭连接
2. 慢查询：某些查询执行时间过长，占用连接
3. 并发量激增：流量突增超过连接池容量

**解决方案**
- 紧急：重启服务释放连接，临时扩大连接池
- 短期：代码审查，添加连接自动回收机制
- 长期：引入读写分离，优化慢查询
</example>

请开始你的分析：
"""
        return prompt

        # 执行查询

    def query(self, query: str, query_type: str = "analysis") -> Dict:
        """
        执行查询并生成响应
        
        Args:
            query: 用户查询
            query_type: 查询类型，可选值: analysis, general_chat, multi_turn, error_classification, performance_analysis, security_analysis
            
        Returns:
            包含响应和检索统计的字典
        """
        # 根据查询类型决定是否进行RAG检索
        if query_type == "general_chat":
            # 通用对话模式，不进行RAG检索
            print(f"💬 [通用对话模式] 跳过RAG检索，直接调用LLM")
            response = self._generate_general_response(query)
            return {
                "response": response,
                "retrieval_stats": 0,
                "query_type": query_type
            }
        else:
            # 日志分析模式，进行RAG检索
            print(f"🔍 [日志分析模式] 进行RAG检索")
            log_results = self.retrieve_logs(query)
            response = self.generate_response(query, log_results, query_type)
            
            return {
                "response": response,
                "retrieval_stats": len(log_results),
                "query_type": query_type
            }
    
    def _generate_general_response(self, query: str) -> str:
        """
        生成通用对话回复（不使用RAG）
        
        Args:
            query: 用户查询
            
        Returns:
            LLM生成的回复
        """
        # 构建简单的对话prompt
        simple_prompt = f"""你是一个专业的技术助手。请直接回答用户的问题，提供准确、有用的信息。

用户问题：{query}

请回答："""
        
        try:
            response = self.llm.complete(simple_prompt)
            return response.text
        except Exception as e:
            logger.error(f"通用对话LLM调用失败: {e}")
            return f"抱歉，我无法回答您的问题。错误信息: {str(e)}"

    # 示例使用


if __name__ == "__main__":
    # 初始化系统
    system = TopKLogSystem(
        log_path="./data/log",
        llm="deepseek-r1:7b",
        embedding_model="bge-large"
    )

    # 基础日志分析示例
    print("\n=== 基础日志分析示例 ===")
    query = "如何解决数据库连接池耗尽的问题？"
    result = system.query(query, query_type="analysis")
    print("查询:", query)
    print("查询类型:", result["query_type"])
    print("检索统计:", result["retrieval_stats"])
    print("响应:", result["response"])
    
    # 错误分类示例
    print("\n=== 错误分类示例 ===")
    query = "分析系统中的错误类型和严重程度"
    result = system.query(query, query_type="error_classification")
    print("查询:", query)
    print("查询类型:", result["query_type"])
    print("检索统计:", result["retrieval_stats"])
    print("响应:", result["response"])
    
    # 性能分析示例
    print("\n=== 性能分析示例 ===")
    query = "分析系统性能瓶颈并提供优化建议"
    result = system.query(query, query_type="performance_analysis")
    print("查询:", query)
    print("查询类型:", result["query_type"])
    print("检索统计:", result["retrieval_stats"])
    print("响应:", result["response"])
