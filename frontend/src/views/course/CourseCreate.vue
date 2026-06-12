<template>
  <div class="course-create">
    <el-card class="create-card">
      <h1>智能互动教学平台</h1>
      <p class="hint">输入学习主题，AI 将生成结构化课程大纲</p>
      <el-input
        v-model="title"
        placeholder="例如：Python 数据结构基础"
        size="large"
        @keyup.enter="submit"
      />
      <div class="actions">
        <el-button size="large" @click="title = ''">清空</el-button>
        <el-button type="primary" size="large" :loading="loading" @click="submit">
          进入课堂
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createCourse } from '@/api/course'

const router = useRouter()
const title = ref('')
const loading = ref(false)

async function submit() {
  if (!title.value.trim()) {
    ElMessage.warning('请输入学习主题')
    return
  }
  loading.value = true
  try {
    const { data } = await createCourse({ title: title.value.trim() })
    router.push({ name: 'course-player', params: { id: data.course_id || 1 } })
  } catch {
    ElMessage.error('创建课程失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.course-create {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.create-card {
  width: 100%;
  max-width: 560px;
}
.hint {
  color: #666;
  margin-bottom: 16px;
}
.actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
