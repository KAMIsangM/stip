<template>
  <el-card class="progress-card" shadow="never">
    <div class="row">
      <span>生成进度</span>
      <el-tag size="small">{{ status }}</el-tag>
    </div>
    <el-progress :percentage="percentage" :stroke-width="8" />
    <p class="step">{{ stepLabel }}</p>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{ courseId: number }>()

const currentStep = ref(0)
const totalSteps = ref(6)
const status = ref('pending')
const stepName = ref('等待开始')

const percentage = computed(() =>
  totalSteps.value ? Math.round((currentStep.value / totalSteps.value) * 100) : 0,
)
const stepLabel = computed(() => `${stepName.value} (${currentStep.value}/${totalSteps.value})`)

// TODO: WebSocket /ws/v1/generation/{courseId} with HTTP poll fallback
void props.courseId
</script>

<style scoped>
.progress-card {
  margin: 16px;
}
.row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.step {
  margin: 8px 0 0;
  font-size: 13px;
  color: #666;
}
</style>
