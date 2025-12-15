import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: 'CS2-YCY-Link 控制面板' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
