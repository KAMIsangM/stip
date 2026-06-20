<template>
  <div class="audio-player" :class="{ compact: compact }">
    <!-- Play / Pause -->
    <el-button
      :icon="playing ? VideoPause : VideoPlay"
      :size="compact ? 'small' : 'default'"
      circle
      @click="toggle"
    />

    <!-- Time display -->
    <span v-if="showTime" class="audio-time">{{ formatTime(currentTime) }}</span>

    <!-- Progress bar -->
    <el-slider
      v-model="progress"
      :max="100"
      :size="compact ? 'small' : 'default'"
      class="audio-slider"
      @change="seek"
    />

    <!-- Duration -->
    <span v-if="showTime" class="audio-duration">{{ formatTime(duration) }}</span>

    <!-- Replay button -->
    <el-button
      v-if="showReplay"
      :icon="RefreshRight"
      :size="compact ? 'small' : 'default'"
      circle
      @click="replay"
    />

    <!-- Volume control (non-compact mode) -->
    <el-slider
      v-if="!compact"
      v-model="volume"
      :max="100"
      style="width: 80px"
      @change="setVolume"
    />

    <!-- Hidden audio element -->
    <audio
      ref="audioRef"
      :src="src"
      preload="auto"
      @loadedmetadata="onLoaded"
      @timeupdate="onTimeUpdate"
      @play="playing = true"
      @pause="playing = false"
      @ended="onEnded"
      @error="onError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { VideoPause, VideoPlay, RefreshRight } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  src: string
  autoPlay?: boolean
  compact?: boolean
  showTime?: boolean
  showReplay?: boolean
}>(), {
  autoPlay: false,
  compact: false,
  showTime: true,
  showReplay: true,
})

const emit = defineEmits<{
  ended: []
  playing: [playing: boolean]
}>()

const audioRef = ref<HTMLAudioElement>()
const playing = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(100)
const hasError = ref(false)

// ------------------------------------------------------------------
// Public methods (exposed via defineExpose)
// ------------------------------------------------------------------

function toggle() {
  const el = audioRef.value
  if (!el || hasError.value) return
  if (playing.value) {
    el.pause()
  } else {
    void el.play().catch(() => {
      // Autoplay may be blocked; user needs to click
    })
  }
}

function replay() {
  const el = audioRef.value
  if (!el) return
  el.currentTime = 0
  progress.value = 0
  if (!playing.value) {
    void el.play().catch(() => {})
  }
}

function seek(val: number | number[]) {
  const el = audioRef.value
  if (!el?.duration) return
  el.currentTime = ((val as number) / 100) * el.duration
}

function setVolume(val: number | number[]) {
  const el = audioRef.value
  if (!el) return
  el.volume = (val as number) / 100
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ------------------------------------------------------------------
// Audio events
// ------------------------------------------------------------------

function onLoaded() {
  const el = audioRef.value
  if (!el) return
  duration.value = el.duration
  hasError.value = false

  if (props.autoPlay) {
    void el.play().catch(() => {
      // Autoplay blocked — user interaction required
    })
  }
}

function onTimeUpdate() {
  const el = audioRef.value
  if (!el?.duration) return
  currentTime.value = el.currentTime
  progress.value = (el.currentTime / el.duration) * 100
}

function onEnded() {
  playing.value = false
  progress.value = 100
  emit('ended')
  emit('playing', false)
}

function onError() {
  hasError.value = true
  playing.value = false
}

// ------------------------------------------------------------------
// Watchers
// ------------------------------------------------------------------

watch(
  () => props.src,
  () => {
    playing.value = false
    progress.value = 0
    currentTime.value = 0
    duration.value = 0
    hasError.value = false
  },
)

watch(playing, (val) => {
  emit('playing', val)
})

// Expose methods for parent components
defineExpose({ toggle, replay, seek, setVolume })
</script>

<style scoped>
.audio-player {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  background: #f8f9fb;
  border-radius: 8px;
  padding: 8px 16px;
}

.audio-player.compact {
  gap: 8px;
  padding: 4px 12px;
}

.audio-slider {
  flex: 1;
  min-width: 80px;
}

.audio-time,
.audio-duration {
  font-size: 13px;
  color: #909399;
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: center;
}

.audio-player.compact .audio-time,
.audio-player.compact .audio-duration {
  font-size: 12px;
  min-width: 28px;
}
</style>
