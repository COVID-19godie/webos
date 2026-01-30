<template>
  <div class="desktop-container" @dragover.prevent @drop.stop.prevent="onDesktopDrop">
    <div class="wallpaper"></div>
    
    <!-- 灵动岛 -->
    <DynamicIsland 
      ref="dynamicIsland"
      @open-launcher="launcherVisible = true"
      @open-finder="openFinder"
    />
    
    <div class="desktop-icons">
      <DesktopIcon
        v-for="icon in desktopIcons"
        :key="icon.id"
        :icon="icon"
        :editMode="store.editMode"
        @open="handleOpen"
        @delete="deleteIcon"
        @longpress="enterEditMode"
      />
    </div>
    
    <Window v-for="win in winStore.windows" :key="win.id" :win="win" />
    
    <Taskbar @open-launcher="launcherVisible = true" />
    <Launcher :visible="launcherVisible" @update:visible="launcherVisible = $event" />
    
    <input type="file" ref="fileInput" style="display: none" @change="onFileSelected" />
    <input type="file" ref="h5Input" accept=".zip" style="display: none" @change="onH5Selected" />

    <div v-if="settingsVisible" class="settings-overlay" @click.self="settingsVisible = false">
      <div class="settings-panel">
        <div class="settings-title">同步设置</div>
        <div class="settings-row">
          <label>当前租户</label>
          <select v-model="currentTenantId" @change="onTenantChange">
            <option v-for="t in tenantOptions" :key="t.id" :value="String(t.id)">{{ t.name }}</option>
          </select>
        </div>
        <div class="settings-row">
          <label>允许上传到云端</label>
          <input type="checkbox" v-model="syncSettings.uploadEnabled" />
        </div>
        <div class="settings-row">
          <label>冲突策略</label>
          <select v-model="syncSettings.conflictStrategy">
            <option value="server_wins">以云端为准</option>
            <option value="client_wins">以本地为准</option>
          </select>
        </div>
        <div class="settings-row hint">上次同步：{{ syncSettings.lastSyncAt || '未同步' }}</div>
        <div class="settings-actions">
          <button @click="runSync">立即同步</button>
          <button class="secondary" @click="saveSettings">保存设置</button>
        </div>
      </div>
    </div>
    
    <div v-if="loadingState.isUploading" class="upload-progress-overlay">
      <div class="upload-progress-container">
        <div class="upload-progress-bar">
          <div class="upload-progress-fill" :style="{ width: loadingState.uploadProgress + '%' }"></div>
        </div>
        <div class="upload-progress-text">{{ loadingState.uploadMessage }}</div>
      </div>
    </div>

    <!-- 备案号 - 页面最底部 -->
    <div class="beian-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" class="beian-link">豫ICP备2026001662号</a>
      <span class="beian-divider">|</span>
      <a href="http://www.beian.gov.cn/portal/registerSystemInfo" target="_blank" class="beian-link">
        <img src="https://beian.mps.gov.cn/img/logo01.dd7ff50e.png" alt="公网安备" class="beian-icon" />
        豫公网安备41130202000548号
      </a>
    </div>

    <div v-if="store.editMode" class="edit-toolbar">
      <button @click="organizeDesktopIcons">整理图标</button>
      <button class="secondary" @click="exitEditMode">完成</button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import JSZip from 'jszip' // ⚠️ 请确保已执行 npm install jszip
import { useDesktopStore } from '@/stores/desktopStore'
import { useWindowStore } from '@/stores/windowStore'
import { desktopApi, tenantApi, syncApi } from '@/api'
import DesktopIcon from '@/components/os/DesktopIcon.vue'
import Window from '@/components/os/Window.vue'
import Taskbar from '@/components/os/Taskbar.vue'
import Launcher from '@/components/os/Launcher.vue'
import DynamicIsland from '@/components/os/DynamicIsland.vue'
import { syncService } from '@/services/sync/syncService'

const store = useDesktopStore()
const winStore = useWindowStore()
const fileInput = ref(null)
const h5Input = ref(null)
const launcherVisible = ref(false)
const dynamicIsland = ref(null)

