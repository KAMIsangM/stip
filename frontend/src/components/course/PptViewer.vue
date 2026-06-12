<template>
  <div class="ppt-viewer">
    <el-carousel
      ref="carouselRef"
      :initial-index="currentIndex"
      height="420px"
      indicator-position="outside"
      @change="onSlideChange"
    >
      <el-carousel-item v-for="(slide, idx) in slides" :key="idx">
        <div class="slide">
          <img
            v-if="slide.image_url"
            :src="slide.image_url"
            class="slide-image"
            alt=""
          />
          <div v-else class="slide-placeholder">PPT</div>
          <h2>{{ slide.title }}</h2>
          <ul>
            <li v-for="(bullet, i) in slide.bullets" :key="i">{{ bullet }}</li>
          </ul>
        </div>
      </el-carousel-item>
    </el-carousel>
    <div class="controls">
      <el-button @click="prev">上一页</el-button>
      <span>{{ currentIndex + 1 }} / {{ slides.length }}</span>
      <el-button @click="next">下一页</el-button>
    </div>
    <AudioPlayer v-if="currentNarration" :src="currentNarration" />
  </div>
</template>

<script setup lang="ts">
/**
 * MVP PPT renderer — slide JSON carousel + synced narration (TECH-002 §6).
 * Backend PPTGenerator outputs content_json.slides[]; optional .pptx export is separate.
 */
import { computed, ref } from 'vue'
import AudioPlayer from '@/components/common/AudioPlayer.vue'

export interface PptSlide {
  title: string
  bullets: string[]
  image_url?: string
  notes?: string
}

const props = defineProps<{
  slides: PptSlide[]
  narrationUrls?: string[]
}>()

const carouselRef = ref<{ setActiveItem: (i: number) => void }>()
const currentIndex = ref(0)

const currentNarration = computed(
  () => props.narrationUrls?.[currentIndex.value] ?? '',
)

function onSlideChange(index: number) {
  currentIndex.value = index
}

function prev() {
  const nextIdx = Math.max(0, currentIndex.value - 1)
  carouselRef.value?.setActiveItem(nextIdx)
  currentIndex.value = nextIdx
}

function next() {
  const nextIdx = Math.min(props.slides.length - 1, currentIndex.value + 1)
  carouselRef.value?.setActiveItem(nextIdx)
  currentIndex.value = nextIdx
}
</script>

<style scoped>
.ppt-viewer {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.slide {
  padding: 24px;
  height: 100%;
  box-sizing: border-box;
}
.slide-image {
  max-width: 100%;
  max-height: 160px;
  object-fit: contain;
  margin-bottom: 12px;
}
.slide-placeholder {
  width: 120px;
  height: 80px;
  background: #eee;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  margin-bottom: 12px;
  border-radius: 4px;
}
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
}
</style>
