<script setup>
defineProps({
  clickable: { type: Boolean, default: true },
  risk: { type: String, default: '' } // '', 'danger', 'amber'
})
</script>

<template>
  <div
    class="mini-card"
    :class="{
      'clickable': clickable,
      'risk-mini': risk === 'danger',
      'risk-mini-amber': risk === 'amber'
    }"
  >
    <slot />
  </div>
</template>
