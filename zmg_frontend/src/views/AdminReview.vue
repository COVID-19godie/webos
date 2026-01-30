<template>
  <div class="admin-container">
    <div class="header">
      <div class="title">审核后台</div>
      <div class="subtitle">应用审核与专题排序</div>
    </div>

    <div class="tabs">
      <button :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">待审核</button>
      <button :class="{ active: activeTab === 'collections' }" @click="activeTab = 'collections'">专题排序</button>
    </div>

    <div v-if="activeTab === 'review'" class="panel">
      <div class="panel-title">待审核列表</div>
      <div class="review-toolbar">
        <label class="select-all">
          <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
          全选
        </label>
        <input v-model="reviewReason" class="reason-input" placeholder="审核理由（可选）" />
        <button class="primary" @click="bulkApprove">批量通过</button>
        <button class="danger" @click="bulkReject">批量拒绝</button>
      </div>
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="pendingApps.length === 0" class="empty">暂无待审核</div>
      <div v-else class="review-list">
        <div v-for="app in pendingApps" :key="app.id" class="review-card">
          <label class="select-box">
            <input type="checkbox" :value="app.id" v-model="selectedIds" />
          </label>
          <div class="card-main">
            <div class="card-title">{{ app.title }}</div>
            <div class="card-summary">{{ app.summary || '暂无简介' }}</div>
            <div class="card-meta">{{ typeLabel(app.link_type) }}</div>
          </div>
          <div class="card-actions">
            <button class="primary" @click="approve(app)">通过</button>
            <button class="danger" @click="reject(app)">拒绝</button>
            <button class="secondary" @click="openApp(app)">预览</button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="panel">
      <div class="panel-title">专题卡片拖拽排序</div>
      <div class="collection-picker">
        <label>选择专题</label>
        <select v-model="selectedCollectionId" @change="loadCollectionItems">
          <option v-for="col in collections" :key="col.id" :value="col.id">{{ col.title }}</option>
        </select>
      </div>
      <div v-if="collectionItems.length === 0" class="empty">暂无条目</div>
      <div v-else class="card-grid">
        <div
          v-for="(item, index) in collectionItems"
          :key="item.id"
          class="drag-card"
          draggable="true"
          @dragstart="onDragStart(index)"
          @dragover.prevent
          @drop="onDrop(index)"
        >
          <div class="drag-handle">⋮⋮</div>
          <div class="drag-title">{{ item.app.title }}</div>
        </div>
      </div>
      <div class="actions">
        <button class="primary" @click="saveOrder">保存排序</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { appStoreApi } from '@/api'

const activeTab = ref('review')
const loading = ref(false)
const pendingApps = ref([])
const selectedIds = ref([])
const reviewReason = ref('')
const collections = ref([])
const selectedCollectionId = ref(null)
const collectionItems = ref([])
const dragIndex = ref(null)
const isAllSelected = computed(() => pendingApps.value.length > 0 && selectedIds.value.length === pendingApps.value.length)

const typeLabel = (value) => {
  const map = { h5: 'H5应用', video: '视频链接', doc: '文章/文档', image: '图片集', other: '其他' }
  return map[value] || '其他'
}

const loadPending = async () => {
  loading.value = true
  try {
    const res = await appStoreApi.list({ status: 'pending' })
    pendingApps.value = res.data.results || res.data
    selectedIds.value = []
  } catch (err) {
    console.error('加载失败', err)
    pendingApps.value = []
  } finally {
    loading.value = false
  }
}

const approve = async (app) => {
  try {
    await appStoreApi.approve(app.id, { reason: reviewReason.value })
    pendingApps.value = pendingApps.value.filter(i => i.id !== app.id)
    selectedIds.value = selectedIds.value.filter(id => id !== app.id)
  } catch (err) {
    alert('无权限或操作失败')
  }
}

const reject = async (app) => {
  try {
    await appStoreApi.reject(app.id, { reason: reviewReason.value })
    pendingApps.value = pendingApps.value.filter(i => i.id !== app.id)
    selectedIds.value = selectedIds.value.filter(id => id !== app.id)
  } catch (err) {
    alert('无权限或操作失败')
  }
}

const openApp = (app) => window.open(app.link, '_blank')

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = pendingApps.value.map(app => app.id)
  }
}

