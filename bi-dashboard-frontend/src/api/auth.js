import api from './index'

/** 用户登录 */
export function login(username, password) {
  return api.post('/auth/login', { username, password })
}

/** 用户登出 */
export function logout() {
  return api.post('/auth/logout')
}

/** 获取当前用户信息 */
export function fetchCurrentUser() {
  return api.get('/auth/me')
}
