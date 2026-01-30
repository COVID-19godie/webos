import { defineStore } from 'pinia'

export const useWindowStore = defineStore('window', {
  state: () => ({
    windows: [],
    activeId: null,
    zIndexCounter: 100
  }),

  actions: {
    openWindow(icon) {
      const openExternalWindow = (url) => {
        if (!url) return
        window.open(url, '_blank', 'noopener,noreferrer,width=1200,height=800')
      }

      // 1. 优先判断：如果是文件夹，强制拦截并打开内部窗口
      if (icon.type === 'category' || (icon.data && icon.data.icon === 'folder')) {
        this.createDesktopWindow(icon)
        return
      }

      // 2. 如果是外部链接，默认打开新标签页（允许指定在窗口内打开）
      if (icon.type === 'resource' && icon.data.kind === 'link') {
        if (icon.data.link) {
          const link = icon.data.link
          if (icon.data.open_mode === 'external' || ['/creator', '/store', '/watch', '/apps/game-center', '/apps/virtual-lab'].includes(link)) {
            openExternalWindow(link)
          } else if (icon.data.open_mode === 'window') {
            this.createDesktopWindow(icon)
          } else {
            window.open(link, '_blank')
          }
        }
        return
      }

      // 3. 其他资源（图片、视频、文档）打开内部预览窗口
      this.createDesktopWindow(icon)
    },

    createDesktopWindow(icon) {
      const existing = this.windows.find(w => w.id === icon.id)
      if (existing) {
        this.activateWindow(icon.id)
        return
      }

      const newIndex = this.windows.length
      this.windows.push({
        id: icon.id,
        title: icon.title,
        icon: icon.data?.icon_class || 'fa-solid fa-folder',
        type: icon.type,
        data: icon.data,
        x: 100 + (newIndex * 30),
        y: 50 + (newIndex * 30),
        w: 800,
        h: 600,
        zIndex: ++this.zIndexCounter,
        isMinimized: false,
        isMaximized: false
      })
      this.activeId = icon.id
    },

    closeWindow(id) {
      this.windows = this.windows.filter(w => w.id !== id)
    },

    activateWindow(id) {
      const win = this.windows.find(w => w.id === id)
      if (win) {
        win.isMinimized = false
        win.zIndex = ++this.zIndexCounter
        this.activeId = id
      }
    },

    updateWindow(id, payload) {
      const win = this.windows.find(w => w.id === id)
      if (win) Object.assign(win, payload)
    },
    
    toggleMaximize(id) {
      const win = this.windows.find(w => w.id === id)
      if (win) win.isMaximized = !win.isMaximized
    },
    
    minimizeWindow(id) {
      const win = this.windows.find(w => w.id === id)
      if (win) win.isMinimized = true
    },

    minimizeAll() {
      this.windows.forEach(win => {
        win.isMinimized = true
      })
      this.activeId = null
    }
  }
})