// 打开访达
const openFinder = () => {
  winStore.openWindow({
    id: 'finder_root',
    title: '访达',
    type: 'category',
    data: { id: 'root' },
    icon: 'fa-solid fa-face-smile'
  })
  // 触发灵动岛脉冲动画
  dynamicIsland.value?.triggerPulse()
}
const settingsVisible = ref(false)
const isElectron = computed(() => {
  return navigator.userAgent.toLowerCase().indexOf(' electron/') > -1
})
const tenantOptions = ref([])
const currentTenantId = ref(localStorage.getItem('current_tenant_id') || '')
const syncSettings = reactive({
  uploadEnabled: false,
  conflictStrategy: 'server_wins',
  lastSyncAt: null
})


// 上传状态
const loadingState = reactive({ 
  isUploading: false, 
  uploadProgress: 0, 
  uploadMessage: '' 
})

// 过滤桌面图标：只显示根目录下的分类和资源
const desktopIcons = computed(() => store.icons.filter(icon => {
  const pid = icon.parent_folder || icon.parent_folder_id
  const isAtRoot = pid === 'root' || !pid || pid === 0
  return isAtRoot && (icon.type === 'category' || icon.type === 'resource')
}))

// 初始化加载
onMounted(() => store.fetchIcons('root'))

const handleOpen = (icon) => {
  if (store.editMode) return
  winStore.openWindow(icon)
  // 触发灵动岛脉冲动画
  dynamicIsland.value?.triggerPulse()
}

const enterEditMode = () => store.setEditMode(true)
const exitEditMode = () => store.setEditMode(false)

const deleteIcon = async (icon) => {
  if (!icon?.id) return
  try {
    await desktopApi.delete(icon.id)
    store.fetchIcons('root')
  } catch (err) {
    alert(`删除失败: ${desktopApi.handleError(err)}`)
  }
}

const organizeDesktopIcons = () => {
  const icons = [...desktopIcons.value].sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  const startX = 20
  const startY = 80
  const colWidth = 90
  const rowHeight = 100
  const maxCols = Math.max(1, Math.floor((window.innerWidth - 40) / colWidth))
  icons.forEach((icon, idx) => {
    const col = idx % maxCols
    const row = Math.floor(idx / maxCols)
    const x = startX + col * colWidth
    const y = startY + row * rowHeight
    store.updatePosition(icon.id, x, y)
  })
}

const readAllEntries = (reader) => new Promise((resolve, reject) => {
  const entries = []
  const readBatch = () => {
    reader.readEntries(batch => {
      if (!batch.length) return resolve(entries)
      entries.push(...batch)
      readBatch()
    }, reject)
  }
  readBatch()
})

const addDirectoryToZip = async (dirEntry, zip, basePath = '') => {
  const reader = dirEntry.createReader()
  const entries = await readAllEntries(reader)
  for (const entry of entries) {
    if (entry.isFile) {
      const file = await new Promise(resolve => entry.file(resolve))
      const relativePath = `${basePath}${entry.name}`
      zip.file(relativePath, file)
    } else if (entry.isDirectory) {
      await addDirectoryToZip(entry, zip, `${basePath}${entry.name}/`)
    }
  }
}

// 🟢 核心交互：全能拖拽处理
// 找到 onDesktopDrop 函数，将其内部逻辑替换为：

