<template>
  <div class="chat-container">
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <SessionList
        :sessions="sessions"
        :current-session="currentSession"
        @select="handleSelectSession"
        @delete="handleDeleteSession"
        @create="handleCreateSession"
      />

      <div class="user-info">
        <div class="user-actions">
          <button class="secondary" @click="handleClearHistory">
            清空当前会话
          </button>
          <button class="danger" @click="handleLogout">退出登录</button>
        </div>
      </div>
    </div>

    <div class="chat-area">
      <div class="chat-header">
        <button 
          class="sidebar-toggle-btn" 
          @click="toggleSidebar"
          :title="sidebarCollapsed ? '展开会话栏' : '收起会话栏'"
        >
          <svg v-if="sidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <polyline points="9 6 15 12 9 18"></polyline>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="21" y1="12" x2="3" y2="12"></line>
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
        
        <div class="header-center">
          <h1 class="header-title">
            <span class="title-main">LogOracle</span>
            <span class="subtitle-cn">日志神谕</span>
          </h1>
          <p class="header-desc">智能日志分析平台 · 洞察系统真相</p>
          <h2 class="header-session">当前会话: {{ currentSession }}</h2>
        </div>
        
        <button class="settings-btn" @click="showSettings = true" title="设置">
          ⚙️
        </button>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="messages-container">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="welcome-content">
            <h3>欢迎使用 LogOracle 日志神谕</h3>
            <p>基于 RAG 技术的智能日志分析平台</p>
            <div class="features">
              <div class="feature-item">🔍 智能检索</div>
              <div class="feature-item">💡 深度分析</div>
              <div class="feature-item">🎯 精准诊断</div>
              <div class="feature-item">📊 多维度洞察</div>
            </div>
            <p class="start-hint">开始提问，让 LogOracle 为您揭示日志中的真相</p>
          </div>
        </div>

        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :is-user="msg.isUser"
          :content="msg.content"
          :timestamp="msg.timestamp"
        />

        <div v-if="loading" class="loading-indicator">
          <div class="loading"></div>
          <p>LogOracle 正在分析日志，洞察真相中...</p>
        </div>
      </div>

      <ChatInput :loading="loading" @send="handleSendMessage" @stop="handleStopGeneration" />
    </div>

    <!-- 设置弹窗 -->
    <Settings v-if="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useStore } from "../store";
import api from "../api";
import SessionList from "../components/SessionList.vue";
import ChatMessage from "../components/ChatMessage.vue";
import ChatInput from "../components/ChatInput.vue";
import Settings from "../components/Settings.vue";

const store = useStore();
const router = useRouter();

// 用于取消流式请求的 AbortController
let abortController = null;

// 设置弹窗显示状态
const showSettings = ref(false);

// 侧边栏收起状态（默认收起）
const sidebarCollapsed = ref(true);

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value.toString());
};

// 从 localStorage 恢复侧边栏状态
onMounted(() => {
  const saved = localStorage.getItem('sidebarCollapsed');
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true';
  }
  loadHistory(currentSession.value);
});

// 计算属性
const sessions = computed(() => store.sessions);
const currentSession = computed(() => store.currentSession);
const messages = computed(() => store.messages[currentSession.value] || []);
const loading = computed(() => store.loading);
const error = computed(() => store.error);

// 初始化加载历史记录
const loadHistory = async (sessionId) => {
  try {
    store.setLoading(true);
    const response = await api.getHistory(sessionId);
    store.loadHistory(sessionId, response.data.history);
  } catch (err) {
    store.setError(err.response?.data?.error || "加载历史记录失败");
  } finally {
    store.setLoading(false);
  }
};


// 处理选择会话
const handleSelectSession = async (sessionId) => {
  store.setCurrentSession(sessionId);
  await loadHistory(sessionId);
};

// 处理删除会话
const handleDeleteSession = async (sessionId) => {
  try {
    await api.clearHistory(sessionId);
    store.removeSession(sessionId);
    store.clearSessionMessages(sessionId);
  } catch (err) {
    store.setError(err.response?.data?.error || "删除会话失败");
  }
};

// 处理创建会话
const handleCreateSession = (sessionId) => {
  store.addSession(sessionId);
  store.clearSessionMessages(sessionId);
};

// 处理发送消息
const handleSendMessage = async (content, queryType) => {
  try {
    store.setLoading(true);
    
    // 创建新的 AbortController
    abortController = new AbortController();
    
    // 1. 先添加用户消息到界面
    const userMessageId = Date.now();
    store.addMessage(currentSession.value, true, content, userMessageId);
    
    // 2. 等待一小段时间，确保用户消息 ID 和 AI 消息 ID 不同
    await new Promise(resolve => setTimeout(resolve, 10));
    
    // 3. 添加一个空的 AI 回复消息占位，用于流式更新
    const botMessageId = Date.now();
    store.addMessage(currentSession.value, false, "", botMessageId);
    
    // 4. 使用流式 API，逐步更新 AI 回复
    await api.chatStream(
      currentSession.value,
      content,
      queryType,
      abortController.signal,  // 传递取消信号
      // onMessage: 收到增量内容时更新 AI 消息
      (fullContent) => {
        store.updateMessage(currentSession.value, botMessageId, fullContent);
      },
      // onError: 错误处理
      (error) => {
        if (error !== 'AbortError') {  // 忽略取消错误
          store.setError(error);
        }
        store.setLoading(false);
        abortController = null;
      },
      // onComplete: 完成
      (finalContent) => {
        store.updateMessage(currentSession.value, botMessageId, finalContent);
        store.setLoading(false);
        abortController = null;
      }
    );
  } catch (err) {
    if (err.name !== 'AbortError') {  // 忽略取消错误
      store.setError(err.message || "发送消息失败");
    }
    store.setLoading(false);
    abortController = null;
  }
};

