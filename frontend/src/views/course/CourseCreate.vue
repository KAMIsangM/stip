<template>
  <div class="home">
    <!-- ================================================================== -->
    <!-- Top Bar                                                               -->
    <!-- ================================================================== -->
    <header class="top-bar">
      <div class="top-bar-brand">SITP · 智能教学平台</div>
      <div class="top-bar-actions">
        <span class="user-name">{{ authStore.username || '用户' }}</span>
        <el-button text size="small" style="color: #94a3b8" @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </header>

    <!-- ================================================================== -->
    <!-- Hero Section                                                         -->
    <!-- ================================================================== -->
    <section class="hero-section">
      <div class="hero-bg-deco">
        <div class="float-orb orb-1"></div>
        <div class="float-orb orb-2"></div>
        <div class="float-orb orb-3"></div>
        <div class="grid-dots"></div>
      </div>
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          基于最新 AI 多智能体技术
        </div>
        <h1 class="hero-title">
          智能互动
          <span class="title-highlight">教学平台</span>
        </h1>
        <p class="hero-desc">
          输入一个主题，AI 自动生成完整课程 — 知识图谱、PPT课件、互动动画、语音讲解，一站式沉浸学习
        </p>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-icon">🧠</span>
            <span class="stat-label">AI 知识建模</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">📊</span>
            <span class="stat-label">智能课件生成</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">🎮</span>
            <span class="stat-label">互动式学习</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">🎙️</span>
            <span class="stat-label">语音讲解</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ================================================================== -->
    <!-- Create Card                                                         -->
    <!-- ================================================================== -->
    <section class="create-section">
      <div class="create-card">
        <div class="create-card-inner">
          <div class="card-header">
            <h2>开始学习之旅</h2>
            <p>告诉 AI 你想学什么，剩下的交给我们</p>
          </div>

          <div class="input-group">
            <el-input
              v-model="title"
              placeholder="例如：Python 数据结构基础、机器学习入门、高等数学微积分…"
              size="large"
              class="main-input"
              :disabled="loading"
              @keyup.enter="submit"
            >
              <template #prefix>
                <el-icon :size="18"><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- Advanced options -->
          <el-collapse-transition>
            <div v-if="showAdvanced" class="advanced-area">
              <div class="adv-row">
                <label>补充描述</label>
                <el-input
                  v-model="description"
                  type="textarea"
                  :rows="2"
                  placeholder="描述你的学习目标和知识背景，帮助 AI 定制更精准的课程"
                  :disabled="loading"
                />
              </div>

              <div class="adv-row">
                <label>知识图谱预设</label>
                <el-select
                  v-model="presetId"
                  placeholder="选择一个预置知识库（可选）"
                  clearable
                  :disabled="loading"
                  style="width: 100%"
                >
                  <el-option
                    v-for="p in presets"
                    :key="p.id"
                    :label="`${p.name} (${p.node_count} 知识点)`"
                    :value="p.id"
                  />
                </el-select>
              </div>

              <!-- Preset list -->
              <div v-if="presets.length > 0" class="preset-inline-list">
                <span class="presets-hint">已有预设：</span>
                <div v-for="p in presets" :key="'pl-' + p.id" class="preset-chip">
                  <span>{{ p.name }}</span>
                  <span class="preset-chip-meta">{{ p.node_count }} 节点</span>
                  <el-popconfirm
                    title="确定删除该预设吗？"
                    confirm-button-text="删除"
                    cancel-button-text="取消"
                    @confirm="handleDeletePreset(p.id)"
                  >
                    <template #reference>
                      <span class="preset-chip-del">&times;</span>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
            </div>
          </el-collapse-transition>

          <div class="card-footer">
            <el-button text type="primary" size="small" @click="showAdvanced = !showAdvanced">
              <el-icon><ArrowUpBold v-if="showAdvanced" /><ArrowDownBold v-else /></el-icon>
              {{ showAdvanced ? '收起高级选项' : '高级选项' }}
            </el-button>

            <div class="footer-actions">
              <el-button size="large" :disabled="loading" @click="title = ''; description = ''; presetId = undefined">
                清空
              </el-button>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                :disabled="!title.trim()"
                class="btn-start"
                @click="submit"
              >
                <span v-if="!loading">🚀 开始学习</span>
                <span v-else>AI 正在为您生成课程…</span>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================================================================== -->
    <!-- Feature Highlights                                                   -->
    <!-- ================================================================== -->
    <section class="features-section">
      <h3 class="section-title">平台特色</h3>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feat-icon-wrap feat-icon-kg">
            <span>🧠</span>
          </div>
          <h4>知识图谱</h4>
          <p>自动构建知识点关系网络，直观展示知识结构</p>
        </div>
        <div class="feature-card">
          <div class="feat-icon-wrap feat-icon-ppt">
            <span>📊</span>
          </div>
          <h4>PPT 课件</h4>
          <p>AI 生成精美教学幻灯片，分章节结构化呈现</p>
        </div>
        <div class="feature-card">
          <div class="feat-icon-wrap feat-icon-int">
            <span>🎮</span>
          </div>
          <h4>互动动画</h4>
          <p>算法可视化、流程图、公式推导等互动展示</p>
        </div>
        <div class="feature-card">
          <div class="feat-icon-wrap feat-icon-audio">
            <span>🎙️</span>
          </div>
          <h4>语音讲解</h4>
          <p>自动生成章节语音，支持边听边学</p>
        </div>
      </div>
    </section>

    <!-- ================================================================== -->
    <!-- Recent Courses                                                       -->
    <!-- ================================================================== -->
    <section v-if="recentCourses.length > 0" class="recent-section">
      <div class="recent-header">
        <h3 class="section-title">最近课程</h3>
        <span class="recent-count">{{ recentCourses.length }} 门课程</span>
      </div>
      <div class="recent-grid">
        <div
          v-for="c in recentCourses"
          :key="c.id"
          class="recent-card"
          @click="router.push({ name: 'course-player', params: { id: c.id } })"
        >
          <div class="rc-cover">
            <div class="rc-cover-inner">
              <span class="rc-emoji">{{ getCourseEmoji(c.title) }}</span>
            </div>
            <div class="rc-status-chip" :class="'chip-' + c.status">{{ statusLabel(c.status) }}</div>
          </div>
          <div class="rc-body">
            <h5 class="rc-title">{{ c.title }}</h5>
            <div class="rc-meta">
              <el-icon :size="12"><Clock /></el-icon>
              <span>{{ formatDate(c.created_at) }}</span>
            </div>
          </div>
          <el-popconfirm
            title="确定要删除该课程吗？所有相关数据将被永久删除。"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @click.stop
            @confirm="handleDeleteCourse(c.id)"
          >
            <template #reference>
              <span class="rc-delete" @click.stop>
                <el-icon :size="14"><Close /></el-icon>
              </span>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </section>

    <!-- ================================================================== -->
    <!-- Footer                                                               -->
    <!-- ================================================================== -->
    <footer class="home-footer">
      <span>智能互动教学平台 &copy; 2026</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, Close, Search, ArrowDownBold, ArrowUpBold } from '@element-plus/icons-vue'
