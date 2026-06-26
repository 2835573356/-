import api from './index'

/** 上传 Excel 文件，触发影刀异步流程（立即返回 running 记录） */
export function uploadExcel(file) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 90000
  })
}

/** 轮询上传处理进度 */
export function fetchUploadStatus(id) {
  return api.get(`/upload/${id}/status`)
}

/** 最近的上传记录 */
export function fetchUploadRecords(limit = 20) {
  return api.get('/upload/records', { params: { limit } })
}

/** 单条上传记录详情 */
export function fetchUploadRecord(id) {
  return api.get(`/upload/records/${id}`)
}

/** 删除单条上传记录 */
export function deleteUploadRecord(id) {
  return api.delete(`/upload/records/${id}`)
}
