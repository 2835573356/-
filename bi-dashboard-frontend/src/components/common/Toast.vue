<script setup>
import { ref } from 'vue'

const toasts = ref([])
let id = 0

function show(message, type = 'info') {
  const toastId = ++id
  toasts.value.push({ id: toastId, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== toastId)
  }, 3000)
}

function remove(toastId) {
  toasts.value = toasts.value.filter(t => t.id !== toastId)
}

defineExpose({ show })
</script>

<template>
  <div class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast"
      :class="{
        'toast-success': toast.type === 'success',
        'toast-error': toast.type === 'error',
        'toast-warn': toast.type === 'warn',
        'toast-info': toast.type === 'info'
      }"
      @click="remove(toast.id)"
    >
      {{ toast.message }}
    </div>
  </div>
</template>
