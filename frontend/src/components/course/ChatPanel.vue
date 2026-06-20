<template>
  <div class="chat-panel" :class="{ collapsed }">
    <!-- Expand trigger bar (always visible when collapsed, sits at right edge) -->
    <div v-if="collapsed" class="chat-collapsed-trigger" @click="toggleCollapse">
      <el-tooltip content="展开 AI 助手" placement="left">
        <div class="trigger-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="expand-icon">
            <path d="M15 15l-6-6 6-6" />
          </svg>
          <span class="trigger-label">AI</span>
          <div class="collapsed-dot" v-if="messages.length > 0" />
        </div>
      </el-tooltip>
    </div>

    <!-- Expanded state -->
    <template v-if="!collapsed">
      <!-- Header -->
      <div class="chat-header">
        <div class="chat-header-left">
          <svg class="chat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
          <span class="chat-title">AI 学习助手</span>
        </div>
        <div class="chat-header-actions">
          <el-button text size="small" @click="clearLocal">清空</el-button>
          <el-button text size="small" @click="toggleCollapse">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="collapse-icon">
              <path d="M15 15l-6-6 6-6" />
            </svg>
          </el-button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="msgContainer" class="chat-messages">
        <div v-if="messages.length === 0" class="chat-empty">
          <div class="chat-empty-icon">💬</div>
          <p>有问题随时问我，我会基于当前课程内容为你解答</p>
        </div>

        <div
          v-for="(msg, i) in messages"
          :key="msg.id || i"
          class="chat-bubble"
          :class="msg.role"
        >
          <div class="bubble-avatar">
            <template v-if="msg.role === 'user'">
              <svg viewBox="0 0 24 24" fill="currentColor" class="avatar-icon">
                <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2c0 .66.54 1.2 1.2 1.2h16.8c.66 0 1.2-.54 1.2-1.2v-1.2c0-3.2-6.4-4.8-9.6-4.8z" />
              </svg>
            </template>
            <template v-else>
              <svg viewBox="0 0 24 24" fill="currentColor" class="avatar-icon ai-avatar">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
              </svg>
            </template>
          </div>
          <div class="bubble-body">
            <div class="bubble-role">{{ msg.role === 'user' ? '你' : 'AI 助手' }}</div>
            <div class="bubble-content" v-html="renderContent(msg.content)" />
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="sending" class="chat-bubble assistant">
          <div class="bubble-avatar">
            <svg viewBox="0 0 24 24" fill="currentColor" class="avatar-icon ai-avatar">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
            </svg>
          </div>
          <div class="bubble-body">
            <div class="bubble-role">AI 助手</div>
            <div class="bubble-typing">
              <span class="typing-dot" />
              <span class="typing-dot" />
              <span class="typing-dot" />
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-input-area">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题…"
          :disabled="sending"
          resize="none"
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button
          type="primary"
          :disabled="!input.trim() || sending"
          :loading="sending"
          @click="handleSend"
          class="send-btn"
        >
          <template v-if="!sending">
            <svg viewBox="0 0 24 24" fill="currentColor" class="send-icon">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </template>
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getChatHistory, sendMessage, clearChatHistory } from '@/api/chat'
import type { ChatMessage } from '@/api/chat'

const props = defineProps<{
  courseId: number
  chapterId: number | null
  initialCollapsed?: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle', collapsed: boolean): void
}>()

const messages = ref<ChatMessage[]>([])
const input = ref('')
const sending = ref(false)
const collapsed = ref(props.initialCollapsed ?? false)
const msgContainer = ref<HTMLElement | null>(null)

function toggleCollapse() {
  collapsed.value = !collapsed.value
  emit('toggle', collapsed.value)
}

// ---------------------------------------------------------------------------
// Load history
// ---------------------------------------------------------------------------
async function loadHistory() {
  try {
    const { data } = await getChatHistory(props.courseId, props.chapterId)
    messages.value = data.messages || []
    await scrollToBottom()
  } catch {
    messages.value = []
  }
}

