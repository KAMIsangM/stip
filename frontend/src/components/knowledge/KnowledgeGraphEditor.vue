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
        <button :class="{ active: tab === 'edgeList' }" @click="tab = 'edgeList'; loadEdgeList()">边列表</button>
        <button :class="{ active: tab === 'preset' }" @click="tab = 'preset'">保存为预设</button>
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
        <div v-if="edgeNodesLoading" class="kge-list-status">加载节点列表…</div>
        <template v-else>
          <label>
            源节点 <span class="req">*</span>
            <select v-model.number="edgeForm.source_node_id" required>
              <option :value="0" disabled>请选择源节点…</option>
              <option v-for="n in edgeNodeOptions" :key="n.id" :value="n.id">
                {{ n.name }} ({{ n.type }}, ID: {{ n.id }})
              </option>
            </select>
          </label>
          <label>
            目标节点 <span class="req">*</span>
            <select v-model.number="edgeForm.target_node_id" required>
              <option :value="0" disabled>请选择目标节点…</option>
              <option v-for="n in edgeNodeOptions" :key="n.id" :value="n.id">
                {{ n.name }} ({{ n.type }}, ID: {{ n.id }})
              </option>
            </select>
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
        </template>
      </form>

      <!-- node list with edit & delete -->
      <div v-if="tab === 'list'" class="kge-list">
        <div v-if="listLoading" class="kge-list-status">加载中…</div>
        <div v-else-if="nodeList.length === 0" class="kge-list-status">暂无节点</div>
        <ul v-else>
          <li v-for="n in nodeList" :key="n.id">
            <!-- view mode -->
            <template v-if="editingNodeId !== n.id">
              <span class="kge-node-name">
                <i :style="{ background: typeColor(n.type) }" class="kge-dot" />
                {{ n.name }}
                <small>({{ n.type }}, {{ n.importance }})</small>
              </span>
              <span class="kge-row-actions">
                <button class="kge-edit-btn" @click="handleEditNode(n)">编辑</button>
                <button class="kge-del" @click="handleDeleteNode(n.id)" :disabled="deletingId === n.id">
                  {{ deletingId === n.id ? '…' : '删除' }}
                </button>
              </span>
            </template>
            <!-- edit mode -->
            <template v-else>
              <div class="kge-inline-edit">
                <input v-model="editNodeForm.name" placeholder="名称" class="kge-inline-input" />
                <select v-model="editNodeForm.type" class="kge-inline-select">
                  <option value="概念">概念</option>
                  <option value="技能">技能</option>
                  <option value="记忆">记忆</option>
                  <option value="实践">实践</option>
                  <option value="综合">综合</option>
                </select>
                <input v-model.number="editNodeForm.importance" type="number" min="0" max="1" step="0.05" class="kge-inline-input-num" />
                <button class="kge-save-btn" @click="handleSaveNodeEdit()">保存</button>
                <button class="kge-cancel-btn" @click="cancelNodeEdit()">取消</button>
              </div>
            </template>
          </li>
        </ul>
        <span v-if="listMsg" class="kge-msg" :class="{ 'kge-err': listErr }">{{ listMsg }}</span>
      </div>

      <!-- edge list -->
      <div v-if="tab === 'edgeList'" class="kge-list">
        <div v-if="edgeListLoading" class="kge-list-status">加载中…</div>
        <div v-else-if="edgeList.length === 0" class="kge-list-status">暂无边</div>
        <ul v-else>
          <li v-for="e in edgeList" :key="e.id" class="kge-edge-row">
            <!-- view mode -->
            <template v-if="editingEdgeId !== e.id">
              <span class="kge-edge-info">
                <span class="kge-edge-src">{{ e.sourceName }}</span>
                <span class="kge-edge-arrow">→</span>
                <span class="kge-edge-rel">{{ e.relation_type }}</span>
                <span class="kge-edge-arrow">→</span>
                <span class="kge-edge-tgt">{{ e.targetName }}</span>
              </span>
              <span class="kge-row-actions">
                <button class="kge-edit-btn" @click="handleEditEdge(e)">编辑</button>
                <button class="kge-del" @click="handleDeleteEdge(e.id)" :disabled="deletingEdgeId === e.id">
                  {{ deletingEdgeId === e.id ? '…' : '删除' }}
                </button>
              </span>
            </template>
            <!-- edit mode -->
            <template v-else>
              <div class="kge-inline-edit">
                <span class="kge-edge-fixed">{{ e.sourceName }} → </span>
                <select v-model="editEdgeForm.relation_type" class="kge-inline-select">
                  <option value="prerequisite">前驱后继</option>
                  <option value="contains">包含</option>
                  <option value="causal">因果</option>
                  <option value="related">关联</option>
                </select>
                <span class="kge-edge-fixed"> → {{ e.targetName }}</span>
                <button class="kge-save-btn" @click="handleSaveEdgeEdit()">保存</button>
                <button class="kge-cancel-btn" @click="cancelEdgeEdit()">取消</button>
              </div>
            </template>
          </li>
        </ul>
        <span v-if="edgeListMsg" class="kge-msg" :class="{ 'kge-err': edgeListErr }">{{ edgeListMsg }}</span>
      </div>

      <!-- save as preset -->
      <form v-if="tab === 'preset'" class="kge-form" @submit.prevent="handleSaveAsPreset">
        <p class="kge-hint">将当前课程的知识图谱保存为预设模板，之后创建新课程时可直接选用。</p>
        <label>
          预设名称 <span class="req">*</span>
          <input v-model="presetForm.name" placeholder="例如：数据结构进阶" required maxlength="100" />
        </label>
        <label>
          描述（可选）
          <textarea v-model="presetForm.description" rows="2" placeholder="简要描述该知识图谱的内容" />
        </label>
        <button class="kge-submit" :disabled="presetSaving" type="submit">
          {{ presetSaving ? '保存中…' : '保存为预设' }}
        </button>
        <span v-if="presetMsg" class="kge-msg" :class="{ 'kge-err': presetErr }">{{ presetMsg }}</span>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createNode,
  createEdge,
  deleteNode,
  updateNode,
  updateEdge,
  deleteEdge,
  getKnowledgeGraph,
  saveAsPreset,
  type NodeCreatePayload,
  type NodeUpdatePayload,
  type EdgeCreatePayload,
  type EdgeUpdatePayload,
  type PresetSavePayload,
} from '@/api/knowledge'

