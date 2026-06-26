<template>
  <div class="ppt-viewer" tabindex="0" @keydown="handleKeydown" ref="viewerRef">
    <!-- ============================================================ -->
    <!-- Title Slide (封面)                                            -->
    <!-- ============================================================ -->
    <div v-if="currentLayout === 'title'" class="slide title-slide">
      <div class="title-slide-bg">
        <!-- 装饰 blob -->
        <div class="blob blob-tr"></div>
        <div class="blob blob-bl"></div>
        <div class="blob blob-cr"></div>
        <!-- 标题卡片 -->
        <div class="title-card">
          <h1 class="title-main">{{ currentSlide?.title }}</h1>
        </div>
        <!-- 副标题 -->
        <p class="title-sub">{{ chapterTitle }}</p>
        <!-- 波浪装饰 -->
        <div class="wave-decor"></div>
      </div>
      <div class="slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Content Slide (标准内容页)                                     -->
    <!-- ============================================================ -->
    <div v-else-if="currentLayout === 'content'" class="slide content-slide">
      <!-- 顶部标题栏 -->
      <div class="content-header">
        <h2 class="content-title">{{ currentSlide?.title }}</h2>
      </div>
      <!-- 主体内容 -->
      <div class="content-body">
        <div class="content-card">
          <div
            v-for="(bullet, i) in currentSlide?.bullets"
            :key="i"
            class="bullet-item"
          >
            <span class="bullet-badge">{{ i + 1 }}</span>
            <span class="bullet-text">{{ bullet }}</span>
          </div>
        </div>
      </div>
      <!-- 侧边装饰彩条 -->
      <div class="side-stripes">
        <span v-for="c in 4" :key="c" class="stripe" :class="'stripe-' + c"></span>
      </div>
      <div class="slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Two-Column Slide (两栏对比)                                    -->
    <!-- ============================================================ -->
    <div v-else-if="currentLayout === 'two_column'" class="slide two-col-slide">
      <div class="two-col-header">
        <h2 class="two-col-title">{{ currentSlide?.title }}</h2>
      </div>
      <div class="two-col-body">
        <!-- 左栏 -->
        <div class="col-card col-left">
          <div class="col-card-header left-header">
            <span class="col-card-icon">◆</span>
            <span>{{ currentSlide?.left_title || '左侧' }}</span>
          </div>
          <div class="col-card-bullets">
            <div
              v-for="(b, i) in currentSlide?.left_bullets"
              :key="'l' + i"
              class="col-bullet"
            >
              <span class="col-bullet-dot">●</span>
              <span>{{ b }}</span>
            </div>
            <div v-if="!currentSlide?.left_bullets?.length" class="col-empty">
              暂无内容
            </div>
          </div>
        </div>
        <!-- 分隔线 -->
        <div class="col-divider">
          <span>VS</span>
        </div>
        <!-- 右栏 -->
        <div class="col-card col-right">
          <div class="col-card-header right-header">
            <span class="col-card-icon">◆</span>
            <span>{{ currentSlide?.right_title || '右侧' }}</span>
          </div>
          <div class="col-card-bullets">
            <div
              v-for="(b, i) in currentSlide?.right_bullets"
              :key="'r' + i"
              class="col-bullet"
            >
              <span class="col-bullet-dot right-dot">●</span>
              <span>{{ b }}</span>
            </div>
            <div v-if="!currentSlide?.right_bullets?.length" class="col-empty">
              暂无内容
            </div>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Chart Slide (图表页)                                          -->
    <!-- ============================================================ -->
    <div v-else-if="currentLayout === 'chart'" class="slide chart-slide">
      <div class="chart-header">
        <h2 class="chart-title">{{ currentSlide?.title }}</h2>
      </div>
      <div class="chart-body">
        <!-- 左侧图表 -->
        <div class="chart-container">
          <div ref="chartRef" class="chart-canvas"></div>
          <div v-if="!chartData" class="chart-placeholder">
            <span class="chart-ph-icon">📊</span>
            <span>暂无图表数据</span>
          </div>
        </div>
        <!-- 右侧分析说明 -->
        <div class="chart-insight">
          <div class="insight-header">
            <span class="insight-icon">📊</span>
            <span>{{ chartData?.title || '数据分析' }}</span>
          </div>
          <div class="insight-bullets">
            <div
              v-for="(b, i) in currentSlide?.bullets"
              :key="i"
              class="insight-item"
            >
              <span class="insight-arrow">→</span>
              <span>{{ b }}</span>
            </div>
            <div v-if="!currentSlide?.bullets?.length" class="insight-empty">
              暂无分析说明
            </div>
          </div>
        </div>
      </div>
      <div class="slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- Summary Slide (总结页)                                        -->
    <!-- ============================================================ -->
    <div v-else-if="currentLayout === 'summary'" class="slide summary-slide">
      <div class="summary-bg">
        <div class="blob blob-sum-tr"></div>
        <div class="blob blob-sum-bl"></div>
        <!-- 总结标题 -->
        <div class="summary-title-card">
          <h2 class="summary-main-title">{{ currentSlide?.title || '本章总结' }}</h2>
        </div>
        <!-- 总结要点卡片 -->
        <div class="summary-items">
          <div
            v-for="(b, i) in currentSlide?.bullets"
            :key="i"
            class="summary-item"
            :class="'summary-item-' + (i % 3)"
          >
            <span class="summary-item-icon">{{ summaryIcons[i % summaryIcons.length] }}</span>
            <span class="summary-item-text">{{ b }}</span>
          </div>
          <div v-if="!currentSlide?.bullets?.length" class="summary-empty">
            暂无总结内容
          </div>
        </div>
        <!-- 波浪装饰 -->
        <div class="wave-decor-sum"></div>
      </div>
      <div class="slide-footer">
        <span class="footer-chapter">{{ chapterTitle }}</span>
        <span class="footer-page">{{ currentIndex + 1 }} / {{ slides.length }}</span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- 导航控件                                                      -->
    <!-- ============================================================ -->
    <div class="controls">
      <el-button class="nav-btn" @click="prev" :disabled="currentIndex === 0">
        <el-icon><ArrowLeft /></el-icon>
        上一页
      </el-button>
      <div class="nav-dots">
        <span
          v-for="(slide, idx) in slides"
          :key="idx"
          class="nav-dot"
          :class="{
            active: idx === currentIndex,
            'dot-title': slide.layout === 'title',
            'dot-content': slide.layout === 'content' || !slide.layout,
            'dot-two-col': slide.layout === 'two_column',
            'dot-chart': slide.layout === 'chart',
            'dot-summary': slide.layout === 'summary',
          }"
          :title="slide.title"
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

    <!-- 键盘提示 -->
    <div class="keyboard-hint">
      <el-icon><VideoPlay /></el-icon>
      <span>使用 ← → 方向键切换幻灯片</span>
    </div>

    <!-- ============================================================ -->
    <!-- 老师讲解旁白区域                                               -->
    <!-- ============================================================ -->
    <div v-if="currentNotes || currentNarration" class="narration-section">
      <div class="narration-header">
        <el-icon><Microphone /></el-icon>
        <span>老师讲解</span>
        <el-tag size="small" type="warning" class="narration-page-tag">
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
 * PPT Viewer — Warm Orange Illustration Style
 * Matches backend python-pptx export design with #FF8C42 primary palette.
 * Supports 5 layouts: title, content, two_column, chart, summary.
 * Keyboard shortcuts: ← → to navigate slides.
 */
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Microphone, WarningFilled, ArrowLeft, ArrowRight, Download, VideoPlay } from '@element-plus/icons-vue'
import AudioPlayer from '@/components/common/AudioPlayer.vue'
import * as echarts from 'echarts'

