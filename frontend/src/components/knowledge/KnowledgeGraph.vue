<template>
  <div class="kg-wrapper">
    <!-- loading -->
    <div v-if="loading" class="kg-status">
      <div class="kg-spinner" />
      <span>加载知识图谱中…</span>
    </div>

    <!-- error -->
    <div v-else-if="error" class="kg-status kg-error">
      <span class="kg-error-icon">⚠</span>
      <span>{{ error }}</span>
      <button class="kg-retry-btn" @click="loadGraph">重试</button>
    </div>

    <!-- empty -->
    <div v-else-if="nodeCount === 0" class="kg-status kg-empty">
      <span>暂无知识图谱数据</span>
    </div>

    <!-- main content: chart + detail panel -->
    <div v-show="nodeCount > 0" class="kg-body">
      <!-- chart -->
      <div ref="chartRef" class="graph" />

      <!-- node detail panel -->
      <transition name="slide" @after-enter="onDetailEnter" @after-leave="onDetailLeave">
        <div v-if="selectedNode" class="kg-detail">
          <button class="detail-close" @click="clearSelection">✕</button>

          <div class="detail-header">
            <div class="detail-type-badge" :style="{ background: typeColor(selectedNode.type) }">
              {{ typeLabel(selectedNode.type) }}
            </div>
            <h3 class="detail-title">{{ selectedNode.name }}</h3>
          </div>

          <div class="detail-section">
            <span class="detail-label">重要度</span>
            <div class="detail-bar-wrap">
              <div
                class="detail-bar"
                :style="{ width: (selectedNode.importance ?? 0.5) * 100 + '%' }"
              />
            </div>
            <span class="detail-value">{{ ((selectedNode.importance ?? 0.5) * 100).toFixed(0) }}%</span>
          </div>

          <div v-if="selectedNode.description" class="detail-section">
            <span class="detail-label">描述</span>
            <p class="detail-desc">{{ selectedNode.description }}</p>
          </div>

          <!-- predecessors -->
          <div v-if="predecessors.length" class="detail-section">
            <span class="detail-label">前驱节点（依赖）</span>
            <div class="detail-node-list">
              <button
                v-for="n in predecessors"
                :key="n.id"
                class="detail-node-btn"
                @click="selectNode(n)"
              >
                {{ n.name }}
              </button>
            </div>
          </div>

          <!-- successors -->
          <div v-if="successors.length" class="detail-section">
            <span class="detail-label">后继节点（被依赖）</span>
            <div class="detail-node-list">
              <button
                v-for="n in successors"
                :key="n.id"
                class="detail-node-btn"
                @click="selectNode(n)"
              >
                {{ n.name }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- shortest-path finder -->
    <div v-if="nodeCount > 0" class="kg-path-finder">
      <div class="path-finder-row">
        <span class="path-finder-label">最短学习路径</span>
        <div class="path-finder-selects">
          <span class="path-finder-hint">起点</span>
          <select
            v-model="pathSource"
            class="path-finder-select"
            @change="onPathSourceChange"
          >
            <option :value="null" disabled>选择起点…</option>
            <option v-for="n in cachedNodes" :key="n.id" :value="n.id">
              {{ n.name }}
            </option>
          </select>
          <span class="path-finder-arrow">→</span>
          <span class="path-finder-hint">终点</span>
          <select
            v-model="pathTarget"
            class="path-finder-select"
            @change="onPathTargetChange"
          >
            <option :value="null" disabled>选择终点…</option>
            <option v-for="n in cachedNodes" :key="n.id" :value="n.id">
              {{ n.name }}
            </option>
          </select>
        </div>
        <button
          class="kg-ctrl-btn path-find-btn"
          :disabled="!pathSource || !pathTarget || pathSource === pathTarget || pathLoading"
          @click="findShortestPath"
        >
          {{ pathLoading ? '查找中…' : '查找路径' }}
        </button>
        <button
          v-if="pathResult !== null"
          class="kg-ctrl-btn path-clear-btn"
          @click="clearPathResult"
        >
          清除路径
        </button>
      </div>

      <!-- path result bar -->
      <transition name="path-fade">
        <div v-if="pathError" class="path-result path-error">
          {{ pathError }}
        </div>
        <div v-else-if="pathResult && pathResult.length > 0" class="path-result path-success">
          <span class="path-result-label">学习路径 ({{ pathResult.length }} 步)：</span>
          <span class="path-result-nodes">
            <!-- eslint-disable-next-line vue/no-v-for-template-key -->
            <template v-for="(nodeId, idx) in pathResult" :key="nodeId">
              <button
                class="path-node-btn"
                :style="{ background: typeColor(getNodeById(nodeId)?.type || 'concept') }"
                @click="selectNode(getNodeById(nodeId))"
              >
                {{ getNodeById(nodeId)?.name || nodeId }}
              </button>
              <span v-if="idx < pathResult.length - 1" class="path-node-arrow">→</span>
            </template>
          </span>
        </div>
      </transition>
    </div>

    <!-- legend + controls -->
    <div v-if="nodeCount > 0" class="kg-footer">
      <div class="kg-legend">
        <span class="legend-item"><i style="background:#5470c6" />概念</span>
        <span class="legend-item"><i style="background:#91cc75" />技能</span>
        <span class="legend-item"><i style="background:#fac858" />记忆</span>
        <span class="legend-item"><i style="background:#ee6666" />实践</span>
        <span class="legend-item"><i style="background:#fc8452" />综合</span>
        <span class="legend-item" style="margin-left:8px;color:#999;font-size:11px">
          {{ cachedNodes?.length || 0 }} 节点 / {{ cachedEdges?.length || 0 }} 边
        </span>
      </div>
      <div class="kg-controls">
        <button
          v-for="lt in ['force', 'circular']"
          :key="lt"
          class="kg-ctrl-btn"
          :class="{ active: currentLayout === lt }"
          @click="switchLayout(lt)"
        >
          {{ lt === 'force' ? '力导向' : '环形' }}
        </button>
        <button class="kg-ctrl-btn" @click="resetView">重置视图</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { getKnowledgeGraph, getShortestPath } from '@/api/knowledge'

const props = defineProps<{ courseId: number }>()

const chartRef = ref<HTMLDivElement>()
const loading = ref(false)
const error = ref('')
const nodeCount = ref(0)
const selectedNode = ref<any>(null)
const predecessors = ref<any[]>([])
const successors = ref<any[]>([])
const currentLayout = ref<string>('force')

// ── shortest-path state ──
const pathSource = ref<number | null>(null)
const pathTarget = ref<number | null>(null)
const pathLoading = ref(false)
const pathResult = ref<number[] | null>(null)
const pathError = ref('')

let chart: echarts.ECharts | null = null
let cachedNodes: any[] = []
let cachedEdges: any[] = []
let cachedLayout: any = {}
let resizeObserver: ResizeObserver | null = null

// ── helpers ──
function typeColor(type: string) {
  return { '概念': '#5470c6', '技能': '#91cc75', '记忆': '#fac858', '实践': '#ee6666', '综合': '#fc8452' }[type] || '#999'
}
function typeLabel(type: string) {
  return { '概念': '概念', '技能': '技能', '记忆': '记忆', '实践': '实践', '综合': '综合' }[type] || type
}

// ── compute predecessors / successors from cached data ──
function computeRelations(nodeId: number) {
  const sid = String(nodeId)
  predecessors.value = cachedEdges
    .filter(e => String(e.target) === sid)
    .map(e => cachedNodes.find(n => String(n.id) === String(e.source)))
    .filter(Boolean)
  successors.value = cachedEdges
    .filter(e => String(e.source) === sid)
    .map(e => cachedNodes.find(n => String(n.id) === String(e.target)))
    .filter(Boolean)
}

function selectNode(node: any) {
  selectedNode.value = node
  computeRelations(node.id)
  // highlight in chart
  if (chart) {
    chart.dispatchAction({ type: 'focusNodeAdjacency', seriesIndex: 0, dataIndex: getNodeIndex(node.id) })
  }
  // resize chart after detail panel appears
  nextTick(() => {
    chart?.resize()
  })
}

function clearSelection() {
  selectedNode.value = null
  predecessors.value = []
  successors.value = []
  chart?.dispatchAction({ type: 'unfocusNodeAdjacency', seriesIndex: 0 })
  // resize chart after detail panel is removed
  nextTick(() => {
    chart?.resize()
  })
}

function getNodeIndex(nodeId: number) {
  return cachedNodes.findIndex(n => n.id === nodeId)
}

function getNodeById(nodeId: number) {
  return cachedNodes.find(n => n.id === nodeId)
}

// ── shortest-path logic ──
function onPathSourceChange() {
  // sync with chart highlight
  if (chart && pathSource.value) {
    highlightPathNodes()
  }
}

function onPathTargetChange() {
  if (chart && pathTarget.value) {
    highlightPathNodes()
  }
}

function highlightPathNodes() {
  if (!chart) return

  // First reset all node highlights
  chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
  chart.dispatchAction({ type: 'unfocusNodeAdjacency', seriesIndex: 0 })

  // Highlight source and target nodes
  const actions: any[] = []
  if (pathSource.value !== null) {
    const srcIdx = getNodeIndex(pathSource.value)
    if (srcIdx >= 0) {
      actions.push({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: srcIdx,
      })
    }
  }
  if (pathTarget.value !== null) {
    const tgtIdx = getNodeIndex(pathTarget.value)
    if (tgtIdx >= 0) {
      actions.push({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: tgtIdx,
      })
    }
  }
  if (actions.length > 0) {
    chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
    actions.forEach(a => chart!.dispatchAction(a))
  }
}

async function findShortestPath() {
  if (!pathSource.value || !pathTarget.value || pathSource.value === pathTarget.value) return

  pathLoading.value = true
  pathError.value = ''
  pathResult.value = null

  try {
    const { data } = await getShortestPath(props.courseId, pathSource.value, pathTarget.value)
    if (data.path && data.path.length > 0) {
      pathResult.value = data.path
      applyPathHighlight(data.path)
    } else {
      pathError.value = data.message || '未找到从起点到终点的学习路径'
      pathResult.value = null
      clearPathHighlight()
    }
  } catch (err: any) {
    pathError.value = err?.response?.data?.detail || err?.message || '查询路径失败'
    pathResult.value = null
    clearPathHighlight()
  } finally {
    pathLoading.value = false
  }
}

function applyPathHighlight(pathNodeIds: number[]) {
  if (!chart || pathNodeIds.length === 0) return

  const pathEdgeSet = new Set<string>()

  // Build edge keys for edges on the path
  for (let i = 0; i < pathNodeIds.length - 1; i++) {
    const from = String(pathNodeIds[i])
    const to = String(pathNodeIds[i + 1])
    pathEdgeSet.add(`${from}->${to}`)
  }

  // Downplay all first
  chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
  chart.dispatchAction({ type: 'unfocusNodeAdjacency', seriesIndex: 0 })

  // Highlight path nodes
  pathNodeIds.forEach(nodeId => {
    const idx = getNodeIndex(nodeId)
    if (idx >= 0) {
      chart!.dispatchAction({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: idx,
      })
    }
  })

  // Highlight path edges by dispatching highlight on edges
  // ECharts graph edges: we can use the dataIndex based on edge order
  pathEdgeSet.forEach(edgeKey => {
    const edgeIdx = cachedEdges.findIndex(
      e => `${String(e.source)}->${String(e.target)}` === edgeKey
    )
    if (edgeIdx >= 0) {
      chart!.dispatchAction({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: cachedNodes.length + edgeIdx,
      })
    }
  })

  // Focus on path nodes adjacency to dim non-path nodes
  pathNodeIds.forEach(nodeId => {
    const idx = getNodeIndex(nodeId)
    if (idx >= 0) {
      chart!.dispatchAction({
        type: 'focusNodeAdjacency',
        seriesIndex: 0,
        dataIndex: idx,
      })
    }
  })
}

function clearPathHighlight() {
  if (!chart) return
  chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
  chart.dispatchAction({ type: 'unfocusNodeAdjacency', seriesIndex: 0 })
}

function clearPathResult() {
  pathResult.value = null
  pathError.value = ''
  pathSource.value = null
  pathTarget.value = null
  clearPathHighlight()
}

// ── detail panel transition hooks ──
function onDetailEnter() {
  nextTick(() => chart?.resize())
}
function onDetailLeave() {
  nextTick(() => chart?.resize())
}

// ── layout switching ──
function switchLayout(layout: string) {
  currentLayout.value = layout
  cachedLayout.layout = layout
  // Update the chart series layout
  if (chart) {
    const option: any = {
      series: [{
        type: 'graph',
        layout: layout,
        force: layout === 'force' ? (cachedLayout.force || {}) : undefined,
        circular: layout === 'circular' ? (cachedLayout.circular || {}) : undefined,
      }],
    }
    // Only set circular rotateLabel if circular
    if (layout === 'circular') {
      option.series[0].circular = { rotateLabel: true }
    }
    chart.setOption(option, { notMerge: false })
  }
}

function resetView() {
  currentLayout.value = 'force'
  cachedLayout.layout = 'force'
  // Fully re-render with original data and layout
  if (chart) {
    chart.dispose()
    chart = null
    nextTick(() => renderChart())
  }
}

// ── chart init helper ──
function renderChart() {
  if (!chartRef.value) return
  if (cachedNodes.length === 0) return

  const rect = chartRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    requestAnimationFrame(() => renderChart())
    return
  }

  chart ??= echarts.init(chartRef.value)

  chart.setOption(
    {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'edge') {
            return `${params.data.label?.formatter || params.data.relation_type || ''}`
          }
          const d = params.data || {}
          return `<b>${d.name}</b><br/>类型: ${typeLabel(d.type)}<br/>重要度: ${((d.importance ?? 0.5) * 100).toFixed(0)}%${d.description ? '<br/>' + d.description : ''}`
        },
      },
      series: [
        {
          type: 'graph',
          layout: cachedLayout.layout || 'force',
          roam: cachedLayout.roam ?? true,
          ...(cachedLayout.force ? { force: cachedLayout.force } : {}),
          ...(cachedLayout.circular ? { circular: cachedLayout.circular } : {}),
          draggable: true,
          emphasis: {
            focus: 'adjacency',
            scale: 1.8,
            label: { fontSize: 14, fontWeight: 'bold' },
          },
          data: cachedNodes.map(
            (n: any) => ({
              id: String(n.id),
              name: n.name,
              type: n.type,
              importance: n.importance,
              description: n.description,
              symbolSize: n.symbolSize || 40,
              itemStyle: n.itemStyle || {},
              label: { show: true, fontSize: 11 },
            }),
          ),
          links: cachedEdges.map(
            (e: any) => ({
              source: String(e.source),
              target: String(e.target),
              relation_type: e.relation_type,
              lineStyle: e.lineStyle || { color: '#aaa', width: 1 },
              label: e.label || { show: true, formatter: e.relation_type, fontSize: 10 },
            }),
          ),
        },
      ],
    },
    { notMerge: true },
  )

  // click → open detail panel
  chart.off('click')
  chart.on('click', (params: any) => {
    if (params.dataType === 'node') {
      const nodeData = cachedNodes.find(n => String(n.id) === String(params.data.id))
      if (nodeData) selectNode(nodeData)
    }
  })
}

