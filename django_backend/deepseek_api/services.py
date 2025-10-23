import time
import threading
from typing import Dict, Any, Optional
from django.core.cache import cache
import hashlib
from .models import APIKey, RateLimit, ConversationSession
from django.conf import settings

# 全局配置
# API_KEY_LENGTH = 32
# TOKEN_EXPIRY_SECONDS = 3600
# RATE_LIMIT_MAX = 5  # 每分钟最大请求数
# RATE_LIMIT_INTERVAL = 60

# 线程锁用于速率限制
rate_lock = threading.Lock()

# 全局单例：TopKLogSystem 实例（懒加载）
_log_system_instance = None
_log_system_lock = threading.Lock()

def get_log_system():
    """
    获取 TopKLogSystem 单例实例（懒加载 + 线程安全）
    只在第一次调用时初始化，后续直接返回已有实例
    """
    global _log_system_instance
    
    if _log_system_instance is None:
        with _log_system_lock:
            # 双重检查锁定模式（避免多线程重复初始化）
            if _log_system_instance is None:
                from topklogsystem import TopKLogSystem
                from model_config import CURRENT_CONFIG
                import logging
                logger = logging.getLogger(__name__)
                
                logger.info("初始化 TopKLogSystem 单例实例...")
                logger.info(f"使用模型: LLM={CURRENT_CONFIG['llm']}, Embedding={CURRENT_CONFIG['embedding_model']}")
                
                _log_system_instance = TopKLogSystem(
                    log_path="./data/log",
                    llm=CURRENT_CONFIG['llm'],
                    embedding_model=CURRENT_CONFIG['embedding_model']
                )
                logger.info("TopKLogSystem 初始化完成！")
    
    return _log_system_instance

def deepseek_r1_api_call(prompt: str, query_type: str = "analysis") -> str:
    """
    调用 DeepSeek-R1 API（使用单例模式，避免重复初始化）
    
    Args:
        prompt: 用户输入的问题
        query_type: 查询类型（analysis, error_classification, performance_analysis, security_analysis）
    
    Returns:
        LLM 的响应文本
    """
    # 获取全局单例实例（首次调用会初始化，后续直接复用）
    system = get_log_system()
    
    # 执行查询
    result = system.query(prompt, query_type=query_type)
    time.sleep(0.5)
    
    print(result["response"])
    return result["response"]

def create_api_key(user: str) -> str:
    """创建 API Key 并保存到数据库"""
    key = APIKey.generate_key()
    expiry = time.time() + settings.TOKEN_EXPIRY_SECONDS
    
    api_key = APIKey.objects.create(
        key=key,
        user=user,
        expiry_time=expiry
    )
    
    # 创建对应的速率限制记录
    RateLimit.objects.create(
        api_key=api_key,
        reset_time=time.time() + settings.RATE_LIMIT_INTERVAL
    )
    
    return key

def validate_api_key(key_str: str) -> bool:
    """验证 API Key 是否存在且未过期"""
    try:
        api_key = APIKey.objects.get(key=key_str)
        if api_key.is_valid():
            return True
        else:
            api_key.delete()  # 删除过期key
            return False
    except APIKey.DoesNotExist:
        return False

def check_rate_limit(key_str: str) -> bool:
    """检查 API Key 的请求频率是否超过限制"""
    with rate_lock:
        try:
            # api_key = APIKey.objects.get(key=key_str)
            # rate_limit = RateLimit.objects.get(api_key=api_key)
            rate_limit = RateLimit.objects.select_related('api_key').get(api_key__key=key_str)
            
            current_time = time.time()
            if current_time > rate_limit.reset_time:
                rate_limit.count = 1
                rate_limit.reset_time = current_time + settings.RATE_LIMIT_INTERVAL
                rate_limit.save()
                return True
            elif rate_limit.count < settings.RATE_LIMIT_MAX:
                rate_limit.count += 1
                rate_limit.save()
                return True
            else:
                return False
        except RateLimit.DoesNotExist:
            # 如果速率限制记录不存在，创建一个新的
            try:
                current_time = time.time()
                api_key = APIKey.objects.get(key=key_str)
                RateLimit.objects.create(
                    api_key=api_key,
                    count=1,
                    reset_time=current_time + settings.RATE_LIMIT_INTERVAL
                )
                return True
            except APIKey.DoesNotExist:
                return False

# def get_or_create_session(session_id: str, user: APIKey) -> ConversationSession:
    # """获取或创建会话，关联当前用户（通过API Key）"""
    # session, created = ConversationSession.objects.get_or_create(
        # session_id=session_id,
        # user=user,  # 绑定用户
        # defaults={'context': ''}
    # )
    # return session

def get_or_create_session(session_id: str, user: APIKey) -> ConversationSession:
    """
    获取或创建用户的专属会话：
    - 若用户+session_id已存在 → 加载旧会话（保留历史）
    - 若不存在 → 创建新会话（空历史）
    """
    session, created = ConversationSession.objects.get_or_create(
        session_id=session_id,  # 匹配会话ID
        user=user,              # 匹配当前用户（关键！避免跨用户会话冲突）
        defaults={'context': ''}
    )
    # 调试日志：确认是否创建新会话（created=True 表示新会话）
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"会话 {session_id}（用户：{user.user}）{'创建新会话' if created else '加载旧会话'}")
    return session

def get_cached_reply(prompt: str, session_id: str, user: APIKey) -> str | None:
    """缓存键包含 session_id 和 user，避免跨会话冲突"""
    cache_key = f"reply:{user.user}:{session_id}:{hash(prompt)}"
    return cache.get(cache_key)

def set_cached_reply(prompt: str, reply: str, session_id: str, user: APIKey, timeout=3600):
    cache_key = f"reply:{user.user}:{session_id}:{hash(prompt)}"
    cache.set(cache_key, reply, timeout)


def generate_cache_key(original_key: str) -> str:
    """
    生成安全的缓存键。
    对原始字符串进行哈希处理，确保键长度固定且仅包含安全字符。
    """
    # 使用SHA256哈希函数生成固定长度的键（64位十六进制字符串）
    hash_obj = hashlib.sha256(original_key.encode('utf-8'))
    return hash_obj.hexdigest()
