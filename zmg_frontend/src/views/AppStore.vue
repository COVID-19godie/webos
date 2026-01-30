<template>
  <div class="store-container">
    <div class="store-header">
      <div class="title">应用商店 · H5</div>
      <div class="subtitle">云端商店 + GitHub 热门项目，仅展示 H5 应用</div>
      <div class="tab-bar">
        <button :class="{ active: activeTab === 'cloud' }" @click="activeTab = 'cloud'">云端商店</button>
        <button :class="{ active: activeTab === 'github' }" @click="activeTab = 'github'">GitHub 热门</button>
      </div>
    </div>

    <div class="tab-content" v-if="activeTab === 'cloud'">
      <div class="panel">
        <div class="panel-title">上传 H5 应用到云端应用库</div>
        <div class="actions">
          <button class="primary" @click="zipInput?.click()">上传 ZIP</button>
          <button class="ghost" @click="folderInput?.click()">上传文件夹</button>
          <button class="ghost" @click="addH5Link">上传链接</button>
        </div>
        <input ref="zipInput" type="file" accept=".zip" style="display: none" @change="onZipSelected" />
        <input ref="folderInput" type="file" webkitdirectory mozdirectory style="display: none" @change="onFolderSelected" />
      </div>

      <div class="panel">
        <div class="panel-title">云端 H5 应用</div>
        <div v-if="cloudTags.length" class="tag-bar">
          <span
            v-for="tag in cloudTags"
            :key="tag"
            :class="{ active: cloudTagFilter.includes(tag) }"
            @click="toggleCloudTag(tag)"
          >
            #{{ tag }}
          </span>
        </div>
        <div v-if="cloudLoading" class="empty">加载中...</div>
        <div v-else-if="cloudApps.length === 0" class="empty">暂无应用</div>
        <div v-else class="app-grid">
          <div v-for="app in filteredCloudApps" :key="app.id" class="app-card">
            <div class="app-cover">
              <img v-if="app.cover" :src="app.cover" alt="" />
              <div v-else class="cover-placeholder">
                <i class="fa-brands fa-html5"></i>
              </div>
            </div>
            <div class="app-title">{{ app.title }}</div>
            <div class="app-summary">{{ app.summary || '暂无简介' }}</div>
            <div v-if="app.tags?.length" class="tag-list">
              <span v-for="t in app.tags" :key="t.id">#{{ t.name }}</span>
            </div>
            <div class="app-actions">
              <button @click="installCloudApp(app)">安装到云端应用库</button>
              <button class="secondary" @click="openLink(app.link)">查看</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="tab-content" v-else>
      <div class="panel">
        <div class="panel-title">GitHub 热门 H5</div>
        <div class="search-row">
          <input v-model="githubQuery" placeholder="搜索项目或 user:username" />
          <select v-model="githubSort">
            <option value="stars">热度</option>
            <option value="updated">更新</option>
            <option value="forks">Fork</option>
          </select>
          <button class="primary" @click="loadGithub">搜索</button>
        </div>
        <div v-if="githubTopics.length" class="tag-bar">
          <span
            v-for="topic in githubTopics"
            :key="topic"
            :class="{ active: githubTopicFilter.includes(topic) }"
            @click="toggleGithubTopic(topic)"
          >
            #{{ topic }}
          </span>
        </div>
        <div v-if="githubLoading" class="empty">加载中...</div>
        <div v-else-if="githubRepos.length === 0" class="empty">暂无结果</div>
        <div v-else class="app-grid">
          <div v-for="repo in filteredGithubRepos" :key="repo.full_name" class="app-card">
            <div class="app-cover">
              <img v-if="repo.owner_avatar" :src="repo.owner_avatar" alt="" />
              <div v-else class="cover-placeholder">
                <i class="fa-brands fa-github"></i>
              </div>
            </div>
            <div class="app-title">{{ repo.full_name }}</div>
            <div class="app-summary">{{ repo.description || '暂无简介' }}</div>
            <div v-if="repo.topics?.length" class="tag-list">
              <span v-for="topic in repo.topics" :key="topic">#{{ topic }}</span>
            </div>
            <div class="app-meta">⭐ {{ repo.stars }}</div>
            <div class="app-actions">
              <button @click="installGithub(repo)">安装到云端应用库</button>
              <button class="secondary" @click="openLink(repo.html_url)">查看</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="uploadState.isUploading" class="upload-overlay">
      <div class="upload-card">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadState.progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ uploadState.message }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import JSZip from 'jszip'
