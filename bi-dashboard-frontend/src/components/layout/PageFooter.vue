<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <footer class="text-center text-xs t-tertiary mt-10 pb-6">
    <div>© 2026 Community Operations Intelligence · Generated from 314 records · Liquid Glass × Bento Grid</div>
    <div class="mt-1">最后刷新时间: {{ appStore.lastRefreshTime || '—' }}</div>
  </footer>
</template>
