import { defineStore } from 'pinia'
import { desktopApi } from '@/api'
import { localStore } from '@/services/storage/localStore'

const getUserId = () => localStorage.getItem('user_id') || 'default'
const getTenantId = () => localStorage.getItem('current_tenant_id') || 'default'

export const useDesktopStore = defineStore('desktop', {
  state: () => ({
    icons: [],        // 当前显示的图标列表
    loading: false,   // 加载状态
    currentFolderId: 'root', // 当前所在的文件夹ID (root代表桌面)
    clipboard: null,  // 剪贴板(复制/粘贴用)
    editMode: false,  // 长按进入整理模式
  }),

  actions: {
    // 1. 获取图标列表
    async fetchIcons(parentId = 'root') {
      this.loading = true
      this.currentFolderId = parentId
      const userId = getUserId()
      const tenantId = getTenantId()
      try {
        const localIcons = await localStore.getIcons(tenantId, userId)
        if (localIcons.length) {
          this.icons = localIcons
        }
        const res = await desktopApi.getList(parentId)
        this.icons = res.data.results || res.data // 兼容分页或不分页
        await localStore.saveIcons(tenantId, userId, this.icons)
      } catch (err) {
        console.error('获取图标失败:', err)
      } finally {
        this.loading = false
      }
    },

    // 2. 🟢 核心功能：处理拖拽归档 (文件 -> 文件夹)
    async handleDrop(draggedIconId, targetFolderId) {
      // 防止自己拖给自己
      if (draggedIconId == targetFolderId) return

      console.log(`[Store] 移动图标 ${draggedIconId} -> 文件夹 ${targetFolderId}`)

      // 乐观更新：先从界面上移除，让用户感觉"秒在"
      const originalList = [...this.icons] // 备份以防失败
      this.icons = this.icons.filter(icon => icon.id !== draggedIconId)

      try {
        // 调用后端 API
        await desktopApi.moveIcon(draggedIconId, targetFolderId)
      } catch (err) {
        console.error('移动失败，回滚状态', err)
        alert(`移动失败: ${desktopApi.handleError(err)}`)
        this.icons = originalList // 恢复原状
      }
    },

    // 3. 更新位置 (拖拽到桌面空白处)
    async updatePosition(id, x, y) {
      const userId = getUserId()
      const tenantId = getTenantId()
      // 找到本地图标更新坐标，实现丝滑跟手
      const icon = this.icons.find(i => i.id === id)
      if (icon) {
        icon.x = x
        icon.y = y
      }
      await localStore.queueIconUpdate(tenantId, userId, {
        id,
        x,
        y,
        updated_at: new Date().toISOString()
      })
      // 后台静默保存
      try {
        await desktopApi.updatePos(id, x, y)
      } catch (err) {
        console.error('位置保存失败', err)
      }
    },

    setEditMode(value) {
      this.editMode = value
    },

    toggleEditMode() {
      this.editMode = !this.editMode
    }
  }
})