import { appStoreApi, desktopApi, githubApi } from '@/api'

const activeTab = ref('cloud')
const zipInput = ref(null)
const folderInput = ref(null)

const cloudApps = ref([])
const cloudLoading = ref(false)

const githubRepos = ref([])
const githubLoading = ref(false)
const githubQuery = ref('')
const githubSort = ref('stars')
const cloudTagFilter = ref([])
const githubTopicFilter = ref([])

const uploadState = ref({
  isUploading: false,
  progress: 0,
  message: ''
})

const loadCloudApps = async () => {
  cloudLoading.value = true
  try {
    const res = await appStoreApi.list({ link_type: 'h5' })
    cloudApps.value = res.data.results || res.data || []
  } catch (err) {
    console.error('加载云端应用失败', err)
  } finally {
    cloudLoading.value = false
  }
}

const loadGithub = async () => {
  githubLoading.value = true
  try {
    const queryParts = []
    if (githubQuery.value) queryParts.push(githubQuery.value)
    queryParts.push('topic:h5')
    const res = await githubApi.listRepos({
      q: queryParts.join(' '),
      sort: githubSort.value
    })
    githubRepos.value = res.data.items || []
  } catch (err) {
    console.error('加载 GitHub 失败', err)
  } finally {
    githubLoading.value = false
  }
}

const installZip = async (file, title) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', title || file.name.replace(/\.zip$/i, ''))
  formData.append('parent_id', 4)
  const response = await desktopApi.installH5App(formData)
  if (response.data.status !== 'success') {
    throw new Error(response.data.msg || '安装失败')
  }
}

const onZipSelected = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  uploadState.value = { isUploading: true, progress: 0, message: '正在上传...' }
  try {
    await installZip(file)
    uploadState.value = { isUploading: true, progress: 100, message: '安装成功' }
  } catch (err) {
    alert(`安装失败: ${desktopApi.handleError(err)}`)
  } finally {
    setTimeout(() => {
      uploadState.value = { isUploading: false, progress: 0, message: '' }
    }, 600)
    e.target.value = ''
  }
}

const onFolderSelected = async (e) => {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  uploadState.value = { isUploading: true, progress: 0, message: '正在打包...' }
  try {
    const zip = new JSZip()
    files.forEach((file) => {
      const path = file.webkitRelativePath || file.name
      zip.file(path, file)
    })
    const folderName = (files[0].webkitRelativePath || 'h5app').split('/')[0] || 'h5app'
    const blob = await zip.generateAsync({ type: 'blob' }, (meta) => {
      uploadState.value = { isUploading: true, progress: Math.min(99, Math.round(meta.percent)), message: '正在打包...' }
    })
    const zipFile = new File([blob], `${folderName}.zip`, { type: 'application/zip' })
    uploadState.value = { isUploading: true, progress: 99, message: '正在上传...' }
    await installZip(zipFile, folderName)
    uploadState.value = { isUploading: true, progress: 100, message: '安装成功' }
  } catch (err) {
    alert(`安装失败: ${desktopApi.handleError(err)}`)
  } finally {
    setTimeout(() => {
      uploadState.value = { isUploading: false, progress: 0, message: '' }
    }, 600)
    e.target.value = ''
  }
}

const addH5Link = async () => {
  const title = prompt('应用名称')
  if (!title) return
  const link = prompt('应用链接（H5）')
  if (!link) return
  try {
    await desktopApi.createLink({
      title,
      link,
      icon_class: 'fa-brands fa-html5',
      parent_id: 4
    })
    alert('已添加到云端应用库')
  } catch (err) {
    alert(`创建失败: ${desktopApi.handleError(err)}`)
  }
}

const installCloudApp = async (app) => {
  if (!app.link) return
  try {
    await desktopApi.createLink({
      title: app.title,
      link: app.link,
      icon_class: 'fa-brands fa-html5',
      parent_id: 4
    })
    alert('已安装到云端应用库')
  } catch (err) {
    alert(`安装失败: ${desktopApi.handleError(err)}`)
  }
}

const installGithub = async (repo) => {
  const link = repo.homepage || repo.html_url
  if (!link) return
  try {
    await desktopApi.createLink({
      title: repo.full_name,
      link,
      icon_class: 'fa-brands fa-github',
      parent_id: 4
    })
    alert('已安装到云端应用库')
  } catch (err) {
    alert(`安装失败: ${desktopApi.handleError(err)}`)
  }
}

const openLink = (url) => {
  if (url) window.open(url, '_blank')
}

