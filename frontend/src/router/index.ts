import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'scripts',
        name: 'ScriptList',
        component: () => import('@/views/ScriptList.vue'),
        meta: { title: '脚本管理' },
      },
      {
        path: 'scripts/:id',
        name: 'ScriptDetail',
        component: () => import('@/views/ScriptDetail.vue'),
        meta: { title: '脚本详情' },
      },
      {
        path: 'instances',
        name: 'InstanceList',
        component: () => import('@/views/InstanceList.vue'),
        meta: { title: '实例管理' },
      },
      {
        path: 'instances/create',
        name: 'InstanceCreate',
        component: () => import('@/views/InstanceCreate.vue'),
        meta: { title: '创建实例' },
      },
      {
        path: 'instances/:id',
        name: 'InstanceDetail',
        component: () => import('@/views/InstanceDetail.vue'),
        meta: { title: '实例详情' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫: 检查登录状态
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  if (to.meta.public || token) {
    next()
  } else {
    next('/login')
  }
})

export default router
