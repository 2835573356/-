import api, { sentimentToEnglish } from './index'

/** 帖子列表（分页+筛选） */
export function fetchPosts(params = {}) {
  const p = { ...params }
  // Convert sentiment to English if it's Chinese
  if (p.sentiment) {
    p.sentiment = sentimentToEnglish(p.sentiment)
  }
  return api.get('/posts', { params: p })
}

/** 帖子详情 */
export function fetchPostById(id) {
  return api.get(`/posts/${id}`)
}

/** 新增帖子 */
export function createPost(data) {
  return api.post('/posts', data)
}

/** 更新帖子 */
export function updatePost(id, data) {
  return api.put(`/posts/${id}`, data)
}

/** 删除帖子 */
export function deletePost(id) {
  return api.delete(`/posts/${id}`)
}

/** 获取所有分类列表 */
export function fetchCategoriesList() {
  return api.get('/posts/categories-list')
}
