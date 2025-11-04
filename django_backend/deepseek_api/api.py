from ninja import NinjaAPI, Router
# from ninja.security import BaseAuth
from django.http import HttpRequest
from typing import Optional
from . import services
from django.conf import settings
from .schemas import LoginIn, LoginOut, ChatIn, ChatOut, HistoryOut, ErrorResponse
from .models import APIKey
from .services import get_or_create_session, deepseek_r1_api_call, get_cached_reply, set_cached_reply
from .conversation_manager import ConversationManager, ConversationType
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

# 初始化对话管理器
conversation_manager = ConversationManager(max_context_length=4000, max_turns=10)

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
    
    # 4. 智能上下文管理 → 新增！
    print(f"\n🧠 [智能对话管理] 开始分析对话类型和上下文...")
    
    # 解析历史对话
    historical_turns = conversation_manager.parse_conversation_history(session.context)
    print(f"🧠 [历史解析] 解析出 {len(historical_turns)} 轮历史对话")
    
    # 使用轻量级模型分类当前对话类型
    conversation_type, classification_details = conversation_manager.classify_conversation_type(user_input, len(historical_turns) > 0)
    print(f"🧠 [智能分类] 对话类型: {conversation_type.value}")
    print(f"🧠 [分类详情] 意图: {classification_details['intent_type']}, 置信度: {classification_details['confidence']:.3f}")
    print(f"🧠 [模型信息] 使用模型: {classification_details['model_used']}, 耗时: {classification_details['processing_time']:.3f}秒")
    
    # 压缩历史上下文
    compressed_turns = conversation_manager.compress_context(historical_turns)
    print(f"🧠 [上下文压缩] 压缩后保留 {len(compressed_turns)} 轮对话")
    
    # 使用意图分类结果判断是否需要RAG检索
    use_rag, rag_decision = conversation_manager.should_use_rag(conversation_type, user_input, classification_details)
    
    # 根据前端选择的查询类型决定是否使用RAG
    if query_type == "general_chat":
        # 日常聊天模式，不使用RAG
        use_rag = False
        rag_decision['decision_reason'] = "前端选择日常聊天模式，不使用RAG检索"
        print(f"💬 [日常聊天] 前端选择日常聊天模式，跳过RAG检索")
    elif query_type == "analysis":
        # 日志分析模式，使用RAG
        use_rag = True
        rag_decision['decision_reason'] = "前端选择日志分析模式，使用RAG检索"
        print(f"🔍 [日志分析] 前端选择日志分析模式，使用RAG检索")
    else:
        # 默认使用意图分类器的判断结果
        # 对于明显的通用聊天问题（GENERAL_QA、GREETING），跳过RAG
        from .intent_classifier import IntentType
        intent_type_str = classification_details.get('intent_type', '')
        is_general_chat_intent = intent_type_str in ['general_qa', 'greeting']
        
        if is_general_chat_intent:
            use_rag = False
            rag_decision['decision_reason'] = f"意图分类为通用聊天（{intent_type_str}），跳过RAG检索"
            print(f"💬 [跳过RAG] 意图分类为通用聊天（{intent_type_str}），跳过RAG检索")
    
    print(f"🧠 [智能RAG决策] 使用RAG: {use_rag}")
    print(f"🧠 [决策原因] {rag_decision['decision_reason']}")
    print(f"🧠 [决策详情] 意图置信度: {rag_decision['intent_confidence']:.3f}, 意图类型: {rag_decision['intent_type']}")
    
    # 构建LLM上下文
    llm_context = conversation_manager.build_context_for_llm(compressed_turns, user_input, conversation_type)
    
    print(f"\n🔧 [上下文构建]")
    print(f"   原始历史长度: {len(session.context)} 字符")
    print(f"   压缩后长度: {len(llm_context)} 字符")
    print(f"   对话类型: {conversation_type.value}")
    print(f"   使用RAG: {use_rag}")
    print(f"🔧 [LLM上下文] ↓↓↓")
    print("-" * 60)
    print(llm_context)
    print("-" * 60)
    
    # 根据对话类型选择不同的处理逻辑
    if use_rag:
        # 使用RAG + 对话历史
        prompt = llm_context  # 对话历史作为基础上下文
        print(f"🔧 [RAG模式] 将使用对话历史 + RAG检索结果")
    else:
        # 纯对话模式，不使用RAG
        prompt = llm_context
        print(f"🔧 [对话模式] 仅使用对话历史，不进行RAG检索")
    
    logger.info(f"传递给大模型的prompt：\n{prompt}")  # 调试日志
    logger.info(f"查询类型：{query_type}")  # 记录查询类型
    
    # 5. 调用大模型（根据模式选择不同策略）
    print(f"\n🔍 [缓存检查] 检查是否有缓存回复...")
    cached_reply = get_cached_reply(prompt, session_id, user)
    if cached_reply:
        reply = cached_reply
        print(f"✅ [缓存命中] 使用缓存回复，长度: {len(reply)} 字符")
        print(f"💾 [缓存回复] {reply[:100]}{'...' if len(reply) > 100 else ''}")
    else:
        print(f"❌ [缓存未命中] 调用大模型API...")
        
        if use_rag:
            # RAG模式：传递原始用户查询给RAG系统（RAG系统会自己检索日志）
            print(f"🔍 [RAG模式] 使用RAG检索 + 对话历史")
            print(f"🔍 [RAG查询] 原始查询: '{user_input}'")
            print(f"🔍 [RAG查询] 查询类型: '{query_type}'")
            # RAG系统会基于用户查询检索日志，然后结合对话历史生成回答
            # 将用户查询和对话历史都传递给RAG系统
            rag_query = user_input  # RAG系统使用原始查询进行检索
            reply = deepseek_r1_api_call(rag_query, query_type)  # RAG系统会处理检索
        else:
            # 纯对话模式：直接调用大模型，不使用RAG检索
            print(f"💬 [对话模式] 纯对话，不使用RAG检索")
            print(f"💬 [对话查询] 查询: '{user_input}'")
            # 这里可以调用一个简化的LLM接口，不进行RAG检索
            reply = deepseek_r1_api_call(prompt, "general_chat")  # 使用通用对话模式
        
        print(f"🤖 [大模型回复] 长度: {len(reply)} 字符")
        print(f"🤖 [回复内容] {reply[:100]}{'...' if len(reply) > 100 else ''}")
        
        # 设置缓存时传入session_id和user
        set_cached_reply(prompt, reply, session_id, user)
        print(f"💾 [缓存保存] 回复已缓存")
    
    # 6. 智能上下文保存 → 改进！
    print(f"\n💾 [智能上下文保存] 使用对话管理器更新历史...")
    
    # 添加新的对话轮次
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = {
        "query_type": query_type,
        "conversation_type": conversation_type.value,
        "used_rag": use_rag,
        "original_turns": len(historical_turns),
        "compressed_turns": len(compressed_turns),
        # 新增：意图分类详情
        "intent_classification": classification_details,
        "rag_decision": rag_decision
    }
    
    updated_turns = conversation_manager.add_new_turn(
        compressed_turns, user_input, reply, conversation_type, timestamp, metadata
    )
    
    print(f"💾 [对话轮次] 添加新轮次，当前总轮次: {len(updated_turns)}")
    print(f"💾 [元数据] {metadata}")
    
    # 格式化为存储字符串
    new_context = conversation_manager.format_context_for_storage(updated_turns)
    old_context_length = len(session.context)
    new_context_length = len(new_context)
    
    print(f"💾 [上下文更新] 长度变化: {old_context_length} → {new_context_length} 字符")
    print(f"💾 [压缩效果] 压缩比: {new_context_length/max(old_context_length, 1):.2f}")
    
    # 更新会话
    session.context = new_context
    session.save()
    
    print(f"💾 [保存完成] 智能上下文已保存到数据库")
    print(f"💾 [最终状态] 会话ID: {session.session_id}, 轮次: {len(updated_turns)}, 长度: {len(session.context)} 字符")
    
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
