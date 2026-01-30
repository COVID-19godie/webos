<template>
  <div 
    v-show="!win.isMinimized"
    ref="windowRef"
    class="window-container"
    :class="{ 'maximized': win.isMaximized, 'active': winStore.activeId === win.id }"
    :style="windowStyle"
    @mousedown="activate"
  >
    <div class="window-header" @dblclick="toggleMaximize" @mousedown="startDrag">
      <div class="window-title">
        <div class="window-nav">
          <button class="nav-btn" @click.stop="goBack" title="返回">
            <i class="fa-solid fa-arrow-left"></i>
          </button>
          <button class="nav-btn" @click.stop="goHome" title="主页">
            <i class="fa-solid fa-house"></i>
          </button>
        </div>
        <i :class="win.icon" style="margin-right:8px;"></i>
        {{ displayTitle }}
      </div>
      <div class="window-controls">
        <button class="btn-min" @click.stop="minimize">-</button>
        <button class="btn-max" @click.stop="toggleMaximize">□</button>
        <button class="btn-close" @click.stop="close">×</button>
      </div>
    </div>

    <div class="window-body">
      
      <div v-if="isLoading" class="global-loading">
        <i class="fa-solid fa-spinner fa-spin"></i>
        <span style="margin-top: 10px;">正在加载资源...</span>
      </div>

      <FolderView 
        v-if="win.type === 'category'" 
        :folderId="win.data.id" 
      />

      <div v-else-if="checkType(win) === 'image'" class="preview-box">
        <img 
          :src="win.data.file || win.data.cover" 
          @load="finishLoading" 
          @error="finishLoading" 
        />
      </div>

      <div v-else-if="checkType(win) === 'video'" class="preview-box">
        <video 
          :src="win.data.file" 
          controls 
          autoplay 
          @loadeddata="finishLoading" 
          @error="finishLoading"
        ></video>
      </div>

      <div 
        v-else-if="checkType(win) === 'word'" 
        class="office-preview doc-content" 
        v-html="wordHtml"
      ></div>

      <div 
        v-else-if="checkType(win) === 'excel'" 
        class="office-preview" 
        v-html="excelHtml"
      ></div>

      <div 
        v-else-if="checkType(win) === 'pdf'" 
        class="pdf-scroll-container"
      >
        <VuePdfEmbed 
          :source="win.data.file" 
          class="pdf-content" 
          @loaded="finishLoading"
          @loading-failed="finishLoading"
        />
      </div>

      <div v-else-if="checkType(win) === 'app' || checkType(win) === 'html'" class="empty-state">
        <i class="fa-solid fa-arrow-up-right-from-square"></i>
        <p>该应用已禁用内嵌预览，请在新窗口打开</p>
        <button class="download-btn" @click="openExternal">打开应用</button>
      </div>

      <div v-else class="empty-state">
        <i class="fa-solid fa-download"></i>
        <p>此文件不支持预览</p>
        <a v-if="win.data.file" :href="win.data.file" download class="download-btn">下载文件</a>
      </div>
    </div>
    
    <div class="resize-handle" @mousedown="startResize"></div>
  </div>
</template>

<script setup>
import { computed, ref, onUnmounted, defineAsyncComponent, onMounted } from 'vue'
import { useWindowStore } from '@/stores/windowStore'
import VuePdfEmbed from 'vue-pdf-embed'

const props = defineProps(['win'])
const winStore = useWindowStore()
const FolderView = defineAsyncComponent(() => import('./FolderView.vue'))

// 🟢 状态控制
const isLoading = ref(true)
const wordHtml = ref('')
const excelHtml = ref('')

// === 初始化 Loading 状态 ===
if (props.win.type === 'category') {
  isLoading.value = false
} else {
  // 如果是无法预览的类型，直接取消 loading
  const type = checkType(props.win)
  if (!['image', 'video', 'word', 'excel', 'pdf'].includes(type)) {
    isLoading.value = false
  }
}

const finishLoading = () => { isLoading.value = false }

// === 类型辅助函数 ===
function checkType(win) {
  if (win.type === 'category') return 'category'
  if (win.data.kind === 'link') return 'app'
  const url = win.data.file || ''
  const ext = url.split('.').pop().toLowerCase()
  
  if (['jpg','jpeg','png','gif','webp','bmp'].includes(ext)) return 'image'
  if (['mp4','webm','ogg','mov'].includes(ext)) return 'video'
  if (['docx'].includes(ext)) return 'word'
  if (['xlsx','xls','csv'].includes(ext)) return 'excel'
  if (['pdf'].includes(ext)) return 'pdf'
  if (['html','htm'].includes(ext)) return 'html'
  return 'other'
}

