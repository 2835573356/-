<script setup>
import Chip from '@/components/common/Chip.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    required: true
    // shape: { change_type, change_percent, description, bar_percent }
  }
})

defineEmits(['click'])

const chipType = computed(() => {
  const map = { surge: 'danger', increase: 'warn', stable: 'info', decrease: 'ok' }
  return map[props.data.change_type] || 'default'
})

const chipLabel = computed(() => {
  const map = { surge: '突增', increase: '上升', stable: '持平', decrease: '下降' }
  return map[props.data.change_type] || props.data.change_type
})

const barColor = computed(() => {
  const map = {
    danger: 'linear-gradient(90deg, #ef4444, #f87171)',
    warn: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
    ok: 'linear-gradient(90deg, #10b981, #34d399)',
    info: 'linear-gradient(90deg, #3b82f6, #60a5fa)'
  }
  return map[chipType.value] || 'linear-gradient(90deg, #3b82f6, #60a5fa)'
})
</script>

<template>
  <div class="glass specular" style="padding: 24px; cursor: pointer;" @click="$emit('click')">
    <div class="section-sub t-tertiary" style="margin-bottom: 8px;">今日 vs 昨日</div>

    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
      <Chip :type="chipType">{{ chipLabel }}</Chip>
      <span class="t-danger" style="font-size: 28px; font-weight: 700;">{{ data.change_percent }}%</span>
    </div>

    <p class="t-secondary" style="font-size: 13px; line-height: 1.6; margin-bottom: 12px;">{{ data.description }}</p>

    <ProgressBar :percent="data.bar_percent" :color="barColor" />
  </div>
</template>
