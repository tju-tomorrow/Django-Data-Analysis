from ninja import NinjaAPI, Router
# from ninja.security import BaseAuth
from django.http import HttpRequest
from typing import Optional
from . import services
from django.conf import settings
from .schemas import LoginIn, LoginOut, ChatIn, ChatOut, HistoryOut, ErrorResponse
from .models import APIKey
from .services import get_or_create_session, deepseek_r1_api_call, get_cached_reply, set_cached_reply
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

api = NinjaAPI(title="KAI API", version="0.0.1")

# class ApiKeyAuth(AuthBase):
    # def authenticate(self, request):
        # auth_header = request.headers.get("Authorization")
        # if not auth_header:
            # return None  # 未提供认证信息，返回None表示认证失败
        
        # try:
            # # 解析 Authorization 头（格式：Bearer <api_key>）
            # scheme, key = auth_header.split()
            # if scheme.lower() != "bearer":
                # return None  # 认证方案不是Bearer，失败
            
            # # 查询对应的APIKey对象（验证有效性）
            # api_key = APIKey.objects.get(key=key)
            # # 返回APIKey对象（而非字符串），后续可通过request.auth访问
            # return api_key  
        # except (ValueError, APIKey.DoesNotExist):
            # # 解析失败或APIKey不存在，返回None表示认证失败
            # return None

