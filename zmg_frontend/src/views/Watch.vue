<template>
  <div class="watch-container">
    <div class="header">
      <div class="title">观看中心</div>
      <div class="subtitle">只关注内容与体验</div>
      <div class="search-bar">
        <input v-model="query" placeholder="搜索应用/知识链接..." />
        <button @click="loadApps">搜索</button>
      </div>
    </div>

    <div class="filters">
      <button :class="{ active: filterType === '' }" @click="setType('')">全部</button>
      <button v-for="t in typeOptions" :key="t.value" :class="{ active: filterType === t.value }" @click="setType(t.value)">
        {{ t.label }}
      </button>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="apps.length === 0" class="empty">暂无内容</div>
    <div v-else class="grid">
      <div v-for="app in apps" :key="app.id" class="card">
        <div class="card-title">{{ app.title }}</div>
        <div class="card-summary">{{ app.summary || '暂无简介' }}</div>
        <div class="card-tags">
          <span v-for="t in app.tags" :key="t.id">#{{ t.name }}</span>
        </div>
        <div class="card-actions">
          <button @click="viewApp(app)">观看/打开</button>
          <button class="secondary" @click="likeApp(app)">点赞 {{ app.like_count }}</button>
        </div>
        <div class="card-meta">{{ typeLabel(app.link_type) }} · 浏览 {{ app.view_count }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { appStoreApi } from '@/api'

const apps = ref([])
const loading = ref(false)
const query = ref('')
const filterType = ref('')

const typeOptions = [
  { value: 'h5', label: 'H5应用' },
  { value: 'video', label: '视频链接' },
  { value: 'doc', label: '文章/文档' },
  { value: 'image', label: '图片集' },
  { value: 'other', label: '其他' }
]

const typeLabel = (value) => {
  const item = typeOptions.find(t => t.value === value)
  return item ? item.label : '其他'
}

const loadApps = async () => {
  loading.value = true
  try {
    const params = {}
    if (query.value) params.search = query.value
    if (filterType.value) params.link_type = filterType.value
    const res = await appStoreApi.list(params)
    apps.value = res.data.results || res.data
  } catch (err) {
    console.error('加载失败', err)
  } finally {
    loading.value = false
  }
}

const setType = (value) => {
  filterType.value = value
  loadApps()
}

const viewApp = async (app) => {
  try {
    const res = await appStoreApi.view(app.id)
    app.view_count = res.data.view_count
  } catch (err) {}
  window.open(app.link, '_blank')
}

const likeApp = async (app) => {
  try {
    const res = await appStoreApi.like(app.id)
    app.like_count = res.data.like_count
  } catch (err) {}
}

onMounted(loadApps)
</script>

<style scoped>
.watch-container { padding: 30px; background: var(--bg); min-height: 100vh; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.header { text-align: center; margin-bottom: 18px; }
.title { font-size: 28px; font-weight: 700; color: var(--text); }
.subtitle { color: var(--muted); margin-top: 6px; }
.search-bar { margin-top: 14px; display: flex; justify-content: center; gap: 10px; }
.search-bar input { width: 420px; padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; }
.search-bar button { padding: 10px 16px; border-radius: var(--radius-sm); border: none; background: var(--accent); color: #fff; cursor: pointer; }
.filters { text-align: center; margin-bottom: 18px; }
.filters button { margin: 4px 6px 0 0; padding: 6px 10px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.filters button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.card { border: 1px solid #e5e7eb; border-radius: var(--radius-lg); padding: 12px; background: #fff; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,0.08); }
.card-title { font-weight: 600; }
.card-summary { color: #6b7280; font-size: 12px; margin-top: 4px; }
.card-tags { margin-top: 6px; font-size: 12px; color: #4b5563; }
.card-tags span { margin-right: 6px; }
.card-actions { margin-top: 10px; display: flex; gap: 6px; }
.card-actions button { padding: 6px 8px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; font-size: 12px; }
.card-actions button.secondary { color: #374151; }
.card-meta { margin-top: 8px; font-size: 12px; color: #9ca3af; }
.empty { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
