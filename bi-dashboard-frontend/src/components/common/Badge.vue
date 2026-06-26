<script setup>
defineProps({
  priority: { type: String, default: 'P2' }
})
</script>

<template>
  <span
    class="px-2.5 py-1 rounded-lg text-xs font-semibold"
    :class="{
      'badge-p0': priority === 'P0',
      'badge-p1': priority === 'P1',
      'badge-p2': priority === 'P2'
    }"
  >
    <slot>{{ priority }}</slot>
  </span>
</template>
