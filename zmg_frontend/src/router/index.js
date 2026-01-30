import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Desktop from '@/views/Desktop.vue'
import AppStore from '@/views/AppStore.vue'
import Watch from '@/views/Watch.vue'
import Creator from '@/views/Creator.vue'
import AdminReview from '@/views/AdminReview.vue'
import Notebook from '@/views/Notebook.vue'
import GameCenter from '@/views/GameCenter.vue'
import VirtualLab from '@/views/VirtualLab.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { 
    path: '/', 
    name: 'Desktop', 
    component: Desktop,
    beforeEnter: (to, from, next) => {
      // 简单的登录检查
      const token = localStorage.getItem('access_token')
      if (!token) next('/login')
      else next()
    }
  },
  {
    path: '/store',
    name: 'AppStore',
    component: AppStore,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) next('/login')
      else next()
    }
  },
  {
    path: '/watch',
    name: 'Watch',
    component: Watch,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) next('/login')
      else next()
    }
  },
  {
    path: '/creator',
    name: 'Creator',
    component: Creator,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) next('/login')
      else next()
    }
  },
  {
    path: '/admin-review',
    name: 'AdminReview',
    component: AdminReview,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) return next('/login')
      const role = localStorage.getItem('user_role')
      if (role !== 'admin') return next('/creator')
      return next()
    }
  },
  {
    path: '/apps/notebook',
    name: 'Notebook',
    component: Notebook,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) return next('/login')
      return next()
    }
  },
  {
    path: '/apps/game-center',
    name: 'GameCenter',
    component: GameCenter,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) return next('/login')
      return next()
    }
  },
  {
    path: '/apps/virtual-lab',
    name: 'VirtualLab',
    component: VirtualLab,
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('access_token')
      if (!token) return next('/login')
      return next()
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router