export interface ChartData {
  type: 'bar' | 'pie' | 'line'
  title: string
  categories: string[]
  series: { name: string; values: number[] }[]
}

export interface PptSlide {
  title: string
  layout?: 'title' | 'content' | 'two_column' | 'chart' | 'summary'
  bullets?: string[]
  image_url?: string
  notes?: string
  // two_column layout fields
  left_title?: string
  left_bullets?: string[]
  right_title?: string
  right_bullets?: string[]
  // chart layout fields
  chart?: ChartData
}

const props = defineProps<{
  slides: PptSlide[]
  narrationUrls?: string[]
  chapterTitle?: string
  fileUrl?: string
}>()

const currentIndex = ref(0)
const viewerRef = ref<HTMLElement | null>(null)
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// Summary icons for decorative purposes
const summaryIcons = ['💡', '✓', '★', '📖', '🔑', '🎯', '📌', '🚀']

const currentSlide = computed(() => props.slides[currentIndex.value] ?? null)

const currentLayout = computed(() => {
  const layout = currentSlide.value?.layout
  // First slide without explicit layout → title
  if (currentIndex.value === 0 && (!layout || layout === 'content')) {
    return 'title'
  }
  return layout || 'content'
})

const currentNarration = computed(
  () => props.narrationUrls?.[currentIndex.value] ?? '',
)