// ── main loader ──
async function loadGraph() {
  loading.value = true
  error.value = ''
  selectedNode.value = null
  clearPathResult()
  try {
    const { data } = await getKnowledgeGraph(props.courseId)
    cachedNodes = data.nodes || []
    cachedEdges = data.edges || []
    cachedLayout = data.layout_config || {}
    currentLayout.value = cachedLayout.layout || 'force'
    nodeCount.value = cachedNodes.length

    if (nodeCount.value === 0) return

    if (chartRef.value) {
      renderChart()
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || '加载知识图谱失败'
    nodeCount.value = 0
  } finally {
    loading.value = false
  }
}

function handleResize() {
  chart?.resize()
}

function setupResizeObserver() {
  if (!chartRef.value) return
  resizeObserver?.disconnect()
  resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)
}

// ── watchers ──
watch(chartRef, () => {
  if (chartRef.value && cachedNodes.length > 0) {
    nextTick(() => {
      renderChart()
      setupResizeObserver()
    })
  }
})

watch(
  () => props.courseId,
  async () => {
    chart?.dispose()
    chart = null
    cachedNodes = []
    cachedEdges = []
    cachedLayout = {}
    selectedNode.value = null
    await nextTick()
    loadGraph()
  },
)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  chart?.dispose()
})

