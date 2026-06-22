<template>
  <div class="player">
    <header class="player-header">
      <el-button text @click="$router.push('/')">
        ← 返回首页
      </el-button>
      <div class="header-center">
        <!-- Inline progress bar when generating -->
        <div v-if="showContentProgress" class="header-progress">
          <span class="progress-label">AI 生成中</span>
          <el-progress
            :percentage="contentProgressPct"
            :stroke-width="6"
            :show-text="false"
            style="width: 120px"
          />
        </div>
        <div class="header-info">
          <span class="course-title">{{ courseTitle }}</span>
          <el-tag v-if="courseStatus" :type="statusTagType(courseStatus)" size="small">
            {{ statusLabel(courseStatus) }}
          </el-tag>
        </div>
      </div>
      <el-button
        v-if="courseStatus === 'outlined'"
        type="primary"
        size="small"
        :loading="generating"
        @click="triggerGenerate"
      >
        生成教学内容
      </el-button>
    </header>

    <div class="player-body">
      <!-- Chapter sidebar -->
      <aside class="chapter-sidebar">
        <h4>课程大纲</h4>
        <div v-if="chapters.length === 0 && loading" class="empty-chapters">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else-if="chapters.length === 0" class="empty-chapters">
          <el-empty description="暂无章节" :image-size="60" />
        </div>
        <div
          v-for="ch in chapters"
          :key="ch.id"
          class="chapter-item"
          :class="{ active: activeChapter === ch.id }"
          @click="activeChapter = ch.id"
        >
          <div class="chapter-order">{{ ch.order }}</div>
          <div class="chapter-content">
            <div class="chapter-title">{{ ch.title }}</div>
            <div class="chapter-kps" v-if="ch.knowledge_points?.length">
              <el-tag
                v-for="(kp, i) in ch.knowledge_points"
                :key="i"
                size="small"
                class="kp-tag"
              >{{ kp }}</el-tag>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main content area -->
      <main class="player-main">
        <ModalTab v-model="activeModal" />

        <div class="content-area">
          <!-- Loading content for current chapter -->
          <div v-if="contentLoading" class="content-loading">
            <div class="content-spinner" />
            <span>加载内容中…</span>
          </div>

          <template v-else-if="activeChapter">
            <!-- PPT -->
            <PptViewer
              v-if="activeModal === 'ppt' && pptSlides.length"
              :slides="pptSlides"
              :narration-urls="narrationUrls"
              :chapter-title="currentChapterTitle"
              :file-url="pptFileUrl"
            />
            <!-- MindMap -->
            <MindMap
              v-else-if="activeModal === 'mindmap'"
              :course-id="courseId"
              :mindmap-data="currentMindMapData"
            />
            <!-- KnowledgeGraph -->
            <div v-else-if="activeModal === 'knowledge_graph'" class="kg-section">
              <KnowledgeGraph ref="kgRef" :course-id="courseId" />
              <KnowledgeGraphEditor :course-id="courseId" @updated="onGraphUpdated" />
            </div>
            <!-- Text -->
            <template v-else-if="activeModal === 'text'">
              <div v-if="currentTextSections.length" class="text-content">
                <div v-for="(sec, i) in currentTextSections" :key="i" class="text-section">
                  <h3>{{ sec.heading }}</h3>
                  <p v-for="(p, j) in sec.paragraphs" :key="j" class="text-para">{{ p }}</p>
                  <div v-if="sec.embedded_questions?.length" class="text-questions">
                    <el-collapse>
                      <el-collapse-item
                        v-for="(q, qi) in sec.embedded_questions"
                        :key="qi"
                        :title="`检验 ${Number(qi) + 1}: ${q.question}`"
                      >
                        <p><b>答案：</b>{{ q.answer }}</p>
                        <p><b>解析：</b>{{ q.explanation }}</p>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </div>
              </div>
              <el-empty v-else description="该章节暂无文本内容" :image-size="80" />
            </template>
            <!-- Quiz -->
            <template v-else-if="activeModal === 'quiz'">
              <div v-if="quizQuestions.length" class="quiz-content">
                <div class="quiz-header">
                  <h3>{{ quizTitle }}</h3>
                  <div class="quiz-score" v-if="quizTotalScore > 0">
                    得分：{{ quizEarnedScore }} / {{ quizTotalScore }}
                  </div>
                </div>
                <div v-for="(q, qi) in quizQuestions" :key="qi" class="quiz-item">
                  <div class="quiz-q-header">
                    <el-tag :type="q.type === 'mcq' ? 'primary' : q.type === 'tf' ? 'success' : 'warning'" size="small">
                      {{ q.type === 'mcq' ? '选择题' : q.type === 'tf' ? '判断题' : '简答题' }}
                    </el-tag>
                    <span class="quiz-q-num">第 {{ qi + 1 }} 题</span>
                  </div>
                  <p class="quiz-q-text">{{ q.question }}</p>
                  <!-- MCQ -->
                  <div v-if="q.type === 'mcq' && q.options" class="quiz-options">
                    <el-radio-group v-model="quizAnswers[qi]" @change="checkAnswer(qi, q)">
                      <el-radio v-for="(opt, oi) in q.options" :key="oi" :value="opt[0]">{{ opt }}</el-radio>
                    </el-radio-group>
                  </div>
                  <!-- True/False -->
                  <div v-else-if="q.type === 'tf'">
                    <el-radio-group v-model="quizAnswers[qi]" @change="checkAnswer(qi, q)">
                      <el-radio value="true">正确</el-radio>
                      <el-radio value="false">错误</el-radio>
                    </el-radio-group>
                  </div>
                  <!-- Short answer -->
                  <div v-else-if="q.type === 'short_answer'" class="quiz-short-answer">
                    <el-input
                      v-model="quizAnswers[qi]"
                      type="textarea"
                      :rows="2"
                      placeholder="请输入你的答案"
                      @change="checkAnswer(qi, q)"
                    />
                  </div>
                  <div v-if="quizResults[qi] !== undefined" class="quiz-result" :class="quizResults[qi] ? 'correct' : 'wrong'">
                    {{ quizResults[qi] ? '✓ 正确' : '✗ 错误' }}
                    <span v-if="!quizResults[qi]"> — {{ q.explanation || `参考答案: ${q.answer}` }}</span>
                  </div>
                </div>
                <!-- Quiz summary -->
                <div v-if="quizScoreComputed" class="quiz-summary">
                  <el-alert
                    :title="quizSummaryText"
                    :type="quizEarnedScore >= quizPassScore ? 'success' : 'warning'"
                    :closable="false"
                    show-icon
                  />
                </div>
              </div>
              <el-empty v-else description="该章节暂无测验内容" :image-size="80" />
            </template>
            <!-- Interactive HTML -->
            <template v-else-if="activeModal === 'interactive_html'">
              <InteractiveViewer
                v-if="interactiveSections.length"
                :sections="interactiveSections"
                :glossary="interactiveGlossary"
              />
              <el-empty v-else description="该章节暂无互动教材内容" :image-size="80" />
            </template>
            <!-- Fallback: only shown when no modal matches -->
            <el-empty
              v-else-if="courseStatus === 'draft' || courseStatus === 'outlined'"
              description="内容尚未生成，点击「生成教学内容」开始"
            />
            <el-empty v-else description="暂无该模块内容" :image-size="80" />
          </template>

          <el-empty v-else description="请选择一个章节" />
        </div>
      </main>

      <!-- Chat panel -->
      <aside class="chat-sidebar" :style="{ width: chatCollapsed ? '48px' : '360px', minWidth: chatCollapsed ? '48px' : '360px' }">
        <ChatPanel :course-id="courseId" :chapter-id="activeChapter" :initial-collapsed="true" @toggle="onChatToggle" />
      </aside>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ModalTab from '@/components/course/ModalTab.vue'
