<template>
  <div class="player">
    <header class="player-header">
      <el-button text @click="$router.push('/')">返回</el-button>
      <span>{{ courseTitle }}</span>
    </header>
    <main class="player-main">
      <ModalTab v-model="activeModal" />
      <PptViewer
        v-if="activeModal === 'ppt'"
        :slides="pptSlides"
        :narration-urls="narrationUrls"
      />
      <KnowledgeGraph v-else-if="activeModal === 'mindmap'" :course-id="courseId" />
      <el-empty v-else description="内容生成中…" />
    </main>
    <GenerationProgress :course-id="courseId" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import ModalTab from '@/components/course/ModalTab.vue'
import PptViewer from '@/components/course/PptViewer.vue'
import KnowledgeGraph from '@/components/knowledge/KnowledgeGraph.vue'
import GenerationProgress from '@/components/GenerationProgress.vue'
import type { PptSlide } from '@/components/course/PptViewer.vue'

const route = useRoute()
const courseId = computed(() => Number(route.params.id))
const courseTitle = ref('课程播放器')
const activeModal = ref('ppt')

const pptSlides = ref<PptSlide[]>([
  {
    title: '示例幻灯片',
    bullets: ['Slide JSON 轮播渲染', '旁白音频同步播放'],
    image_url: undefined,
    notes: '欢迎使用 SITP',
  },
])
const narrationUrls = ref<string[]>([])
</script>

<style scoped>
.player {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.player-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.player-main {
  flex: 1;
  padding: 16px;
}
</style>
