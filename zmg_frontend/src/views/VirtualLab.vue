<template>
  <div class="lab-container">
    <div class="lab-header">
      <div class="title">虚拟实验室 · 实验类 H5 应用商店</div>
      <div class="subtitle">按学段与学科分类，快速找到课堂实验</div>
      <div class="header-actions">
        <input v-model="query" placeholder="搜索实验应用..." />
        <button @click="loadApps">搜索</button>
        <button class="ghost" @click="openStore">应用商店</button>
        <button class="ghost" @click="openWatch">观看中心</button>
      </div>
    </div>

    <div class="lab-body">
      <div class="sidebar">
        <div class="section">
          <div class="section-title">学段</div>
          <div class="chips">
            <button
              v-for="level in levels"
              :key="level.id"
              :class="{ active: selectedLevel === level.id }"
              @click="selectLevel(level.id)"
            >
              {{ level.label }}
            </button>
          </div>
        </div>

        <div class="section">
          <div class="section-title">学科</div>
          <div class="chips">
            <button
              v-for="subject in currentSubjects"
              :key="subject"
              :class="{ active: selectedSubject === subject }"
              @click="selectSubject(subject)"
            >
              {{ subject }}
            </button>
          </div>
        </div>

        <div class="section">
          <div class="section-title">提交实验应用</div>
          <div class="submit-form">
            <input v-model="form.title" placeholder="标题" />
            <input v-model="form.link" placeholder="H5 链接" />
            <input v-model="form.summary" placeholder="简介（可选）" />
            <button @click="submitApp">提交审核</button>
          </div>
          <div class="hint">建议标签：虚拟实验 + 学段 + 学科</div>
        </div>
      </div>

      <div class="main">
        <div class="section">
          <div class="section-title">
            {{ currentLevelLabel }} · {{ selectedSubject }}
          </div>
          <div v-if="loading" class="empty">加载中...</div>
          <div v-else-if="apps.length === 0" class="empty">暂无内容</div>
          <div v-else class="app-grid">
            <div v-for="app in apps" :key="app.id" class="app-card">
              <div class="app-title">{{ app.title }}</div>
              <div class="app-summary">{{ app.summary || '暂无简介' }}</div>
              <div class="app-tags">
                <span v-for="t in app.tags" :key="t.id">#{{ t.name }}</span>
              </div>
              <div class="app-actions">
                <button @click="openApp(app)">打开</button>
                <button class="secondary" @click="likeApp(app)">点赞 {{ app.like_count }}</button>
                <button class="secondary" @click="viewApp(app)">浏览 {{ app.view_count }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { appStoreApi } from '@/api'

const levels = [
  { id: 'junior', label: '初中', subjects: ['物理', '化学', '生物', '地理'] },
  { id: 'senior', label: '高中', subjects: ['物理', '化学', '生物', '地理'] },
  { id: 'college', label: '大学', subjects: ['物理', '化学', '生物', '电学', '材料', '计算机'] }
]

const selectedLevel = ref(levels[0].id)
const selectedSubject = ref(levels[0].subjects[0])
const apps = ref([])
const loading = ref(false)
const query = ref('')

const form = ref({
  title: '',
  link: '',
  summary: ''
})

const currentLevel = computed(() => levels.find(l => l.id === selectedLevel.value) || levels[0])
const currentLevelLabel = computed(() => currentLevel.value.label)
const currentSubjects = computed(() => currentLevel.value.subjects)

const selectLevel = (id) => {
  selectedLevel.value = id
  selectedSubject.value = currentLevel.value.subjects[0]
  loadApps()
}

const selectSubject = (subject) => {
  selectedSubject.value = subject
  loadApps()
}

const loadApps = async () => {
  loading.value = true
  try {
    const params = {
      link_type: 'h5'
    }
    const level = currentLevelLabel.value
    const subject = selectedSubject.value
    const searchText = [query.value, level, subject, '实验'].filter(Boolean).join(' ')
    const tagText = ['虚拟实验', level, subject].join(',')
    if (searchText) params.search = searchText
    params.tags = tagText
    const res = await appStoreApi.list(params)
    apps.value = res.data.results || res.data
  } catch (err) {
    console.error('加载虚拟实验失败', err)
    apps.value = []
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
    link_type: 'h5',
    tag_names: ['虚拟实验', currentLevelLabel.value, selectedSubject.value]
  }
  try {
    await appStoreApi.submit(payload)
    form.value = { title: '', link: '', summary: '' }
    await loadApps()
    alert('提交成功，等待审核')
  } catch (err) {
    alert('提交失败')
  }
}

const openApp = (app) => window.open(app.link, '_blank')

const likeApp = async (app) => {
  try {
    const res = await appStoreApi.like(app.id)
    app.like_count = res.data.like_count
  } catch (err) {
    console.error('点赞失败', err)
  }
}

const viewApp = async (app) => {
  try {
    const res = await appStoreApi.view(app.id)
    app.view_count = res.data.view_count
    openApp(app)
  } catch (err) {
    openApp(app)
  }
}

const openStore = () => window.open('/store', '_blank')
const openWatch = () => window.open('/watch', '_blank')

onMounted(loadApps)
</script>

<style scoped>
.lab-container { padding: 28px; background: var(--bg); min-height: 100vh; overflow-y: auto; }
.lab-header { text-align: center; margin-bottom: 20px; }
.title { font-size: 26px; font-weight: 700; color: var(--text); }
.subtitle { color: var(--muted); margin-top: 6px; }
.header-actions { margin-top: 16px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
.header-actions input { width: 360px; padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; }
.header-actions button { padding: 10px 14px; border-radius: var(--radius-sm); border: none; background: var(--accent); color: #fff; cursor: pointer; }
.header-actions button.ghost { background: #fff; color: #374151; border: 1px solid #e5e7eb; }

.lab-body { display: flex; gap: 18px; }
.sidebar { width: 280px; }
.main { flex: 1; }
.section { background: var(--surface); border-radius: var(--radius-lg); padding: 16px; margin-bottom: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.section-title { font-weight: 600; margin-bottom: 10px; }

.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chips button { padding: 6px 12px; border-radius: 999px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.chips button.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.submit-form { display: grid; gap: 8px; }
.submit-form input { padding: 8px 10px; border-radius: 8px; border: 1px solid #e5e7eb; }
.submit-form button { padding: 10px; border-radius: 8px; border: none; background: #10b981; color: #fff; cursor: pointer; }
.hint { margin-top: 8px; color: #9ca3af; font-size: 12px; }

.app-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.app-card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; background: #fff; transition: transform 0.18s ease, box-shadow 0.18s ease; }
.app-card:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,0.08); }
.app-title { font-weight: 600; }
.app-summary { color: #6b7280; font-size: 12px; margin-top: 4px; }
.app-tags { margin-top: 6px; font-size: 12px; color: #4b5563; }
.app-tags span { margin-right: 6px; }
.app-actions { margin-top: 10px; display: flex; gap: 6px; }
.app-actions button { padding: 6px 8px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; font-size: 12px; }
.app-actions button.secondary { color: #374151; }
.empty { color: #9ca3af; font-size: 13px; }

@media (max-width: 1024px) {
  .lab-body { flex-direction: column; }
  .sidebar { width: 100%; }
  .app-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .header-actions input { width: 100%; }
  .app-grid { grid-template-columns: 1fr; }
}
</style>