const displayTitle = computed(() => {
  const t = props.win.title || '未命名'
  if (props.win.type === 'category') return t
  return t.replace(/\.[^/.]+$/, "")
})

const openExternal = () => {
  const url = props.win.data?.link || props.win.data?.file
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer,width=1200,height=800')
}

// === 加载 Office 文件 ===
const loadOffice = async () => {
  const type = checkType(props.win)
  if (type !== 'word' && type !== 'excel') return

  const url = props.win.data.file
  if (!url) { finishLoading(); return }

  try {
    const resp = await fetch(url)
    const arrayBuffer = await resp.arrayBuffer()

    if (type === 'word') {
      if (window.mammoth) {
        const result = await window.mammoth.convertToHtml({ arrayBuffer })
        wordHtml.value = result.value
      } else {
        wordHtml.value = '<div class="error">渲染引擎未加载，请检查网络或libs目录</div>'
      }
    } else if (type === 'excel') {
      if (window.XLSX) {
        const wb = window.XLSX.read(arrayBuffer, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        excelHtml.value = window.XLSX.utils.sheet_to_html(ws)
      } else {
        excelHtml.value = '<div class="error">渲染引擎未加载，请检查网络或libs目录</div>'
      }
    }
  } catch (e) {
    console.error(e)
    const msg = `<div class="error">加载失败: ${e.message}</div>`
    if (type==='word') wordHtml.value = msg
    if (type==='excel') excelHtml.value = msg
  } finally {
    finishLoading()
  }
}

// === 生命周期 ===
onMounted(() => {
  const type = checkType(props.win)
  if (['word', 'excel'].includes(type)) {
    // 延迟加载，优先渲染窗口框架
    setTimeout(loadOffice, 50) 
  }
})

// === 窗口基础操作 ===
const windowRef = ref(null)
const activate = () => winStore.activateWindow(props.win.id)
const minimize = () => winStore.minimizeWindow(props.win.id)
const close = () => winStore.closeWindow(props.win.id)
const toggleMaximize = () => winStore.toggleMaximize(props.win.id)
const goBack = () => winStore.closeWindow(props.win.id)
const goHome = () => winStore.minimizeAll()

const windowStyle = computed(() => {
  if (props.win.isMaximized) return {}
  return {
    left: props.win.x + 'px', top: props.win.y + 'px',
    width: props.win.w + 'px', height: props.win.h + 'px',
    zIndex: props.win.zIndex
  }
})

// === 拖拽逻辑 ===
let isDragging = false
let dragOffset = { x: 0, y: 0 }

const startDrag = (e) => {
  if (props.win.isMaximized) return
  isDragging = true
  dragOffset.x = e.clientX - props.win.x
  dragOffset.y = e.clientY - props.win.y
  activate()
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', stopDrag)
  // 拖拽时屏蔽 iframe/webview 事件
  document.querySelectorAll('iframe, webview').forEach(f => f.style.pointerEvents = 'none')
}

const onDragMove = (e) => {
  if (!isDragging) return
  winStore.updateWindow(props.win.id, { 
    x: e.clientX - dragOffset.x, 
    y: e.clientY - dragOffset.y 
  })
}

const stopDrag = () => {
  isDragging = false
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', stopDrag)
  document.querySelectorAll('iframe, webview').forEach(f => f.style.pointerEvents = 'auto')
}

// === 缩放逻辑 ===
let isResizing = false
let initialSize = { w: 0, h: 0, x: 0, y: 0 }

const startResize = (e) => {
  e.preventDefault()
  isResizing = true
  initialSize = { w: props.win.w, h: props.win.h, x: e.clientX, y: e.clientY }
  activate()
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', stopResize)
  document.querySelectorAll('iframe, webview').forEach(f => f.style.pointerEvents = 'none')
}

const onResizeMove = (e) => {
  if (!isResizing) return
  const newW = Math.max(300, initialSize.w + (e.clientX - initialSize.x))
  const newH = Math.max(200, initialSize.h + (e.clientY - initialSize.y))
  winStore.updateWindow(props.win.id, { w: newW, h: newH })
}

const stopResize = () => {
  isResizing = false
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
  document.querySelectorAll('iframe, webview').forEach(f => f.style.pointerEvents = 'auto')
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
/* ================== 窗口容器 ================== */
.window-container { 
  position: absolute; 
  display: flex; 
  flex-direction: column; 
  background: white; 
  border-radius: 8px; 
  box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
  overflow: hidden; 
  min-width: 300px; 
  min-height: 200px; 
  transition: box-shadow 0.2s; 
}

.window-container.active { 
  z-index: 100; 
  box-shadow: 0 15px 40px rgba(0,0,0,0.4); 
  border: 1px solid rgba(0,0,0,0.1); 
}

.window-container.maximized { 
  top: 0 !important; 
  left: 0 !important; 
  width: 100% !important; 
  height: 100% !important; 
  border-radius: 0; 
  transform: none !important; 
}

/* ================== 标题栏 ================== */
.window-header { 
  height: 40px; 
  background: #f5f5f7; 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  padding: 0 12px; 
  cursor: default; 
  user-select: none; 
  border-bottom: 1px solid #e0e0e0; 
  flex-shrink: 0; 
}

.window-title { 
  font-weight: 500; 
  font-size: 14px; 
  color: #333; 
  display: flex; 
  align-items: center; 
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-right: 10px;
}

.window-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;
}

.nav-btn {
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #4b5563;
}

.nav-btn:hover {
  background: rgba(0,0,0,0.06);
}

.window-controls { 
  display: flex; 
  gap: 6px; 
  flex-shrink: 0;
}

.window-controls button { 
  border: none; 
  background: transparent; 
  width: 28px; 
  height: 28px; 
  cursor: pointer; 
  border-radius: 4px; 
  font-size: 16px; 
  color: #555; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  transition: background 0.2s;
}

.window-controls button:hover { 
  background: rgba(0,0,0,0.1); 
}

.btn-close:hover { 
  background: #ff4d4f !important; 
  color: white !important; 
}

/* ================== 内容区域 ================== */
.window-body { 
  flex: 1; 
  overflow: hidden; 
  position: relative; 
  background: #fff; 
  display: flex; 
  flex-direction: column; 
}

/* 🟢 Loading 动画 */
.global-loading {
  position: absolute; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%;
  background: white; 
  display: flex; 
  flex-direction: column;
  align-items: center; 
  justify-content: center; 
  z-index: 50;
  color: #666; 
  font-size: 14px;
}
.global-loading i { 
  font-size: 32px; 
  color: #4dabf7; 
  margin-bottom: 15px; 
}

/* 预览框通用样式 */
.preview-box { 
  width: 100%; 
  height: 100%; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: #000; 
}
.preview-box img, .preview-box video { 
  max-width: 100%; 
  max-height: 100%; 
  object-fit: contain; 
}


/* 兜底空状态 */
.empty-state { 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center; 
  height: 100%; 
  color: #999; 
}
.empty-state i { 
  font-size: 48px; 
  margin-bottom: 10px; 
  color: #ccc; 
}

.download-btn { 
  margin-top: 10px; 
  padding: 6px 15px; 
  background: #4dabf7; 
  color: white; 
  border-radius: 4px; 
  text-decoration: none; 
  font-size: 13px; 
}

.resize-handle { 
  position: absolute; 
  right: 0; 
  bottom: 0; 
  width: 15px; 
  height: 15px; 
  cursor: se-resize; 
  z-index: 10; 
}

/* Office & PDF 专用 */
.office-preview { 
  flex: 1; 
  overflow: auto; 
  padding: 20px; 
  background: white; 
}
.doc-content { 
  line-height: 1.6; 
  color: #333; 
}
.error { 
  color: #e03131; 
  text-align: center; 
  padding: 20px; 
}

:deep(table) { 
  border-collapse: collapse; 
  width: 100%; 
  font-size: 14px; 
}
:deep(td), :deep(th) { 
  border: 1px solid #ddd; 
  padding: 8px; 
}
:deep(tr:nth-child(even)) { 
  background-color: #f9f9f9; 
}

.pdf-scroll-container { 
  flex: 1; 
  overflow: auto; 
  background: #525659; 
  display: flex; 
  justify-content: center; 
  padding: 20px; 
}
.pdf-content { 
  width: 100%; 
  max-width: 900px; 
  box-shadow: 0 5px 15px rgba(0,0,0,0.3); 
}

@media (max-width: 768px) {
  .window-container {
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    border-radius: 0;
  }

  .window-header {
    height: 44px;
    padding: 0 10px;
  }

  .window-title {
    font-size: 13px;
  }

  .window-controls button {
    width: 32px;
    height: 32px;
  }

  .resize-handle {
    display: none;
  }
}
</style>