const currentNotes = computed(
  () => props.slides?.[currentIndex.value]?.notes ?? '',
)

const chapterTitle = computed(
  () => props.chapterTitle || props.slides?.[0]?.title || '',
)

const chartData = computed(() => currentSlide.value?.chart ?? null)

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

// Keyboard shortcuts
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    prev()
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    next()
  }
}

// Focus the viewer when mounted so keyboard events work
onMounted(() => {
  viewerRef.value?.focus()
})

// ── ECharts rendering ──
function renderChart() {
  if (!chartRef.value || !chartData.value) return

  // Dispose old instance
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  const cd = chartData.value
  const warmColors = ['#FF8C42', '#4ECDC4', '#FFE66D', '#FF6B6B', '#957FCD', '#7EFFE4']

  chartInstance = echarts.init(chartRef.value)

  const isPie = cd.type === 'pie'
  const isLine = cd.type === 'line'

  const option: echarts.EChartsOption = {
    title: {
      text: cd.title,
      left: 'center',
      top: 8,
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#3D2C2C',
      },
    },
    tooltip: {
      trigger: isPie ? 'item' : 'axis',
      formatter: isPie ? '{b}: {c} ({d}%)' : undefined,
    },
    legend: isPie ? {
      bottom: 8,
      textStyle: { fontSize: 11, color: '#8B7E7E' },
    } : {
      bottom: 8,
      textStyle: { fontSize: 11, color: '#8B7E7E' },
    },
    grid: isPie ? undefined : {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true,
    },
    xAxis: isPie ? undefined : {
      type: 'category',
      data: cd.categories,
      axisLabel: { color: '#8B7E7E', fontSize: 11 },
      axisLine: { lineStyle: { color: '#FFBF80' } },
      axisTick: { show: false },
    },
    yAxis: isPie ? undefined : {
      type: 'value',
      axisLabel: { color: '#8B7E7E', fontSize: 11 },
      splitLine: { lineStyle: { color: '#FFF0E0' } },
    },
    series: cd.series.map((s, i) => {
      if (isPie) {
        return {
          name: s.name,
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '55%'],
          data: s.values.map((v, j) => ({
            value: v,
            name: cd.categories[j] || `项目${j + 1}`,
          })),
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' },
          },
          itemStyle: {
            borderRadius: 6,
            borderColor: '#FFF8F0',
            borderWidth: 2,
          },
          color: warmColors,
          label: {
            fontSize: 10,
            color: '#8B7E7E',
          },
        } as echarts.SeriesOption
      }
      return {
        name: s.name,
        type: isLine ? 'line' : 'bar',
        data: s.values,
        itemStyle: {
          color: warmColors[i % warmColors.length],
          borderRadius: isLine ? 0 : 6,
        },
        lineStyle: isLine ? {
          color: warmColors[i % warmColors.length],
          width: 3,
        } : undefined,
        symbol: isLine ? 'circle' : undefined,
        symbolSize: isLine ? 8 : undefined,
        smooth: isLine,
        barMaxWidth: 40,
        emphasis: {
          itemStyle: {
            shadowBlur: 8,
            shadowColor: 'rgba(255,140,66,0.3)',
          },
        },
      } as echarts.SeriesOption
    }),
  }

  chartInstance.setOption(option)
}

// Watch for chart data changes
watch([chartData, () => currentIndex.value], () => {
  nextTick(() => {
    if (currentLayout.value === 'chart') {
      // Small delay to ensure DOM is ready
      setTimeout(() => renderChart(), 100)
    }
  })
})

// Handle resize
function onResize() {
  chartInstance?.resize()
}
window.addEventListener('resize', onResize)