import PptViewer from '@/components/course/PptViewer.vue'
import InteractiveViewer from '@/components/course/InteractiveViewer.vue'
import MindMap from '@/components/knowledge/MindMap.vue'
import KnowledgeGraph from '@/components/knowledge/KnowledgeGraph.vue'
import KnowledgeGraphEditor from '@/components/knowledge/KnowledgeGraphEditor.vue'
import ChatPanel from '@/components/course/ChatPanel.vue'
import { getCourse, triggerGenerate as triggerGenerateApi, getProgress } from '@/api/course'
import { getChapterContents } from '@/api/content'
import type { PptSlide } from '@/components/course/PptViewer.vue'
import type { ScenePlan } from '@/api/course'

const route = useRoute()
const courseId = computed(() => Number(route.params.id))

// Course data
const courseTitle = ref('课程加载中…')
const courseStatus = ref('')
const chapters = ref<any[]>([])

/** Current chapter title for PPT header display */
const currentChapterTitle = computed(() => {
  const ch = chapters.value.find(c => c.id === activeChapter.value)
  return ch?.title || ''
})
const scenePlan = ref<ScenePlan | null>(null)
const activeChapter = ref<number | null>(null)
const activeModal = ref('text')
const generating = ref(false)
const showContentProgress = ref(false)
const contentProgressPct = ref(0)
const loading = ref(true)
const contentLoading = ref(false)
const chatCollapsed = ref(true)
let progressPollTimer: ReturnType<typeof setInterval> | null = null

