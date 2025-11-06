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
          <button
            class="action-button secondary"
            @click="clearInput"
            :disabled="!message.trim() || loading"
          >
            清除
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

const sendMessage = () => {
  const content = message.value.trim();
  if (content) {
    emits("send", content, selectedQueryType.value);
    message.value = "";
  }
};

// 处理日志分析按钮点击
const handleAnalysis = () => {
  // 日志分析模式下，使用默认提示词
  emits("send", "分析系统日志", "analysis");
};

const stopGeneration = () => {
  emits("stop");
};

const clearInput = () => {
  message.value = "";
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
}

/* 日志分析模式 */
.analysis-mode {
  display: flex;
  gap: 0.75rem;
  align-items: stretch;
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
  transition: all 0.2s ease;
  box-shadow: var(--shadow);
}

.analysis-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.15), 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.analysis-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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
  flex: 1;
  min-height: 80px;
  max-height: 200px;
  resize: vertical;
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--input-border);
  border-radius: var(--radius);
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.2s ease;
  line-height: 1.5;
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
