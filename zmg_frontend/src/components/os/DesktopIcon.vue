<template>
  <div 
    class="desktop-icon"
    :class="{ 
      'is-dragging': isDragging, 
      'in-folder': isInsideFolder 
    }"
    :style="positionStyle"
    @mousedown="onMouseDown"
    @pointerdown="onPointerDown"
    @pointerup="onPointerUp"
    @pointercancel="onPointerCancel"
    @click="onClick"
    @dblclick.stop="onDblClick"
    @dragstart.prevent
  >
    <button v-if="editMode" class="icon-delete" @click.stop="onDelete">×</button>
    <div class="icon-img-container">
      <img 
        v-if="icon.type === 'category' || (icon.data && icon.data.icon === 'folder')" 
        src="https://cdn-icons-png.flaticon.com/512/716/716784.png" 
        class="icon-img"
      />
      <img 
        v-else-if="icon.data && (icon.data.cover || icon.data.kind === 'image')" 
        :src="icon.data.cover || icon.data.file" 
        class="icon-img"
      />
      <i 
        v-else-if="icon.data && icon.data.icon_class" 
        :class="icon.data.icon_class" 
        class="icon-font"
      ></i>
      <i v-else class="fa-solid fa-file icon-font"></i>
    </div>
    
    <div class="icon-title">{{ displayTitle }}</div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useDesktopStore } from '@/stores/desktopStore'

const props = defineProps({
  icon: Object,
  editMode: Boolean
})
const emit = defineEmits(['open', 'delete', 'longpress'])
const store = useDesktopStore()

// 🟢 隐藏后缀名计算属性
const displayTitle = computed(() => {
  const title = props.icon.title || '未命名'
  // 文件夹不需要处理
  if (props.icon.type === 'category') return title
  // 正则替换：去掉最后一个点及其后面的字符
  return title.replace(/\.[^/.]+$/, "")
})

// 判断是否在文件夹内
const isInsideFolder = computed(() => {
  const pid = props.icon.parent_folder || props.icon.parent_folder_id
  return pid && pid !== 'root' && pid !== 0
})

// 位置样式
const positionStyle = computed(() => {
  if (isInsideFolder.value) {
    return { position: 'relative' }
  }
  return {
    left: props.icon.x + 'px',
    top: props.icon.y + 'px',
    position: 'absolute'
  }
})

// --- 拖拽逻辑 ---
const isDragging = ref(false)
let startX = 0, startY = 0
let initialLeft = 0, initialTop = 0
let hasMoved = false

const isTouchDevice = () => {
  return typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)
}

const onMouseDown = (e) => {
  if (props.editMode || e.button !== 0 || isInsideFolder.value || isTouchDevice()) return 

  startX = e.clientX
  startY = e.clientY
  initialLeft = props.icon.x
  initialTop = props.icon.y
  hasMoved = false

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

const onMouseMove = (e) => {
  const dx = e.clientX - startX
  const dy = e.clientY - startY

  if (!hasMoved && Math.abs(dx) < 5 && Math.abs(dy) < 5) return

  hasMoved = true
  isDragging.value = true
  store.updatePosition(props.icon.id, initialLeft + dx, initialTop + dy)
}

const onMouseUp = () => {
  isDragging.value = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
}

// --- 事件 ---
const onDblClick = () => {
  if (props.editMode) return
  if (!hasMoved) emit('open', props.icon)
}
const onClick = () => {
  if (props.editMode) return
  const isLink = props.icon?.data?.kind === 'link'
  if (!hasMoved && (isTouchDevice() || isLink)) emit('open', props.icon)
}

let longPressTimer = null
let pressStart = { x: 0, y: 0 }

const onPointerDown = (e) => {
  if (props.editMode || e.button === 2) return
  pressStart = { x: e.clientX, y: e.clientY }
  clearTimeout(longPressTimer)
  longPressTimer = setTimeout(() => {
    emit('longpress', props.icon)
  }, 600)
  window.addEventListener('pointermove', onPointerMove)
}

const onPointerMove = (e) => {
  const dx = Math.abs(e.clientX - pressStart.x)
  const dy = Math.abs(e.clientY - pressStart.y)
  if (dx > 5 || dy > 5) {
    clearTimeout(longPressTimer)
    window.removeEventListener('pointermove', onPointerMove)
  }
}

const onPointerUp = () => {
  clearTimeout(longPressTimer)
  window.removeEventListener('pointermove', onPointerMove)
}

const onPointerCancel = () => {
  clearTimeout(longPressTimer)
  window.removeEventListener('pointermove', onPointerMove)
}

const onDelete = () => emit('delete', props.icon)
</script>

<style scoped>
.desktop-icon {
  width: 80px; height: 90px; display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
  cursor: pointer; padding: 6px; border-radius: 12px; user-select: none; transition: background 0.2s, transform 0.2s; z-index: 10;
}
.desktop-icon:hover { background-color: rgba(255, 255, 255, 0.25); transform: translateY(-2px); }

.desktop-icon.in-folder { margin: 10px; }
.desktop-icon.in-folder .icon-title { color: #333 !important; text-shadow: none !important; }
.desktop-icon.in-folder:hover { background-color: rgba(0, 0, 0, 0.05); }

.icon-img-container { width: 52px; height: 52px; display: flex; align-items: center; justify-content: center; margin-bottom: 6px; }
.icon-img { width: 100%; height: 100%; object-fit: contain; pointer-events: none; }

/* 针对不同类型文件的图标颜色优化 */
.icon-font { font-size: 40px; color: #4dabf7; text-shadow: 0 2px 4px rgba(0,0,0,0.18); }

.icon-title {
  color: white; font-size: 12px; text-align: center; text-shadow: 0 1px 3px rgba(0,0,0,0.7);
  word-break: break-all; line-height: 1.2;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.is-dragging { opacity: 0.8; z-index: 1000; pointer-events: none; }

.icon-delete {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: #ff4d4f;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .desktop-icon {
    width: 78px;
    height: 86px;
    padding: 4px;
    position: relative !important;
    left: auto !important;
    top: auto !important;
  }

  .icon-img-container {
    width: 48px;
    height: 48px;
    margin-bottom: 4px;
  }

  .icon-title {
    font-size: 11px;
  }

  .desktop-icon:hover {
    background-color: transparent;
    transform: none;
  }
}
</style>