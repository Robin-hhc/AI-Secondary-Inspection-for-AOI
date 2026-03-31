import { createRouter, createWebHistory } from 'vue-router'
import { authAPI } from '../api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/annotation'
      },
      {
        path: 'annotation',
        name: 'Annotation',
        component: () => import('../views/Annotation.vue'),
        meta: { title: '标注' }
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('../views/Statistics.vue'),
        meta: { title: '统计' }
      },
      {
        path: 'model',
        name: 'Model',
        component: () => import('../views/Model.vue'),
        meta: { title: '模型管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
