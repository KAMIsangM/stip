<template>
  <div class="interactive-viewer">
    <!-- Title -->
    <h2 v-if="title" class="iv-title">{{ title }}</h2>

    <!-- Animation Cards Grid -->
    <div v-if="animations.length > 0" class="iv-animation-section">
      <h3 class="iv-section-title">
        <span class="section-icon">🎬</span> 知识点动画演示
        <el-tag size="small" type="info" effect="plain">{{ animations.length }} 个动画</el-tag>
      </h3>
      <div class="anim-grid">
        <div
          v-for="(anim, ai) in animations"
          :key="ai"
          class="anim-card"
          @click="openAnimation(ai)"
        >
          <div class="anim-card-icon">
            <span v-if="anim.animation_type === 'sort_animation'">📊</span>
            <span v-else-if="anim.animation_type === 'data_structure'">🔗</span>
            <span v-else-if="anim.animation_type === 'flowchart_step'">🔄</span>
            <span v-else-if="anim.animation_type === 'formula_derivation'">📐</span>
            <span v-else-if="anim.animation_type === 'code_execution'">💻</span>
            <span v-else>🎯</span>
          </div>
          <div class="anim-card-body">
            <div class="anim-card-title">{{ anim.title }}</div>
            <div class="anim-card-desc">{{ anim.description }}</div>
            <div class="anim-card-kp">
              <el-tag size="small" :type="getAnimTagType(anim.animation_type)">
                {{ getAnimTypeLabel(anim.animation_type) }}
              </el-tag>
              <span class="kp-name">{{ anim.knowledge_point }}</span>
            </div>
          </div>
          <div class="anim-card-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- Exercises Section -->
    <div v-if="exercises.length > 0" class="iv-exercise-section">
      <h3 class="iv-section-title">
        <span class="section-icon">✏️</span> 互动练习
        <el-tag size="small" type="warning" effect="plain">{{ exercises.length }} 题</el-tag>
      </h3>

      <div v-for="(exercise, ei) in exercises" :key="'ex' + ei" class="ex-card">
        <el-alert
          :title="exercise.instruction || '互动练习'"
          type="info"
          :closable="false"
          show-icon
        />

        <!-- Drag sort exercise -->
        <div v-if="exercise.type === 'drag_sort'" class="ex-drag-sort">
          <div
            v-for="(item, idx) in sortState[ei] || []"
            :key="item"
            class="sort-item"
            draggable="true"
            @dragstart="onDragStart(ei, idx, $event)"
            @dragover="onDragOver($event)"
            @drop="onDrop(ei, idx, $event)"
            @dragend="onDragEnd"
          >
            <span class="sort-handle">⠿</span>
            <span class="sort-num">{{ idx + 1 }}</span>
            <span class="sort-label">{{ item }}</span>
          </div>
          <el-button
            size="small"
            type="primary"
            plain
            class="sort-check-btn"
            @click="checkSortAnswer(ei, exercise)"
          >
            检查答案
          </el-button>
          <div v-if="sortResults[ei] !== undefined" class="ex-result" :class="sortResults[ei] ? 'correct' : 'wrong'">
            {{ sortResults[ei] ? '✓ 排序正确！' : '✗ 排序不正确，请重试' }}
          </div>
          <div v-if="sortResults[ei] !== undefined && !sortResults[ei]" class="ex-hint">
            正确顺序：{{ getExerciseItems(exercise)?.join(' → ') }}
          </div>
        </div>

        <!-- Fill blank exercise -->
        <div v-else-if="exercise.type === 'fill_blank'" class="ex-fill-blank">
          <div v-for="(blank, bi) in getExerciseBlanks(exercise)" :key="bi" class="blank-row">
            <label>{{ blank.prompt || `填空 ${bi + 1}` }}</label>
            <el-input
              v-model="fillAnswers[`${ei}-${bi}`]"
              :placeholder="blank.placeholder || '请输入答案'"
              size="small"
              class="blank-input"
              @change="() => checkFillAnswer(ei, exercise)"
            />
            <span
              v-if="fillResults[`${ei}-${bi}`] !== undefined"
              class="blank-feedback"
              :class="fillResults[`${ei}-${bi}`] ? 'correct' : 'wrong'"
            >
              {{ fillResults[`${ei}-${bi}`] ? '✓' : `✗ (答案: ${blank.answer})` }}
            </span>
          </div>
        </div>

        <!-- Choice exercise -->
        <div v-else-if="exercise.type === 'choice'" class="ex-choice">
          <p class="ex-question">{{ getExerciseQuestion(exercise) }}</p>
          <el-radio-group
            v-model="choiceAnswers[ei]"
            @change="() => checkChoiceAnswer(ei, exercise)"
          >
            <el-radio
              v-for="(opt, oi) in getExerciseOptions(exercise)"
              :key="oi"
              :value="typeof opt === 'string' ? opt[0] : opt.value"
            >
              {{ typeof opt === 'string' ? opt : opt.label }}
            </el-radio>
          </el-radio-group>
          <div v-if="choiceResults[ei] !== undefined" class="ex-result" :class="choiceResults[ei] ? 'correct' : 'wrong'">
            {{ choiceResults[ei] ? '✓ 回答正确！' : '✗ 回答错误' }}
            <span v-if="!choiceResults[ei] && (exercise as any).explanation">
              — {{ (exercise as any).explanation }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Glossary -->
    <div v-if="glossary.length" class="iv-glossary">
      <h3 class="iv-section-title">
        <span class="section-icon">📖</span> 术语表
      </h3>
      <div class="glossary-grid">
        <div v-for="(term, ti) in glossary" :key="ti" class="glossary-item">
          <el-tag size="small" effect="plain" type="info">{{ term.term }}</el-tag>
          <span class="glossary-def">{{ term.definition }}</span>
        </div>
      </div>
    </div>

    <!-- Animation Viewer Dialog -->
    <el-dialog
      v-model="animDialogVisible"
      :title="currentAnim?.title || '动画演示'"
      width="95%"
      top="2vh"
      :close-on-click-modal="false"
      destroy-on-close
      class="anim-dialog"
    >
      <template #header="{ close, titleId, titleClass }">
        <div class="dialog-header">
          <div class="dialog-header-left">
            <span class="dialog-kp-tag">
              <el-tag size="small" :type="currentAnim ? getAnimTagType(currentAnim.animation_type) : 'info'">
                {{ currentAnim ? getAnimTypeLabel(currentAnim.animation_type) : '' }}
              </el-tag>
            </span>
            <span :id="titleId" :class="titleClass" class="dialog-title-text">{{ currentAnim?.title }}</span>
          </div>
        </div>
      </template>

      <div v-if="currentAnim" class="anim-frame-wrapper">
        <div class="anim-frame-controls">
          <el-button-group>
            <el-button size="small" @click="animReloadKey++" :icon="RefreshRight">
              刷新动画
            </el-button>
            <el-button size="small" @click="openInNewTab" :icon="TopRight">
              新窗口打开
            </el-button>
          </el-button-group>
          <span class="anim-kp-label">{{ currentAnim.knowledge_point }}</span>
        </div>
        <div class="anim-frame-container">
          <iframe
            v-if="currentAnimHtmlPath"
            :key="animReloadKey"
            :src="currentAnimHtmlPath"
            class="anim-iframe"
            sandbox="allow-scripts allow-same-origin"
            frameborder="0"
          />
          <div v-else class="anim-no-file">
            <el-icon :size="48"><VideoPlay /></el-icon>
            <p>动画文件暂未生成</p>
            <p class="hint">请先生成互动教材内容</p>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ArrowRight, Close, RefreshRight, TopRight, VideoPlay } from '@element-plus/icons-vue'
