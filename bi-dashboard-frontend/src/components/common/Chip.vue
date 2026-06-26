<script setup>
defineProps({
  type: { type: String, default: 'default' },
  label: { type: String, default: '' },
  clickable: { type: Boolean, default: false }
})
</script>

<template>
  <span
    class="chip"
    :class="{
      'chip-clickable': clickable,
      'chip-danger': type === 'danger',
      'chip-warn': type === 'warn',
      'chip-ok': type === 'ok',
      'chip-info': type === 'info'
    }"
  >
    <slot />
    <span v-if="label">{{ label }}</span>
  </span>
</template>