onUnmounted(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
/* ===================================================================
   PPT Viewer — Warm Orange Illustration Style
   Primary: #FF8C42  Secondary: #4ECDC4  Accent: #FFE66D, #FF6B6B
   =================================================================== */

.ppt-viewer {
  background: transparent;
  border-radius: 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  outline: none;
}

/* ─── Slide Base ─── */
.slide {
  position: relative;
  min-height: 420px;
  border-radius: 12px;
  overflow: hidden;
  animation: slideIn 0.35s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.slide-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 28px;
  background: #FFF5EB;
  border-top: 1px solid #FFE0C0;
}

.footer-chapter {
  font-size: 12px;
  color: #8B7E7E;
}

.footer-page {
  font-size: 12px;
  color: #FF8C42;
  font-weight: 600;
}

/* ─── Title Slide ─── */
.title-slide {
  box-shadow: 0 4px 24px rgba(255, 140, 66, 0.15);
}

.title-slide-bg {
  position: relative;
  height: 460px;
  background: linear-gradient(160deg, #FF8C42 0%, #FF6B35 35%, #FFAA55 70%, #FFE66D 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 装饰 blob */
.blob {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.blob-tr {
  width: 280px;
  height: 280px;
  top: -100px;
  right: -70px;
  background: rgba(255, 191, 128, 0.35);
}

.blob-bl {
  width: 200px;
  height: 200px;
  bottom: -60px;
  left: -60px;
  background: rgba(126, 255, 228, 0.3);
}

.blob-cr {
  width: 140px;
  height: 140px;
  top: 60%;
  right: 8%;
  background: rgba(255, 107, 107, 0.25);
}

/* 标题卡片 */
.title-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 28px 48px;
  box-shadow: 0 8px 32px rgba(255, 107, 53, 0.25);
  z-index: 1;
  max-width: 85%;
}

.title-main {
  font-size: 36px;
  font-weight: 700;
  color: #FF6B35;
  margin: 0;
  text-align: center;
  line-height: 1.4;
  letter-spacing: 1px;
}

/* 副标题 */
.title-sub {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.9);
  margin: 20px 0 0 0;
  z-index: 1;
  font-weight: 400;
  letter-spacing: 1.5px;
}

/* 波浪装饰 */
.wave-decor {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 8px;
  background: repeating-linear-gradient(
    90deg,
    #FFE66D 0px,
    #FFE66D 40px,
    transparent 40px,
    transparent 50px
  );
  opacity: 0.6;
}

/* ─── Content Slide ─── */
.content-slide {
  background: #FFF8F0;
  box-shadow: 0 2px 16px rgba(255, 140, 66, 0.08);
  border: 1px solid #FFE0C0;
  display: flex;
  flex-direction: column;
}

.content-header {
  background: linear-gradient(135deg, #FF8C42 0%, #FF6B35 100%);
  padding: 20px 32px;
  position: relative;
}

.content-header::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #FFE66D 0%, transparent 100%);
}

.content-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  line-height: 1.3;
  padding-left: 16px;
  border-left: 4px solid #FFE66D;
}

.content-body {
  flex: 1;
  padding: 28px 32px;
  display: flex;
  align-items: flex-start;
}

.content-card {
  width: 100%;
  background: #fff;
  border-radius: 10px;
  padding: 24px 32px;
  border: 1px solid #FFE0C0;
  box-shadow: 0 2px 8px rgba(255, 140, 66, 0.04);
}

/* Bullet 条目 */
.bullet-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid #FFF0E0;
}

.bullet-item:last-child {
  border-bottom: none;
}

.bullet-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  min-width: 26px;
  border-radius: 50%;
  background: #FF8C42;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.bullet-text {
  font-size: 17px;
  color: #3D2C2C;
  line-height: 1.7;
  font-weight: 400;
}

