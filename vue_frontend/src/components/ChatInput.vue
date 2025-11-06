<template>
  <div class="chat-input-container">
    <div class="input-top-row">
      <select
        v-model="selectedQueryType"
        class="query-type-select"
        :disabled="loading"
      >
        <option value="analysis">日志分析</option>
        <option value="general_chat">日常聊天</option>
      </select>
      <textarea
        v-model="message"
        class="chat-input"
        placeholder="输入消息..."
        @keyup.enter.exact="sendMessage"
        @keyup.enter.shift="addNewline"
        :disabled="loading"
      ></textarea>
    </div>
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
  align-items: center;
}

.query-type-select {
  padding: 0.5rem;
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  background-color: var(--input-bg);
  color: var(--text-color);
  cursor: pointer;
  height: 40px; /* Make it consistent with the textarea height */
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
