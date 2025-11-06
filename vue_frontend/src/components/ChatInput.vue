<template>
  <div class="chat-input-container">
    <!-- 模式切换标签页 -->
    <div class="mode-tabs">
      <button
        class="tab-button"
        :class="{ active: selectedQueryType === 'general_chat' }"
        @click="selectedQueryType = 'general_chat'"
        :disabled="loading"
      >
        <span class="tab-icon">💬</span>
        <span class="tab-label">日常聊天</span>
      </button>
      <button
        class="tab-button"
        :class="{ active: selectedQueryType === 'analysis' }"
        @click="selectedQueryType = 'analysis'"
        :disabled="loading"
      >
        <span class="tab-icon">📊</span>
        <span class="tab-label">日志分析</span>
      </button>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <!-- 日志分析模式：显示按钮 -->
      <div v-if="selectedQueryType === 'analysis'" class="analysis-mode">
        <button
          class="analysis-button primary"
          @click="handleAnalysis"
          :disabled="loading"
        >
          <span v-if="!loading" class="button-content">
            <span class="button-icon">🔍</span>
            <span>点击进行日志分析</span>
          </span>
          <span v-else class="button-content">
            <span class="spinner"></span>
            <span>正在分析...</span>
          </span>
        </button>
        <button
          v-if="loading"
          class="stop-button danger"
          @click="stopGeneration"
        >
          停止生成
        </button>
      </div>
      
      <!-- 日常聊天模式：显示输入框 -->
      <template v-else>
        <textarea
          v-model="message"
          class="chat-input"
          placeholder="输入消息..."
          @keyup.enter.exact="sendMessage"
          @keyup.enter.shift="addNewline"
          :disabled="loading"
        ></textarea>
        <div class="input-actions">
          <!-- 联网搜索开关（暂不支持） -->
          <button
            class="web-search-toggle tooltip-container"
            :disabled="true"
            type="button"
          >
            <span class="web-search-icon">🌐</span>
            <span class="web-search-label">离线</span>
            <span class="tooltip">deepseek-api暂不支持联网</span>
          </button>
          <button
            v-if="!loading"
            class="action-button primary"
            @click="sendMessage"
            :disabled="!message.trim()"
          >
            发送
          </button>
          <button
            v-else
            class="action-button danger"
            @click="stopGeneration"
          >
            停止生成
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from "vue";

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});

const emits = defineEmits(["send", "stop"]);

const message = ref("");
const selectedQueryType = ref("general_chat"); // 默认查询类型改为日常聊天
const webSearchEnabled = ref(false); // 联网搜索开关

const sendMessage = () => {
  const content = message.value.trim();
  if (content) {
    // 只在日常聊天模式下传递web_search参数
    const webSearch = selectedQueryType.value === "general_chat" ? webSearchEnabled.value : false;
    emits("send", content, selectedQueryType.value, webSearch);
    message.value = "";
  }
};

const toggleWebSearch = (event) => {
  if (!props.loading) {
    webSearchEnabled.value = !webSearchEnabled.value;
    // 点击后移除焦点，避免按钮保持激活状态
    if (event && event.target) {
      event.target.blur();
    }
  }
};

// 处理日志分析按钮点击
const handleAnalysis = () => {
  // 日志分析模式下，使用默认提示词，不启用联网搜索
  emits("send", "分析系统日志", "analysis", false);
};

const stopGeneration = () => {
  emits("stop");
};

const addNewline = () => {
  message.value += "\n";
};
</script>

<style scoped>
.chat-input-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--card-bg);
}