import type { AnimationItem, InteractiveExercise, GlossaryTerm, AnimationType } from '@/types/interactive'

// ===== Props =====
const props = withDefaults(defineProps<{
  title?: string
  animations?: AnimationItem[]
  htmlFiles?: string[]
  exercises?: InteractiveExercise[]
  glossary?: GlossaryTerm[]
}>(), {
  animations: () => [],
  htmlFiles: () => [],
  exercises: () => [],
  glossary: () => [],
})

// ===== Animation dialog state =====
const animDialogVisible = ref(false)
const currentAnimIndex = ref(-1)
const animReloadKey = ref(0)

const currentAnim = computed(() => {
  if (currentAnimIndex.value >= 0 && currentAnimIndex.value < props.animations.length) {
    return props.animations[currentAnimIndex.value]
  }
  return null
})

const currentAnimHtmlPath = computed(() => {
  if (!currentAnim.value) return null
  // Try html_path first, then look up in htmlFiles array by index
  if (currentAnim.value.html_path) return currentAnim.value.html_path
  if (props.htmlFiles.length > currentAnimIndex.value) {
    return props.htmlFiles[currentAnimIndex.value]
  }
  return null
})

function openAnimation(index: number) {
  currentAnimIndex.value = index
  animReloadKey.value++
  animDialogVisible.value = true
}

