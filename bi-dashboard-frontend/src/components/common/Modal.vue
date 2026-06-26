<script setup>
import { watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '详情' }
})

const emit = defineEmits(['close'])

watch(() => props.show, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})

function onOverlayClick(e) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <div v-if="show" class="modal-overlay" @click="onOverlayClick">
    <div class="modal-content" @click.stop>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h3 style="font-size:18px;font-weight:600;" class="t-primary">{{ title }}</h3>
        <span class="chip chip-clickable" @click="emit('close')" style="font-size:18px;">✕</span>
      </div>
      <slot />
    </div>
  </div>
</template>
