<template>
  <div class="course-create">
    <el-card class="create-card" shadow="hover">
      <div class="hero">
        <h1>智能互动教学平台</h1>
        <p class="subtitle">基于 AI 多智能体的沉浸式学习体验</p>
      </div>

      <div class="form-section">
        <label class="input-label">学习主题</label>
        <el-input
          v-model="title"
          placeholder="输入你想学习的内容，例如：Python 数据结构基础、机器学习入门..."
          size="large"
          class="title-input"
          :disabled="loading"
          @keyup.enter="submit"
        >
          <template #prefix>
            <span style="color: #909399;">主题</span>
          </template>
        </el-input>

        <el-collapse-transition>
          <div v-if="showAdvanced" class="advanced-section">
            <label class="input-label">补充描述（可选）</label>
            <el-input
              v-model="description"
              type="textarea"
              :rows="2"
              placeholder="描述你的学习目标和背景，帮助 AI 更好地定制课程"
              :disabled="loading"
            />

            <label class="input-label" style="margin-top: 12px;">预置知识图谱（可选）</label>
            <el-select
              v-model="presetId"
              placeholder="选择预置知识库"
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

            <!-- Preset list with delete -->
            <div v-if="presets.length > 0" class="preset-list">
              <span class="preset-list-label">已有预设知识图谱：</span>
              <div v-for="p in presets" :key="'pl-' + p.id" class="preset-item">
                <span class="preset-item-name">{{ p.name }}</span>
                <span class="preset-item-meta">{{ p.node_count }} 节点 · {{ p.edge_count }} 边</span>
                <el-popconfirm
                  title="确定删除该预设吗？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm="handleDeletePreset(p.id)"
                >
                  <template #reference>
                    <el-button type="danger" size="small" :icon="DeleteIcon" circle />
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-collapse-transition>

        <el-button
          text
          type="primary"
          size="small"
          class="toggle-advanced"
          @click="showAdvanced = !showAdvanced"
        >
          {{ showAdvanced ? '收起 ▲' : '更多选项 ▼' }}
        </el-button>
      </div>

      <div class="actions">
        <el-button size="large" :disabled="loading" @click="title = ''; description = ''; presetId = undefined">
          清空
        </el-button>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!title.trim()"
          @click="submit"
        >
          {{ loading ? 'AI 正在生成课程大纲...' : '开始学习' }}
        </el-button>
      </div>
    </el-card>

    <!-- Recent courses -->
    <div v-if="recentCourses.length > 0" class="recent-section">
      <h3>最近课程</h3>
      <div class="recent-grid">
        <el-card
          v-for="c in recentCourses"
          :key="c.id"
          class="recent-card"
          shadow="hover"
          @click="router.push({ name: 'course-player', params: { id: c.id } })"
        >
          <div class="card-title">{{ c.title }}</div>
          <div class="card-meta">
            <el-tag :type="statusTagType(c.status)" size="small">{{ statusLabel(c.status) }}</el-tag>
            <span class="card-date">{{ formatDate(c.created_at) }}</span>
          </div>
          <el-popconfirm
            title="确定要删除该课程吗？所有相关数据将被永久删除。"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @click.stop
            @confirm="handleDeleteCourse(c.id)"
          >
            <template #reference>
              <el-button
                class="card-delete-btn"
                type="danger"
                size="small"
                :icon="DeleteIcon"
                circle
                @click.stop
              />
            </template>
          </el-popconfirm>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete as DeleteIcon } from '@element-plus/icons-vue'
import { createCourse, listCourses, deleteCourse } from '@/api/course'
import { listPresets, deletePreset } from '@/api/knowledge'

const router = useRouter()

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
    // Silently fail — presets are optional
  }
})

async function loadRecentCourses() {
  try {
    const { data } = await listCourses({ page: 1, page_size: 20 })
    recentCourses.value = data.list || []
  } catch {
    // Silently fail — recent courses are optional
  }
}

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

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------
async function submit() {
  const trimmed = title.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入学习主题')
    return
  }

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
  }
}

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

function formatDate(iso: string | null): string {
  if (!iso) return ''
  // 后端存的是北京时间 naive datetime，isoformat() 如 "2026-06-18T17:03:00"
  const raw = iso.length >= 16 ? iso.slice(0, 16) : iso
  return raw.replace('T', ' ')
}
</script>

<style scoped>
.course-create {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 32px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%);
}

.hero {
  text-align: center;
  margin-bottom: 24px;
}

.hero h1 {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.create-card {
  width: 100%;
  max-width: 600px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 500;
}

.title-input {
  margin-bottom: 4px;
}

.advanced-section {
  margin-top: 8px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.toggle-advanced {
  align-self: flex-start;
  margin-top: 4px;
  padding: 0;
  font-size: 13px;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* Recent courses */
.recent-section {
  width: 100%;
  max-width: 600px;
}

.recent-section h3 {
  font-size: 16px;
  color: #606266;
  margin: 0 0 12px;
}

.recent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.recent-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.recent-card:hover {
  transform: translateY(-2px);
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-date {
  font-size: 12px;
  color: #c0c4cc;
}

.recent-card {
  position: relative;
}

.card-delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
  width: 28px;
  height: 28px;
  font-size: 14px;
}

.recent-card:hover .card-delete-btn {
  opacity: 1;
}

/* Preset list in advanced section */
.preset-list {
  margin-top: 10px;
}

.preset-list-label {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-bottom: 6px;
}

.preset-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 4px;
}

.preset-item-name {
  font-size: 13px;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preset-item-meta {
  font-size: 11px;
  color: #c0c4cc;
  white-space: nowrap;
}
</style>
