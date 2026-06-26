<script setup>
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'

const appStore = useAppStore()
const { toasts } = useToast()

onMounted(() => {
  appStore.initTheme()
})

function toastIcon(type) {
  switch (type) {
    case 'success': return '✅'
    case 'error': return '❌'
    case 'warn': return '⚠️'
    default: return 'ℹ️'
  }
}
</script>

<template>
  <!-- Ambient orbs -->
  <div class="ambient-orb orb-1"></div>
  <div class="ambient-orb orb-2"></div>
  <div class="ambient-orb orb-3"></div>
  <div class="ambient-orb orb-4"></div>

  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <!-- Global Toast Container -->
  <Teleport to="body">
    <div class="toast-container">
      <transition-group name="toast-fade">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="'toast-' + toast.type"
        >
          <span class="toast-icon">{{ toastIcon(toast.type) }}</span>
          <span class="toast-message">{{ toast.message }}</span>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>
