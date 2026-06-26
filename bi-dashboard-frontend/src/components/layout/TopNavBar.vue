<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const refreshing = ref(false)

function onRefresh() {
  if (refreshing.value) return
  refreshing.value = true
  emit('refresh')
  // Spin for at least one animation cycle so the click is acknowledged
  setTimeout(() => { refreshing.value = false }, 800)
}

defineProps({
  sampleCount: { type: Number, default: 0 }
})

const emit = defineEmits(['refresh', 'open-date-picker', 'export-dashboard'])

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()
const dropdownOpen = ref(false)

const navLinks = [
  { path: '/dashboard', label: '📊 看板总览' },
  { path: '/trend', label: '📈 趋势分析' },
  { path: '/issues', label: '🔍 问题分析' },
  { path: '/risk', label: '⚠️ 风险中心' },
  { path: '/posts', label: '📋 帖子管理' }
]

function navigate(path) {
  router.push(path)
  dropdownOpen.value = false
}

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function toggleTheme() {
  appStore.toggleTheme()
  dropdownOpen.value = false
}

function closeDropdown() {
  dropdownOpen.value = false
}

function handleLogout() {
  authStore.logout()
  dropdownOpen.value = false
  router.push('/login')
}
</script>

<template>
  <nav class="top-nav sticky top-0 z-50 px-6 md:px-12 py-4 md:py-5">
    <div class="max-w-[1440px] mx-auto flex items-center justify-between gap-4">
      <div class="flex items-center gap-4 flex-shrink-0">
        <div class="w-10 h-10 rounded-2xl flex items-center justify-center cursor-pointer"
             style="background: linear-gradient(135deg, #3b82f6, #6366f1); box-shadow: 0 8px 24px rgba(59,130,246,0.35), inset 0 1px 0 rgba(255,255,255,0.5);"
             @click="navigate('/dashboard')" title="返回首页">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-5"/>
          </svg>
        </div>
        <div style="cursor:pointer;" @click="navigate('/dashboard')">
          <div class="text-lg md:text-xl font-semibold tracking-wide t-primary">影刀社区 · 运营数据看板</div>
          <div class="text-xs t-tertiary">Community Operations Intelligence · Enterprise Edition</div>
        </div>
      </div>

      <!-- Desktop nav links -->
      <div class="hidden md:flex items-center gap-2 lg:gap-3 desktop-nav-links flex-1 justify-center px-4">
        <button
          v-for="link in navLinks" :key="link.path"
          class="nav-link"
          :class="{ active: route.path === link.path }"
          @click="navigate(link.path)"
        >{{ link.label }}</button>
      </div>

      <div class="flex items-center gap-3 md:gap-4">
        <span class="hidden lg:flex items-center gap-3 xl:gap-4">
          <span class="chip chip-info chip-clickable status-chip" @click="$emit('open-date-picker')" title="点击切换数据周期">
            📅 {{ appStore.dateRange.start.replace(/-/g, '/') }} — {{ appStore.dateRange.end.replace(/-/g, '/') }}
          </span>
          <span class="chip status-chip">📊 总帖子 {{ sampleCount.toLocaleString() }} 条</span>
          <span class="nav-divider"></span>
        </span>
        <span class="chip chip-clickable refresh-btn" :class="{ spinning: refreshing }" @click="onRefresh" title="刷新数据">🔄</span>
        <span class="chip chip-clickable" @click="toggleTheme" title="切换主题">{{ appStore.isDark ? '☀️' : '🌓' }}</span>
        <div class="dropdown-container">
          <div class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold cursor-pointer"
               style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;"
               @click.stop="toggleDropdown" title="用户菜单">
            管
          </div>
          <div v-if="dropdownOpen" class="dropdown-menu" @click.stop>
            <button class="dropdown-item" style="color:#ef4444;" @click="handleLogout">🚪 退出登录</button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