function onChatToggle(collapsed: boolean) {
  chatCollapsed.value = collapsed
  // Trigger resize after CSS transition (0.3s) completes so embedded
  // charts/iframes can recalculate their layout dimensions.
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'))
  }, 350)
}

// Content state
const pptSlides = ref<PptSlide[]>([])
const pptFileUrl = ref('')
const narrationUrls = ref<string[]>([])
const currentMindMapData = ref<any>(null)
const currentTextSections = ref<any[]>([])
const quizQuestions = ref<any[]>([])
const quizTitle = ref('')
const quizAnswers = ref<Record<number, string>>({})
const quizResults = ref<Record<number, boolean>>({})
const interactiveSections = ref<any[]>([])
const interactiveTitle = ref('')
const interactiveGlossary = ref<any[]>([])

// KnowledgeGraph ref for editor-triggered refresh
const kgRef = ref<InstanceType<typeof KnowledgeGraph> | null>(null)

// ---------------------------------------------------------------------------
// Load content for the active chapter
// ---------------------------------------------------------------------------
async function loadChapterContent() {
  if (!activeChapter.value) return
  contentLoading.value = true
  // Reset content
  pptSlides.value = []
  currentMindMapData.value = null
  currentTextSections.value = []
  quizQuestions.value = []
  quizTitle.value = ''
  quizAnswers.value = {}
  quizResults.value = {}
  quizTotalScore.value = 0
  quizPassScore.value = 0
  interactiveSections.value = []
  interactiveTitle.value = ''
  interactiveGlossary.value = []

  try {
    const response = await getChapterContents(activeChapter.value)
    const data = response?.data
    if (!data) {
      console.debug('No content data for chapter', activeChapter.value)
      return
    }
    const byModal = data.by_modal || {}

    // Parse PPT
    const pptMods = byModal['ppt'] || []
    if (pptMods.length && pptMods[0].content_json) {
      const parsed = JSON.parse(pptMods[0].content_json)
      pptSlides.value = parsed.slides || []
      // Use narration URLs from backend if available
      narrationUrls.value = parsed.narration_urls || []
      // PPT file download URL
      pptFileUrl.value = pptMods[0].file_path || ''
    } else {
      pptFileUrl.value = ''
    }

    // Parse mindmap
    const mmMods = byModal['mindmap'] || []
    console.log('[DEBUG CoursePlayer] mindmap mods:', mmMods.length, mmMods)
    if (mmMods.length && mmMods[0].content_json) {
      currentMindMapData.value = JSON.parse(mmMods[0].content_json)
      console.log('[DEBUG CoursePlayer] currentMindMapData set:', JSON.stringify(currentMindMapData.value).substring(0, 200))
    } else {
      console.warn('[DEBUG CoursePlayer] mindmap data MISSING or empty:', { len: mmMods.length, hasJson: mmMods[0]?.content_json ? 'yes' : 'no' })
      currentMindMapData.value = null
    }

    // Parse text
    const textMods = byModal['text'] || []
    if (textMods.length && textMods[0].content_json) {
      const parsed = JSON.parse(textMods[0].content_json)
      currentTextSections.value = parsed.sections || []
    }

    // Parse quiz
    const quizMods = byModal['quiz'] || []
    if (quizMods.length && quizMods[0].content_json) {
      const parsed = JSON.parse(quizMods[0].content_json)
      quizQuestions.value = parsed.questions || []
      quizTitle.value = parsed.quiz_title || ''
      quizTotalScore.value = parsed.total_score || parsed.questions?.length || 0
      quizPassScore.value = parsed.pass_score || Math.ceil((parsed.questions?.length || 0) * 0.6)
    }

    // Parse interactive
    const intMods = byModal['interactive_html'] || []
    if (intMods.length && intMods[0].content_json) {
      const parsed = JSON.parse(intMods[0].content_json)
      interactiveSections.value = parsed.sections || []
      interactiveTitle.value = parsed.title || ''
      interactiveGlossary.value = parsed.glossary || []
    }
  } catch (err: any) {
    // Content may not be generated yet — that's okay
    console.debug('No content for chapter', activeChapter.value)
  } finally {
    contentLoading.value = false
  }
}

