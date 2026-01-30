<template>
  <div class="dock-wrapper">
    <div class="mac-dock glass-panel">
      <div class="dock-group left-group">
        <div class="dock-item" @click="toggleStartMenu" title="启动台">
        <div class="icon-box launchpad-icon">
          <i class="fa-solid fa-rocket"></i>
        </div>
        <div class="tooltip">启动台</div>
      </div>

        <div class="dock-item" @click="openFinder" title="访达">
        <div class="icon-box finder-icon">
          <i class="fa-solid fa-face-smile"></i>
        </div>
        <div class="dot"></div>
        <div class="tooltip">访达</div>
      </div>

        <div class="dock-item" @click="openStore" title="应用商店">
        <div class="icon-box store-icon">
          <i class="fa-solid fa-store"></i>
        </div>
        <div class="tooltip">应用商店</div>
      </div>

        <div class="dock-item" @click="openWatch" title="观看中心">
        <div class="icon-box watch-icon">
          <i class="fa-solid fa-circle-play"></i>
        </div>
        <div class="tooltip">观看中心</div>
      </div>

        <div class="dock-item" @click="openCreator" title="创作者中心">
        <div class="icon-box creator-icon">
          <i class="fa-solid fa-pen-nib"></i>
        </div>
        <div class="tooltip">创作者中心</div>
      </div>

        <div v-if="isAdmin" class="dock-item" @click="openAdmin" title="审核后台">
        <div class="icon-box admin-icon">
          <i class="fa-solid fa-shield-halved"></i>
        </div>
        <div class="tooltip">审核后台</div>
      </div>

        <div class="dock-item" @click="openGameCenter" title="游戏中心">
        <div class="icon-box game-center-icon">
          <i class="fa-solid fa-gamepad"></i>
        </div>
        <div class="tooltip">游戏中心</div>
      </div>

        <div class="dock-item" @click="openVirtualLab" title="虚拟实验室">
        <div class="icon-box virtual-lab-icon">
          <i class="fa-solid fa-flask"></i>
        </div>
        <div class="tooltip">虚拟实验室</div>
      </div>
      </div>

      <div class="dock-spacer"></div>

      <div class="dock-group right-group">
        <div class="dock-item" @click="openCloudMenu" title="去云端逛逛">
          <div class="icon-box cloud-icon">
            <i class="fa-solid fa-cloud"></i>
          </div>
          <div class="tooltip">去云端逛逛</div>
        </div>
        <div
          v-for="win in orderedWindows"
          :key="win.id"
          class="dock-item"
          :class="{ 'minimized': win.isMinimized }"
          @click="handleTaskClick(win)"
        >
          <div class="icon-box app-icon">
            <i v-if="win.type === 'category'" class="fa-solid fa-folder folder-color"></i>
            <i v-else :class="getIconClass(win)" class="file-color"></i>
          </div>
          <div class="dot"></div>
          <div class="tooltip">{{ win.title }}</div>
        </div>
      </div>

    </div>
  </div>

  <ContextMenu
    :visible="cloudMenuVisible"
    :x="cloudMenuX"
    :y="cloudMenuY"
    :items="cloudMenuItems"
    @close="closeCloudMenu"
  />
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useWindowStore } from '@/stores/windowStore'
import ContextMenu from './ContextMenu.vue'
// 🔴 删除了 import { defineEmits } from 'vue' -> 不需要导入

const emit = defineEmits(['open-launcher'])
const winStore = useWindowStore()
const isAdmin = computed(() => localStorage.getItem('user_role') === 'admin')
const orderedWindows = computed(() => {
  return [...winStore.windows].sort((a, b) => a.zIndex - b.zIndex)
})

const openFinder = () => {
  console.log('正在打开访达：根目录')
  // 这里的 id 必须唯一，防止重复打开多个相同的访达窗口
  winStore.openWindow({
    id: 'finder_root',
    title: '访达',
    type: 'category',
    data: { id: 'root' },
    icon: 'fa-solid fa-face-smile'
  })
}

const openExternalWindow = (url) => {
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer,width=1200,height=800')
}

const openStore = () => openExternalWindow('/store')
const openWatch = () => openExternalWindow('/watch')
const openCreator = () => openExternalWindow('/creator')
const openAdmin = () => window.open('/admin-review', '_blank')
const openGameCenter = () => openExternalWindow('/apps/game-center')

const openVirtualLab = () => openExternalWindow('/apps/virtual-lab')

const cloudMenuVisible = ref(false)
const cloudMenuX = ref(0)
const cloudMenuY = ref(0)
const cloudMenuItems = [
  {
    label: '观看中心',
    icon: 'fa-solid fa-circle-play',
    action: () => openExternalWindow('/watch')
  },
  {
    label: '应用商店',
    icon: 'fa-solid fa-store',
    action: () => openExternalWindow('/store')
  }
]

const openCloudMenu = (e) => {
  cloudMenuX.value = e.clientX
  cloudMenuY.value = e.clientY
  cloudMenuVisible.value = true
}

const closeCloudMenu = () => {
  cloudMenuVisible.value = false
}

const onGlobalClick = () => {
  if (cloudMenuVisible.value) closeCloudMenu()
}

onMounted(() => window.addEventListener('click', onGlobalClick))
onUnmounted(() => window.removeEventListener('click', onGlobalClick))

