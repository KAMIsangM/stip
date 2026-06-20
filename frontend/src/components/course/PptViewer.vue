<template>
  <div class="ppt-viewer">
    <!-- 第一张：标题页（封面） -->
    <div v-if="currentIndex === 0" class="title-cover">
      <div class="title-cover-bg">
        <div class="title-decor-circle title-decor-tr"></div>
        <div class="title-decor-circle title-decor-bl"></div>
        <div class="title-cover-content">
          <h1 class="title-cover-title">{{ slides[0]?.title }}</h1>
          <div class="title-cover-divider"></div>
          <p class="title-cover-subtitle">{{ chapterTitle }}</p>
        </div>
      </div>
    </div>

    <!-- 内容页 -->
    <div v-else class="content-slide">
      <div class="content-slide-header">
        <h2 class="content-slide-title">{{ currentSlide?.title }}</h2>
      </div>
      <div class="content-slide-body">
        <div class="content-slide-card">
          <div class="bullet-item" v-for="(bullet, i) in currentSlide?.bullets" :key="i">
            <span class="bullet-dot">●</span>
            <span class="bullet-text">{{ bullet }}</span>
          </div>
        </div>
      </div>
      <div class="content-slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- 导航控件 -->
    <div class="controls">
      <el-button class="nav-btn" @click="prev" :disabled="currentIndex === 0">
        <el-icon><ArrowLeft /></el-icon>
        上一页
      </el-button>
      <div class="nav-dots">
        <span
          v-for="(_, idx) in slides"
          :key="idx"
          class="nav-dot"
          :class="{ active: idx === currentIndex }"
          @click="goTo(idx)"
        ></span>
      </div>
      <el-button class="nav-btn" @click="next" :disabled="currentIndex === slides.length - 1">
        下一页
        <el-icon><ArrowRight /></el-icon>
      </el-button>
      <el-button
        v-if="fileUrl"
        class="nav-btn download-btn"
        @click="downloadPpt"
      >
        <el-icon><Download /></el-icon>
        下载 PPT
      </el-button>
    </div>

    <!-- 老师讲解旁白区域 -->
    <div v-if="currentNotes || currentNarration" class="narration-section">
      <div class="narration-header">
        <el-icon><Microphone /></el-icon>
        <span>老师讲解</span>
        <el-tag size="small" type="info" class="narration-page-tag">
          第 {{ currentIndex + 1 }} 页
        </el-tag>
      </div>
      <div v-if="currentNotes" class="narration-text">
        <p>{{ currentNotes }}</p>
      </div>
      <div v-if="currentNarration" class="narration-bar">
        <AudioPlayer
          :key="`narration-${currentIndex}`"
          :src="currentNarration"
          compact
        />
      </div>
      <div v-else-if="currentNotes" class="narration-no-audio">
        <el-icon><WarningFilled /></el-icon>
        <span>音频尚未生成，请先生成教学内容</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * PPT Viewer — Academic Education style, matching .pptx export design.
 * Slides are rendered natively (no carousel wrapper), with title-cover page
 * and content slides styled with header bars, cards, and decor elements.
 *
 * Narration behavior:
 * - When narrationUrls are provided, the matching audio plays on demand.
 * - Text notes are displayed alongside the audio player.
 */
import { computed, ref } from 'vue'
import { Microphone, WarningFilled, ArrowLeft, ArrowRight, Download } from '@element-plus/icons-vue'
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
  chapterTitle?: string
  fileUrl?: string
}>()

const currentIndex = ref(0)

const currentSlide = computed(() => props.slides[currentIndex.value] ?? null)

const currentNarration = computed(
  () => props.narrationUrls?.[currentIndex.value] ?? '',
)

const currentNotes = computed(
  () => props.slides?.[currentIndex.value]?.notes ?? '',
)

const chapterTitle = computed(
  () => props.chapterTitle || props.slides?.[0]?.title || '',
)

function goTo(idx: number) {
  currentIndex.value = idx
}

function prev() {
  currentIndex.value = Math.max(0, currentIndex.value - 1)
}

function next() {
  currentIndex.value = Math.min(props.slides.length - 1, currentIndex.value + 1)
}