function checkAnswer(qi: number, q: any) {
  const userAnswer = quizAnswers.value[qi]
  if (!userAnswer) return
  if (q.type === 'mcq') {
    quizResults.value[qi] = userAnswer === q.answer
  } else if (q.type === 'tf') {
    const expected = q.answer === true ? 'true' : 'false'
    quizResults.value[qi] = userAnswer === expected
  } else if (q.type === 'short_answer') {
    // Fuzzy match for short answer: check if answer contains key terms
    const expected = (q.answer || '').trim().toLowerCase()
    const given = userAnswer.trim().toLowerCase()
    quizResults.value[qi] = given.length > 0 && expected.length > 0 &&
      (given.includes(expected) || expected.includes(given))
  }
}

// Quiz scoring
const quizTotalScore = ref(0)
const quizPassScore = ref(0)

const quizEarnedScore = computed(() => {
  const totalQ = quizQuestions.value.length
  if (totalQ === 0) return 0
  const scorePerQuestion = (quizTotalScore.value || 100) / totalQ
  return Math.round(quizQuestions.value.reduce((sum, _q, qi) => {
    return sum + (quizResults.value[qi] ? scorePerQuestion : 0)
  }, 0))
})

const quizScoreComputed = computed(() => {
  return Object.keys(quizResults.value).length >= quizQuestions.value.length
})

const quizSummaryText = computed(() => {
  if (!quizScoreComputed.value) return ''
  const earned = quizEarnedScore.value
  const total = quizTotalScore.value || quizQuestions.value.length
  const pass = quizPassScore.value || Math.ceil(total * 0.6)
  return earned >= pass
    ? `恭喜！得分 ${earned}/${total}，通过测验！`
    : `得分 ${earned}/${total}，未达到及格线 ${pass}/${total}，请继续努力！`
})

// ── KnowledgeGraph editor callback ──
function onGraphUpdated() {
  // Reload the KnowledgeGraph component
  if (kgRef.value && typeof (kgRef.value as any).loadGraph === 'function') {
    (kgRef.value as any).loadGraph()
  }
}