import { createCourse, listCourses, deleteCourse } from '@/api/course'
import { listPresets, deletePreset } from '@/api/knowledge'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

// Form state
const title = ref('')
const description = ref('')
const presetId = ref<number | undefined>(undefined)
const showAdvanced = ref(false)
const loading = ref(false)

// Recent courses
interface RecentCourse {
  id: number
  title: string
  status: string
  created_at: string | null
}
const recentCourses = ref<RecentCourse[]>([])

// Presets
interface Preset {
  id: number
  name: string
  node_count: number
  edge_count: number
}
const presets = ref<Preset[]>([])

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------
onMounted(async () => {
  await loadRecentCourses()
  try {
    const { data } = await listPresets()
    presets.value = data.presets || []
  } catch {
    // Silently fail
  }
})

async function loadRecentCourses() {
  try {
    const { data } = await listCourses({ page: 1, page_size: 20 })
    recentCourses.value = data.list || []
  } catch {
    // Silently fail
  }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
async function handleDeleteCourse(courseId: number) {
  try {
    await deleteCourse(courseId)
    ElMessage.success('课程已删除')
    recentCourses.value = recentCourses.value.filter(c => c.id !== courseId)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '删除课程失败'
    ElMessage.error(msg)
  }
}

async function handleDeletePreset(id: number) {
  try {
    await deletePreset(id)
    ElMessage.success('预设已删除')
    presets.value = presets.value.filter(p => p.id !== id)
    if (presetId.value === id) {
      presetId.value = undefined
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '删除预设失败'
    ElMessage.error(msg)
  }
}

const submitLock = ref(false)

async function submit() {
  if (submitLock.value) return
  const trimmed = title.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入学习主题')
    return
  }

  submitLock.value = true
  loading.value = true
  try {
    const { data } = await createCourse({
      title: trimmed,
      description: description.value.trim() || undefined,
      preset_id: presetId.value,
    })

    const courseId = data.course_info?.id
    if (courseId) {
      router.push({ name: 'course-player', params: { id: courseId } })
    } else {
      ElMessage.error('创建课程失败：未返回课程 ID')
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '创建课程失败，请检查后端服务是否启动'
    ElMessage.error(msg)
  } finally {
    loading.value = false
    submitLock.value = false
  }
}

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

function formatDate(iso: string | null): string {
  if (!iso) return ''
  const raw = iso.length >= 16 ? iso.slice(0, 16) : iso
  return raw.replace('T', ' ')
}

function getCourseEmoji(title: string): string {
  const map: Record<string, string> = {
    python: '🐍',
    java: '☕',
    c: '⚙️',
    数据: '📊',
    算法: '🔢',
    排序: '🔀',
    机器: '🤖',
    深度: '🧠',
    数学: '📐',
    微积分: '∫',
    统计: '📈',
    网络: '🌐',
    前端: '🎨',
    后端: '⚡',
    数据库: '🗄️',
  }
  for (const [key, emoji] of Object.entries(map)) {
    if (title.toLowerCase().includes(key)) return emoji
  }
  return '📚'
}
</script>

<style scoped>
/* ========================================================================= */
/* Variables                                                                  */
/* ========================================================================= */
.home {
  --c-primary: #6366f1;
  --c-primary-dark: #4f46e5;
  --c-primary-light: #818cf8;
  --c-accent: #f59e0b;
  --c-bg: #f0f4ff;
  --c-surface: #ffffff;
  --c-border: #e2e8f0;
  --c-text: #1e293b;
  --c-text-dim: #64748b;
  --c-text-muted: #94a3b8;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.03);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.08);
  --shadow-xl: 0 12px 32px rgba(0,0,0,0.1);
}

/* ========================================================================= */
/* Top Bar                                                                    */
/* ========================================================================= */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 48px;
  border-bottom: 1px solid #e2e8f0;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
}

.top-bar-brand {
  font-size: 13px;
  font-weight: 600;
  color: #6366f1;
  letter-spacing: 0.02em;
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}

/* ========================================================================= */
/* Layout                                                                     */
/* ========================================================================= */
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f4ff 0%, #f5f3ff 30%, #ecfeff 60%, #f0f4ff 100%);
  padding-bottom: 40px;
  overflow-x: hidden;
}

