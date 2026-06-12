<template>
  <div class="audio-player">
    <el-button :icon="playing ? 'VideoPause' : 'VideoPlay'" circle @click="toggle" />
    <el-slider v-model="progress" :max="100" @change="seek" />
    <audio ref="audioRef" :src="src" @timeupdate="onTimeUpdate" @ended="playing = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ src: string }>()
const audioRef = ref<HTMLAudioElement>()
const playing = ref(false)
const progress = ref(0)

function toggle() {
  const el = audioRef.value
  if (!el) return
  if (playing.value) {
    el.pause()
  } else {
    void el.play()
  }
  playing.value = !playing.value
}

function onTimeUpdate() {
  const el = audioRef.value
  if (!el?.duration) return
  progress.value = (el.currentTime / el.duration) * 100
}

function seek(val: number | number[]) {
  const el = audioRef.value
  if (!el?.duration) return
  el.currentTime = ((val as number) / 100) * el.duration
}

watch(
  () => props.src,
  () => {
    playing.value = false
    progress.value = 0
  },
)
</script>

<style scoped>
.audio-player {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}
</style>
