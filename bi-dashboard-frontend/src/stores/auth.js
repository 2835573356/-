import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isAuthenticated = ref(!!token.value)

  async function login(username, password) {
    const result = await authApi.login(username, password)
    // Backend returns { token: "...", user: {...} }
    token.value = result.token || result.access_token
    user.value = result.user || { username, role: 'viewer' }
    isAuthenticated.value = true
    localStorage.setItem('token', token.value)
    if (user.value.display_name || user.value.displayName) {
      localStorage.setItem('user', JSON.stringify(user.value))
    }
    return result
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      const u = await authApi.fetchCurrentUser()
      user.value = u
    } catch {
      // Token expired or invalid
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    // Optionally notify backend
    authApi.logout().catch(() => {})
  }

  // Try to restore user from localStorage on init
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    try { user.value = JSON.parse(savedUser) } catch { /* ignore */ }
  }

  return { user, token, isAuthenticated, login, logout, fetchCurrentUser }
})