function openInNewTab() {
  if (currentAnimHtmlPath.value) {
    window.open(currentAnimHtmlPath.value, '_blank')
  }
}

// ===== Exercise state =====
const sortState = ref<string[][]>([])
const sortResults = ref<Record<number, boolean>>({})
const fillAnswers = ref<Record<string, string>>({})
const fillResults = ref<Record<string, boolean>>({})
const choiceAnswers = ref<Record<number, string>>({})
const choiceResults = ref<Record<number, boolean>>({})

// HTML5 drag-and-drop state
const dragSectionIdx = ref(-1)
const dragItemIdx = ref(-1)

function initSortState() {
  const newState: string[][] = []
  props.exercises.forEach((ex) => {
    if (ex.type === 'drag_sort' && ex.items) {
      const items = [...ex.items]
      for (let j = items.length - 1; j > 0; j--) {
        const k = Math.floor(Math.random() * (j + 1))
        ;[items[j], items[k]] = [items[k], items[j]]
      }
      newState.push(items)
    } else {
      newState.push([])
    }
  })
  sortState.value = newState
}

function resetExerciseState() {
  sortResults.value = {}
  fillAnswers.value = {}
  fillResults.value = {}
  choiceAnswers.value = {}
  choiceResults.value = {}
  initSortState()
}

watch(() => props.exercises, resetExerciseState, { immediate: true, deep: true })

// Drag handlers
function onDragStart(si: number, idx: number, event: DragEvent) {
  dragSectionIdx.value = si
  dragItemIdx.value = idx
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(idx))
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
}

function onDrop(si: number, targetIdx: number, event: DragEvent) {
  event.preventDefault()
  const fromIdx = dragItemIdx.value
  const fromSi = dragSectionIdx.value
  if (fromSi !== si || fromIdx === targetIdx || fromIdx < 0) return

  const items = sortState.value[si]
  if (!items) return

  const [moved] = items.splice(fromIdx, 1)
  items.splice(targetIdx, 0, moved)
  sortState.value[si] = [...items]

  dragSectionIdx.value = -1
  dragItemIdx.value = -1
}

function onDragEnd() {
  dragSectionIdx.value = -1
  dragItemIdx.value = -1
}

function checkSortAnswer(si: number, exercise: any) {
  if (!exercise.correct_order || !exercise.items) return
  const current = sortState.value[si]
  if (!current) return
  const correctSorted = exercise.correct_order.map((i: number) => exercise.items[i])
  const isCorrect =
    current.length === correctSorted.length &&
    current.every((item: string, i: number) => item === correctSorted[i])
  sortResults.value[si] = isCorrect
}

function checkFillAnswer(si: number, exercise: any) {
  const blanks = exercise.blanks || []
  blanks.forEach((blank: any, bi: number) => {
    const key = `${si}-${bi}`
    const answer = fillAnswers.value[key]?.trim().toLowerCase() || ''
    const expected = (blank.answer || '').trim().toLowerCase()
    fillResults.value[key] = answer === expected
  })
}

function checkChoiceAnswer(si: number, exercise: any) {
  if (!exercise.answer) return
  choiceResults.value[si] = choiceAnswers.value[si] === exercise.answer
}

// ===== Exercise helper functions (avoid 'as any' in template) =====
function getExerciseItems(exercise: any): string[] | undefined {
  return exercise?.items
}
function getExerciseBlanks(exercise: any): any[] {
  return exercise?.blanks || []
}
function getExerciseQuestion(exercise: any): string {
  return exercise?.question || ''
}
function getExerciseOptions(exercise: any): any[] {
  return exercise?.options || []
}

// ===== Helper functions =====
function getAnimTypeLabel(type: AnimationType): string {
  const labels: Record<AnimationType, string> = {
    sort_animation: '排序动画',
    data_structure: '数据结构',
    flowchart_step: '流程演示',
    formula_derivation: '公式推导',
    code_execution: '代码执行',
  }
  return labels[type] || type
}

function getAnimTagType(type: AnimationType): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const types: Record<AnimationType, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    sort_animation: 'primary',
    data_structure: 'success',
    flowchart_step: 'warning',
    formula_derivation: 'danger',
    code_execution: 'info',
  }
  return types[type] || 'info'
}
</script>

