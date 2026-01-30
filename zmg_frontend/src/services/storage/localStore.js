const DB_NAME = 'webos_local_store'
const DB_VERSION = 1

const openDb = () => new Promise((resolve, reject) => {
  const request = indexedDB.open(DB_NAME, DB_VERSION)
  request.onupgradeneeded = () => {
    const db = request.result
    if (!db.objectStoreNames.contains('icons')) {
      db.createObjectStore('icons', { keyPath: 'key' })
    }
    if (!db.objectStoreNames.contains('settings')) {
      db.createObjectStore('settings', { keyPath: 'key' })
    }
    if (!db.objectStoreNames.contains('pending')) {
      db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true })
    }
  }
  request.onsuccess = () => resolve(request.result)
  request.onerror = () => reject(request.error)
})

const buildKey = (tenantId, userId) => `${tenantId || 'default'}:${userId || 'default'}`

const withStore = async (storeName, mode, callback) => {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, mode)
    const store = tx.objectStore(storeName)
    const result = callback(store)
    tx.oncomplete = () => resolve(result)
    tx.onerror = () => reject(tx.error)
  })
}

export const localStore = {
  async saveIcons(tenantId, userId, icons) {
    const prefix = buildKey(tenantId, userId)
    await this.clearIcons(tenantId, userId)
    return withStore('icons', 'readwrite', store => {
      icons.forEach(icon => {
        store.put({ key: `${prefix}:${icon.id}`, prefix, icon })
      })
    })
  },

  async getIcons(tenantId, userId) {
    const prefix = buildKey(tenantId, userId)
    const items = []
    await withStore('icons', 'readonly', store => {
      const request = store.openCursor()
      request.onsuccess = () => {
        const cursor = request.result
        if (cursor) {
          if (cursor.value.prefix === prefix) items.push(cursor.value.icon)
          cursor.continue()
        }
      }
    })
    return items
  },

  async clearIcons(tenantId, userId) {
    const prefix = buildKey(tenantId, userId)
    return withStore('icons', 'readwrite', store => {
      const request = store.openCursor()
      request.onsuccess = () => {
        const cursor = request.result
        if (cursor) {
          if (cursor.value.prefix === prefix) cursor.delete()
          cursor.continue()
        }
      }
    })
  },

  async getSettings(tenantId, userId) {
    const key = buildKey(tenantId, userId)
    const result = await withStore('settings', 'readonly', store => store.get(key))
    return result?.settings || null
  },

  async saveSettings(tenantId, userId, settings) {
    const key = buildKey(tenantId, userId)
    return withStore('settings', 'readwrite', store => store.put({ key, settings }))
  },

  async queueIconUpdate(tenantId, userId, payload) {
    const key = buildKey(tenantId, userId)
    return withStore('pending', 'readwrite', store => store.add({ key, type: 'icon_update', payload }))
  },

  async getPendingIconUpdates(tenantId, userId) {
    const key = buildKey(tenantId, userId)
    const items = []
    await withStore('pending', 'readonly', store => {
      const request = store.openCursor()
      request.onsuccess = () => {
        const cursor = request.result
        if (cursor) {
          if (cursor.value.key === key && cursor.value.type === 'icon_update') {
            items.push({ id: cursor.key, payload: cursor.value.payload })
          }
          cursor.continue()
        }
      }
    })
    return items
  },

  async clearPending(ids) {
    return withStore('pending', 'readwrite', store => {
      ids.forEach(id => store.delete(id))
    })
  }
}
