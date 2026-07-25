<template>
  <div class="support-chat-widget" :class="{ open: panelOpen }">
    <button
      v-if="!panelOpen"
      class="support-fab"
      type="button"
      aria-label="智能客服"
      title="智能客服"
      @click="panelOpen = true"
    >
      <el-icon><ChatDotRound /></el-icon>
    </button>

    <section v-else class="support-panel" aria-label="智能客服">
      <header class="support-header">
        <div>
          <strong>智能客服</strong>
          <span>{{ userStore.isAuthenticated ? '已登录' : '匿名' }}</span>
        </div>
        <button class="icon-button" type="button" aria-label="关闭智能客服" title="关闭" @click="panelOpen = false">
          <el-icon><Close /></el-icon>
        </button>
      </header>

      <div ref="messagesRef" class="support-messages">
        <article
          v-for="message in messages"
          :key="message.id"
          :class="['chat-row', message.role]"
        >
          <div class="chat-bubble">{{ message.content }}</div>
          <div v-if="message.sources?.length" class="source-list">
            <div class="source-title">来源</div>
            <component
              :is="source.path?.startsWith('/#') ? 'a' : 'div'"
              v-for="source in message.sources"
              :key="`${source.type}-${source.path}-${source.title}`"
              class="source-item"
              :href="source.path?.startsWith('/#') ? source.path : undefined"
            >
              <span class="source-kind">{{ sourceKindLabel(source.type) }}</span>
              <span class="source-main">{{ source.title }}</span>
              <small>{{ source.snippet || source.path }}</small>
            </component>
          </div>
        </article>

        <div v-if="loading" class="chat-row assistant">
          <div class="chat-bubble loading-bubble">正在整理回答...</div>
        </div>
      </div>

      <form class="support-input" @submit.prevent="sendMessage">
        <el-input
          v-model="draft"
          type="textarea"
          resize="none"
          :rows="2"
          maxlength="500"
          show-word-limit
          placeholder="输入问题或物品线索"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <button class="send-button" type="submit" :disabled="loading || !draft.trim()" aria-label="发送" title="发送">
          <el-icon><Promotion /></el-icon>
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { ChatDotRound, Close, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { supportApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const panelOpen = ref(false)
const draft = ref('')
const loading = ref(false)
const messagesRef = ref(null)
const sessionId = ref(localStorage.getItem('foundit.support.sessionId') || '')
const newMessageId = () => {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}
const messages = ref([
  {
    id: newMessageId(),
    role: 'assistant',
    content: '你好，请直接描述你的问题或物品线索。',
    sources: [],
  },
])

const sourceKindLabel = (type) => ({
  knowledge: '知识库',
  item: '物品',
  personal: '个人',
}[type] || '来源')

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const sendMessage = async () => {
  const content = draft.value.trim()
  if (!content || loading.value) return

  messages.value.push({
    id: newMessageId(),
    role: 'user',
    content,
    sources: [],
  })
  draft.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const res = await supportApi.chat({
      message: content,
      session_id: sessionId.value || undefined,
      channel: 'web',
    })
    sessionId.value = res.data.session_id
    localStorage.setItem('foundit.support.sessionId', sessionId.value)
    messages.value.push({
      id: newMessageId(),
      role: 'assistant',
      content: res.data.answer || '暂时没有可用回答。',
      sources: res.data.sources || [],
    })
  } catch (error) {
    const detail = error.response?.data?.detail
    const content = typeof detail === 'string' ? detail : '智能客服暂时不可用，请稍后再试。'
    messages.value.push({
      id: newMessageId(),
      role: 'assistant',
      content,
      sources: [],
    })
    if (error.response?.status !== 429) {
      ElMessage.error(content)
    }
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.support-chat-widget {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 900;
}

.support-fab {
  width: 52px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--accent-soft-border);
  border-radius: 50%;
  background: var(--foundit-blue);
  color: #fff;
  box-shadow: 0 12px 32px rgba(37, 99, 235, 0.28);
  cursor: pointer;
}

.support-fab .el-icon {
  font-size: 24px;
}

.support-panel {
  width: min(380px, calc(100vw - 32px));
  height: min(620px, calc(100vh - 104px));
  min-height: 420px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--surface-color);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.18);
}

.support-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 14px 0 18px;
  border-bottom: 1px solid var(--border-color);
}

.support-header strong {
  display: block;
  color: var(--text-primary);
  font-size: 15px;
}

.support-header span {
  display: block;
  margin-top: 2px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.icon-button,
.send-button {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: 50%;
  background: var(--surface-color);
  color: var(--text-secondary);
  cursor: pointer;
}

.icon-button:hover,
.send-button:hover:not(:disabled) {
  color: var(--accent-soft-text);
  border-color: var(--accent-soft-border);
  background: var(--accent-soft-hover);
}

.send-button {
  background: var(--foundit-blue);
  color: #fff;
  border-color: var(--foundit-blue);
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.support-messages {
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
  background: var(--surface-muted);
}

.chat-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

.chat-row.user {
  align-items: flex-end;
}

.chat-row.assistant {
  align-items: flex-start;
}

.chat-bubble {
  max-width: 88%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-primary);
  background: var(--surface-color);
  font-size: 14px;
  line-height: 1.55;
}

.chat-row.user .chat-bubble {
  color: #fff;
  border-color: var(--foundit-blue);
  background: var(--foundit-blue);
}

.loading-bubble {
  color: var(--text-secondary);
}

.source-list {
  width: min(320px, 92%);
  display: grid;
  gap: 8px;
}

.source-title {
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 700;
}

.source-item {
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  background: var(--surface-color);
}

a.source-item:hover {
  border-color: var(--accent-soft-border);
  background: var(--accent-soft-hover);
}

.source-kind {
  width: fit-content;
  padding: 2px 6px;
  border-radius: 999px;
  color: var(--accent-soft-text);
  background: var(--accent-soft);
  font-size: 11px;
  font-weight: 800;
}

.source-main {
  font-size: 13px;
  font-weight: 800;
}

.source-item small {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.support-input {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid var(--border-color);
  background: var(--surface-color);
}

.support-input :deep(.el-textarea) {
  flex: 1;
}

.support-input :deep(.el-textarea__inner) {
  min-height: 48px !important;
  max-height: 96px;
}

@media (max-width: 640px) {
  .support-chat-widget {
    right: 16px;
    bottom: 16px;
  }

  .support-panel {
    width: calc(100vw - 32px);
    height: min(620px, calc(100vh - 88px));
  }
}
</style>
