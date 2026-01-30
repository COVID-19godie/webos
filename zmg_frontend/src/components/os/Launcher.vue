<template>
  <Transition name="launcher-fade">
    <div v-if="visible" class="launcher-overlay" @click.self="close">
      <div class="launcher-content">
        <div class="search-bar">
          <i class="fa-solid fa-magnifying-glass"></i>
          <input v-model="searchQuery" type="text" placeholder="搜索应用..." />
        </div>

        <div class="apps-grid">
          <div v-if="loading" class="loading-state">
            <i class="fa-solid fa-spinner fa-spin"></i> 加载中...
          </div>
          
          <div v-else-if="filteredApps.length === 0" class="empty-state">
            暂无应用
          </div>

          <div v-else 
               v-for="app in filteredApps" 
               :key="app.id" 
               class="app-item"
               @click="openApp(app)">
            
            <div class="app-icon">
              <img v-if="app.data.cover" :src="app.data.cover" />
              <i v-else-if="app.data.icon_class" 
                 :class="app.data.icon_class"
                 :style="{ color: getIconColor(app.data.icon_class) }"></i>
              <i v-else class="fa-solid fa-cube" style="color: #adb5bd"></i>
            </div>
            
            <div class="app-name">{{ app.title }}</div>
          </div>
        </div>
        
        <div class="launcher-pagination">
          <span class="dot active"></span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { desktopApi } from '@/api'
import { useWindowStore } from '@/stores/windowStore'

const props = defineProps(['visible'])
const emit = defineEmits(['update:visible'])
const winStore = useWindowStore()

const apps = ref([])
const loading = ref(false)
const searchQuery = ref('')

const whiteboardUrl = import.meta.env.VITE_WHITEBOARD_URL || 'https://www.onenote.com/'

const builtInApps = [
  {
    id: 'builtin_notebook',
    title: '电子黑板',
    type: 'resource',
    data: {
      kind: 'link',
      link: whiteboardUrl,
      icon_class: 'fa-solid fa-pen-to-square',
      open_mode: 'external'
    }
  },
  {
    id: 'builtin_game_center',
    title: '游戏中心',
    type: 'resource',
    data: {
      kind: 'link',
      link: '/apps/game-center',
      icon_class: 'fa-solid fa-gamepad',
      open_mode: 'external'
    }
  },
  {
    id: 'builtin_virtual_lab',
    title: '虚拟实验室',
    type: 'resource',
    data: {
      kind: 'link',
      link: '/apps/virtual-lab',
      icon_class: 'fa-solid fa-flask',
      open_mode: 'external'
    }
  }
]

// 🟢 加载应用列表
const loadApps = async () => {
  loading.value = true
  try {
    // 策略A: 读取 ID=4 (应用库) 的内容
    // 策略B: 如果你想显示所有内容，可能需要后端增加一个 'all_apps' 的接口
    // 这里先读取我们刚刚安装 H5 应用的 ID=4 文件夹
    const res = await desktopApi.getList(4) 
    
    // 如果你还想显示桌面的应用，可以用 Promise.all 合并：
    // const [appsRes, desktopRes] = await Promise.all([desktopApi.getList(4), desktopApi.getList('root')])
    // apps.value = [...appsRes.data, ...desktopRes.data]
    
    const remoteApps = res.data.results || res.data
    const merged = [...builtInApps, ...(remoteApps || [])]
    const seen = new Set()
    apps.value = merged.filter(app => {
      const key = app?.id || app?.title || app?.data?.link
      if (!key || seen.has(key)) return false
      seen.add(key)
      return true
    })
  } catch (e) {
    console.error('启动台加载失败', e)
    apps.value = []
  } finally {
    loading.value = false
  }
}

// 监听显示状态，每次打开时刷新
watch(() => props.visible, (newVal) => {
  if (newVal) {
    searchQuery.value = ''
    loadApps()
  }
})

const filteredApps = computed(() => {
  if (!searchQuery.value) return apps.value
  return apps.value.filter(app => 
    app.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const openApp = (app) => {
  winStore.openWindow(app)
  close()
}

const close = () => {
  emit('update:visible', false)
}

// 辅助颜色函数
const getIconColor = (cls) => {
  if (!cls) return '#adb5bd'
  if (cls.includes('gamepad')) return '#be4bdb'
  if (cls.includes('html5')) return '#f06529'
  if (cls.includes('folder')) return '#ffd43b'
  return '#4dabf7'
}
</script>

<style scoped>
.launcher-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.4); /* 毛玻璃背景更深一点 */
  backdrop-filter: blur(20px);
  z-index: 9999;
  display: flex; flex-direction: column; align-items: center; padding-top: 80px;
}

.search-bar {
  width: 400px; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px; padding: 12px 20px; display: flex; align-items: center; gap: 10px;
  color: white; margin-bottom: 40px; transition: all 0.3s;
}
.search-bar:focus-within { background: rgba(255, 255, 255, 0.25); width: 440px; }
.search-bar input { background: transparent; border: none; outline: none; color: white; flex: 1; font-size: 16px; }
.search-bar input::placeholder { color: rgba(255, 255, 255, 0.6); }

.apps-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 40px;
  width: 80%; max-width: 1000px; max-height: 60vh; overflow-y: auto;
  padding: 20px;
}

.app-item {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  cursor: pointer; transition: transform 0.2s;
}
.app-item:hover { transform: scale(1.1); }

.app-icon {
  width: 64px; height: 64px; background: rgba(255,255,255,0.1);
  border-radius: 14px; display: flex; align-items: center; justify-content: center;
}
.app-icon img { width: 100%; height: 100%; object-fit: cover; border-radius: 14px; }
.app-icon i { font-size: 32px; }

.app-name { color: white; font-size: 13px; text-shadow: 0 1px 3px rgba(0,0,0,0.5); text-align: center; }

/* 动画 */
.launcher-fade-enter-active, .launcher-fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.launcher-fade-enter-from, .launcher-fade-leave-to { opacity: 0; transform: scale(1.1); }

@media (max-width: 768px) {
  .launcher-overlay {
    padding-top: 60px;
  }

  .search-bar {
    width: calc(100% - 40px);
    max-width: 520px;
    margin-bottom: 20px;
  }

  .search-bar:focus-within {
    width: calc(100% - 32px);
  }

  .apps-grid {
    width: calc(100% - 24px);
    max-height: 70vh;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
  }

  .app-icon {
    width: 56px;
    height: 56px;
  }
}

@media (max-width: 480px) {
  .apps-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }

  .app-name {
    font-size: 12px;
  }
}
</style>