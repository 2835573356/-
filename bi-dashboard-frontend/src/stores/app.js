import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const theme = ref(localStorage.getItem('theme') || 'light')
  const isDark = computed(() => theme.value === 'dark')
  const lastRefreshTime = ref('')
  const dateRange = ref({ start: '2026-06-20', end: '2026-06-25' })
  const isOnline = ref(true)

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    document.body.classList.toggle('dark', theme.value === 'dark')
  }

  function initTheme() {
    document.body.classList.toggle('dark', theme.value === 'dark')
  }

  function setDateRange(start, end) {
    dateRange.value = { start, end }
  }

  function refreshData() {
    lastRefreshTime.value = new Date().toLocaleString('zh-CN')
  }

  return { theme, isDark, lastRefreshTime, dateRange, isOnline, toggleTheme, initTheme, setDateRange, refreshData }
})
