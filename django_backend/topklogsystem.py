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
        self._build_vectorstore()

    # 加载数据并构建索引
    def _build_vectorstore(self):
        vector_store_path = "./data/vector_stores"
        os.makedirs(vector_store_path, exist_ok=True)  # exist_ok=True 目录存在时不报错

        chroma_client = chromadb.PersistentClient(path=vector_store_path)  # chromadb 持久化

        # ChromaVectorStore 将 collection 与 store 绑定
        # 也是将 Chroma 包装为 llama-index 的接口
        # StorageContext存储上下文， 包含Vector Store、Document Store、Index Store 等
        log_collection = chroma_client.get_or_create_collection("log_collection")

        # 构建 log 库 index
        log_vector_store = ChromaVectorStore(chroma_collection=log_collection)
        log_storage_context = StorageContext.from_defaults(vector_store=log_vector_store)
        if log_documents := self._load_documents(self.log_path):
            self.log_index = VectorStoreIndex.from_documents(
                log_documents,
                storage_context=log_storage_context,
                show_progress=True,
            )
            logger.info(f"日志库索引构建完成，共 {len(log_documents)} 条日志")

    @staticmethod
    # 加载文档数据
    def _load_documents(data_path: str) -> List[Document]:
        if not os.path.exists(data_path):
            logger.warning(f"数据路径不存在: {data_path}")
            return []

        documents = []
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
                else:  # .txt or .md, .json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        doc = Document(text=content, )
                        documents.append(doc)
            except Exception as e:
                logger.error(f"加载文档失败 {file_path}: {e}")
        return documents

        # 检索相关日志

    def retrieve_logs(self, query: str, top_k: int = 10) -> List[Dict]:
        if not self.log_index:
            return []

        try:
            retriever = self.log_index.as_retriever(similarity_top_k=top_k)  # topK
            results = retriever.retrieve(query)

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.text,
                    "score": result.score
                })
            return formatted_results
        except Exception as e:
            logger.error(f"日志检索失败: {e}")
            return []

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
            query_type: 查询类型，可选值: analysis, multi_turn, error_classification, performance_analysis, security_analysis
            
        Returns:
            包含响应和检索统计的字典
        """
        log_results = self.retrieve_logs(query)
        response = self.generate_response(query, log_results, query_type)  # 生成响应

        return {
            "response": response,
            "retrieval_stats": len(log_results),
            "query_type": query_type
        }

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
