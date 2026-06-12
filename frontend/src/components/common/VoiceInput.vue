<template>
  <div class="voice-input">
    <el-button :type="recording ? 'danger' : 'primary'" @click="toggle">
      {{ recording ? '停止' : '语音提问' }}
    </el-button>
    <span v-if="partialText" class="partial">{{ partialText }}</span>
  </div>
</template>

<script setup lang="ts">
import { onUnmounted, ref } from 'vue'

const recording = ref(false)
const partialText = ref('')
let mediaStream: MediaStream | null = null

async function toggle() {
  if (recording.value) {
    stop()
    return
  }
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
  recording.value = true
  // TODO: WebSocket /ws/v1/voice/chat PCM chunks
}

function stop() {
  mediaStream?.getTracks().forEach((t) => t.stop())
  mediaStream = null
  recording.value = false
}

onUnmounted(stop)
</script>

<style scoped>
.voice-input {
  display: flex;
  align-items: center;
  gap: 12px;
}
.partial {
  color: #666;
  font-size: 13px;
}
</style>
