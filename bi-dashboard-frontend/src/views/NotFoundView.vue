<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center relative z-10 px-6">
    <div class="glass p-10 text-center max-w-md">
      <div style="font-size:72px;margin-bottom:16px;">🔮</div>
      <h1 class="text-3xl font-semibold t-primary mb-2">404</h1>
      <p class="t-secondary mb-6">页面未找到，或已被移除。</p>
      <button class="btn btn-primary" @click="router.push('/dashboard')">← 返回看板首页</button>
    </div>
  </div>
</template>
