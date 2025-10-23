"""
模型配置文件
可以根据需求选择不同的 LLM 和 Embedding 模型
"""

# ==================== 推荐的模型配置 ====================

# 配置 1：快速轻量（推荐用于开发和测试）
FAST_CONFIG = {
    "llm": "qwen2.5:3b",                    # Qwen 3B 模型，速度快，内存占用小
    "embedding_model": "nomic-embed-text",  # 轻量级 embedding 模型
    "llm_timeout": 300.0,                   # 5 分钟
    "embedding_timeout": 180.0,             # 3 分钟
    "context_window": 4096,
}

# 配置 2：平衡性能（推荐用于生产环境）
BALANCED_CONFIG = {
    "llm": "qwen2.5:7b",                    # Qwen 7B 模型，性能更好
    "embedding_model": "nomic-embed-text",  # 轻量级 embedding 模型
    "llm_timeout": 600.0,                   # 10 分钟
    "embedding_timeout": 300.0,             # 5 分钟
    "context_window": 8192,
}

# 配置 3：高质量分析（需要大内存）
HIGH_QUALITY_CONFIG = {
    "llm": "deepseek-r1:7b",                # DeepSeek R1 7B，分析质量最高
    "embedding_model": "bge-large",         # BGE Large，embedding 质量最高
    "llm_timeout": 900.0,                   # 15 分钟
    "embedding_timeout": 600.0,             # 10 分钟
    "context_window": 4096,
}

# 配置 4：超快速（用于快速测试）
ULTRA_FAST_CONFIG = {
    "llm": "qwen2.5:1.5b",                  # Qwen 1.5B，极快
    "embedding_model": "nomic-embed-text",  # 轻量级 embedding 模型
    "llm_timeout": 180.0,                   # 3 分钟
    "embedding_timeout": 120.0,             # 2 分钟
    "context_window": 2048,
}

# ==================== 当前使用的配置 ====================
# 修改这里来切换不同的配置
CURRENT_CONFIG = FAST_CONFIG

# ==================== 可用的 Ollama 模型列表 ====================
"""
LLM 模型（大小按从小到大排序）：
1. qwen2.5:0.5b    - 500M，极快，适合简单任务
2. qwen2.5:1.5b    - 1.5GB，很快，适合快速测试
3. qwen2.5:3b      - 3GB，快速且质量不错（推荐）
4. qwen2.5:7b      - 7GB，性能好，适合生产
5. llama3.2:3b     - 3GB，Meta 的轻量模型
6. gemma2:2b       - 2GB，Google 的轻量模型
7. mistral:7b      - 7GB，性能好的开源模型
8. deepseek-r1:7b  - 7GB，分析质量高但慢

Embedding 模型：
1. nomic-embed-text     - 轻量级，速度快（推荐）
2. mxbai-embed-large    - 中等大小，性能好
3. bge-large           - 大模型，质量最高但慢
4. all-minilm          - 超轻量，适合快速测试

如何下载模型：
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
"""

# ==================== 模型性能对比 ====================
"""
| 模型配置          | 内存占用 | 初始化时间 | 响应速度 | 分析质量 | 推荐场景       |
|------------------|---------|-----------|---------|---------|--------------|
| ULTRA_FAST       | ~2GB    | 1-2 分钟  | 很快     | 一般     | 快速测试      |
| FAST (当前)      | ~4GB    | 3-5 分钟  | 快      | 良好     | 开发/测试     |
| BALANCED         | ~8GB    | 5-7 分钟  | 中等     | 很好     | 生产环境      |
| HIGH_QUALITY     | ~12GB   | 8-10 分钟 | 慢      | 最好     | 深度分析      |
"""

