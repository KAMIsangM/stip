<template>
  <div ref="chartRef" class="graph" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { getKnowledgeGraph } from '@/api/knowledge'

const props = defineProps<{ courseId: number }>()
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

async function loadGraph() {
  const { data } = await getKnowledgeGraph(props.courseId)
  if (!chartRef.value) return
  chart ??= echarts.init(chartRef.value)
  chart.setOption({
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        data: (data.nodes || []).map((n: { id: number; name: string }) => ({
          id: String(n.id),
          name: n.name,
          symbolSize: 40,
        })),
        links: (data.edges || []).map(
          (e: { source_node_id: number; target_node_id: number; relation_type: string }) => ({
            source: String(e.source_node_id),
            target: String(e.target_node_id),
            label: { show: true, formatter: e.relation_type },
          }),
        ),
        force: { repulsion: 200, edgeLength: 120 },
      },
    ],
  })
}

onMounted(loadGraph)
watch(() => props.courseId, loadGraph)
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.graph {
  width: 100%;
  height: 480px;
  background: #fff;
  border-radius: 8px;
}
</style>
