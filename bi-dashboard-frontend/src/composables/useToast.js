import { ref } from 'vue'

/** Global reactive toast state — import and use from anywhere */
const toasts = ref([])
let _id = 0

/**
 * Show a toast notification.
 * @param {string} message - Toast text
 * @param {'success'|'error'|'warn'|'info'} [type='info'] - Toast style
 * @param {number} [duration=4000] - Auto-dismiss ms (0 = sticky)
 * @returns {number} toast id
 */
export function showToast(message, type = 'info', duration = 4000) {
  const id = ++_id
  toasts.value.push({ id, message, type, duration })
  if (duration > 0) {
    setTimeout(() => dismissToast(id), duration)
  }
  return id
}

/** Remove a specific toast by id */
export function dismissToast(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

/**
 * Vue composable that returns reactive toast state.
 * Use in App.vue: const { toasts } = useToast()
 */
export function useToast() {
  return { toasts }
}