// ---------------------------------------------------------------------------
// Send message
// ---------------------------------------------------------------------------
async function handleSend() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  sending.value = true

  try {
    const { data } = await sendMessage(props.courseId, {
      chapter_id: props.chapterId,
      message: text,
    })
    messages.value.push(data.user_message)
    messages.value.push(data.reply)
    await scrollToBottom()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '发送失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    sending.value = false
  }
}

// ---------------------------------------------------------------------------
// Clear chat history (local + server)
// ---------------------------------------------------------------------------
async function clearLocal() {
  if (messages.value.length === 0) return
  try {
    await clearChatHistory(props.courseId, props.chapterId)
    messages.value = []
    ElMessage.success('聊天记录已清空')
  } catch {
    ElMessage.error('清空失败，请稍后重试')
  }
}

// ---------------------------------------------------------------------------
// Simple markdown-like rendering
// ---------------------------------------------------------------------------
function renderContent(text: string): string {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  // Newlines
  html = html.replace(/\n/g, '<br/>')
  return html
}

// ---------------------------------------------------------------------------
// Scroll to bottom
// ---------------------------------------------------------------------------
async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

// ---------------------------------------------------------------------------
// Watch chapter change → reload history
// ---------------------------------------------------------------------------
watch(() => props.chapterId, () => {
  loadHistory()
})

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  overflow: hidden;
  position: relative;
}

/* ── Collapsed trigger bar ── */
.chat-collapsed-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 16px 0;
  height: 100%;
  cursor: pointer;
  user-select: none;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  transition: background 0.2s;
}

.chat-collapsed-trigger:hover {
  background: #ecf5ff;
}

.trigger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
}

.trigger-label {
  font-size: 11px;
  font-weight: 600;
  color: #409eff;
  writing-mode: vertical-rl;
  letter-spacing: 2px;
}

.expand-icon {
  width: 18px;
  height: 18px;
  color: #409eff;
  transform: rotate(180deg);
}

.collapsed-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  animation: pulse-dot 2s infinite;
  position: absolute;
  top: -4px;
  right: -4px;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ── Header ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-icon {
  width: 20px;
  height: 20px;
  color: #409eff;
}

.collapse-icon {
  width: 16px;
  height: 16px;
  color: #909399;
}

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

/* ── Messages ── */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;  /* critical for flex overflow */
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.chat-empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
  opacity: 0.6;
}

/* ── Bubble ── */
.chat-bubble {
  display: flex;
  gap: 10px;
  animation: bubbleIn 0.25s ease;
}

.chat-bubble.user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.chat-bubble.user .bubble-avatar {
  background: #409eff;
}

.avatar-icon {
  width: 18px;
  height: 18px;
}

.chat-bubble.user .avatar-icon {
  color: #fff;
}

.chat-bubble.assistant .avatar-icon {
  color: #409eff;
}

.ai-avatar {
  color: #409eff;
}

.bubble-body {
  max-width: 78%;
}

.bubble-role {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.chat-bubble.user .bubble-role {
  text-align: right;
}

.bubble-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.65;
  color: #303133;
  background: #f5f7fa;
  word-break: break-word;
}

.chat-bubble.user .bubble-content {
  background: #409eff;
  color: #fff;
}

.bubble-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 12px;
}

.chat-bubble.user .bubble-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.bubble-content :deep(strong) {
  font-weight: 600;
}

/* ── Typing dots ── */
.bubble-typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 16px;
}

.typing-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typingBounce 1.4s infinite ease-in-out both;
}

.typing-dot:nth-child(1) {
  animation-delay: 0s;
}
.typing-dot:nth-child(2) {
  animation-delay: 0.16s;
}
.typing-dot:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes typingBounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Input ── */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #f2f3f5;
  flex-shrink: 0;
  align-items: flex-end;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 13px;
  padding: 8px 12px;
}

.send-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
}

.send-icon {
  width: 18px;
  height: 18px;
}
</style>