const onDesktopDrop = async (e) => {
  if (!isElectron.value) {
    alert('Web端仅支持链接内容，文件管理请使用桌面App。')
    return
  }
  if (loadingState.isUploading) return; 
  
  const items = e.dataTransfer.items
  if (!items) return;
  
  loadingState.isUploading = true
  loadingState.uploadProgress = 0
  
  try {
    // 先把 items 转成数组，因为 dataTransfer 在 await 后会失效
    const entries = []
    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry()
      if (entry) entries.push(entry)
    }

    const total = entries.length
    for (let i = 0; i < total; i++) {
      const entry = entries[i]
      
      loadingState.uploadMessage = `处理文件 ${i+1}/${total}: ${entry.name}`
      
      if (entry.isDirectory) {
        loadingState.uploadMessage = `检测文件夹: ${entry.name}`
        const zip = new JSZip()
        await addDirectoryToZip(entry, zip)
        loadingState.uploadMessage = `正在打包应用: ${entry.name}`
        const blob = await zip.generateAsync({ type: 'blob' })
        const zipFile = new File([blob], `${entry.name}.zip`, { type: 'application/zip' })
        await handleArchiveInstall(zipFile, e.clientX, e.clientY)
        loadingState.uploadProgress = ((i + 1) / total) * 100
        continue
      }
      if (entry.isFile) {
        // 获取 File 对象
        const file = await new Promise(resolve => entry.file(resolve))
        const filename = file.name.toLowerCase()

        // 🟢 核心判断：如果是 Zip，直接尝试安装为 H5 应用
        if (filename.endsWith('.zip')) {
          loadingState.uploadMessage = `正在安装应用: ${file.name}`
          
          // 调用安装函数
          await handleArchiveInstall(file, e.clientX, e.clientY)
          
          // ⚠️ 重要：安装完后直接进入下一次循环，不要再执行下面的普通上传！
          loadingState.uploadProgress = ((i + 1) / total) * 100
          continue 
        } 
        
        // 普通文件上传
        try {
          loadingState.uploadMessage = `上传文件: ${file.name}`
          await desktopApi.upload(file, e.clientX, e.clientY)
        } catch (error) {
          console.error('上传失败', error)
        }
      }
      // 更新进度
      loadingState.uploadProgress = ((i + 1) / total) * 100
    }
    
    loadingState.uploadMessage = '处理完成'
    store.fetchIcons('root')
    
    setTimeout(() => {
      loadingState.isUploading = false
      loadingState.uploadProgress = 0
      loadingState.uploadMessage = ''
    }, 1000)
    
  } catch (error) {
    loadingState.isUploading = false
    alert(`操作失败: ${desktopApi.handleError(error)}`)
  }
}

// 🟢 改进的压缩包安装处理
const handleArchiveInstall = async (file, x, y) => {
  try {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      throw new Error('仅支持上传 ZIP 格式的 H5 应用包')
    }
    // 1. 安装流程
    const formData = new FormData()
    const appName = file.name.replace(/\.zip$/i, '')
    
    formData.append('file', file)
    formData.append('title', appName)
    // 🟢 修正：安装到 ID 为 4 的文件夹（应用/其他），确保在访达中可见
    formData.append('parent_id', 4) 
    formData.append('x', x)
    formData.append('y', y)
    
    const response = await desktopApi.installH5App(formData)
    
    if (response.data.status === 'success') {
      console.log('H5应用安装成功')
    } else {
      throw new Error(response.data.msg)
    }
  } catch (err) { 
    throw err // 向上抛出给调用者处理
  }
}


const onFileSelected = async (e) => {
  if (!isElectron.value) {
    alert('Web端仅支持链接内容，文件管理请使用桌面App。')
    return
  }
  const file = e.target.files[0]
  if (file) { 
    await desktopApi.upload(file)
    store.fetchIcons('root')
  }
}

const onH5Selected = async (e) => {
  if (!isElectron.value) {
    alert('Web端仅支持链接内容，文件管理请使用桌面App。')
    return
  }
  const file = e.target.files[0]
  if (file) {
    loadingState.isUploading = true
    loadingState.uploadMessage = '正在安装...'
    loadingState.uploadProgress = 0
    
    try {
      await handleArchiveInstall(file, 100, 100)
      loadingState.uploadMessage = '安装成功！'
      loadingState.uploadProgress = 100
      setTimeout(() => {
        loadingState.isUploading = false
        loadingState.uploadProgress = 0
        loadingState.uploadMessage = ''
        alert(`H5应用安装成功！\n请前往"访达" -> "应用库"查看。`)
      }, 500)
    } catch (error) {
      loadingState.isUploading = false
      alert(`安装失败: ${desktopApi.handleError(error)}`)
    }
  }
}

const loadTenants = async () => {
  try {
    const res = await tenantApi.list()
    tenantOptions.value = res.data || []
    if (!currentTenantId.value && tenantOptions.value.length) {
      currentTenantId.value = String(tenantOptions.value[0].id)
      localStorage.setItem('current_tenant_id', currentTenantId.value)
    }
  } catch (err) {
    console.error('加载租户失败', err)
  }
}

