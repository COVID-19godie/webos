import { syncApi } from '@/api'
import { localStore } from '@/services/storage/localStore'

const getUserId = () => localStorage.getItem('user_id') || 'default'
const getTenantId = () => localStorage.getItem('current_tenant_id') || 'default'

export const syncService = {
  async loadSettings() {
    const userId = getUserId()
    const tenantId = getTenantId()
    const local = await localStore.getSettings(tenantId, userId)
    return local || {
      uploadEnabled: false,
      conflictStrategy: 'server_wins',
      lastSyncAt: null
    }
  },

  async saveSettings(settings) {
    const userId = getUserId()
    const tenantId = getTenantId()
    await localStore.saveSettings(tenantId, userId, settings)
  },

  async syncNow() {
    const tenantId = getTenantId()
    const userId = getUserId()
    const settings = await this.loadSettings()

    if (settings.uploadEnabled) {
      const pending = await localStore.getPendingIconUpdates(tenantId, userId)
      if (pending.length) {
        const payload = {
          conflict_strategy: settings.conflictStrategy,
          icons: pending.map(item => item.payload)
        }
        await syncApi.push(payload)
        await localStore.clearPending(pending.map(item => item.id))
      }
    }

    const pullPayload = { since: settings.lastSyncAt }
    const res = await syncApi.pull(pullPayload)
    const data = res.data?.data || {}
    if (data.icons) {
      await localStore.saveIcons(tenantId, userId, data.icons)
    }

    const serverTime = data.server_time
    const updated = {
      ...settings,
      lastSyncAt: serverTime || new Date().toISOString()
    }
    await localStore.saveSettings(tenantId, userId, updated)
    return updated
  }
}
