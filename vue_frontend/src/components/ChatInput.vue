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
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--card-bg);
  color: var(--text-color);
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

.query-type-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.messageBox {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2d2d2d;
  padding: 0 15px;
  border-radius: 10px;
  border: 1px solid rgb(63, 63, 63);
  transition: border-color 0.3s;
}

.messageBox:focus-within {
  border: 1px solid rgb(110, 110, 110);
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
  stroke: #fff;
}

.fileUploadWrapper label:hover svg circle {
  stroke: #fff;
  fill: #3c3c3c;
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
  color: white;
  font-size: 10px;
  white-space: nowrap;
  background-color: #000;
  padding: 6px 10px;
  border: 1px solid #3c3c3c;
  border-radius: 5px;
  box-shadow: 0px 5px 10px rgba(0, 0, 0, 0.596);
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
  color: white;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

#messageInput::placeholder {
  color: #6c6c6c;
}

.messageBox:focus-within #sendButton:not(:disabled) svg path {
  fill: #3c3c3c;
  stroke: white;
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
  fill: #3c3c3c;
  stroke: white;
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

/* 深色主题适配 */
:root[data-theme="dark"] .messageBox {
  background-color: #2d2d2d;
  border: 1px solid rgb(63, 63, 63);
}

:root[data-theme="dark"] .messageBox:focus-within {
  border: 1px solid rgb(110, 110, 110);
}

/* 浅色主题适配 */
:root[data-theme="light"] .messageBox,
:root .messageBox {
  background-color: #f5f5f5;
  border: 1px solid #d0d0d0;
}

:root[data-theme="light"] .messageBox:focus-within,
:root .messageBox:focus-within {
  border: 1px solid #8c8c8c;
}

:root[data-theme="light"] #messageInput,
:root #messageInput {
  color: #1e293b;
}

:root[data-theme="light"] #messageInput::placeholder,
:root #messageInput::placeholder {
  color: #94a3b8;
}
</style>