def api_key_auth(request):
    """验证请求头中的API Key"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None  # 未提供认证信息，返回None表示认证失败

    try:
        # 解析格式：Bearer <api_key>
        scheme, key = auth_header.split()
        if scheme.lower() != "bearer":
            return None  # 认证方案错误

        # 验证API Key是否存在
        api_key = APIKey.objects.get(key=key)
        return api_key  # 认证成功，返回APIKey对象
    except (ValueError, APIKey.DoesNotExist):
        return None  # 解析失败或Key不存在，认证失败

router = Router(auth=api_key_auth)

@api.post("/login", response={200: LoginOut, 400: ErrorResponse, 403: ErrorResponse})
def login(request, data: LoginIn):
    """
    登录接口：接收用户名和密码，验证后返回 API Key
    密码统一为"secret"，作为示例
    """
    username = data.username.strip()
    password = data.password.strip()
    
    if not username or not password:
        return 400, {"error": "用户名和密码不能为空"}
    
    if password != 'secret':
        return 403, {"error": "密码错误"}
    
    key = services.create_api_key(username)
    return {"api_key": key, "expiry": settings.TOKEN_EXPIRY_SECONDS}

@router.post("/chat", response={200: ChatOut, 401: ErrorResponse})
def chat(request, data: ChatIn):
    print("=" * 80)
    print("🚀 [数据流追踪] 开始处理 Chat 请求")
    print("=" * 80)
    
    # 1. 认证验证（确保用户已登录）
    if not request.auth:
        print("❌ [认证失败] 未提供有效的API Key")
        return 401, {"error": "请先登录获取API Key"}
    
    print(f"✅ [认证成功] 用户: {request.auth.user}, API Key: {request.auth.key[:8]}...")
    
    # 2. 解析参数（确保 session_id 有效）
    session_id = data.session_id.strip() or "default_session"
    user_input = data.user_input.strip()
    query_type = data.query_type or "analysis"  # 获取查询类型，默认为 analysis
    
    print(f"📝 [请求参数] session_id: '{session_id}', query_type: '{query_type}'")
    print(f"📝 [用户输入] {user_input}")
    
    if not user_input:
        print("❌ [参数错误] 用户输入为空")
        return 400, {"error": "请输入消息内容"}
    
    # 3. 获取会话（加载旧会话或创建新会话）
    user = request.auth  # 从认证获取当前用户（APIKey对象）
    print(f"\n🔍 [会话查询] 正在获取会话 session_id='{session_id}', user='{user.user}'")
    session = get_or_create_session(session_id, user)
    
    print(f"📊 [会话状态] 会话ID: {session.session_id}")
    print(f"📊 [会话用户] {session.user.user}")
    print(f"📊 [历史长度] {len(session.context)} 字符")
    if session.context:
        print(f"📊 [历史内容预览] {session.context[:200]}{'...' if len(session.context) > 200 else ''}")
    else:
        print("📊 [历史内容] 空（新会话）")
    
    # 4. 拼接上下文（历史记录 + 当前输入）→ 关键！
    # 若 session.context 不为空，说明是旧会话（带历史）
    # 从session获取纯净的对话历史（仅用户输入和回复）
    pure_context = session.context
    # 拼接prompt：纯历史 + 当前用户输入（不含时间戳）
    prompt = pure_context + f"用户：{user_input}\n回复："
    
    print(f"\n🔧 [上下文构建]")
    print(f"   历史上下文长度: {len(pure_context)} 字符")
    print(f"   完整prompt长度: {len(prompt)} 字符")
    print(f"🔧 [完整Prompt] ↓↓↓")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    
    logger.info(f"传递给大模型的prompt：\n{prompt}")  # 调试日志
    logger.info(f"查询类型：{query_type}")  # 记录查询类型
    
    # 5. 调用大模型（带完整上下文）
    # 获取缓存时传入session_id和user
    print(f"\n🔍 [缓存检查] 检查是否有缓存回复...")
    cached_reply = get_cached_reply(prompt, session_id, user)
    if cached_reply:
        reply = cached_reply
        print(f"✅ [缓存命中] 使用缓存回复，长度: {len(reply)} 字符")
        print(f"💾 [缓存回复] {reply[:100]}{'...' if len(reply) > 100 else ''}")
    else:
        print(f"❌ [缓存未命中] 调用大模型API...")
        reply = deepseek_r1_api_call(prompt, query_type)  # 传递 query_type
        print(f"🤖 [大模型回复] 长度: {len(reply)} 字符")
        print(f"🤖 [回复内容] {reply[:100]}{'...' if len(reply) > 100 else ''}")
        # 设置缓存时传入session_id和user
        set_cached_reply(prompt, reply, session_id, user)
        print(f"💾 [缓存保存] 回复已缓存")
    
    # 6. 保存上下文到会话（更新历史记录）
    print(f"\n💾 [上下文更新] 保存新的对话到数据库...")
    old_context_length = len(session.context)
    new_entry = f"用户：{user_input}\n回复：{reply}\n"
    session.context += new_entry
    new_context_length = len(session.context)
    
    print(f"💾 [内存更新] 上下文长度: {old_context_length} → {new_context_length} 字符")
    print(f"💾 [新增条目] {new_entry.strip()}")
    print(f"💾 [数据库保存] 调用 session.save() 持久化到数据库...")
    
    session.save()  # 持久化到数据库
    
    print(f"💾 [保存完成] 会话已成功保存到数据库")
    print(f"💾 [最终状态] 会话ID: {session.session_id}, 总长度: {len(session.context)} 字符")
    
    # session.update_context(user_input, reply)
    
    print(f"\n✅ [请求完成] 返回回复给前端")
    print("=" * 80)

    return {
        "reply": reply,
        # 前端需要的时间戳由前端生成，后端可返回当前时间供参考
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

# 1. 修复 history 接口
@router.get("/history", response={200: HistoryOut})
def history(request, session_id: str = "default_session"):
    """查看对话历史接口：根据session_id返回对话历史"""
    print("=" * 80)
    print("📚 [历史查询] 开始处理 History 请求")
    print("=" * 80)
    
    # 直接使用 session_id 参数，无需通过 data
    processed_session_id = session_id.strip() or "default_session"
    user_api_key = request.auth.key
    
    print(f"📚 [查询参数] session_id: '{processed_session_id}'")
    print(f"📚 [用户信息] user: '{request.auth.user}', API Key: {user_api_key[:8]}...")
    
    session = services.get_or_create_session(processed_session_id, request.auth)
    
    print(f"📚 [历史内容] 长度: {len(session.context)} 字符")
    if session.context:
        print(f"📚 [内容预览] {session.context[:200]}{'...' if len(session.context) > 200 else ''}")
    else:
        print("📚 [内容预览] 空（无历史记录）")
    
    print(f"📚 [返回结果] 历史记录已准备完毕")
    print("=" * 80)
    
    return {"history": session.context}


# 2. 修复 clear_history 接口
@router.delete("/history", response={200: dict})
def clear_history(request, session_id: str = "default_session"):
    """清空对话历史接口"""
    print("=" * 80)
    print("🗑️ [历史清空] 开始处理 Clear History 请求")
    print("=" * 80)
    
    # 直接使用 session_id 参数，无需通过 data
    processed_session_id = session_id.strip() or "default_session"
    user_api_key = request.auth.key
    
    print(f"🗑️ [清空参数] session_id: '{processed_session_id}'")
    print(f"🗑️ [用户信息] user: '{request.auth.user}', API Key: {user_api_key[:8]}...")
    
    session = services.get_or_create_session(processed_session_id, request.auth)
    
    print(f"🗑️ [清空前状态] 历史长度: {len(session.context)} 字符")
    if session.context:
        print(f"🗑️ [清空前内容] {session.context[:100]}{'...' if len(session.context) > 100 else ''}")
    
    session.clear_context()
    
    print(f"🗑️ [清空完成] 历史记录已清空")
    print(f"🗑️ [清空后状态] 历史长度: {len(session.context)} 字符")
    print("=" * 80)
    
    return {"message": "历史记录已清空"}

# 将路由添加到API
api.add_router("", router)