function downloadPpt() {
  if (!props.fileUrl) return
  const a = document.createElement('a')
  a.href = props.fileUrl
  a.download = ''
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>

<style scoped>
/* ===================================================================
   PPT Viewer — Academic Education Style
   Matches python-pptx export design: deep blue gradient, decor bars,
   warm white backgrounds, custom bullet dots.
   =================================================================== */

.ppt-viewer {
  background: transparent;
  border-radius: 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

/* ─── 标题页（封面） ─── */
.title-cover {
  position: relative;
  height: 460px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(26, 86, 168, 0.15);
}

.title-cover-bg {
  width: 100%;
  height: 100%;
  background: linear-gradient(160deg, #0f3b78 0%, #1a56a8 40%, #2566bb 70%, #3b7dd8 100%);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 装饰圆 */
.title-decor-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(37, 102, 187, 0.35);
  pointer-events: none;
}

.title-decor-tr {
  width: 260px;
  height: 260px;
  top: -80px;
  right: -60px;
}

.title-decor-bl {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
}

.title-cover-content {
  text-align: center;
  z-index: 1;
  padding: 0 40px;
}

.title-cover-title {
  font-size: 38px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 24px 0;
  line-height: 1.35;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.title-cover-divider {
  width: 80px;
  height: 3px;
  background: rgba(168, 200, 250, 0.7);
  margin: 0 auto 20px;
  border-radius: 2px;
}

.title-cover-subtitle {
  font-size: 18px;
  color: rgba(168, 200, 250, 0.9);
  margin: 0;
  font-weight: 400;
  letter-spacing: 1px;
}

/* ─── 内容页 ─── */
.content-slide {
  min-height: 420px;
  background: #fafcff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(26, 86, 168, 0.08);
  border: 1px solid #e8f0fe;
  display: flex;
  flex-direction: column;
}

/* 顶部深蓝标题栏 */
.content-slide-header {
  background: linear-gradient(135deg, #1a56a8 0%, #2566bb 100%);
  padding: 20px 32px;
  position: relative;
}

.content-slide-header::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #a8c8fa 0%, transparent 100%);
}

.content-slide-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  line-height: 1.3;
  padding-left: 16px;
  border-left: 4px solid #a8c8fa;
}

/* 主体内容区 */
.content-slide-body {
  flex: 1;
  padding: 28px 32px;
  display: flex;
  align-items: flex-start;
}

.content-slide-card {
  width: 100%;
  background: #fff;
  border-radius: 10px;
  padding: 24px 32px;
  border: 1px solid #e8f0fe;
  box-shadow: 0 2px 8px rgba(26, 86, 168, 0.04);
}

/* bullet 条目 */
.bullet-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f5ff;
}

.bullet-item:last-child {
  border-bottom: none;
}

.bullet-dot {
  color: #1a56a8;
  font-size: 16px;
  line-height: 1.6;
  flex-shrink: 0;
  margin-top: 2px;
}

.bullet-text {
  font-size: 17px;
  color: #2d3747;
  line-height: 1.7;
  font-weight: 400;
}

/* 内容页脚 */
.content-slide-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: #f0f5ff;
  border-top: 1px solid #e8f0fe;
}

.footer-chapter {
  font-size: 12px;
  color: #5f6b7a;
}

.footer-page {
  font-size: 12px;
  color: #1a56a8;
  font-weight: 600;
}

/* ─── 导航控件 ─── */
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
  padding: 0 16px;
}

.nav-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.nav-btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(26, 86, 168, 0.2);
}

.download-btn {
  margin-left: 12px;
  color: #1a56a8;
  border-color: #1a56a8;
}

.download-btn:hover {
  background: #1a56a8;
  color: #fff;
}

.nav-dots {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #c8d6e5;
  cursor: pointer;
  transition: all 0.25s ease;
}

.nav-dot.active {
  background: #1a56a8;
  width: 28px;
  border-radius: 5px;
}

.nav-dot:hover:not(.active) {
  background: #a8c8fa;
}

/* ─── 老师讲解旁白区域 ─── */
.narration-section {
  margin-top: 20px;
  padding: 18px 22px;
  background: linear-gradient(135deg, #f0f5ff 0%, #fafbff 100%);
  border: 1px solid #d9e2f3;
  border-radius: 12px;
  border-left: 4px solid #1a56a8;
}

.narration-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 15px;
  font-weight: 600;
  color: #1a3a6b;
}

.narration-header .el-icon {
  font-size: 18px;
  color: #1a56a8;
}

.narration-page-tag {
  margin-left: auto;
}

.narration-text {
  margin-bottom: 14px;
  padding: 14px 18px;
  background: #fff;
  border-radius: 8px;
  border: 1px dashed #d9e2f3;
}

.narration-text p {
  margin: 0;
  font-size: 15px;
  color: #333;
  line-height: 1.8;
  text-align: justify;
}

.narration-bar {
  margin-top: 8px;
}

.narration-no-audio {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 6px;
  font-size: 13px;
  color: #ad8b00;
}

.narration-no-audio .el-icon {
  font-size: 15px;
}
</style>
