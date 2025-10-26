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
    print(f"\n🤖 [大模型调用] 开始调用 DeepSeek-R1 API")
    print(f"🤖 [调用参数] query_type: '{query_type}'")
    print(f"🤖 [Prompt长度] {len(prompt)} 字符")
    
    # 获取全局单例实例（首次调用会初始化，后续直接复用）
    system = get_log_system()
    
    # 执行查询
    print(f"🤖 [API请求] 发送请求到大模型...")
    result = system.query(prompt, query_type=query_type)
    time.sleep(0.5)
    
    response = result["response"]
    print(f"🤖 [API响应] 收到回复，长度: {len(response)} 字符")
    print(f"🤖 [回复内容] {response[:100]}{'...' if len(response) > 100 else ''}")
    
    return response

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
    print(f"🔍 [数据库查询] 查找会话: session_id='{session_id}', user='{user.user}'")
    
    session, created = ConversationSession.objects.get_or_create(
        session_id=session_id,  # 匹配会话ID
        user=user,              # 匹配当前用户（关键！避免跨用户会话冲突）
        defaults={'context': ''}
    )
    
    # 调试日志：确认是否创建新会话（created=True 表示新会话）
    import logging
    logger = logging.getLogger(__name__)
    
    if created:
        print(f"✨ [数据库操作] 创建新会话 - ID: {session.id}, session_id: '{session.session_id}'")
        print(f"✨ [新会话详情] 用户: {session.user.user}, 上下文: 空")
        logger.info(f"会话 {session_id}（用户：{user.user}）创建新会话")
    else:
        print(f"📂 [数据库操作] 加载现有会话 - ID: {session.id}, session_id: '{session.session_id}'")
        print(f"📂 [现有会话详情] 用户: {session.user.user}, 上下文长度: {len(session.context)} 字符")
        print(f"📂 [会话创建时间] {session.created_at}")
        print(f"📂 [会话更新时间] {session.updated_at}")
        if session.context:
            print(f"📂 [历史上下文预览] {session.context[:150]}{'...' if len(session.context) > 150 else ''}")
        logger.info(f"会话 {session_id}（用户：{user.user}）加载旧会话")
    
    return session

def get_cached_reply(prompt: str, session_id: str, user: APIKey) -> str | None:
    """缓存键包含 session_id 和 user，避免跨会话冲突"""
    cache_key = f"reply:{user.user}:{session_id}:{hash(prompt)}"
    print(f"🔍 [缓存查询] 缓存键: {cache_key}")
    
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"✅ [缓存命中] 找到缓存回复，长度: {len(cached_result)} 字符")
        print(f"💾 [缓存内容] {cached_result[:80]}{'...' if len(cached_result) > 80 else ''}")
    else:
        print(f"❌ [缓存未命中] 缓存中没有找到对应回复")
    
    return cached_result

def set_cached_reply(prompt: str, reply: str, session_id: str, user: APIKey, timeout=3600):
    cache_key = f"reply:{user.user}:{session_id}:{hash(prompt)}"
    print(f"💾 [缓存保存] 保存回复到缓存")
    print(f"💾 [缓存键] {cache_key}")
    print(f"💾 [缓存内容] 长度: {len(reply)} 字符, 过期时间: {timeout}秒")
    print(f"💾 [回复预览] {reply[:80]}{'...' if len(reply) > 80 else ''}")
    
    cache.set(cache_key, reply, timeout)
    print(f"✅ [缓存完成] 回复已成功保存到缓存")


def generate_cache_key(original_key: str) -> str:
    """
    生成安全的缓存键。
    对原始字符串进行哈希处理，确保键长度固定且仅包含安全字符。
    """
    # 使用SHA256哈希函数生成固定长度的键（64位十六进制字符串）
    hash_obj = hashlib.sha256(original_key.encode('utf-8'))
    return hash_obj.hexdigest()