const cloudTags = computed(() => {
  const set = new Set()
  cloudApps.value.forEach(app => {
    (app.tags || []).forEach(tag => set.add(tag.name))
  })
  return Array.from(set)
})

const githubTopics = computed(() => {
  const set = new Set()
  githubRepos.value.forEach(repo => {
    (repo.topics || []).forEach(topic => set.add(topic))
  })
  return Array.from(set)
})

const filteredCloudApps = computed(() => {
  if (!cloudTagFilter.value.length) return cloudApps.value
  return cloudApps.value.filter(app => {
    const names = (app.tags || []).map(tag => tag.name)
    return cloudTagFilter.value.every(tag => names.includes(tag))
  })
})

const filteredGithubRepos = computed(() => {
  if (!githubTopicFilter.value.length) return githubRepos.value
  return githubRepos.value.filter(repo => {
    const topics = repo.topics || []
    return githubTopicFilter.value.every(topic => topics.includes(topic))
  })
})

const toggleCloudTag = (tag) => {
  const idx = cloudTagFilter.value.indexOf(tag)
  if (idx >= 0) cloudTagFilter.value.splice(idx, 1)
  else cloudTagFilter.value.push(tag)
}

const toggleGithubTopic = (topic) => {
  const idx = githubTopicFilter.value.indexOf(topic)
  if (idx >= 0) githubTopicFilter.value.splice(idx, 1)
  else githubTopicFilter.value.push(topic)
}

onMounted(() => {
  loadCloudApps()
  loadGithub()
})
</script>

<style scoped>
.store-container { padding: 30px; background: var(--bg); min-height: 100vh; }
.store-header { text-align: center; margin-bottom: 20px; }
.title { font-size: 28px; font-weight: 700; color: var(--text); }
.subtitle { color: var(--muted); margin-top: 6px; }
.tab-bar { margin-top: 14px; display: flex; justify-content: center; gap: 10px; }
.tab-bar button { padding: 8px 16px; border-radius: 999px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }
.tab-bar button.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.tab-content { display: grid; gap: 16px; }
.panel { background: var(--surface); border-radius: var(--radius-lg); padding: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.06); }
.panel-title { font-weight: 600; margin-bottom: 12px; }
.actions { display: flex; gap: 12px; flex-wrap: wrap; }
.actions .primary { padding: 10px 16px; border-radius: var(--radius-sm); border: none; background: var(--accent); color: #fff; cursor: pointer; }
.actions .ghost { padding: 10px 16px; border-radius: var(--radius-sm); border: 1px solid #e5e7eb; background: #fff; cursor: pointer; }

.search-row { display: flex; gap: 10px; flex-wrap: wrap; }
.search-row input { flex: 1; min-width: 220px; padding: 8px 10px; border-radius: 8px; border: 1px solid #e5e7eb; }
.search-row select { padding: 8px 10px; border-radius: 8px; border: 1px solid #e5e7eb; }
.search-row button { padding: 8px 14px; border-radius: 8px; border: none; background: var(--accent); color: #fff; cursor: pointer; }

.app-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.app-card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; background: #fff; }
.app-title { font-weight: 600; }
.app-summary { color: #6b7280; font-size: 12px; margin-top: 4px; }
.app-meta { color: #9ca3af; font-size: 12px; margin-top: 6px; }
.app-actions { margin-top: 10px; display: flex; gap: 8px; }
.app-actions button { padding: 6px 10px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer; font-size: 12px; }
.app-actions button.secondary { color: #374151; }
.empty { color: #9ca3af; font-size: 13px; }

.tag-bar { margin: 10px 0 6px; display: flex; flex-wrap: wrap; gap: 8px; }
.tag-bar span { padding: 4px 10px; border-radius: 999px; background: #eef2ff; cursor: pointer; font-size: 12px; }
.tag-bar span.active { background: var(--accent); color: #fff; }

.tag-list { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; color: #4b5563; }

.app-cover {
  width: 100%;
  height: 120px;
  border-radius: 10px;
  overflow: hidden;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.app-cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-placeholder { color: #9ca3af; font-size: 28px; }

.upload-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.upload-card {
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  width: 320px;
  text-align: center;
}
.progress-bar { width: 100%; height: 8px; background: #f0f0f0; border-radius: 6px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #4dabf7, #339af0); transition: width 0.3s ease; }
.progress-text { margin-top: 12px; font-size: 13px; color: #333; }

@media (max-width: 1024px) {
  .app-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .app-grid { grid-template-columns: 1fr; }
}
</style>