// ---------------------------------------------------------------------------
// Load course data
// ---------------------------------------------------------------------------
async function loadCourse() {
  loading.value = true
  try {
    const { data } = await getCourse(courseId.value)
    const info = data.course_info
    courseTitle.value = info?.title || '未命名课程'
    courseStatus.value = info?.status || 'draft'
    chapters.value = data.chapters || []
    scenePlan.value = data.scene_plan || null

    // If course is currently generating, show progress component and poll
    if (courseStatus.value === 'generating') {
      showContentProgress.value = true
      startProgressPolling()
    }

    if (chapters.value.length > 0) {
      activeChapter.value = chapters.value[0].id
    }

    // Auto-select first recommended modal from scene plan (only on initial load)
    // Commented out: let user choose, default to 'text'
    // if (scenePlan.value?.global_modals?.length) {
    //   activeModal.value = scenePlan.value.global_modals[0]
    // }

    // Generating state is tracked via courseStatus
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '加载课程失败'
    ElMessage.error(msg)
    courseTitle.value = '加载失败'
  } finally {
    loading.value = false
  }
}

async function triggerGenerate() {
  generating.value = true
  try {
    const { data } = await triggerGenerateApi(courseId.value)
    ElMessage.success(data?.message || '内容生成任务已提交')
    courseStatus.value = 'generating'
    showContentProgress.value = true
    startProgressPolling()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '触发生成失败'
    ElMessage.error(msg)
  } finally {
    generating.value = false
  }
}

/** Poll progress to update header progress bar and detect completion */
function startProgressPolling() {
  if (progressPollTimer) return
  progressPollTimer = setInterval(async () => {
    try {
      const { data } = await getProgress(courseId.value)
      contentProgressPct.value = data.percentage ?? 0

      if (data.status === 'done') {
        stopProgressPolling()
        onContentGenerationCompleted()
      } else if (data.status === 'failed') {
        stopProgressPolling()
        onContentGenerationFailed(data.error_message || '未知错误')
      }
    } catch {
      // ignore
    }
  }, 2000)
}

function stopProgressPolling() {
  if (progressPollTimer) {
    clearInterval(progressPollTimer)
    progressPollTimer = null
  }
}

/** Called when content generation completes */
function onContentGenerationCompleted() {
  stopProgressPolling()
  showContentProgress.value = false
  contentProgressPct.value = 100
  courseStatus.value = 'ready'
  ElMessage.success('教学内容生成完成！')
  loadCourse()
}

/** Called when content generation fails */
function onContentGenerationFailed(errorMsg: string) {
  stopProgressPolling()
  showContentProgress.value = false
  contentProgressPct.value = 0
  courseStatus.value = 'error'
  ElMessage.error(`内容生成失败：${errorMsg}`)
}

// Watch activeChapter → reload content
watch(activeChapter, () => {
  if (courseStatus.value === 'ready') {
    loadChapterContent()
  }
})

onMounted(() => {
  loadCourse()
})

onUnmounted(() => {
  stopProgressPolling()
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    outlined: '已生成大纲',
    generating: '生成中',
    ready: '已完成',
    error: '失败',
  }
  return map[status] || status
}

function statusTagType(status: string): 'info' | 'success' | 'warning' | 'danger' | '' {
  const map: Record<string, 'info' | 'success' | 'warning' | 'danger' | ''> = {
    draft: 'info',
    outlined: 'success',
    generating: 'warning',
    ready: 'success',
    error: 'danger',
  }
  return map[status] || 'info'
}

</script>

<style scoped>
.player {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.player-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  z-index: 10;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  justify-content: center;
}

.header-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.progress-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.course-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.player-body {
  flex: 1;
  display: flex;
  min-height: 0;
  align-items: flex-start;
}

/* Chapter sidebar */
.chapter-sidebar {
  width: 280px;
  min-width: 280px;
  height: calc(100vh - 52px); /* align with chat sidebar */
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 16px 0;
  position: sticky;
  top: 0;
  align-self: flex-start;
  flex-shrink: 0;
}