// 处理停止生成
const handleStopGeneration = () => {
  if (abortController) {
    abortController.abort();
    
    // 找到最后一条 AI 消息，添加停止提示
    const sessionMessages = store.messages[currentSession.value];
    if (sessionMessages && sessionMessages.length > 0) {
      const lastMessage = sessionMessages[sessionMessages.length - 1];
      if (!lastMessage.isUser) {
        // 在 AI 回复后添加停止提示
        const currentContent = lastMessage.content || '';
        const updatedContent = currentContent + '\n\n---\n_用户停止生成_';
        store.updateMessage(currentSession.value, lastMessage.id, updatedContent);
      }
    }
    
    store.setLoading(false);
    abortController = null;
  }
};

// 处理清空历史
const handleClearHistory = async () => {
  if (confirm(`确定要清空当前会话 "${currentSession.value}" 的历史记录吗？`)) {
    try {
      await api.clearHistory(currentSession.value);
      store.clearSessionMessages(currentSession.value);
    } catch (err) {
      store.setError(err.response?.data?.error || "清空历史记录失败");
    }
  }
};

// 处理退出登录
const handleLogout = () => {
  if (confirm("确定要退出登录吗？")) {
    store.clearApiKey();
    router.push("/login");
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  overflow: hidden; /* 防止整体页面被撑宽 */
  max-width: 100vw; /* 限制最大宽度为视口宽度 */
}

.sidebar {
  width: 300px;
  min-width: 300px;
  max-width: 300px;
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg);
  border-right: 1px solid var(--border-color);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
              opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              max-width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  z-index: 1;
  will-change: transform, opacity, width;
  opacity: 1;
}

.sidebar.collapsed {
  transform: translate3d(-100%, 0, 0);
  width: 0;
  min-width: 0;
  max-width: 0;
  opacity: 0;
  border-right: none;
  pointer-events: none;
}

/* 侧边栏内容动画 */
.sidebar > * {
  transition: opacity 0.2s ease, transform 0.2s ease;
  opacity: 1;
  transform: translateX(0);
}

.sidebar.collapsed > * {
  opacity: 0;
  transform: translateX(-10px);
  pointer-events: none;
}

.user-info {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  animation: fadeInUp 0.3s ease-out 0.2s backwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-actions {
  display: flex;
  gap: 0.5rem;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  min-width: 0; /* 关键：允许flex子元素缩小 */
  overflow: hidden; /* 防止内容溢出 */
}

.chat-header {
  padding: 1.5rem 1rem;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.sidebar-toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--text-primary);
  flex-shrink: 0;
  position: absolute;
  left: 1rem;
  z-index: 10;
  will-change: transform;
}

.sidebar-toggle-btn:hover {
  background-color: var(--hover-color);
  transform: scale3d(1.1, 1.1, 1);
}

.header-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  animation: fadeInUp 0.4s ease-out;
  will-change: transform, opacity;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translate3d(0, 10px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.header-title {
  color: var(--primary-color);
  margin: 0;
  font-size: 2rem;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  animation: fadeInUp 0.4s ease-out 0.05s both;
  will-change: transform, opacity;
}

.title-main {
  font-weight: 700;
  letter-spacing: -0.02em;
}

.subtitle-cn {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 400;
  font-style: italic;
  opacity: 0.9;
}

.header-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 400;
  margin-bottom: 0.5rem;
  animation: fadeInUp 0.4s ease-out 0.1s both;
  letter-spacing: 0.02em;
  will-change: transform, opacity;
}

.header-session {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin: 0;
  padding: 0.25rem 0.75rem;
  background-color: var(--bg-secondary);
  border-radius: 12px;
  display: inline-block;
  animation: fadeInUp 0.4s ease-out 0.15s both;
  transition: background-color 0.2s ease, transform 0.2s ease;
  will-change: transform, opacity;
}

.header-session:hover {
  background-color: var(--hover-color);
  transform: translate3d(0, -1px, 0);
}

.messages-container {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 关键：允许flex子元素缩小 */
  max-width: 100%; /* 限制最大宽度为父容器的100% */
  /* 优化滚动性能 */
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  contain: layout style paint;
}

.empty-state {
  margin: auto;
  color: var(--text-secondary);
  text-align: center;
  padding: 2rem;
  max-width: 600px;
}

.welcome-content h3 {
  color: var(--primary-color);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.welcome-content > p {
  font-size: 1rem;
  margin-bottom: 1.5rem;
  color: var(--text-secondary);
}

.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  margin: 1.5rem 0;
}

.feature-item {
  padding: 0.5rem 1rem;
  background-color: var(--card-bg);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  border: 1px solid var(--border-color);
}

.start-hint {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-top: 1.5rem;
  font-style: italic;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem auto;
  color: var(--text-secondary);
}

.settings-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--text-primary);
  position: absolute;
  right: 1rem;
  z-index: 10;
  will-change: transform;
}

.settings-btn:hover {
  background-color: var(--hover-color);
  transform: scale3d(1.1, 1.1, 1) rotate(90deg);
}
</style>