loadGraph()
window.addEventListener('resize', handleResize)
// Setup ResizeObserver after initial render (chartRef will be available in nextTick)
nextTick(() => setupResizeObserver())
</script>

<style scoped>
.kg-wrapper {
  position: relative;
  width: 100%;
  height: 520px;
  display: flex;
  flex-direction: column;
}

.kg-body {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;
}

.graph {
  flex: 1;
  min-height: 0;
  background: #fff;
  border-radius: 8px;
}

/* ── status overlay ── */
.kg-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 480px;
  color: #666;
  gap: 12px;
  font-size: 14px;
}
.kg-error { color: #d32f2f; }
.kg-error-icon { font-size: 36px; }
.kg-retry-btn {
  padding: 6px 20px;
  border: 1px solid #d32f2f;
  border-radius: 4px;
  background: #fff;
  color: #d32f2f;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.kg-retry-btn:hover {
  background: #d32f2f;
  color: #fff;
}

/* ── spinner ── */
.kg-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #5470c6;
  border-radius: 50%;
  animation: kg-spin 0.8s linear infinite;
}
@keyframes kg-spin {
  to { transform: rotate(360deg); }
}

/* ── shortest-path finder ── */
.kg-path-finder {
  background: #f8f9fb;
  border-bottom: 1px solid #eee;
  padding: 10px 16px;
  flex-shrink: 0;
}
.path-finder-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.path-finder-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}
.path-finder-selects {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.path-finder-hint {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}
.path-finder-arrow {
  font-size: 16px;
  color: #5470c6;
  font-weight: bold;
}
.path-finder-select {
  flex: 1;
  min-width: 120px;
  max-width: 220px;
  padding: 5px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  background: #fff;
  color: #333;
  cursor: pointer;
  outline: none;
}
.path-finder-select:focus {
  border-color: #5470c6;
}
.path-find-btn {
  white-space: nowrap;
}
.path-find-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.path-clear-btn {
  white-space: nowrap;
  color: #d32f2f;
  border-color: #d32f2f;
}
.path-clear-btn:hover {
  background: #d32f2f;
  color: #fff;
}

/* path result */
.path-result {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.path-error {
  background: #fff3f3;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
}
.path-success {
  background: #f0f9f4;
  color: #333;
  border: 1px solid #c8e6c9;
}
.path-result-label {
  font-weight: 600;
  color: #2e7d32;
  white-space: nowrap;
}
.path-result-nodes {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.path-node-btn {
  padding: 3px 10px;
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.path-node-btn:hover {
  opacity: 0.8;
}
.path-node-arrow {
  font-size: 12px;
  color: #999;
}

/* path result fade transition */
.path-fade-enter-active,
.path-fade-leave-active {
  transition: all 0.25s ease;
}
.path-fade-enter-from,
.path-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── footer: legend + controls ── */
.kg-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fff;
  border-top: 1px solid #eee;
  border-radius: 0 0 8px 8px;
  flex-shrink: 0;
}
.kg-legend {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: #555;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.legend-item i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.kg-controls {
  display: flex;
  gap: 6px;
}
.kg-ctrl-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.kg-ctrl-btn:hover {
  border-color: #5470c6;
  color: #5470c6;
}
.kg-ctrl-btn.active {
  background: #5470c6;
  color: #fff;
  border-color: #5470c6;
}

/* ── detail panel ── */
.kg-detail {
  width: 300px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #eee;
  border-radius: 0 8px 8px 0;
  padding: 20px 16px;
  overflow-y: auto;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
  position: relative;
  margin-left: 8px;
}

.detail-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
  line-height: 1;
}
.detail-close:hover { color: #333; }

.detail-header {
  margin-bottom: 16px;
}
.detail-type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  color: #fff;
  font-size: 12px;
  margin-bottom: 8px;
}
.detail-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #222;
}

.detail-section {
  margin-bottom: 16px;
}
.detail-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}
.detail-value {
  font-size: 14px;
  color: #333;
}
.detail-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

/* importance bar */
.detail-bar-wrap {
  display: inline-block;
  width: 70%;
  height: 8px;
  background: #eee;
  border-radius: 4px;
  vertical-align: middle;
  margin-right: 8px;
}
.detail-bar {
  height: 100%;
  background: linear-gradient(90deg, #91cc75, #5470c6);
  border-radius: 4px;
  transition: width 0.4s ease;
}

/* node list buttons */
.detail-node-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.detail-node-btn {
  padding: 4px 10px;
  border: 1px solid #ddd;
  border-radius: 12px;
  background: #fafafa;
  color: #555;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.detail-node-btn:hover {
  background: #5470c6;
  color: #fff;
  border-color: #5470c6;
}

/* ── slide transition ── */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