const handleTaskClick = (win) => {
  if (win.isMinimized) {
    winStore.activateWindow(win.id)
  } else if (winStore.activeId === win.id) {
    winStore.minimizeWindow(win.id)
  } else {
    winStore.activateWindow(win.id)
  }
}

const toggleStartMenu = () => {
  emit('open-launcher')
}

const getIconClass = (win) => {
  // 优先使用传递进来的 icon_class
  if (win.data && win.data.icon_class) return win.data.icon_class
  // 其次尝试 win.icon
  if (win.icon) return win.icon
  // 默认图标
  return 'fa-solid fa-file'
}
</script>

<style scoped>
/* 容器：负责把 Dock 放在底部居中 */
.dock-wrapper {
  position: fixed;
  bottom: 36px; /* 调高一点，给底部备案号留空间 */
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  z-index: 9999;
  pointer-events: none;
  perspective: 1000px;
}

/* Dock 本体 */
.mac-dock {
  pointer-events: auto;
  display: flex;
  align-items: flex-end;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  box-shadow: 
    0 10px 20px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  gap: 8px;
  min-width: 520px;
  transition: all 0.4s cubic-bezier(0.32, 0.72, 0, 1);
  transform-style: preserve-3d;
}

.mac-dock:hover {
  background: rgba(255, 255, 255, 0.35);
  box-shadow: 
    0 15px 35px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.15) inset;
}

.dock-group {
  display: flex;
  align-items: flex-end;
  gap: 6px;
}

.dock-spacer {
  flex: 1;
}

.dock-item {
  position: relative;
  width: 50px;
  height: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s ease, filter 0.2s ease;
}

.dock-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
}

.icon-box {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 
    0 4px 8px rgba(0,0,0,0.2),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  transition: box-shadow 0.2s ease;
}

.dock-item:hover .icon-box {
  box-shadow: 
    0 8px 20px rgba(0,0,0,0.3),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset,
    0 0 20px rgba(255, 255, 255, 0.2);
}

/* 点击反馈动画 */
.dock-item:active {
  filter: brightness(0.95);
}

.dock-item:active .icon-box {
  transform: none;
}

.launchpad-icon {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  color: #555;
}

.finder-icon {
  background: linear-gradient(135deg, #2980b9 0%, #6dd5fa 100%);
  color: white;
  font-size: 28px;
}

.store-icon {
  background: linear-gradient(135deg, #ffd43b 0%, #ffa94d 100%);
  color: #4a3b00;
}

.watch-icon {
  background: linear-gradient(135deg, #74c0fc 0%, #4dabf7 100%);
  color: white;
}

.creator-icon {
  background: linear-gradient(135deg, #b197fc 0%, #845ef7 100%);
  color: white;
}

.admin-icon {
  background: linear-gradient(135deg, #adb5bd 0%, #868e96 100%);
  color: white;
}

.game-center-icon {
  background: linear-gradient(135deg, #b197fc 0%, #845ef7 100%);
  color: white;
}

.virtual-lab-icon {
  background: linear-gradient(135deg, #63e6be 0%, #38d9a9 100%);
  color: white;
}

.cloud-icon {
  background: linear-gradient(135deg, #74c0fc 0%, #a5d8ff 100%);
  color: white;
}

.app-icon {
  background: linear-gradient(135deg, #f8f9fa 0%, #dee2e6 100%);
}

.folder-color { color: #f39c12; }
.file-color { color: #555; }

.minimized .icon-box {
  filter: grayscale(0.8) opacity(0.7);
  transform: scale(0.9);
}

.minimized:hover .icon-box {
  filter: grayscale(0.3) opacity(0.9);
  transform: scale(1);
}

/* 运行指示点 - 更灵动 */
.dot {
  position: absolute;
  bottom: -8px;
  width: 5px;
  height: 5px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.3);
}

.dock-item:hover .dot {
  transform: scale(1.4);
  background: #4ade80;
  box-shadow: 0 0 10px rgba(74, 222, 128, 0.6);
}

/* 提示框 - 更精致 */
.tooltip {
  position: absolute;
  top: -45px;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transform: translateY(8px) scale(0.9);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tooltip::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid rgba(0, 0, 0, 0.85);
}

.dock-item:hover .tooltip {
  opacity: 1;
  transform: translateY(0) scale(1);
}

@media (max-width: 768px) {
  .dock-wrapper {
    bottom: 12px;
    padding: 0 10px;
  }

  .mac-dock {
    min-width: 0;
    width: calc(100% - 20px);
    padding: 8px 10px;
    gap: 6px;
    overflow-x: auto;
  }

  .dock-group {
    gap: 4px;
  }

  .dock-item {
    width: 44px;
    height: 44px;
  }

  .icon-box {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .tooltip,
  .dot {
    display: none;
  }

  .dock-item:hover,
  .dock-item:active {
    transform: none;
    margin: 0;
  }

  .dock-item:hover + .dock-item,
  .dock-item:has(+ .dock-item:hover) {
    transform: none;
    margin: 0;
  }
}

@media (hover: none) {
  .dock-item:hover,
  .dock-item:active {
    transform: none;
    margin: 0;
  }

  .dock-item:hover + .dock-item,
  .dock-item:has(+ .dock-item:hover) {
    transform: none;
    margin: 0;
  }
}
</style>