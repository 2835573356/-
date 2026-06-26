import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as dashboardApi from '@/api/dashboard'
import * as postsApi from '@/api/posts'
import * as adminApi from '@/api/admin'
import { sentimentToChinese } from '@/api/index'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const trend = ref(null)
  const sentiment = ref(null)
  const categories = ref(null)
  const priority = ref(null)
  const rootCause = ref(null)
  const insights = ref(null)
  const riskAlerts = ref(null)
  const hotPosts = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Posts list state
  const posts = ref([])
  const postsTotal = ref(0)
  const postsPage = ref(1)
  const postsTotalPages = ref(0)

  /** Fetch all dashboard data in parallel.
   *  range: { start, end } —— 各"目标日"卡片用 end 作为目标日，趋势图用 start~end。
   *  兼容旧调用：传字符串时按单个目标日处理。
   */
  async function fetchAll(range) {
    loading.value = true
    error.value = null

    const todayStr = new Date().toISOString().split('T')[0]
    let start, end
    if (typeof range === 'string') {
      start = undefined
      end = range || todayStr
    } else if (range && typeof range === 'object') {
      start = range.start
      end = range.end || todayStr
    } else {
      end = todayStr
    }

    try {
      const rangeArg = start ? { start, end } : end
      const results = await Promise.allSettled([
        dashboardApi.fetchSummary(end),
        dashboardApi.fetchTrend(start, end),
        dashboardApi.fetchSentiment(end),
        dashboardApi.fetchCategories(end),
        dashboardApi.fetchPriority(rangeArg),
        dashboardApi.fetchHotPosts(rangeArg),
        dashboardApi.fetchRootCause(end),
        dashboardApi.fetchInsights(end),
        dashboardApi.fetchRiskAlerts(end)
      ])
      const valueAt = (index, fallback = null) => {
        const result = results[index]
        if (result.status === 'fulfilled') return result.value
        console.warn('Dashboard partial fetch failed:', result.reason)
        return fallback
      }
      const sum = valueAt(0, summary.value)
      const trd = valueAt(1, trend.value)
      const sent = valueAt(2, sentiment.value)
      const cats = valueAt(3, categories.value)
      const pri = valueAt(4, priority.value)
      const hot = valueAt(5, hotPosts.value ? { posts: hotPosts.value } : null)
      const rc = valueAt(6, rootCause.value)
      const ins = valueAt(7, insights.value)
      const risk = valueAt(8, riskAlerts.value)
      summary.value = sum
      trend.value = trd
      sentiment.value = sent
      categories.value = cats
      priority.value = pri
      hotPosts.value = (hot?.posts || []).map(p => ({
        ...p,
        sentiment: sentimentToChinese(p.sentiment)
      }))
      rootCause.value = rc
      insights.value = ins
      riskAlerts.value = risk
      const failed = results.find(result => result.status === 'rejected')
      if (failed) error.value = failed.reason?.message || '部分数据加载失败'
    } catch (e) {
      error.value = e.message || '数据加载失败'
      console.error('Dashboard fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  /** Fetch posts list with filters */
  async function fetchPosts(params = {}) {
    loading.value = true
    error.value = null
    try {
      const result = await postsApi.fetchPosts(params)
      posts.value = (result.items || []).map(p => ({
        ...p,
        sentiment: sentimentToChinese(p.sentiment)
      }))
      postsTotal.value = result.total || 0
      postsPage.value = result.page || 1
      postsTotalPages.value = result.total_pages || 0
    } catch (e) {
      error.value = e.message || '帖子加载失败'
    } finally {
      loading.value = false
    }
  }

  /** Get single post by ID */
  async function fetchPostById(id) {
    try {
      const post = await postsApi.fetchPostById(id)
      return { ...post, sentiment: sentimentToChinese(post.sentiment) }
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  /** Mark alert as resolved (requires admin). Returns { ok, error? } */
  async function markAlertResolved(id) {
    if (id <= 0) {
      return { ok: false, error: '动态预警由系统实时生成，无需手动标记处理' }
    }
    try {
      await adminApi.resolveAlert(id)
      // Update local state optimistically
      if (riskAlerts.value?.alerts) {
        const alert = riskAlerts.value.alerts.find(a => a.id === id)
        if (alert) alert.status = 'resolved'
      }
      return { ok: true }
    } catch (e) {
      const msg = e.status === 403
        ? '权限不足：仅管理员可处理告警'
        : e.message || '操作失败'
      console.error('Resolve alert error:', msg)
      return { ok: false, error: msg }
    }
  }

  return {
    summary, trend, sentiment, categories, priority, rootCause, insights, riskAlerts, hotPosts,
    posts, postsTotal, postsPage, postsTotalPages,
    loading, error,
    fetchAll, fetchPosts, fetchPostById, markAlertResolved
  }
})