const openSyncSettings = async () => {
  settingsVisible.value = true
  await loadTenants()
  try {
    const res = await syncApi.getSettings()
    const data = res.data?.data
    if (data) {
      syncSettings.uploadEnabled = data.upload_enabled
      syncSettings.conflictStrategy = data.conflict_strategy
      syncSettings.lastSyncAt = data.last_sync_at
    }
  } catch (err) {
    console.warn('读取云端同步设置失败，使用本地设置')
    const local = await syncService.loadSettings()
    syncSettings.uploadEnabled = local.uploadEnabled
    syncSettings.conflictStrategy = local.conflictStrategy
    syncSettings.lastSyncAt = local.lastSyncAt
  }
}

const saveSettings = async () => {
  const payload = {
    upload_enabled: syncSettings.uploadEnabled,
    conflict_strategy: syncSettings.conflictStrategy
  }
  try {
    await syncApi.updateSettings(payload)
  } catch (err) {
    console.warn('云端设置保存失败，已保存本地设置')
  }
  await syncService.saveSettings({
    uploadEnabled: syncSettings.uploadEnabled,
    conflictStrategy: syncSettings.conflictStrategy,
    lastSyncAt: syncSettings.lastSyncAt
  })
  settingsVisible.value = false
}

const runSync = async () => {
  try {
    const updated = await syncService.syncNow()
    syncSettings.lastSyncAt = updated.lastSyncAt
    store.fetchIcons('root')
  } catch (err) {
    alert(`同步失败: ${desktopApi.handleError(err)}`)
  }
}

const onTenantChange = () => {
  if (currentTenantId.value) {
    localStorage.setItem('current_tenant_id', currentTenantId.value)
    store.fetchIcons('root')
  }
}
</script>

<style scoped>
.desktop-container { position: fixed; top: 0; left: 0; right: 0; bottom: 0; overflow: hidden; z-index: 1; }
.wallpaper { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background-image: url('https://bing.biturl.top/?resolution=1920&format=image&index=0&mkt=zh-CN'); background-size: cover; }
.desktop-icons {
  position: absolute;
  inset: 0;
}

.upload-progress-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
.upload-progress-container {
  background: white; padding: 30px; border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); min-width: 300px; text-align: center;
}
.upload-progress-bar {
  width: 100%; height: 8px; background: #f0f0f0;
  border-radius: 4px; overflow: hidden; margin-bottom: 15px;
}
.upload-progress-fill {
  height: 100%; background: linear-gradient(90deg, #4dabf7, #339af0);
  border-radius: 4px; transition: width 0.3s ease;
}
.upload-progress-text { font-size: 14px; color: #333; font-weight: 500; }

.settings-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 9998;
}
.settings-panel {
  width: 360px; background: #fff; border-radius: 16px; padding: 20px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3);
}
.settings-title { font-size: 18px; font-weight: 600; margin-bottom: 12px; }
.settings-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 14px; }
.settings-row select { padding: 6px 8px; border-radius: 8px; border: 1px solid #ddd; }
.settings-row input[type="checkbox"] { transform: scale(1.1); }
.settings-row.hint { color: #666; font-size: 12px; }
.settings-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px; }
.settings-actions button {
  padding: 8px 12px; border-radius: 8px; border: none; background: #339af0; color: #fff; cursor: pointer;
}
.settings-actions button.secondary { background: #e9ecef; color: #333; }

/* 备案号 - 页面最底部 */
.beian-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 100;
}

.beian-link {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}

.beian-link:hover {
  color: rgba(255, 255, 255, 1);
}

.beian-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
}

.beian-divider {
  color: rgba(255, 255, 255, 0.3);
  font-size: 11px;
}

.edit-toolbar {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 10001;
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.5);
  padding: 8px 10px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.edit-toolbar button {
  padding: 6px 10px;
  border-radius: 8px;
  border: none;
  background: #339af0;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
}

.edit-toolbar button.secondary {
  background: #e9ecef;
  color: #333;
}

@media (max-width: 768px) {
  .desktop-icons {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(78px, 1fr));
    gap: 8px;
    align-content: start;
    padding: 70px 12px 120px;
    overflow-y: auto;
  }

  .settings-panel {
    width: calc(100% - 32px);
  }

  .settings-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .settings-actions {
    width: 100%;
    justify-content: space-between;
  }

  .upload-progress-container {
    min-width: 0;
    width: calc(100% - 40px);
  }

  .beian-footer {
    display: none;
  }
}
</style>