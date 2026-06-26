<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authStore.login(username.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center relative z-10 px-6">
    <div class="glass p-8 md:p-10 w-full max-w-md">
      <div class="text-center mb-8">
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
             style="background: linear-gradient(135deg, #3b82f6, #6366f1); box-shadow: 0 8px 24px rgba(59,130,246,0.35);">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-5"/>
          </svg>
        </div>
        <h1 class="text-2xl font-semibold t-primary">影刀社区 · 运营数据看板</h1>
        <p class="text-sm t-tertiary mt-2">Community Operations Intelligence</p>
      </div>

      <div v-if="error" class="p-3 rounded-xl mb-4 text-sm" style="background:var(--c-danger-soft);color:#991b1b;">
        ⚠️ {{ error }}
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="text-xs t-tertiary block mb-1">用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" autocomplete="username"
                 class="w-full px-4 py-3 rounded-xl border text-sm" style="outline:none;background:rgba(255,255,255,0.6);">
        </div>
        <div>
          <label class="text-xs t-tertiary block mb-1">密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password"
                 class="w-full px-4 py-3 rounded-xl border text-sm" style="outline:none;background:rgba(255,255,255,0.6);">
        </div>
        <button type="submit" class="btn btn-primary w-full justify-center py-3 text-base" :disabled="loading">
          {{ loading ? '登录中...' : '🔐 登录' }}
        </button>
      </form>

      <p class="text-xs t-tertiary text-center mt-6">
        默认管理员账号：admin / admin123
      </p>
    </div>
  </div>
</template>
