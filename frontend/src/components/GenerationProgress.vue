<template>
  <el-card v-if="visible" class="progress-card" shadow="never">
    <div class="row">
      <span class="label">生成进度</span>
      <el-tag :type="tagType" size="small">{{ statusLabel }}</el-tag>
    </div>
    <el-progress
      :percentage="percentage"
      :stroke-width="8"
      :status="progressStatus"
      :color="progressColor"
    />
    <p class="step">{{ stepLabel }}</p>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import http from '@/api/http'

const props = defineProps<{
  courseId: number
  autoHide?: boolean
}>()

const emit = defineEmits<{
  completed: []
  failed: [error: string]
}>()

// State
const currentStep = ref(0)
const totalSteps = ref(0)
const status = ref('pending')
const stepName = ref('等待开始')
const errorMessage = ref<string | null>(null)
const visible = ref(true)

// WebSocket
let ws: WebSocket | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null
const useWebSocket = ref(true) // prefer WebSocket, fallback to polling

// Computed
const percentage = computed(() =>
  totalSteps.value > 0 ? Math.round((currentStep.value / totalSteps.value) * 100) : 0
)

const stepLabel = computed(() =>
  `${stepName.value} (${currentStep.value}/${totalSteps.value})`
)

const tagType = computed(() => {
  const map: Record<string, string> = {
    pending: 'info',
    outline_generating: 'warning',
    content_generating: 'warning',
    done: 'success',
    failed: 'danger',
    not_started: 'info',
  }
  return map[status.value] || 'info'
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    outline_generating: '大纲生成中',
    content_generating: '内容生成中',
    done: '已完成',
    failed: '失败',
    not_started: '未开始',
  }
  return map[status.value] || status.value
})

const progressStatus = computed<'success' | 'exception' | 'warning' | undefined>(() => {
  if (status.value === 'done') return 'success'
  if (status.value === 'failed') return 'exception'
  return undefined
})

const progressColor = computed(() => {
  if (status.value === 'failed') return '#f56c6c'
  return undefined // default blue
})

// ---------------------------------------------------------------------------
// WebSocket connection
// ---------------------------------------------------------------------------
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const url = `${protocol}//${host}/api/v1/ws/generation/${props.courseId}`

  try {
    ws = new WebSocket(url)

    ws.onopen = () => {
      console.log(`[Progress] WebSocket connected for course ${props.courseId}`)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.error) {
          console.error('[Progress] WebSocket error:', data.error)
          fallbackToPolling()
          return
        }
        updateFromData(data)

        if (data.status === 'done') {
          emit('completed')
          if (props.autoHide !== false) {
            setTimeout(() => { visible.value = false }, 3000)
          }
        } else if (data.status === 'failed') {
          emit('failed', data.error_message || '未知错误')
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      console.warn('[Progress] WebSocket error, falling back to polling')
      fallbackToPolling()
    }

    ws.onclose = () => {
      console.log('[Progress] WebSocket closed')
      ws = null
    }
  } catch {
    console.warn('[Progress] WebSocket not supported, using polling')
    useWebSocket.value = false
    startPolling()
  }
}

function fallbackToPolling() {
  useWebSocket.value = false
  if (ws) {
    ws.close()
    ws = null
  }
  startPolling()
}

// ---------------------------------------------------------------------------
// HTTP polling fallback
// ---------------------------------------------------------------------------
function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(pollProgress, 2000)
  pollProgress() // immediate first poll
}

async function pollProgress() {
  try {
    const { data } = await http.get(`/courses/${props.courseId}/progress`)
    updateFromData(data)

    if (data.status === 'done') {
      stopPolling()
      emit('completed')
      if (props.autoHide !== false) {
        setTimeout(() => { visible.value = false }, 3000)
      }
    } else if (data.status === 'failed') {
      stopPolling()
      emit('failed', data.error_message || '未知错误')
    }
  } catch {
    // Silently retry
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ---------------------------------------------------------------------------
// Data update
// ---------------------------------------------------------------------------
function updateFromData(data: any) {
  currentStep.value = data.current_step ?? currentStep.value
  totalSteps.value = data.total_steps ?? totalSteps.value
  status.value = data.status ?? status.value
  stepName.value = data.step_name ?? stepName.value
  errorMessage.value = data.error_message ?? null
}

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  stopPolling()
})
</script>

<style scoped>
.progress-card {
  margin: 16px;
  background: #fff;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.step {
  margin: 8px 0 0;
  font-size: 13px;
  color: #909399;
}

.error {
  margin: 8px 0 0;
  font-size: 13px;
  color: #f56c6c;
}
</style>
