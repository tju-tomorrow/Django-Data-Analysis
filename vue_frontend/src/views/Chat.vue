<template>
  <div class="chat-container">
    <div class="sidebar">
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
        <div class="header-left">
          <h1>DeepSeek-KAI.v.0.0.1 聊天</h1>
          <h2>当前会话: {{ currentSession }}</h2>
        </div>
        <button class="settings-btn" @click="showSettings = true" title="设置">
          ⚙️
        </button>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="messages-container">
        <div v-if="messages.length === 0" class="empty-state">
          开始与 DeepSeek-KAI.v.0.0.1 的对话吧！
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
          <p>DeepSeek-KAI.v.0.0.1 正在思考...</p>
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

// 挂载时加载当前会话历史
onMounted(() => {
  loadHistory(currentSession.value);
});

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
const handleSendMessage = async (content, queryType, webSearch = false) => {
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
      webSearch,  // 传递联网搜索标志
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
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg);
  border-right: 1px solid var(--border-color);
}

.user-info {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
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
  padding: 1rem;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  color: var(--primary-color);
  margin-bottom: 0.25rem;
}

.header-left h2 {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.messages-container {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 关键：允许flex子元素缩小 */
  max-width: 100%; /* 限制最大宽度为父容器的100% */
}

.empty-state {
  margin: auto;
  color: var(--text-secondary);
  font-size: 1.25rem;
  text-align: center;
  padding: 2rem;
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
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
}

.settings-btn:hover {
  background-color: var(--hover-color);
}
</style>
