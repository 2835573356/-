import api from './index'

/** 4.2.1 看板总览 */
export function fetchSummary(date) {
  return api.get('/dashboard/summary', { params: { target_date: date } })
}

/** 4.2.2 趋势数据 */
export function fetchTrend(start, end) {
  return api.get('/dashboard/trend', { params: { start, end } })
}

/** 4.2.3 情绪分布 */
export function fetchSentiment(date) {
  return api.get('/dashboard/sentiment', { params: { target_date: date } })
}

/** 4.2.4 问题分类 */
export function fetchCategories(date) {
  return api.get('/dashboard/categories', { params: { target_date: date } })
}

/** 4.2.5 热门帖子 */
export function fetchHotPosts(dateOrRange, limit = 8) {
  const params = typeof dateOrRange === 'object'
    ? { target_date: dateOrRange.end, start: dateOrRange.start, end: dateOrRange.end, limit }
    : { target_date: dateOrRange, limit }
  return api.get('/dashboard/hot-posts', { params })
}

/** 优先级分布 */
export function fetchPriority(dateOrRange) {
  const params = typeof dateOrRange === 'object'
    ? { target_date: dateOrRange.end, start: dateOrRange.start, end: dateOrRange.end }
    : { target_date: dateOrRange }
  return api.get('/dashboard/priority', { params })
}

/** 4.2.6 根因分析 */
export function fetchRootCause(date) {
  return api.get('/dashboard/root-cause', { params: { target_date: date } })
}

/** 4.2.7 业务洞察 */
export function fetchInsights(date) {
  return api.get('/dashboard/insights', { params: { target_date: date } })
}

/** 4.2.8 风险告警 */
export function fetchRiskAlerts(date) {
  return api.get('/dashboard/risk-alerts', { params: { target_date: date } })
}

/** 健康度评分详情 */
export function fetchHealthScore(date) {
  return api.get('/dashboard/health-score', { params: { target_date: date } })
}
