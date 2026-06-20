<template>
  <div class="kge-panel">
    <div class="kge-header">
      <h4>图谱编辑</h4>
      <button class="kge-toggle" @click="open = !open">{{ open ? '收起 ▲' : '展开 ▼' }}</button>
    </div>

    <div v-if="open" class="kge-body">
      <!-- tabs -->
      <div class="kge-tabs">
        <button :class="{ active: tab === 'node' }" @click="tab = 'node'">新增节点</button>
        <button :class="{ active: tab === 'edge' }" @click="tab = 'edge'">新增边</button>
        <button :class="{ active: tab === 'list' }" @click="tab = 'list'; loadNodeList()">节点列表</button>
      </div>

      <!-- add node -->
      <form v-if="tab === 'node'" class="kge-form" @submit.prevent="handleAddNode">
        <label>
          名称 <span class="req">*</span>
          <input v-model="nodeForm.name" placeholder="知识点名称" required maxlength="200" />
        </label>
        <label>
          类型
          <select v-model="nodeForm.type">
            <option value="概念">概念</option>
            <option value="技能">技能</option>
            <option value="记忆">记忆</option>
            <option value="实践">实践</option>
            <option value="综合">综合</option>
          </select>
        </label>
        <label>
          重要度 (0~1)
          <input v-model.number="nodeForm.importance" type="number" min="0" max="1" step="0.05" />
        </label>
        <label>
          描述
          <textarea v-model="nodeForm.description" rows="2" placeholder="可选描述" />
        </label>
        <button class="kge-submit" :disabled="nodeSaving" type="submit">
          {{ nodeSaving ? '保存中…' : '添加节点' }}
        </button>
        <span v-if="nodeMsg" class="kge-msg" :class="{ 'kge-err': nodeErr }">{{ nodeMsg }}</span>
      </form>

      <!-- add edge -->
      <form v-if="tab === 'edge'" class="kge-form" @submit.prevent="handleAddEdge">
        <label>
          源节点 ID <span class="req">*</span>
          <input v-model.number="edgeForm.source_node_id" type="number" required min="1" />
        </label>
        <label>
          目标节点 ID <span class="req">*</span>
          <input v-model.number="edgeForm.target_node_id" type="number" required min="1" />
        </label>
        <label>
          关系类型
          <select v-model="edgeForm.relation_type">
            <option value="prerequisite">前驱后继</option>
            <option value="contains">包含</option>
            <option value="causal">因果</option>
            <option value="related">关联</option>
          </select>
        </label>
        <button class="kge-submit" :disabled="edgeSaving" type="submit">
          {{ edgeSaving ? '保存中…' : '添加边' }}
        </button>
        <span v-if="edgeMsg" class="kge-msg" :class="{ 'kge-err': edgeErr }">{{ edgeMsg }}</span>
      </form>

      <!-- node list with delete -->
      <div v-if="tab === 'list'" class="kge-list">
        <div v-if="listLoading" class="kge-list-status">加载中…</div>
        <div v-else-if="nodeList.length === 0" class="kge-list-status">暂无节点</div>
        <ul v-else>
          <li v-for="n in nodeList" :key="n.id">
            <span class="kge-node-name">
              <i :style="{ background: typeColor(n.type) }" class="kge-dot" />
              {{ n.name }}
              <small>({{ n.type }}, {{ n.importance }})</small>
            </span>
            <button class="kge-del" @click="handleDeleteNode(n.id)" :disabled="deletingId === n.id">
              {{ deletingId === n.id ? '…' : '删除' }}
            </button>
          </li>
        </ul>
        <span v-if="listMsg" class="kge-msg" :class="{ 'kge-err': listErr }">{{ listMsg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  createNode,
  createEdge,
  deleteNode,
  getKnowledgeGraph,
  type NodeCreatePayload,
  type EdgeCreatePayload,
} from '@/api/knowledge'

const props = defineProps<{ courseId: number }>()
const emit = defineEmits<{ (e: 'updated'): void }>()

const open = ref(false)
const tab = ref<'node' | 'edge' | 'list'>('node')

// ── node form ──
const nodeForm = reactive<NodeCreatePayload>({
  name: '',
  type: '概念',
  importance: 0.5,
  description: '',
})
const nodeSaving = ref(false)
const nodeMsg = ref('')
const nodeErr = ref(false)

async function handleAddNode() {
  if (!nodeForm.name.trim()) return
  nodeSaving.value = true
  nodeMsg.value = ''
  try {
    await createNode(props.courseId, { ...nodeForm })
    nodeMsg.value = '节点已添加'
    nodeErr.value = false
    nodeForm.name = ''
    nodeForm.description = ''
    emit('updated')
  } catch (err: any) {
    nodeMsg.value = err?.response?.data?.detail || '添加失败'
    nodeErr.value = true
  } finally {
    nodeSaving.value = false
  }
}

// ── edge form ──
const edgeForm = reactive<EdgeCreatePayload>({
  source_node_id: 0,
  target_node_id: 0,
  relation_type: 'related',
})
const edgeSaving = ref(false)
const edgeMsg = ref('')
const edgeErr = ref(false)

async function handleAddEdge() {
  if (!edgeForm.source_node_id || !edgeForm.target_node_id) return
  edgeSaving.value = true
  edgeMsg.value = ''
  try {
    await createEdge(props.courseId, { ...edgeForm })
    edgeMsg.value = '边已添加'
    edgeErr.value = false
    emit('updated')
  } catch (err: any) {
    edgeMsg.value = err?.response?.data?.detail || '添加失败'
    edgeErr.value = true
  } finally {
    edgeSaving.value = false
  }
}

// ── node list ──
const nodeList = ref<any[]>([])
const listLoading = ref(false)
const listMsg = ref('')
const listErr = ref(false)
const deletingId = ref<number | null>(null)

async function loadNodeList() {
  listLoading.value = true
  try {
    const { data } = await getKnowledgeGraph(props.courseId)
    nodeList.value = data.nodes || []
  } catch {
    nodeList.value = []
  } finally {
    listLoading.value = false
  }
}

async function handleDeleteNode(nodeId: number) {
  if (!confirm(`确认删除节点 #${nodeId}？关联边也会被删除。`)) return
  deletingId.value = nodeId
  listMsg.value = ''
  try {
    await deleteNode(props.courseId, nodeId)
    nodeList.value = nodeList.value.filter((n: any) => n.id !== nodeId)
    listMsg.value = `节点 #${nodeId} 已删除`
    listErr.value = false
    emit('updated')
  } catch (err: any) {
    listMsg.value = err?.response?.data?.detail || '删除失败'
    listErr.value = true
  } finally {
    deletingId.value = null
  }
}

function typeColor(t: string) {
  const map: Record<string, string> = { '概念': '#5470c6', '技能': '#91cc75', '记忆': '#fac858', '实践': '#ee6666', '综合': '#fc8452' }
  return map[t] || '#aaa'
}
</script>

<style scoped>
.kge-panel {
  background: #fff;
  border-radius: 8px;
  margin-top: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.kge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f7f8fa;
  border-bottom: 1px solid #eee;
}

.kge-header h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
}