const props = defineProps<{ courseId: number }>()
const emit = defineEmits<{ (e: 'updated'): void }>()

const open = ref(false)
const tab = ref<'node' | 'edge' | 'list' | 'edgeList' | 'preset'>('node')

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
    ElMessage.success('节点已添加')
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
const edgeNodeOptions = ref<any[]>([])
const edgeNodesLoading = ref(false)
const edgeSaving = ref(false)
const edgeMsg = ref('')
const edgeErr = ref(false)

async function loadEdgeNodeOptions() {
  edgeNodesLoading.value = true
  try {
    const { data } = await getKnowledgeGraph(props.courseId)
    edgeNodeOptions.value = data.nodes || []
  } catch {
    edgeNodeOptions.value = []
  } finally {
    edgeNodesLoading.value = false
  }
}

async function handleAddEdge() {
  if (!edgeForm.source_node_id || !edgeForm.target_node_id) return
  edgeSaving.value = true
  edgeMsg.value = ''
  try {
    await createEdge(props.courseId, { ...edgeForm })
    edgeMsg.value = '边已添加'
    edgeErr.value = false
    ElMessage.success('边已添加')
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

// ── node edit (inline) ──
const editingNodeId = ref<number | null>(null)
const editNodeForm = reactive<NodeUpdatePayload>({
  name: '',
  type: '概念',
  importance: 0.5,
  description: '',
})

function handleEditNode(n: any) {
  editingNodeId.value = n.id
  editNodeForm.name = n.name
  editNodeForm.type = n.type
  editNodeForm.importance = n.importance
  editNodeForm.description = n.description || ''
}

async function handleSaveNodeEdit() {
  if (!editingNodeId.value || !editNodeForm.name?.trim()) return
  listMsg.value = ''
  try {
    await updateNode(props.courseId, editingNodeId.value, { ...editNodeForm })
    listMsg.value = '节点已更新'
    listErr.value = false
    ElMessage.success('节点已更新')
    editingNodeId.value = null
    await loadNodeList()
    emit('updated')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '更新失败'
    listMsg.value = msg
    listErr.value = true
    ElMessage.error(msg)
  }
}

function cancelNodeEdit() {
  editingNodeId.value = null
}

async function handleDeleteNode(nodeId: number) {
  try {
    await ElMessageBox.confirm(
      `确认删除节点 #${nodeId}？关联边也会被删除。`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户取消
  }
  deletingId.value = nodeId
  listMsg.value = ''
  try {
    await deleteNode(props.courseId, nodeId)
    nodeList.value = nodeList.value.filter((n: any) => n.id !== nodeId)
    listMsg.value = `节点 #${nodeId} 已删除`
    listErr.value = false
    ElMessage.success(`节点 #${nodeId} 已删除`)
    emit('updated')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '删除失败'
    listMsg.value = msg
    listErr.value = true
    ElMessage.error(msg)
  } finally {
    deletingId.value = null
  }
}

function typeColor(t: string) {
  const map: Record<string, string> = { '概念': '#5470c6', '技能': '#91cc75', '记忆': '#fac858', '实践': '#ee6666', '综合': '#fc8452' }
  return map[t] || '#aaa'
}

// ── edge list ──
const edgeList = ref<any[]>([])
const edgeListLoading = ref(false)
const edgeListMsg = ref('')
const edgeListErr = ref(false)
const editingEdgeId = ref<number | null>(null)
const editEdgeForm = reactive<EdgeUpdatePayload>({ relation_type: 'related' })
const deletingEdgeId = ref<number | null>(null)

async function loadEdgeList() {
  edgeListLoading.value = true
  try {
    const { data } = await getKnowledgeGraph(props.courseId)
    const nodeMap = new Map((data.nodes || []).map((n: any) => [n.id, n.name]))
    edgeList.value = (data.edges || []).map((e: any) => ({
      ...e,
      sourceName: nodeMap.get(e.source_node_id) || `#${e.source_node_id}`,
      targetName: nodeMap.get(e.target_node_id) || `#${e.target_node_id}`,
    }))
  } catch {
    edgeList.value = []
  } finally {
    edgeListLoading.value = false
  }
}

function handleEditEdge(e: any) {
  editingEdgeId.value = e.id
  editEdgeForm.relation_type = e.relation_type
}

async function handleSaveEdgeEdit() {
  if (!editingEdgeId.value || !editEdgeForm.relation_type) return
  edgeListMsg.value = ''
  try {
    await updateEdge(props.courseId, editingEdgeId.value, { ...editEdgeForm })
    edgeListMsg.value = '边已更新'
    edgeListErr.value = false
    ElMessage.success('边已更新')
    editingEdgeId.value = null
    await loadEdgeList()
    emit('updated')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '更新失败'
    edgeListMsg.value = msg
    edgeListErr.value = true
    ElMessage.error(msg)
  }
}

function cancelEdgeEdit() {
  editingEdgeId.value = null
}

async function handleDeleteEdge(edgeId: number) {
  try {
    await ElMessageBox.confirm(
      `确认删除边 #${edgeId}？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  deletingEdgeId.value = edgeId
  edgeListMsg.value = ''
  try {
    await deleteEdge(props.courseId, edgeId)
    edgeList.value = edgeList.value.filter((e: any) => e.id !== edgeId)
    edgeListMsg.value = `边 #${edgeId} 已删除`
    edgeListErr.value = false
    ElMessage.success(`边 #${edgeId} 已删除`)
    emit('updated')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '删除失败'
    edgeListMsg.value = msg
    edgeListErr.value = true
    ElMessage.error(msg)
  } finally {
    deletingEdgeId.value = null
  }
}

// ── save as preset ──
const presetForm = reactive<PresetSavePayload>({
  name: '',
  description: '',
})
const presetSaving = ref(false)
const presetMsg = ref('')
const presetErr = ref(false)

async function handleSaveAsPreset() {
  if (!presetForm.name.trim()) return
  presetSaving.value = true
  presetMsg.value = ''
  try {
    const { data } = await saveAsPreset(props.courseId, { ...presetForm })
    const msg = `预设「${data.preset.name}」已保存（${data.preset.node_count} 个节点，${data.preset.edge_count} 条边）`
    presetMsg.value = msg
    presetErr.value = false
    ElMessage.success(msg)
    presetForm.name = ''
    presetForm.description = ''
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '保存失败'
    presetMsg.value = msg
    presetErr.value = true
    ElMessage.error(msg)
  } finally {
    presetSaving.value = false
  }
}

// 切换到「新增边」tab 时自动加载节点列表
watch(tab, (newTab) => {
  if (newTab === 'edge' && edgeNodeOptions.value.length === 0) {
    loadEdgeNodeOptions()
  }
})
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

/* save as preset hint */
.kge-hint {
  margin: 0 0 4px 0;
  font-size: 12px;
  color: #888;
  line-height: 1.5;
}

/* row actions */
.kge-row-actions {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-shrink: 0;
}

.kge-edit-btn {
  padding: 2px 10px;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  background: #fff;
  color: #5470c6;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.kge-edit-btn:hover {
  background: #5470c6;
  color: #fff;
  border-color: #5470c6;
}

/* inline edit */
.kge-inline-edit {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  width: 100%;
  padding: 4px 0;
}

.kge-inline-input {
  width: 120px;
  padding: 4px 8px;
  border: 1px solid #5470c6;
  border-radius: 3px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
}

.kge-inline-input-num {
  width: 70px;
  padding: 4px 8px;
  border: 1px solid #5470c6;
  border-radius: 3px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
}

.kge-inline-select {
  padding: 4px 6px;
  border: 1px solid #5470c6;
  border-radius: 3px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
}

.kge-save-btn {
  padding: 3px 10px;
  border: none;
  border-radius: 3px;
  background: #5470c6;
  color: #fff;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}

.kge-save-btn:hover {
  background: #4262b0;
}

.kge-cancel-btn {
  padding: 3px 10px;
  border: 1px solid #ddd;
  border-radius: 3px;
  background: #fff;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.kge-cancel-btn:hover {
  background: #f0f0f0;
}

/* edge list */
.kge-edge-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kge-edge-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  min-width: 0;
}

.kge-edge-src,
.kge-edge-tgt {
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.kge-edge-arrow {
  color: #bbb;
  font-size: 11px;
}

.kge-edge-rel {
  padding: 1px 6px;
  background: #f0f0f0;
  border-radius: 3px;
  color: #666;
  font-size: 11px;
  white-space: nowrap;
}

.kge-edge-fixed {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}
</style>