/* 模式切换标签页 */
.mode-tabs {
  display: flex;
  gap: 0.5rem;
  background-color: var(--bg-secondary);
  padding: 0.25rem;
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: transparent;
  border: none;
  border-radius: calc(var(--radius) - 2px);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.tab-button:hover:not(:disabled) {
  background-color: var(--hover-color);
  color: var(--text-primary);
}

.tab-button.active {
  background-color: var(--card-bg);
  color: var(--primary-color);
  box-shadow: var(--shadow);
  font-weight: 600;
}

.tab-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.tab-label {
  white-space: nowrap;
}

/* 输入区域 */
.input-area {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 160px; /* 固定最小高度，确保两种模式高度一致 */
  position: relative; /* 确保内容定位正确 */
}

/* 日志分析模式 */
.analysis-mode {
  display: flex;
  gap: 0.75rem;
  align-items: stretch;
  min-height: 160px; /* 与日常聊天模式高度一致 */
  justify-content: center; /* 垂直居中 */
}

.analysis-button {
  flex: 1;
  min-height: 80px;
  font-size: 1rem;
  font-weight: 500;
  padding: 1rem 1.5rem;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
  
  /* 渐变背景 */
  background: linear-gradient(135deg, 
    rgba(79, 70, 229, 0.1) 0%, 
    rgba(99, 102, 241, 0.15) 50%, 
    rgba(139, 92, 246, 0.1) 100%);
  color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.1), 
              inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.analysis-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.2), 
    transparent);
  transition: left 0.5s ease;
}

.analysis-button:hover:not(:disabled)::before {
  left: 100%;
}

.analysis-button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: linear-gradient(135deg, 
    rgba(79, 70, 229, 0.15) 0%, 
    rgba(99, 102, 241, 0.2) 50%, 
    rgba(139, 92, 246, 0.15) 100%);
  box-shadow: 0 4px 16px rgba(79, 70, 229, 0.2), 
              0 2px 8px rgba(79, 70, 229, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-color: rgba(79, 70, 229, 0.3);
}

.analysis-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  background: linear-gradient(135deg, 
    rgba(79, 70, 229, 0.05) 0%, 
    rgba(99, 102, 241, 0.08) 50%, 
    rgba(139, 92, 246, 0.05) 100%);
}

.button-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  z-index: 1; /* 确保内容在渐变层之上 */
}

.button-icon {
  font-size: 1.2rem;
}

.stop-button {
  min-width: 100px;
  min-height: 80px;
  font-weight: 500;
  border-radius: var(--radius);
  transition: all 0.2s ease;
}

.stop-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

/* 加载动画 */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 日常聊天模式 */
.chat-input {
  width: 100%;
  min-height: 80px;
  max-height: 200px;
  resize: vertical;
  padding: 0.75rem 1rem;
  border: 1px solid var(--input-border);
  border-radius: var(--radius);
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.2s ease;
  line-height: 1.5;
  flex: 1; /* 占据可用空间 */
}

.web-search-toggle {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  height: 44px;
  background-color: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  font-weight: 500;
  outline: none;
  white-space: nowrap;
}

.web-search-toggle:hover:not(:disabled) {
  background-color: var(--hover-color);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: translateY(-1px);
}

.web-search-toggle:focus {
  outline: none;
  box-shadow: none;
}

.web-search-toggle.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
  box-shadow: var(--shadow);
}

.web-search-toggle.active:hover:not(:disabled) {
  background-color: var(--primary-dark);
  border-color: var(--primary-dark);
}

.web-search-toggle.active:focus {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  box-shadow: var(--shadow);
}

.web-search-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  background-color: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.web-search-toggle:disabled:hover {
  background-color: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-secondary);
  transform: none;
}

/* 自定义 Tooltip 样式 */
.tooltip-container {
  position: relative;
}

.tooltip {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  background-color: rgba(30, 41, 59, 0.95);
  color: #ffffff;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateX(-50%) translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  font-weight: 500;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(30, 41, 59, 0.95);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.tooltip-container:hover .tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
  pointer-events: auto;
}

.tooltip-container:disabled:hover .tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.web-search-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.web-search-label {
  font-size: 0.85rem;
  white-space: nowrap;
}

.chat-input:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.75rem;
}

.action-button {
  padding: 0.75rem 1.5rem;
  font-weight: 500;
  border-radius: var(--radius);
  transition: all 0.2s ease;
  min-width: 80px;
}

.action-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tab-label {
    font-size: 0.85rem;
  }
  
  .tab-icon {
    font-size: 1rem;
  }
  
  .analysis-button,
  .stop-button {
    min-height: 60px;
    font-size: 0.9rem;
  }
  
  .chat-input {
    min-height: 60px;
  }
}
</style>
