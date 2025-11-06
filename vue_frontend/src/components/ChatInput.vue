<template>
  <div class="chat-input-wrapper">
    <select
      v-model="selectedQueryType"
      class="query-type-select"
      :disabled="loading"
      @change="handleQueryTypeChange"
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
      <textarea
        required=""
        v-model="message"
        placeholder="输入消息..."
        id="messageInput"
        @keyup.enter.exact="sendMessage"
        @keyup.enter.shift="addNewline"
        :disabled="loading"
        rows="1"
      ></textarea>
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

    <!-- 信息提示模态框 -->
    <div v-if="showInfoModal" class="info-modal-overlay" @click="showInfoModal = false">
      <div class="info-modal" @click.stop>
        <button class="info-close-btn" @click="showInfoModal = false" title="关闭">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <h3 class="info-modal-title">{{ infoModalContent.title }}</h3>
        <p class="info-modal-message">{{ infoModalContent.message }}</p>
        <button class="info-modal-btn" @click="showInfoModal = false">知道了</button>
      </div>
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
const showInfoModal = ref(false);
const infoModalContent = ref({ title: "", message: "" });

// 监听选择框变化
const handleQueryTypeChange = () => {
  if (selectedQueryType.value === "analysis") {
    showInfoModal.value = true;
    infoModalContent.value = {
      title: "日志分析模式",
      message: "基于 RAG（检索增强生成）技术，LogOracle 能够智能检索和分析您的日志数据。系统会先检索相关的日志内容，然后结合上下文生成精准的分析结果，帮助您快速定位问题、洞察系统运行状态。"
    };
  } else if (selectedQueryType.value === "general_chat") {
    showInfoModal.value = true;
    infoModalContent.value = {
      title: "日常聊天模式",
      message: "让我们来聊聊天！在这个模式下，您可以与 LogOracle 进行轻松愉快的对话。"
    };
  }
};

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
  padding: 0.625rem 1rem;
  padding-right: 2.5rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--card-bg);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' d='M2 4l4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  color: var(--text-color);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
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
  height: 100px;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background-color: var(--input-box-bg, var(--card-bg));
  padding: 0 20px;
  border-radius: 12px;
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
  flex-shrink: 0;
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
  height: 22px;
  width: 22px;
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
  min-height: 100%;
  max-height: 100%;
  background-color: transparent;
  outline: none;
  border: none;
  padding: 12px 15px;
  color: var(--input-text, var(--text-primary));
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  resize: none;
  overflow-y: auto;
  vertical-align: top;
}

/* 确保 textarea 内容从顶部开始 */
#messageInput::-webkit-scrollbar {
  width: 6px;
}

#messageInput::-webkit-scrollbar-track {
  background: transparent;
}

#messageInput::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

#messageInput::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
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
  min-width: 44px;
  background-color: transparent;
  outline: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  padding: 0;
  margin-left: 10px;
  flex-shrink: 0;
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
  height: 22px;
  width: 22px;
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

/* 信息提示模态框样式 */
.info-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
  backdrop-filter: blur(4px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.info-modal {
  position: relative;
  width: 90%;
  max-width: 500px;
  background: var(--card-bg);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--border-color);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.info-close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  width: 32px;
  height: 32px;
}

.info-close-btn:hover {
  background-color: var(--hover-color);
  color: var(--text-primary);
  transform: rotate(90deg);
}

.info-modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  font-family: 'Inter', sans-serif;
}

.info-modal-message {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
  font-family: 'Inter', sans-serif;
}

.info-modal-btn {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: var(--primary-color);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Inter', sans-serif;
}

.info-modal-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(129, 140, 248, 0.3);
}

.info-modal-btn:active {
  transform: translateY(0);
}
</style>
