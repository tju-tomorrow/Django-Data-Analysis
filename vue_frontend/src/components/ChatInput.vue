<template>
  <div class="chat-input-container">
    <div class="input-top-row">
      <select
        v-model="selectedQueryType"
        class="query-type-select"
        :disabled="loading"
      >
        <option value="general_chat">日常聊天</option>
        <option value="analysis">日志分析</option>
      </select>
      
      <!-- 日志分析模式：显示按钮 -->
      <div v-if="selectedQueryType === 'analysis'" class="analysis-mode">
        <button
          class="analysis-button primary"
          @click="handleAnalysis"
          :disabled="loading"
        >
          {{ loading ? '正在分析...' : '点击进行日志分析' }}
        </button>
        <button
          v-if="loading"
          class="danger"
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
            class="secondary"
            @click="clearInput"
            :disabled="!message.trim() || loading"
          >
            清除
          </button>
          <button
            v-if="!loading"
            class="primary"
            @click="sendMessage"
            :disabled="!message.trim()"
          >
            发送
          </button>
          <button
            v-else
            class="danger"
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
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.input-top-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  flex-wrap: nowrap;
  width: 100%;
}

.analysis-mode {
  flex: 1;
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
  width: 100%;
}

.analysis-button {
  flex: 1;
  min-height: 80px;
  font-size: 1rem;
  font-weight: 500;
  padding: 1rem;
  white-space: normal;
  word-wrap: break-word;
}

.analysis-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.query-type-select {
  padding: 0.5rem;
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  background-color: var(--input-bg);
  color: var(--text-color);
  cursor: pointer;
  height: 80px; /* Make it consistent with the textarea/button height */
  flex-shrink: 0; /* 防止下拉框被压缩 */
}

.query-type-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-input {
  flex: 1; /* Allow textarea to take available space */
  min-height: 80px;
  resize: vertical;
  width: 100%;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.loading {
  margin-right: 0.5rem;
  vertical-align: middle;
}
</style>
