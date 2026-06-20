<template>
  <div class="mindmap-wrapper">
    <!-- loading -->
    <div v-if="loading" class="mm-status">
      <div class="mm-spinner" />
      <span>加载思维导图中…</span>
    </div>

    <!-- error -->
    <div v-else-if="error" class="mm-status mm-error">
      <span class="mm-error-icon">⚠</span>
      <span>{{ error }}</span>
      <button class="mm-retry-btn" @click="loadMindMap">重试</button>
    </div>

    <!-- empty placeholder when no data -->
    <div v-else-if="!chartReady" class="mm-placeholder">
      <div class="placeholder-icon">🗺️</div>
      <h3>思维导图</h3>
      <p>课程内容生成后将自动展示本章思维导图。</p>
    </div>

    <!-- chart -->
    <div ref="chartRef" class="mm-chart" v-show="chartReady" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  courseId: number
  mindmapData?: any  // preloaded data from parent
}>()

const chartRef = ref<HTMLDivElement>()
const loading = ref(false)
const error = ref('')
const chartReady = ref(false)

let chart: echarts.ECharts | null = null
let treeData: any = null
let resizeObserver: ResizeObserver | null = null

// ── convert mindmap JSON to ECharts tree format ──
function toTreeData(root: any): any {
  if (!root) return null
  return {
    name: root.name || '未命名',
    children: (root.children || []).map((c: any) => toTreeData(c)),
    collapsed: false,
  }
}

// ── render ECharts tree chart ──
async function renderChart() {
  console.log('[DEBUG MindMap] renderChart called:', { hasChartRef: !!chartRef.value, hasTreeData: !!treeData, chartReady: chartReady.value })
  if (!chartRef.value || !treeData) return

  // Make container visible first so it has layout dimensions
  chartReady.value = true
  await nextTick()

  const rect = chartRef.value.getBoundingClientRect()
  console.log('[DEBUG MindMap] chart container rect:', rect.width, 'x', rect.height)
  if (rect.width === 0 || rect.height === 0) {
    console.warn('[DEBUG MindMap] container still 0 size, retrying...')
    requestAnimationFrame(() => renderChart())
    return
  }

  chart ??= echarts.init(chartRef.value)
  console.log('[DEBUG MindMap] chart initialized, setting option...')

  chart.setOption(
    {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => params.name,
      },
      series: [
        {
          type: 'tree',
          data: [treeData],
          top: '5%',
          left: '8%',
          bottom: '5%',
          right: '15%',
          symbolSize: 10,
          orient: 'LR',
          label: {
            position: 'right',
            verticalAlign: 'middle',
            align: 'left',
            fontSize: 13,
            color: '#333',
          },
          leaves: {
            label: {
              position: 'right',
              verticalAlign: 'middle',
              align: 'left',
            },
          },
          emphasis: {
            focus: 'descendant',
          },
          expandAndCollapse: true,
          animationDuration: 550,
          animationDurationUpdate: 400,
          initialTreeDepth: 2,
          roam: true,
        },
      ],
    },
    { notMerge: true },
  )

  console.log('[DEBUG MindMap] rendering complete')
}

// ── load mindmap data ──
async function loadMindMap() {
  // If parent provided preloaded data, use it directly
  if (props.mindmapData?.root) {
    treeData = toTreeData(props.mindmapData.root)
    await nextTick()
    await renderChart()
    return
  }

  // Otherwise fetch from API for course-level mindmap
  loading.value = true
  error.value = ''
  chartReady.value = false
  treeData = null

  try {
    // Try to get mindmap from knowledge graph data
    const { getKnowledgeGraph } = await import('@/api/knowledge')
    const { data } = await getKnowledgeGraph(props.courseId)
    const nodes = data.nodes || []

    if (nodes.length === 0) {
      chartReady.value = false
      return
    }

    // Build tree from knowledge nodes: root = course, children = nodes
    treeData = {
      name: '课程知识点',
      children: nodes.map((n: any) => ({
        name: n.name,
        children: [],
        collapsed: false,
      })),
      collapsed: false,
    }

    await nextTick()
    await renderChart()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || '加载思维导图失败'
  } finally {
    loading.value = false
  }
}

// ── watch mindmapData prop ──
watch(
  () => props.mindmapData,
  (val, oldVal) => {
    console.log('[DEBUG MindMap] watch triggered:', {
      hasVal: !!val,
      hasRoot: !!val?.root,
      rootName: val?.root?.name,
      oldHasRoot: !!oldVal?.root,
      oldRootName: oldVal?.root?.name,
    })
    if (val?.root) {
      treeData = toTreeData(val.root)
      console.log('[DEBUG MindMap] treeData set:', JSON.stringify(treeData).substring(0, 200))
      nextTick(async () => renderChart())
    }
  },
  { immediate: true },
)

onMounted(() => {
  console.log('[DEBUG MindMap] onMounted, mindmapData:', {
    hasProp: !!props.mindmapData,
    hasRoot: !!props.mindmapData?.root,
    rootName: props.mindmapData?.root?.name,
  })
  if (!props.mindmapData?.root) {
    console.log('[DEBUG MindMap] no root in prop, calling loadMindMap()')
    loadMindMap()
  }
  // Use ResizeObserver to detect container size changes (e.g. sidebar collapse/expand)
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<style scoped>
.mindmap-wrapper {
  flex: 1;
  min-height: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #fff;
  border-radius: 8px;
}

.mm-chart {
  width: 100%;
  height: 480px;
}

.mm-placeholder {
  text-align: center;
  color: #999;
}
.placeholder-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
.mm-placeholder h3 {
  font-size: 20px;
  color: #666;
  margin: 0 0 8px;
}
.mm-placeholder p {
  font-size: 14px;
  margin: 0;
}

/* status */
.mm-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: #666;
  font-size: 14px;
}
.mm-error { color: #d32f2f; }
.mm-error-icon { font-size: 36px; }
.mm-retry-btn {
  padding: 6px 20px;
  border: 1px solid #d32f2f;
  border-radius: 4px;
  background: #fff;
  color: #d32f2f;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.mm-retry-btn:hover {
  background: #d32f2f;
  color: #fff;
}

.mm-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: mm-spin 0.8s linear infinite;
}
@keyframes mm-spin {
  to { transform: rotate(360deg); }
}
</style>