const bulkApprove = async () => {
  if (!selectedIds.value.length) return
  try {
    await appStoreApi.bulkApprove({ ids: selectedIds.value, reason: reviewReason.value })
    pendingApps.value = pendingApps.value.filter(app => !selectedIds.value.includes(app.id))
    selectedIds.value = []
  } catch (err) {
    alert('批量通过失败')
  }
}

const bulkReject = async () => {
  if (!selectedIds.value.length) return
  try {
    await appStoreApi.bulkReject({ ids: selectedIds.value, reason: reviewReason.value })
    pendingApps.value = pendingApps.value.filter(app => !selectedIds.value.includes(app.id))
    selectedIds.value = []
  } catch (err) {
    alert('批量拒绝失败')
  }
}

const loadCollections = async () => {
  try {
    const res = await appStoreApi.collections()
    collections.value = res.data || []
    if (!selectedCollectionId.value && collections.value.length) {
      selectedCollectionId.value = collections.value[0].id
    }
    loadCollectionItems()
  } catch (err) {
    collections.value = []
  }
}

const loadCollectionItems = () => {
  const col = collections.value.find(c => c.id === selectedCollectionId.value)
  collectionItems.value = col?.items ? [...col.items].sort((a, b) => a.order - b.order) : []
}

const onDragStart = (index) => {
  dragIndex.value = index
}

const onDrop = (index) => {
  if (dragIndex.value === null) return
  const item = collectionItems.value.splice(dragIndex.value, 1)[0]
  collectionItems.value.splice(index, 0, item)
  dragIndex.value = null
}

const saveOrder = async () => {
  const payload = collectionItems.value.map((item, idx) => ({
    id: item.id,
    order: idx
  }))
  try {
    await appStoreApi.reorderCollection(selectedCollectionId.value, payload)
    alert('排序已保存')
  } catch (err) {
    alert('保存失败：无权限或网络错误')
  }
}

onMounted(() => {
  loadPending()
  loadCollections()
})
</script>

<style scoped>
.admin-container { padding: 30px; background: var(--bg); min-height: 100vh; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.header { text-align: center; margin-bottom: 18px; }
.title { font-size: 28px; font-weight: 700; color: var(--text); }
.subtitle { color: var(--muted); margin-top: 6px; }
.tabs { display: flex; justify-content: center; gap: 10px; margin-bottom: 16px; }
.tabs button { padding: 8px 14px; border-radius: 999px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.tabs button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.panel { background: var(--surface); border-radius: var(--radius-lg); padding: 18px; box-shadow: var(--panel-shadow); }
.panel-title { font-weight: 600; margin-bottom: 10px; }
.review-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
.reason-input { flex: 1; min-width: 220px; padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; }
.select-all { font-size: 13px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.select-box { display: flex; align-items: center; margin-right: 8px; }
.review-toolbar .primary { background: #10b981; color: #fff; border: 1px solid #10b981; border-radius: var(--radius-sm); padding: 6px 10px; cursor: pointer; }
.review-toolbar .danger { background: #ef4444; color: #fff; border: 1px solid #ef4444; border-radius: var(--radius-sm); padding: 6px 10px; cursor: pointer; }
.review-list { display: grid; gap: 10px; }
.review-card { display: flex; justify-content: space-between; align-items: center; border: 1px solid #e5e7eb; border-radius: var(--radius-lg); padding: 12px; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.review-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0,0,0,0.08); }
.card-title { font-weight: 600; }
.card-summary { color: #6b7280; font-size: 12px; margin-top: 4px; }
.card-meta { color: #9ca3af; font-size: 12px; margin-top: 4px; }
.card-actions { display: flex; gap: 8px; }
.card-actions button { padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.card-actions .primary { background: #10b981; color: #fff; border-color: #10b981; }
.card-actions .danger { background: #ef4444; color: #fff; border-color: #ef4444; }
.card-actions .secondary { color: #374151; }
.collection-picker { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.collection-picker select { padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; }
.card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.drag-card { border: 1px solid #e5e7eb; border-radius: var(--radius-lg); padding: 12px; background: #fafafa; display: flex; align-items: center; gap: 10px; cursor: grab; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.drag-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0,0,0,0.08); }
.drag-handle { color: #9ca3af; font-size: 16px; }
.drag-title { font-weight: 500; }
.actions { margin-top: 12px; display: flex; justify-content: flex-end; }
.actions .primary { padding: 8px 14px; border-radius: var(--radius-sm); border: none; background: var(--accent); color: #fff; cursor: pointer; }
.empty { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
