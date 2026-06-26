<script setup>
defineProps({
  percent: { type: Number, default: 0 },
  color: { type: String, default: 'linear-gradient(90deg, #3b82f6, #60a5fa)' }
})
</script>

<template>
  <div class="bar-track">
    <div class="bar-fill" :style="{ width: percent + '%', background: color }"></div>
  </div>
</template>