/* 侧边装饰彩条 */
.side-stripes {
  position: absolute;
  left: 0;
  top: 80px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stripe {
  display: block;
  width: 4px;
  height: 20px;
  border-radius: 0 3px 3px 0;
}

.stripe-1 { background: #FF8C42; }
.stripe-2 { background: #4ECDC4; }
.stripe-3 { background: #FFE66D; }
.stripe-4 { background: #FF6B6B; }

/* ─── Two-Column Slide ─── */
.two-col-slide {
  background: #FFF8F0;
  box-shadow: 0 2px 16px rgba(255, 140, 66, 0.08);
  border: 1px solid #FFE0C0;
  display: flex;
  flex-direction: column;
}

.two-col-header {
  background: linear-gradient(135deg, #FF8C42 0%, #FF6B35 100%);
  padding: 16px 28px;
}

.two-col-header::after {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, #FFE66D 0%, transparent 100%);
  margin-top: 8px;
}

.two-col-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  padding-left: 14px;
  border-left: 4px solid #FFE66D;
}

.two-col-body {
  flex: 1;
  display: flex;
  padding: 20px 16px;
  gap: 0;
  align-items: stretch;
}

.col-card {
  flex: 1;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.col-left {
  background: #FFF5EB;
  border: 1px solid #FFBF80;
  margin-right: 0;
}

.col-right {
  background: #E8F9F3;
  border: 1px solid #7EFFE4;
  margin-left: 0;
}

.col-card-header {
  padding: 12px 16px;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
}

.left-header {
  background: #FF8C42;
}

.right-header {
  background: #4ECDC4;
}

.col-card-icon {
  font-size: 10px;
}

.col-card-bullets {
  flex: 1;
  padding: 16px;
}

.col-bullet {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
  font-size: 15px;
  color: #3D2C2C;
  line-height: 1.6;
  border-bottom: 1px dashed rgba(255, 140, 66, 0.15);
}

.col-left .col-bullet {
  border-bottom-color: rgba(255, 140, 66, 0.15);
}

.col-right .col-bullet {
  border-bottom-color: rgba(78, 205, 196, 0.15);
}

.col-bullet:last-child {
  border-bottom: none;
}

.col-bullet-dot {
  color: #FF8C42;
  font-size: 12px;
  flex-shrink: 0;
  margin-top: 3px;
}

.right-dot {
  color: #4ECDC4;
}

.col-empty {
  padding: 20px;
  text-align: center;
  color: #8B7E7E;
  font-size: 14px;
}

/* 分隔线 */
.col-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  min-width: 40px;
  position: relative;
}

.col-divider::before {
  content: '';
  position: absolute;
  top: 10%;
  bottom: 10%;
  width: 2px;
  background: linear-gradient(180deg, #FFE66D, #FF8C42, #FFE66D);
  border-radius: 1px;
}

.col-divider span {
  background: #FFF8F0;
  padding: 8px 4px;
  font-size: 12px;
  font-weight: 800;
  color: #FF8C42;
  z-index: 1;
  letter-spacing: 1px;
}

/* ─── Chart Slide ─── */
.chart-slide {
  background: #FFF8F0;
  box-shadow: 0 2px 16px rgba(255, 140, 66, 0.08);
  border: 1px solid #FFE0C0;
  display: flex;
  flex-direction: column;
}

.chart-header {
  background: linear-gradient(135deg, #FF8C42 0%, #FF6B35 100%);
  padding: 16px 28px;
}

.chart-header::after {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, #FFE66D 0%, transparent 100%);
  margin-top: 8px;
}

.chart-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  padding-left: 14px;
  border-left: 4px solid #FFE66D;
}

.chart-body {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 16px;
  min-height: 360px;
}

.chart-container {
  flex: 1;
  min-width: 0;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #FFE0C0;
  overflow: hidden;
  position: relative;
}

.chart-canvas {
  width: 100%;
  height: 100%;
  min-height: 340px;
}

.chart-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #8B7E7E;
  font-size: 14px;
}

.chart-ph-icon {
  font-size: 48px;
  opacity: 0.4;
}

/* 右侧分析说明 */
.chart-insight {
  width: 280px;
  min-width: 260px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #FFBF80;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.insight-header {
  padding: 14px 16px;
  background: #FFF5EB;
  font-size: 16px;
  font-weight: 700;
  color: #FF8C42;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #FFE0C0;
}

.insight-icon {
  font-size: 18px;
}

.insight-bullets {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 0;
  font-size: 14px;
  color: #3D2C2C;
  line-height: 1.6;
  border-bottom: 1px solid #FFF0E0;
}

.insight-item:last-child {
  border-bottom: none;
}

.insight-arrow {
  color: #4ECDC4;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.insight-empty {
  padding: 20px;
  text-align: center;
  color: #8B7E7E;
  font-size: 14px;
}

/* ─── Summary Slide ─── */
.summary-slide {
  box-shadow: 0 4px 24px rgba(255, 140, 66, 0.12);
}

.summary-bg {
  position: relative;
  min-height: 420px;
  background: linear-gradient(160deg, #FFF8F0 0%, #FFE0C0 40%, #FFF5EB 70%, #FFE66D 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 32px 40px;
  overflow: hidden;
}

.blob-sum-tr {
  width: 220px;
  height: 220px;
  top: -80px;
  right: -50px;
  background: rgba(255, 140, 66, 0.12);
}

.blob-sum-bl {
  width: 160px;
  height: 160px;
  bottom: -50px;
  left: -40px;
  background: rgba(78, 205, 196, 0.12);
}

/* 总结标题卡片 */
.summary-title-card {
  background: #FF8C42;
  border-radius: 14px;
  padding: 16px 40px;
  box-shadow: 0 6px 20px rgba(255, 107, 53, 0.3);
  z-index: 1;
  margin-bottom: 24px;
}

.summary-main-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-align: center;
}

/* 总结要点 */
.summary-items {
  width: 100%;
  max-width: 750px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-radius: 10px;
  font-size: 16px;
  color: #3D2C2C;
  line-height: 1.5;
}

.summary-item-0 {
  background: rgba(255, 191, 128, 0.25);
}

.summary-item-1 {
  background: rgba(126, 255, 228, 0.2);
}

.summary-item-2 {
  background: rgba(255, 230, 109, 0.25);
}

.summary-item-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.summary-item-text {
  flex: 1;
}

.summary-empty {
  text-align: center;
  color: #8B7E7E;
  padding: 20px;
}

/* 波浪装饰 */
.wave-decor-sum {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background: repeating-linear-gradient(
    90deg,
    #FF8C42 0px,
    #FF8C42 35px,
    transparent 35px,
    transparent 45px
  );
  opacity: 0.35;
}

/* ─── 导航控件 ─── */
.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
  padding: 0 16px;
  flex-wrap: wrap;
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
  border-color: #d1d5db;
  color: #6b7280;
  background: #f9fafb;
}

.nav-btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
  background: #eef2ff;
  color: #6366f1;
  border-color: #a5b4fc;
}

.nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.download-btn {
  margin-left: 12px;
  background: #eef2ff !important;
  border-color: #c7d2fe !important;
  color: #6366f1 !important;
}

.download-btn:hover {
  background: #e0e7ff !important;
  color: #4f46e5 !important;
  border-color: #a5b4fc !important;
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
  background: #d1d5db;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}

.nav-dot.active {
  background: #a5b4fc;
  width: 28px;
  border-radius: 5px;
}

.nav-dot:hover:not(.active) {
  background: rgba(99, 102, 241, 0.4);
  transform: scale(1.3);
}

.nav-dot.dot-title.active { background: #f59e0b; }
.nav-dot.dot-two-col.active { background: #6366f1; }
.nav-dot.dot-chart.active { background: #ec4899; }
.nav-dot.dot-summary.active { background: #8b5cf6; }

/* ─── 键盘提示 ─── */
.keyboard-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 12px;
  color: #64748b;
  opacity: 0.6;
}

.keyboard-hint .el-icon {
  font-size: 14px;
}

/* ─── 老师讲解旁白区域 ─── */
.narration-section {
  margin-top: 20px;
  padding: 18px 22px;
  background: #f0f4ff;
  border: 1px solid #e0e7ff;
  border-radius: 12px;
  border-left: 4px solid #a5b4fc;
}

.narration-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 15px;
  font-weight: 600;
  color: #818cf8;
}

.narration-header .el-icon {
  font-size: 18px;
  color: #818cf8;
}

.narration-page-tag {
  margin-left: auto;
}

.narration-text {
  margin-bottom: 14px;
  padding: 14px 18px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px dashed #c7d2fe;
}

.narration-text p {
  margin: 0;
  font-size: 15px;
  color: #475569;
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
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  font-size: 13px;
  color: #92400e;
}

.narration-no-audio .el-icon {
  font-size: 15px;
}
</style>