.chapter-sidebar h4 {
  font-size: 14px;
  color: #909399;
  padding: 0 16px 12px;
  margin: 0;
  border-bottom: 1px solid #f2f3f5;
}

.empty-chapters {
  padding: 16px;
}

.chapter-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.chapter-item:hover {
  background: #f5f7fa;
}

.chapter-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
}

.chapter-order {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  flex-shrink: 0;
}

.chapter-item.active .chapter-order {
  background: #409eff;
  color: #fff;
}

.chapter-content {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  line-height: 1.4;
  margin-bottom: 4px;
}

.chapter-kps {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.kp-tag {
  font-size: 11px;
}

.chapter-modals {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.modal-tag {
  font-size: 10px;
}

/* Scene overview bar */
.scene-overview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  flex-wrap: wrap;
}

.scene-label {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.scene-modal-tag {
  cursor: pointer;
  transition: transform 0.15s;
}

.scene-modal-tag:hover {
  transform: scale(1.05);
}

/* Main content */
.player-main {
  flex: 1;
  padding: 16px;
  min-width: 0;
  height: calc(100vh - 52px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Chat sidebar */
.chat-sidebar {
  width: 360px;
  min-width: 360px;
  height: calc(100vh - 52px); /* full viewport height minus header */
  background: #fff;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  align-self: flex-start;
  flex-shrink: 0;
  overflow: hidden; /* clip the sliding chat panel */
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.content-area {
  flex: 1;
  margin-top: 12px;
  padding-bottom: 60px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* NOTE: .kg-wrapper styles are scoped in KnowledgeGraph.vue;
   only override when needed for layout contexts */

/* KnowledgeGraph section with editor */
.kg-section {
  flex: 1;
  display: block;
  min-height: 0;
  overflow-y: auto;
}
.kg-section > :deep(.kg-wrapper) {
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* Content loading */
.content-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: #999;
  font-size: 14px;
}
.content-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: content-spin 0.8s linear infinite;
}
@keyframes content-spin {
  to { transform: rotate(360deg); }
}

/* Text content */
.text-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}
.text-section {
  margin-bottom: 24px;
}
.text-section h3 {
  font-size: 18px;
  color: #303133;
  margin: 0 0 12px;
}
.text-para {
  font-size: 14px;
  color: #555;
  line-height: 1.8;
  margin: 0 0 8px;
}
.text-questions {
  margin-top: 12px;
}

/* Quiz content */
.quiz-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}
.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.quiz-header h3 {
  font-size: 18px;
  margin: 0;
  color: #303133;
}
.quiz-score {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}
.quiz-item {
  margin-bottom: 20px;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
}
.quiz-q-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.quiz-q-num {
  font-size: 12px;
  color: #999;
}
.quiz-q-text {
  font-size: 14px;
  color: #333;
  margin: 0 0 10px;
  font-weight: 500;
}
.quiz-options {
  margin-bottom: 8px;
}
.quiz-result {
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 13px;
}
.quiz-result.correct {
  background: #e8f5e9;
  color: #2e7d32;
}
.quiz-result.wrong {
  background: #ffebee;
  color: #c62828;
}
.quiz-short-answer {
  margin-bottom: 8px;
}
.quiz-summary {
  margin-top: 16px;
}

/* Interactive content */
.interactive-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}
.interactive-content h3 {
  font-size: 18px;
  margin: 0 0 16px;
  color: #303133;
}
.interactive-section {
  margin-bottom: 20px;
}
.interactive-section h4 {
  font-size: 16px;
  color: #409eff;
  margin: 0 0 8px;
}
.interactive-md {
  font-size: 14px;
  color: #555;
  line-height: 1.8;
  margin-bottom: 8px;
}
.interactive-exercise {
  margin-top: 10px;
}
</style>
