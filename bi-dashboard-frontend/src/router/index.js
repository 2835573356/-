import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '运营数据看板' }
  },
  {
    path: '/trend',
    name: 'TrendAnalysis',
    component: () => import('@/views/TrendAnalysisView.vue'),
    meta: { title: '趋势分析' }
  },
  {
    path: '/issues',
    name: 'IssueAnalysis',
    component: () => import('@/views/IssueAnalysisView.vue'),
    meta: { title: '问题分析' }
  },
  {
    path: '/risk',
    name: 'RiskCenter',
    component: () => import('@/views/RiskCenterView.vue'),
    meta: { title: '风险中心' }
  },
  {
    path: '/posts',
    name: 'PostList',
    component: () => import('@/views/PostListView.vue'),
    meta: { title: '帖子管理' }
  },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetailView.vue'),
    meta: { title: '帖子详情' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 影刀社区` : '影刀社区 · 运营数据看板'
})

export default router
