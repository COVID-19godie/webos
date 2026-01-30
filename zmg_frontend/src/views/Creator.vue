<template>
  <div class="creator-container">
    <div class="header">
      <div class="title">创作者中心</div>
      <div class="subtitle">上传专注于上传</div>
    </div>

    <div v-if="isAdmin" class="panel admin-panel">
      <div class="panel-title">管理员入口</div>
      <div class="admin-actions">
        <button @click="openAdmin">进入审核后台</button>
      </div>
    </div>

    <div class="panel submit-panel">
      <div class="panel-title">提交链接</div>
      <div class="submit-form">
        <input v-model="form.title" placeholder="标题" />
        <input v-model="form.link" placeholder="链接（H5/视频/文章/图片）" />
        <input v-model="form.summary" placeholder="一句话简介" />
        <input v-model="form.tags" placeholder="标签（逗号分隔）" />
        <select v-model="form.link_type">
          <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <button @click="submitApp">提交审核</button>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">我的提交</div>
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="apps.length === 0" class="empty">暂无内容</div>
      <div v-else class="list">
        <div v-for="app in apps" :key="app.id" class="item">
          <div class="item-main">
            <div class="item-title">{{ app.title }}</div>
            <div class="item-summary">{{ app.summary || '暂无简介' }}</div>
            <div class="item-meta">
              {{ typeLabel(app.link_type) }} · 状态 {{ statusLabel(app.status) }}
            </div>
          </div>
          <div class="item-actions">
            <button @click="openApp(app)">预览</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { appStoreApi } from '@/api'

const apps = ref([])
const loading = ref(false)
const isAdmin = computed(() => localStorage.getItem('user_role') === 'admin')

const typeOptions = [
  { value: 'h5', label: 'H5应用' },
  { value: 'video', label: '视频链接' },
  { value: 'doc', label: '文章/文档' },
  { value: 'image', label: '图片集' },
  { value: 'other', label: '其他' }
]

const form = ref({
  title: '',
  link: '',
  summary: '',
  tags: '',
  link_type: 'h5'
})

const typeLabel = (value) => {
  const item = typeOptions.find(t => t.value === value)
  return item ? item.label : '其他'
}

const statusLabel = (value) => {
  if (value === 'approved') return '已上架'
  if (value === 'rejected') return '已拒绝'
  return '待审核'
}

const loadMine = async () => {
  loading.value = true
  try {
    const res = await appStoreApi.mine()
    apps.value = res.data.results || res.data
  } catch (err) {
    console.error('加载失败', err)
  } finally {
    loading.value = false
  }
}

const submitApp = async () => {
  if (!form.value.title || !form.value.link) return
  const payload = {
    title: form.value.title,
    link: form.value.link,
    summary: form.value.summary,
    link_type: form.value.link_type,
    tag_names: form.value.tags.split(',').map(t => t.trim()).filter(Boolean)
  }
  try {
    await appStoreApi.submit(payload)
    form.value = { title: '', link: '', summary: '', tags: '', link_type: 'h5' }
    await loadMine()
    alert('提交成功，等待审核')
  } catch (err) {
    alert('提交失败')
  }
}

const openApp = (app) => {
  window.open(app.link, '_blank')
}

const openAdmin = () => {
  window.open('/admin-review', '_blank')
}

onMounted(loadMine)
</script>

<style scoped>
.creator-container { padding: 30px; background: var(--bg); min-height: 100vh; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.header { text-align: center; margin-bottom: 18px; }
.title { font-size: 28px; font-weight: 700; color: var(--text); }
.subtitle { color: var(--muted); margin-top: 6px; }
.panel { background: var(--surface); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.06); transition: transform 0.18s ease, box-shadow 0.18s ease; }
.panel:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,0.08); }
.panel-title { font-weight: 600; margin-bottom: 10px; }
.submit-form { display: grid; gap: 10px; grid-template-columns: repeat(2, 1fr); }
.submit-form input, .submit-form select { padding: 8px 10px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; }
.submit-form button { grid-column: span 2; padding: 10px; border-radius: var(--radius-sm); border: none; background: #10b981; color: #fff; cursor: pointer; }
.admin-actions button { padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.list { display: grid; gap: 10px; }
.item { border: 1px solid #e5e7eb; border-radius: var(--radius-lg); padding: 12px; display: flex; justify-content: space-between; align-items: center; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.item:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0,0,0,0.08); }
.item-title { font-weight: 600; }
.item-summary { color: #6b7280; font-size: 12px; margin-top: 4px; }
.item-meta { color: #9ca3af; font-size: 12px; margin-top: 6px; }
.item-actions button { padding: 6px 8px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; font-size: 12px; }
.empty { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
