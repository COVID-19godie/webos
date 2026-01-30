<template>
  <div class="explorer-layout">
    <div class="sidebar">
      <div v-for="section in navSections" :key="section.title" class="nav-section">
        <div class="section-title">{{ section.title }}</div>
        <div
          v-for="item in section.items"
          :key="item.id"
          class="nav-item"
          :class="{ active: String(currentLibraryId) === String(item.id) }"
          @click="loadLibrary(item.id)"
        >
          <i :class="item.icon" :style="{ color: item.color || '#666' }"></i>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </div>
    
    <div class="main-view">
      <div class="toolbar">
        <div class="path-label">当前：{{ currentLabel }}</div>
        <div class="toolbar-actions">
          <button @click="loadLibrary(currentLibraryId)" class="ghost-btn">
            <i class="fa-solid fa-rotate-right"></i> 刷新
          </button>
          <button @click="createFolder" class="ghost-btn">
            <i class="fa-solid fa-folder-plus"></i> 新建文件夹
          </button>
          <button v-if="store.editMode" @click="organizeIcons" class="ghost-btn">
            <i class="fa-solid fa-braille"></i> 整理图标
          </button>
          <button v-if="store.editMode" @click="exitEditMode" class="ghost-btn">
            <i class="fa-solid fa-check"></i> 完成
          </button>
        </div>
      </div>
      <div v-if="loading" class="status-box"><i class="fa-solid fa-spinner fa-spin"></i></div>
      <div v-else-if="icons.length === 0" class="status-box">暂无内容</div>
      <div v-else class="icon-grid">
        <DesktopIcon class="main-view-icon" 
                    v-for="icon in icons" 
                    :key="icon.id" 
                    :icon="icon" 
                    :editMode="store.editMode"
                    @open="handleOpen"
                    @delete="deleteIcon"
                    @longpress="enterEditMode" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { desktopApi } from '@/api'
import { useWindowStore } from '@/stores/windowStore'
import { useDesktopStore } from '@/stores/desktopStore'
import DesktopIcon from './DesktopIcon.vue'

const props = defineProps(['folderId'])
const winStore = useWindowStore()
const store = useDesktopStore()
const icons = ref([])
const loading = ref(false)
const currentLibraryId = ref(props.folderId || 'root') // 记录当前所在的库 ID
const currentLabel = ref('桌面文件')

const navSections = [
  {
    title: '我上传的',
    items: [
      { id: 1, label: '我上传的图像', icon: 'fa-solid fa-cloud', color: '#4dabf7' },
      { id: 2, label: '我上传的影音', icon: 'fa-solid fa-cloud', color: '#4dabf7' },
      { id: 3, label: '我上传的档案', icon: 'fa-solid fa-cloud', color: '#4dabf7' },
      { id: 4, label: '我上传的应用', icon: 'fa-solid fa-gamepad', color: '#4dabf7' }
    ]
  },
  {
    title: '本地存储',
    items: [
      { id: 'root', label: '桌面文件', icon: 'fa-solid fa-desktop', color: '#6c757d' }
    ]
  }
]

const loadLibrary = async (id) => {
  loading.value = true
  currentLibraryId.value = id
  const item = navSections.flatMap(s => s.items).find(i => String(i.id) === String(id))
  currentLabel.value = item ? item.label : '桌面文件'
  try { 
    const res = await desktopApi.getList(id)
    icons.value = res.data.results || res.data 
  } catch(e) { 
    icons.value = []
    console.error(e)
  } finally { 
    loading.value = false 
  }
}

onMounted(() => loadLibrary(props.folderId))
watch(() => props.folderId, (newId) => loadLibrary(newId))

const handleOpen = (icon) => {
  if (store.editMode) return
  winStore.openWindow(icon)
}

const enterEditMode = () => store.setEditMode(true)
const exitEditMode = () => store.setEditMode(false)

const deleteIcon = async (icon) => {
  if (!icon?.id) return
  try {
    await desktopApi.delete(icon.id)
    loadLibrary(currentLibraryId.value)
  } catch (err) {
    alert(`删除失败: ${desktopApi.handleError(err)}`)
  }
}

const organizeIcons = () => {
  icons.value = [...icons.value].sort((a, b) => (a.title || '').localeCompare(b.title || ''))
}

const createFolder = async () => {
  const name = prompt('文件夹名称')
  if (!name) return
  try {
    await desktopApi.createFolder({ name, parent_id: currentLibraryId.value })
    loadLibrary(currentLibraryId.value)
  } catch (err) {
    alert(`创建失败: ${desktopApi.handleError(err)}`)
  }
}
</script>

<style scoped>
.explorer-layout { display: flex; height: 100%; background: #fff; color: #333; }
.sidebar { 
  width: 200px; 
  background: rgba(245, 246, 250, 0.9); 
  border-right: 1px solid rgba(0,0,0,0.06); 
  padding: 18px 12px; 
  flex-shrink: 0;
  backdrop-filter: blur(16px);
}
.section-title { font-size: 11px; color: #8f96a3; margin: 14px 0 6px 12px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
.nav-item { 
  padding: 8px 12px; 
  border-radius: 10px; 
  cursor: pointer; 
  font-size: 13px; 
  display: flex; 
  align-items: center; 
  gap: 10px;
  color: #2f3640;
}
.nav-item:hover { background: rgba(0,0,0,0.06); }
.nav-item.active { background: rgba(52, 152, 219, 0.12); color: #1f6feb; }
.main-view { flex: 1; overflow-y: auto; position: relative; padding: 10px; }
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.path-label { font-size: 13px; color: #4b5563; }
.toolbar-actions { display: flex; gap: 8px; }
.ghost-btn {
  border: 1px solid rgba(0,0,0,0.08);
  background: transparent;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  color: #374151;
}
.ghost-btn:hover { background: rgba(0,0,0,0.04); }

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 15px;
  justify-items: center;
  align-items: start;
}
.status-box { display: flex; align-items: center; justify-content: center; height: 100%; color: #aaa; }

/* 🟢 让访达里的图标文字变深色，否则在白底上看不清 */
:deep(.main-view-icon .icon-title) {
  color: #333 !important;
  text-shadow: none !important;
}
:deep(.main-view-icon .icon-font i) {
  text-shadow: none !important;
}
@media (max-width: 768px) {
  .explorer-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    padding: 10px;
    display: flex;
    gap: 10px;
    overflow-x: auto;
  }

  .nav-section {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .section-title {
    display: none;
  }

  .nav-item {
    white-space: nowrap;
    padding: 6px 10px;
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .icon-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 10px;
  }
}
</style>