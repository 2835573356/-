import api from './index'

/** 告警列表 */
export function fetchAlerts(params = {}) {
  return api.get('/admin/alerts', { params })
}

/** 标记告警已解决 */
export function resolveAlert(id) {
  return api.put(`/admin/alerts/${id}/resolve`)
}

/** 忽略告警 */
export function ignoreAlert(id) {
  return api.put(`/admin/alerts/${id}/ignore`)
}

/** 手动触发数据刷新 */
export function refreshData(date) {
  return api.post('/admin/data/refresh', null, { params: { target_date: date } })
}

/** 批量刷新数据 */
export function refreshDataRange(startDate, endDate) {
  return api.post('/admin/data/refresh-range', null, { params: { start_date: startDate, end_date: endDate } })
}

/** 导出看板报告 */
export function exportDashboard(date) {
  return api.get('/export/dashboard', { params: { target_date: date } })
}
