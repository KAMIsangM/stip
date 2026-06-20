<template>
  <div class="interactive-viewer">
    <!-- Title -->
    <h2 v-if="title" class="iv-title">{{ title }}</h2>

    <!-- Sections -->
    <div v-for="(section, si) in sections" :key="si" class="iv-section">
      <h3 class="iv-heading">{{ section.heading }}</h3>

      <!-- Markdown content -->
      <div v-if="section.content" class="iv-markdown" v-html="renderMarkdown(section.content)" />

      <!-- Flowchart visualization -->
      <div v-if="section.visual_type === 'flowchart' && section.visual_data" class="iv-flowchart">
        <div class="iv-flowchart-label">流程图</div>
        <div class="iv-flowchart-canvas">
          <div v-for="(node, ni) in section.visual_data.nodes" :key="'n' + ni" class="fc-node">
            {{ typeof node === 'string' ? node : node.label || node.id || '' }}
          </div>
        </div>
      </div>

      <!-- Comparison table -->
      <div v-else-if="section.visual_type === 'table' && section.visual_data" class="iv-table-wrap">
        <table class="iv-table">
          <thead v-if="section.visual_data.headers">
            <tr>
              <th v-for="(h, hi) in section.visual_data.headers" :key="'h' + hi">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in section.visual_data.rows" :key="'r' + ri">
              <td v-for="(cell, ci) in row" :key="'c' + ci">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Code example -->
      <div v-else-if="section.visual_type === 'code' && section.visual_data" class="iv-code-block">
        <pre><code>{{ section.visual_data.code || '' }}</code></pre>
      </div>

      <!-- Interactive Exercise -->
      <div v-if="section.interactive_exercise" class="iv-exercise">
        <el-alert
          :title="section.interactive_exercise.instruction || '互动练习'"
          type="info"
          :closable="false"
          show-icon
        />

        <!-- Drag sort exercise -->
        <div v-if="section.interactive_exercise.type === 'drag_sort'" class="ex-drag-sort">
          <div
            v-for="(item, idx) in sortState[si] || []"
            :key="item"
            class="sort-item"
            draggable="true"
            @dragstart="onDragStart(si, idx, $event)"
            @dragover="onDragOver($event)"
            @drop="onDrop(si, idx, $event)"
            @dragend="onDragEnd"
          >
            <span class="sort-handle">⠿</span>
            <span class="sort-label">{{ idx + 1 }}. {{ item }}</span>
          </div>
          <el-button
            size="small"
            type="primary"
            plain
            class="sort-check-btn"
            @click="checkSortAnswer(si, section.interactive_exercise)"
          >
            检查答案
          </el-button>
          <div v-if="sortResults[si] !== undefined" class="ex-result" :class="sortResults[si] ? 'correct' : 'wrong'">
            {{ sortResults[si] ? '✓ 排序正确！' : '✗ 排序不正确，请重试' }}
          </div>
          <div v-if="sortResults[si] !== undefined && !sortResults[si]" class="ex-hint">
            正确顺序：{{ section.interactive_exercise.items?.join(' → ') }}
          </div>
        </div>

        <!-- Fill blank exercise -->
        <div v-else-if="section.interactive_exercise.type === 'fill_blank'" class="ex-fill-blank">
          <div v-for="(blank, bi) in section.interactive_exercise.blanks || []" :key="bi" class="blank-row">
            <label>{{ blank.prompt || `填空 ${bi + 1}` }}</label>
            <el-input
              v-model="fillAnswers[`${si}-${bi}`]"
              :placeholder="blank.placeholder || '请输入答案'"
              size="small"
              class="blank-input"
              @change="() => checkFillAnswer(si, section.interactive_exercise)"
            />
            <span v-if="fillResults[`${si}-${bi}`] !== undefined" class="blank-feedback" :class="fillResults[`${si}-${bi}`] ? 'correct' : 'wrong'">
              {{ fillResults[`${si}-${bi}`] ? '✓' : `✗ (答案: ${blank.answer})` }}
            </span>
          </div>
        </div>

        <!-- Single choice exercise -->
        <div v-else-if="section.interactive_exercise.type === 'choice'" class="ex-choice">
          <p class="ex-question">{{ section.interactive_exercise.question }}</p>
          <el-radio-group
            v-model="choiceAnswers[si]"
            @change="() => checkChoiceAnswer(si, section.interactive_exercise)"
          >
            <el-radio
              v-for="(opt, oi) in section.interactive_exercise.options || []"
              :key="oi"
              :value="typeof opt === 'string' ? opt[0] : opt.value"
            >
              {{ typeof opt === 'string' ? opt : opt.label }}
            </el-radio>
          </el-radio-group>
          <div v-if="choiceResults[si] !== undefined" class="ex-result" :class="choiceResults[si] ? 'correct' : 'wrong'">
            {{ choiceResults[si] ? '✓ 回答正确！' : '✗ 回答错误' }}
            <span v-if="!choiceResults[si] && section.interactive_exercise.explanation">
              — {{ section.interactive_exercise.explanation }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Glossary -->
    <div v-if="glossary.length" class="iv-glossary">
      <h3>术语表</h3>
      <div v-for="(term, ti) in glossary" :key="ti" class="glossary-item">
        <el-tag size="small" effect="plain">{{ term.term }}</el-tag>
        <span class="glossary-def">{{ term.definition }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export interface InteractiveSection {
  heading: string
  content?: string
  visual_type?: string
  visual_data?: any
  interactive_exercise?: {
    type: string
    instruction: string
    items?: string[]
    correct_order?: number[]
    blanks?: { prompt?: string; placeholder?: string; answer: string }[]
    question?: string
    options?: (string | { value: string; label: string })[]
    answer?: string
    explanation?: string
  }
}

export interface GlossaryTerm {
  term: string
  definition: string
}

const props = withDefaults(defineProps<{
  title?: string
  sections: InteractiveSection[]
  glossary?: GlossaryTerm[]
}>(), {
  glossary: () => [],
})

// Exercise state
const sortState = ref<string[][]>([])
const sortResults = ref<Record<number, boolean>>({})
const fillAnswers = ref<Record<string, string>>({})
const fillResults = ref<Record<string, boolean>>({})
const choiceAnswers = ref<Record<number, string>>({})
const choiceResults = ref<Record<number, boolean>>({})

// HTML5 drag-and-drop state
const dragSectionIdx = ref(-1)
const dragItemIdx = ref(-1)

// Initialize sort state from props
function initSortState() {
  props.sections.forEach((sec, i) => {
    if (sec.interactive_exercise?.type === 'drag_sort' && sec.interactive_exercise?.items) {
      const items = [...sec.interactive_exercise.items]
      for (let j = items.length - 1; j > 0; j--) {
        const k = Math.floor(Math.random() * (j + 1))
        ;[items[j], items[k]] = [items[k], items[j]]
      }
      sortState.value[i] = items
    }
  })
}

// Reset all answers
function resetExerciseState() {
  sortResults.value = {}
  fillAnswers.value = {}
  fillResults.value = {}
  choiceAnswers.value = {}
  choiceResults.value = {}
  initSortState()
}

watch(() => props.sections, resetExerciseState, { immediate: true, deep: true })

// HTML5 drag-and-drop handlers
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
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
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
  sortState.value[si] = [...items] // trigger reactivity

  dragSectionIdx.value = -1
  dragItemIdx.value = -1
}

function onDragEnd() {
  dragSectionIdx.value = -1
  dragItemIdx.value = -1
}

// Check sort answer
function checkSortAnswer(si: number, exercise: any) {
  if (!exercise.correct_order || !exercise.items) return
  const current = sortState.value[si]
  if (!current) return
  const correctSorted = exercise.correct_order.map((i: number) => exercise.items[i])
  const isCorrect = current.length === correctSorted.length &&
    current.every((item: string, i: number) => item === correctSorted[i])
  sortResults.value[si] = isCorrect
}

// Check fill blank answer
function checkFillAnswer(si: number, exercise: any) {
  const blanks = exercise.blanks || []
  blanks.forEach((blank: any, bi: number) => {
    const key = `${si}-${bi}`
    const answer = fillAnswers.value[key]?.trim().toLowerCase() || ''
    const expected = (blank.answer || '').trim().toLowerCase()
    fillResults.value[key] = answer === expected
  })
}

// Check choice answer
function checkChoiceAnswer(si: number, exercise: any) {
  if (!exercise.answer) return
  choiceResults.value[si] = choiceAnswers.value[si] === exercise.answer
}

// Simple markdown renderer
function renderMarkdown(md: string): string {
  if (!md) return ''
  let html = md
    .replace(/### (.+)/g, '<h5>$1</h5>')
    .replace(/## (.+)/g, '<h4>$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n/g, '<br>')
  return html
}
</script>

<style scoped>
.interactive-viewer {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  line-height: 1.8;
}

.iv-title {
  font-size: 22px;
  color: #1a56db;
  margin: 0 0 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #ecf5ff;
}

.iv-section {
  margin-bottom: 28px;
}

.iv-heading {
  font-size: 17px;
  color: #303133;
  margin: 0 0 10px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.iv-markdown {
  font-size: 14px;
  color: #555;
  margin-bottom: 12px;
}

.iv-markdown :deep(.inline-code) {
  background: #f0f2f5;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 13px;
}

/* Flowchart */
.iv-flowchart {
  margin: 12px 0;
  padding: 12px;
  background: #fafbfc;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}
.iv-flowchart-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}
.iv-flowchart-canvas {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.fc-node {
  padding: 6px 14px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

/* Table */
.iv-table-wrap {
  margin: 12px 0;
  overflow-x: auto;
}
.iv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.iv-table th,
.iv-table td {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}
.iv-table th {
  background: #f5f7fa;
  font-weight: 600;
}

/* Code block */
.iv-code-block {
  margin: 12px 0;
}
.iv-code-block pre {
  background: #282c34;
  color: #abb2bf;
  padding: 14px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

/* Exercise */
.iv-exercise {
  margin-top: 14px;
  padding: 12px;
  background: #f9fafb;
  border: 1px dashed #d0d5dd;
  border-radius: 8px;
}

/* Drag sort */
.ex-drag-sort {
  margin-top: 10px;
}
.sort-check-btn {
  margin-top: 8px;
}
.sort-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 6px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: grab;
  transition: background 0.15s;
}
.sort-item:hover {
  background: #ecf5ff;
}
.sort-ghost {
  opacity: 0.4;
  background: #409eff;
}
.sort-handle {
  color: #c0c4cc;
  font-size: 16px;
}
.sort-label {
  font-size: 14px;
  color: #333;
}

/* Fill blank */
.ex-fill-blank {
  margin-top: 10px;
}
.blank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.blank-row label {
  font-size: 13px;
  color: #606266;
  min-width: 80px;
}
.blank-input {
  width: 200px;
}
.blank-feedback {
  font-size: 13px;
  font-weight: 500;
}
.blank-feedback.correct {
  color: #2e7d32;
}
.blank-feedback.wrong {
  color: #c62828;
}

/* Choice */
.ex-choice {
  margin-top: 10px;
}
.ex-question {
  font-size: 14px;
  color: #333;
  margin: 0 0 8px;
}

/* Result feedback */
.ex-result {
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 13px;
}
.ex-result.correct {
  background: #e8f5e9;
  color: #2e7d32;
}
.ex-result.wrong {
  background: #ffebee;
  color: #c62828;
}
.ex-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

/* Glossary */
.iv-glossary {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
.iv-glossary h3 {
  font-size: 16px;
  color: #303133;
  margin: 0 0 12px;
}
.glossary-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 13px;
}
.glossary-def {
  color: #606266;
}
</style>