.kge-toggle {
  border: none;
  background: transparent;
  color: #5470c6;
  cursor: pointer;
  font-size: 12px;
}

.kge-body {
  padding: 12px 16px;
}

/* tabs */
.kge-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 14px;
}

.kge-tabs button {
  flex: 1;
  padding: 6px 0;
  border: 1px solid #ddd;
  background: #fafafa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.kge-tabs button:first-child {
  border-radius: 4px 0 0 4px;
}

.kge-tabs button:last-child {
  border-radius: 0 4px 4px 0;
}

.kge-tabs button.active {
  background: #5470c6;
  color: #fff;
  border-color: #5470c6;
}

/* form */
.kge-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kge-form label {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 12px;
  color: #666;
}

.req {
  color: #d32f2f;
}

.kge-form input,
.kge-form select,
.kge-form textarea {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
}

.kge-form input:focus,
.kge-form select:focus,
.kge-form textarea:focus {
  border-color: #5470c6;
}

.kge-submit {
  padding: 7px 0;
  border: none;
  border-radius: 4px;
  background: #5470c6;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}

.kge-submit:hover:not(:disabled) {
  background: #4262b0;
}

.kge-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.kge-msg {
  font-size: 12px;
  color: #2e7d32;
}

.kge-err {
  color: #d32f2f;
}

/* list */
.kge-list {
  max-height: 280px;
  overflow-y: auto;
}

.kge-list-status {
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-size: 13px;
}

.kge-list ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.kge-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.kge-node-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.kge-node-name small {
  color: #999;
  font-size: 11px;
}

.kge-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.kge-del {
  padding: 2px 10px;
  border: 1px solid #e0e0e0;
  border-radius: 3px;
  background: #fff;
  color: #d32f2f;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.kge-del:hover:not(:disabled) {
  background: #d32f2f;
  color: #fff;
  border-color: #d32f2f;
}
</style>
