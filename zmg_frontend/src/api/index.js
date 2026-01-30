import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || '/api'
const api = axios.create({ baseURL: apiBase, timeout: 30000 })

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    const tenantId = localStorage.getItem('current_tenant_id')
    if (tenantId) config.headers['X-Tenant-Id'] = tenantId
    return config
  },
  error => Promise.reject(error)
)

export const authApi = {
  login: (username, password) => api.post('/token/', { username, password })
}

export const desktopApi = {
  getList: (parentId) => api.get('/desktop/', { params: { parent_id: parentId } }),
  updatePos: (id, x, y) => api.patch(`/desktop/${id}/move/`, { x, y }),
  delete: (id) => api.delete(`/desktop/${id}/uninstall/`),
  rename: (id, name) => api.post(`/desktop/${id}/rename/`, { name }),
  createFolder: (data) => api.post('/desktop/create_folder/', data),
  createLink: (data) => api.post('/desktop/create_link/', data),
  
  // 🟢 同步：本地资源转云端公共库
  syncToCloud: (fileId, targetFolder) => api.post(`/desktop/${fileId}/sync/`, { target_id: targetFolder }),
  
  // 🟢 添加缺失的移动图标方法
  moveIcon: (iconId, targetFolderId) => api.patch(`/desktop/${iconId}/move/`, { parent_id: targetFolderId }),

  installH5App: (formData) => api.post('/desktop/install_h5_app/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000 // 增加超时时间
  }),

  upload: (file, x = 50, y = 50) => {
    const formData = new FormData(); formData.append('file', file)
    const fileName = file.name.toLowerCase()
    // ⚠️ ID 请对应：1-图像, 2-影音, 3-文档, 4-其他
    let targetFolder = 4 
    if (/\.(jpg|jpeg|png|gif|svg)$/.test(fileName)) targetFolder = 1 
    if (/\.(mp4|mov|avi|mkv)$/.test(fileName)) targetFolder = 2      
    if (/\.(pdf|doc|docx|ppt|txt)$/.test(fileName)) targetFolder = 3 
    
    formData.append('parent_id', targetFolder)
    formData.append('x', x); formData.append('y', y)
    return api.post('/desktop/upload_file/', formData, { 
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000 // 增加超时时间
    })
  },
  
  // 🟢 统一的错误处理方法
  handleError: (error) => {
    if (error.response) {
      return error.response.data.msg || error.response.data.detail || '请求失败'
    } else if (error.request) {
      return '网络连接失败'
    } else {
      return error.message || '未知错误'
    }
  }
}

export const tenantApi = {
  list: () => api.get('/tenants/'),
  memberships: () => api.get('/memberships/')
}

export const syncApi = {
  getSettings: () => api.get('/sync/settings/'),
  updateSettings: (payload) => api.patch('/sync/settings/', payload),
  pull: (payload) => api.post('/sync/pull/', payload),
  push: (payload) => api.post('/sync/push/', payload)
}

export const appStoreApi = {
  list: (params) => api.get('/apps/', { params }),
  get: (id) => api.get(`/apps/${id}/`),
  mine: () => api.get('/apps/mine/'),
  submit: (payload) => api.post('/apps/', payload),
  approve: (id, payload) => api.post(`/apps/${id}/approve/`, payload),
  reject: (id, payload) => api.post(`/apps/${id}/reject/`, payload),
  like: (id) => api.post(`/apps/${id}/like/`),
  unlike: (id) => api.delete(`/apps/${id}/unlike/`),
  view: (id) => api.post(`/apps/${id}/view/`),
  comment: (id, content) => api.post(`/apps/${id}/comment/`, { content }),
  comments: (id) => api.get(`/apps/${id}/comments/`),
  report: (id, payload) => api.post(`/apps/${id}/report/`, payload),
  tags: () => api.get('/app-tags/'),
  collections: () => api.get('/app-collections/'),
  reorderCollection: (id, items) => api.post(`/app-collections/${id}/reorder/`, { items }),
  bulkApprove: (payload) => api.post('/apps/bulk_approve/', payload),
  bulkReject: (payload) => api.post('/apps/bulk_reject/', payload)
}

export const githubApi = {
  listRepos: (params) => api.get('/github/repos/', { params })
}
export default api