/* ========================================================================= */
/* Hero Section                                                               */
/* ========================================================================= */
.hero-section {
  position: relative;
  padding: 80px 24px 60px;
  text-align: center;
  overflow: hidden;
}

.hero-bg-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* Floating orbs */
.float-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
  animation: float 8s ease-in-out infinite;
}
.orb-1 {
  width: 280px; height: 280px;
  background: #818cf8;
  top: -100px; left: 5%;
  animation-delay: 0s;
}
.orb-2 {
  width: 200px; height: 200px;
  background: #fde68a;
  top: 60px; right: 10%;
  animation-delay: -3s;
}
.orb-3 {
  width: 240px; height: 240px;
  background: #a78bfa;
  bottom: -80px; left: 45%;
  animation-delay: -5s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.04); }
}

/* Dot grid pattern */
.grid-dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(99,102,241,0.06) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(ellipse 60% 50% at 50% 40%, black 30%, transparent 70%);
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 18px;
  border-radius: 99px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.18);
  color: #6366f1;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 24px;
}

.badge-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 16px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.title-highlight {
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 17px;
  color: #64748b;
  line-height: 1.7;
  margin: 0 auto 32px;
  max-width: 540px;
}

/* Hero stats pills */
.hero-stats {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 99px;
  background: rgba(255,255,255,0.8);
  border: 1px solid #e2e8f0;
  font-size: 13px;
  color: #475569;
  backdrop-filter: blur(8px);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.stat-item:hover {
  transform: translateY(-2px);
  border-color: #a5b4fc;
  box-shadow: var(--shadow-md);
}

.stat-icon {
  font-size: 15px;
}

/* ========================================================================= */
/* Create Card                                                                */
/* ========================================================================= */
.create-section {
  padding: 0 24px 48px;
  display: flex;
  justify-content: center;
}

.create-card {
  width: 100%;
  max-width: 620px;
  border-radius: 20px;
  background: #ffffff;
  border: 1px solid #e8ecf4;
  box-shadow: var(--shadow-lg);
  transition: box-shadow 0.3s;
}

.create-card:hover {
  box-shadow: var(--shadow-xl);
}

.create-card-inner {
  padding: 32px;
}

.card-header {
  margin-bottom: 24px;
}

.card-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px;
}

.card-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.input-group {
  margin-bottom: 8px;
}

.main-input :deep(.el-input__wrapper) {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: none !important;
  border-radius: 12px;
  padding: 4px 14px;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}
.main-input :deep(.el-input__wrapper:hover) {
  border-color: #a5b4fc !important;
  background: #f1f5f9 !important;
}
.main-input :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1 !important;
  background: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}

