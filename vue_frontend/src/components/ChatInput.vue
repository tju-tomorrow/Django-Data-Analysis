<template>
  <div class="chat-input-wrapper">
    <select
      v-model="selectedQueryType"
      class="query-type-select"
      :disabled="loading"
    >
      <option value="analysis">日志分析</option>
      <option value="general_chat">日常聊天</option>
    </select>
    <div class="messageBox">
      <div class="fileUploadWrapper">
        <label for="file">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 337 337">
            <circle
              stroke-width="20"
              stroke="#6c6c6c"
              fill="none"
              r="158.5"
              cy="168.5"
              cx="168.5"
            ></circle>
            <path
              stroke-linecap="round"
              stroke-width="25"
              stroke="#6c6c6c"
              d="M167.759 79V259"
            ></path>
            <path
              stroke-linecap="round"
              stroke-width="25"
              stroke="#6c6c6c"
              d="M79 167.138H259"
            ></path>
          </svg>
          <span class="tooltip">添加文件</span>
        </label>
        <input type="file" id="file" name="file" @change="handleFileUpload" />
      </div>
      <input
        required=""
        v-model="message"
        placeholder="输入消息..."
        type="text"
        id="messageInput"
        @keyup.enter.exact="sendMessage"
        :disabled="loading"
      />
      <button
        v-if="!loading"
        id="sendButton"
        @click="sendMessage"
        :disabled="!message.trim()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 664 663">
          <path
            fill="none"
            d="M646.293 331.888L17.7538 17.6187L155.245 331.888M646.293 331.888L17.753 646.157L155.245 331.888M646.293 331.888L318.735 330.228L155.245 331.888"
          ></path>
          <path
            stroke-linejoin="round"
            stroke-linecap="round"
            stroke-width="33.67"
            stroke="#6c6c6c"
            d="M646.293 331.888L17.7538 17.6187L155.245 331.888M646.293 331.888L17.753 646.157L155.245 331.888M646.293 331.888L318.735 330.228L155.245 331.888"
          ></path>
        </svg>
      </button>
      <button
        v-else
        id="sendButton"
        @click="stopGeneration"
        class="stop-button"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 664 663">
          <path
            fill="none"
            d="M646.293 331.888L17.7538 17.6187L155.245 331.888M646.293 331.888L17.753 646.157L155.245 331.888M646.293 331.888L318.735 330.228L155.245 331.888"
          ></path>
          <path
            stroke-linejoin="round"
            stroke-linecap="round"
            stroke-width="33.67"
            stroke="#ef4444"
            d="M646.293 331.888L17.7538 17.6187L155.245 331.888M646.293 331.888L17.753 646.157L155.245 331.888M646.293 331.888L318.735 330.228L155.245 331.888"
          ></path>
        </svg>
      </button>
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
const selectedQueryType = ref("analysis"); // 默认查询类型

const sendMessage = () => {
  const content = message.value.trim();
  if (content) {
    emits("send", content, selectedQueryType.value);
    message.value = "";
  }
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

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    // TODO: 实现文件上传功能
    console.log("文件选择:", file.name);
  }
};
</script>

<style scoped>
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-color);
}

.query-type-select {
  width: fit-content;
  min-width: 120px;
  padding: 0.5rem 1rem;
  padding-right: 2.5rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--card-bg);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' d='M2 4l4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  color: var(--text-color);
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  outline: none;
  position: relative;
}

.query-type-select:hover:not(:disabled) {
  border-color: var(--primary-color);
  background-color: var(--hover-color);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.query-type-select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  background-color: var(--card-bg);
}

.query-type-select:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.query-type-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 深色主题下的下拉箭头颜色 */
:root[data-theme="dark"] .query-type-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%23cbd5e1' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' d='M2 4l4 4 4-4'/%3E%3C/svg%3E");
}

/* 选项样式优化 */
.query-type-select option {
  padding: 0.5rem;
  background-color: var(--card-bg);
  color: var(--text-color);
  border-radius: 4px;
}

.messageBox {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--input-box-bg, var(--card-bg));
  padding: 0 15px;
  border-radius: 10px;
  border: 1px solid var(--input-box-border, var(--border-color));
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.messageBox:focus-within {
  border-color: var(--input-box-focus-border, var(--primary-color));
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
}

.fileUploadWrapper {
  width: fit-content;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
}

#file {
  display: none;
}

.fileUploadWrapper label {
  cursor: pointer;
  width: fit-content;
  height: fit-content;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.fileUploadWrapper label svg {
  height: 18px;
}

.fileUploadWrapper label svg path {
  transition: all 0.3s;
}

.fileUploadWrapper label svg circle {
  transition: all 0.3s;
}

.fileUploadWrapper label:hover svg path {
  stroke: var(--text-primary);
}

.fileUploadWrapper label:hover svg circle {
  stroke: var(--text-primary);
  fill: var(--hover-color);
}

.fileUploadWrapper label:hover .tooltip {
  display: block;
  opacity: 1;
}

.tooltip {
  position: absolute;
  top: -40px;
  display: none;
  opacity: 0;
  color: var(--text-primary);
  font-size: 10px;
  white-space: nowrap;
  background-color: var(--card-bg);
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  box-shadow: var(--shadow);
  transition: all 0.3s;
  z-index: 10;
}

#messageInput {
  flex: 1;
  height: 100%;
  background-color: transparent;
  outline: none;
  border: none;
  padding-left: 10px;
  color: var(--input-text, var(--text-primary));
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

#messageInput::placeholder {
  color: var(--input-placeholder, var(--text-secondary));
  opacity: 0.7;
}

#messageInput:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.messageBox:focus-within #sendButton:not(:disabled) svg path {
  fill: var(--hover-color);
  stroke: var(--primary-color);
}

#sendButton {
  width: fit-content;
  height: 100%;
  background-color: transparent;
  outline: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  padding: 0;
  margin-left: 5px;
}

#sendButton:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

#sendButton:not(:disabled):hover svg path {
  fill: var(--hover-color);
  stroke: var(--primary-color);
}

#sendButton svg {
  height: 18px;
  transition: all 0.3s;
}

#sendButton svg path {
  transition: all 0.3s;
}

#sendButton.stop-button svg path {
  stroke: #ef4444;
}

#sendButton.stop-button:hover svg path {
  stroke: #ff6b6b;
  fill: rgba(239, 68, 68, 0.2);
}

/* SVG 图标颜色优化 */
.fileUploadWrapper label svg circle,
.fileUploadWrapper label svg path {
  stroke: var(--text-secondary);
}

#sendButton svg path {
  stroke: var(--text-secondary);
}

/* 浅色主题适配 */
:root[data-theme="light"] .messageBox {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

:root[data-theme="light"] .messageBox:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}
</style>