<style scoped>
/* ==============================
   Light Theme - Clean & Modern
   ============================== */
.interactive-viewer {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
  background: #f8fafc;
  border-radius: 12px;
  line-height: 1.8;
}

/* ===== Title ===== */
.iv-title {
  font-size: 24px;
  color: #1e293b;
  margin: 0 0 26px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
  position: relative;
}
.iv-title::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 56px;
  height: 3px;
  background: #6366f1;
  border-radius: 2px;
}

/* ===== Section ===== */
.iv-section-title {
  font-size: 17px;
  color: #334155;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.section-icon {
  font-size: 18px;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef2ff;
  border-radius: 8px;
  flex-shrink: 0;
}

/* ===== Animation Cards ===== */
.iv-animation-section {
  margin-bottom: 28px;
}
.anim-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}
.anim-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.anim-card:hover {
  border-color: #6366f1;
  background: #fafafe;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.1), 0 0 0 1px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}
.anim-card-icon {
  font-size: 28px;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef2ff;
  border-radius: 10px;
  transition: all 0.3s;
}
.anim-card:hover .anim-card-icon {
  background: #e0e7ff;
  transform: scale(1.06);
}
.anim-card-body {
  flex: 1;
  min-width: 0;
}
.anim-card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.anim-card-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.anim-card-kp {
  display: flex;
  align-items: center;
  gap: 6px;
}
.kp-name {
  font-size: 11px;
  color: #94a3b8;
}
.anim-card-arrow {
  flex-shrink: 0;
  color: #cbd5e1;
  font-size: 16px;
  transition: all 0.2s;
}
.anim-card:hover .anim-card-arrow {
  color: #6366f1;
  transform: translateX(3px);
}

/* ===== Exercise Section ===== */
.iv-exercise-section {
  margin-bottom: 28px;
}
.ex-card {
  margin-bottom: 14px;
  padding: 20px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

/* ===== Drag sort ===== */
.ex-drag-sort {
  margin-top: 14px;
}
.sort-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  margin-bottom: 6px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}
.sort-item:hover {
  background: #eef2ff;
  border-color: #a5b4fc;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}
.sort-item:active {
  cursor: grabbing;
  background: #e0e7ff;
}
.sort-handle {
  color: #cbd5e1;
  font-size: 16px;
}
.sort-num {
  font-size: 11px;
  color: #94a3b8;
  min-width: 18px;
  text-align: center;
}
.sort-label {
  font-size: 14px;
  color: #334155;
  flex: 1;
  font-weight: 500;
}
.sort-check-btn {
  margin-top: 10px;
}

/* ===== Fill blank ===== */
.ex-fill-blank {
  margin-top: 12px;
}
.blank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.blank-row label {
  font-size: 13px;
  color: #64748b;
  min-width: 80px;
}
.blank-input {
  width: 220px;
}
.blank-feedback {
  font-size: 13px;
  font-weight: 500;
}
.blank-feedback.correct { color: #16a34a; }
.blank-feedback.wrong { color: #dc2626; }

/* ===== Choice ===== */
.ex-choice {
  margin-top: 12px;
}
.ex-question {
  font-size: 14px;
  color: #334155;
  margin: 0 0 10px;
  font-weight: 500;
}

/* ===== Result ===== */
.ex-result {
  margin-top: 10px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}
.ex-result.correct {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}
.ex-result.wrong {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.ex-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  font-style: italic;
}

/* ===== Glossary ===== */
.iv-glossary {
  padding-top: 22px;
  border-top: 1px solid #e2e8f0;
}
.glossary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 8px;
}
.glossary-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s;
}
.glossary-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}
.glossary-def {
  color: #64748b;
  line-height: 1.5;
}

/* ===== Animation Dialog ===== */
.anim-dialog :deep(.el-dialog) {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}
.anim-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}
.anim-dialog :deep(.el-dialog__body) {
  padding: 0;
}
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: #f0f4ff;
  border-bottom: 1px solid #e0e7ff;
}
.dialog-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.dialog-title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.anim-frame-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(95vh - 120px);
}
.anim-frame-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.anim-kp-label {
  font-size: 13px;
  color: #94a3b8;
}

.anim-frame-container {
  flex: 1;
  overflow: hidden;
  background: #ffffff;
}
.anim-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.anim-no-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #94a3b8;
  gap: 12px;
}
.anim-no-file p {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}
.anim-no-file .hint {
  font-size: 12px;
  color: #cbd5e1;
}
</style>