.main-input :deep(.el-input__inner) {
  color: #1e293b;
  font-size: 15px;
}
.main-input :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
}
.main-input :deep(.el-input__prefix) {
  color: #94a3b8;
}

/* Advanced area */
.advanced-area {
  margin-top: 12px;
  padding: 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.adv-row {
  margin-bottom: 12px;
}
.adv-row:last-child {
  margin-bottom: 0;
}

.adv-row label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  font-weight: 500;
}

.adv-row :deep(.el-textarea__inner),
.adv-row :deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  color: #1e293b;
}
.adv-row :deep(.el-textarea__inner:focus),
.adv-row :deep(.el-input__wrapper:focus),
.adv-row :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.07);
}

.adv-row :deep(.el-textarea__inner::placeholder),
.adv-row :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
}

/* Preset chips */
.preset-inline-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.presets-hint {
  font-size: 11px;
  color: #94a3b8;
  margin-right: 2px;
}

.preset-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 99px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  font-size: 12px;
  color: #6366f1;
}

.preset-chip-meta {
  font-size: 10px;
  color: #94a3b8;
}

.preset-chip-del {
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  opacity: 0.4;
  transition: opacity 0.2s, color 0.2s;
  margin-left: 1px;
}
.preset-chip-del:hover {
  opacity: 1;
  color: #ef4444;
}

/* Card footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn-start {
  font-weight: 600;
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25);
  transition: transform 0.2s, box-shadow 0.2s;
}
.btn-start:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99,102,241,0.35);
}
.btn-start:active {
  transform: translateY(0);
}

/* ========================================================================= */
/* Feature Highlights                                                         */
/* ========================================================================= */
.features-section {
  padding: 0 24px 48px;
  text-align: center;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  max-width: 900px;
  margin: 0 auto;
}

.feature-card {
  padding: 28px 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e8ecf4;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.feature-card:hover {
  transform: translateY(-4px);
  border-color: #a5b4fc;
  box-shadow: var(--shadow-lg);
}

.feat-icon-wrap {
  width: 48px; height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 22px;
}

.feat-icon-kg { background: rgba(59, 130, 246, 0.1); }
.feat-icon-ppt { background: rgba(245, 158, 11, 0.1); }
.feat-icon-int { background: rgba(16, 185, 129, 0.1); }
.feat-icon-audio { background: rgba(236, 72, 153, 0.1); }

.feature-card h4 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 6px;
}
.feature-card p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}

/* ========================================================================= */
/* Recent Courses                                                             */
/* ========================================================================= */
.recent-section {
  padding: 0 24px 48px;
  max-width: 1100px;
  margin: 0 auto;
}

.recent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.recent-count {
  font-size: 13px;
  color: #94a3b8;
}

.recent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.recent-card {
  position: relative;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e8ecf4;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.recent-card:hover {
  transform: translateY(-3px);
  border-color: #a5b4fc;
  box-shadow: var(--shadow-lg);
}

.rc-cover {
  height: 80px;
  position: relative;
  background: linear-gradient(135deg, #eef2ff, #f5f3ff);
}

.rc-cover-inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rc-emoji {
  font-size: 28px;
}

.rc-status-chip {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 2px 10px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(255,255,255,0.9);
}

.chip-ready { color: #059669; background: rgba(16,185,129,0.1); }
.chip-generating { color: #d97706; background: rgba(245,158,11,0.1); }
.chip-outlined { color: #2563eb; background: rgba(59,130,246,0.1); }
.chip-draft { color: #64748b; background: rgba(148,163,184,0.1); }
.chip-error { color: #dc2626; background: rgba(239,68,68,0.08); }

.rc-body {
  padding: 14px 16px;
}

.rc-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rc-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #94a3b8;
}

/* Delete button */
.rc-delete {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px; height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.85);
  color: #94a3b8;
  border: 1px solid #e2e8f0;
  opacity: 0;
  transition: opacity 0.2s, background 0.2s, color 0.2s;
  z-index: 2;
}
.recent-card:hover .rc-delete {
  opacity: 1;
}
.rc-delete:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border-color: #fca5a5;
}

/* ========================================================================= */
/* Footer                                                                     */
/* ========================================================================= */
.home-footer {
  text-align: center;
  padding: 0 24px 32px;
  color: #94a3b8;
  font-size: 12px;
}

/* ========================================================================= */
/* Responsive                                                                 */
/* ========================================================================= */
@media (max-width: 640px) {
  .hero-title {
    font-size: 32px;
  }
  .hero-desc {
    font-size: 14px;
  }
  .hero-stats {
    gap: 8px;
  }
  .stat-item {
    padding: 6px 12px;
    font-size: 12px;
  }
  .create-card-inner {
    padding: 20px;
  }
  .card-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .footer-actions {
    justify-content: flex-end;
  }
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
