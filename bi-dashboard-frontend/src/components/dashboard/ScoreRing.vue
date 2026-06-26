<script setup>
import { computed } from 'vue'

const props = defineProps({
  score: { type: Number, required: true }
})

const R = 78
const CIRC = 2 * Math.PI * R // ≈ 490.09

const dashOffset = computed(() => {
  const s = Math.max(0, Math.min(100, props.score || 0))
  return CIRC * (1 - s / 100)
})

// Status color follows the score band
const statusColor = computed(() => {
  if (props.score >= 80) return '#10b981'
  if (props.score >= 60) return '#f59e0b'
  return '#ef4444'
})

const statusLabel = computed(() => {
  if (props.score >= 80) return '健康'
  if (props.score >= 60) return '预警'
  return '高风险'
})
</script>

<template>
  <div class="score-ring">
    <svg width="180" height="180" viewBox="0 0 180 180">
      <!-- Rotate ONLY the arc group so the gauge starts at 12 o'clock.
           Previously the whole <svg> was rotated -90deg, which tilted the number text too. -->
      <g transform="rotate(-90 90 90)">
        <circle class="track" cx="90" cy="90" :r="R" fill="none" stroke-width="14" />
        <circle
          class="progress"
          cx="90"
          cy="90"
          :r="R"
          fill="none"
          stroke-width="14"
          stroke-linecap="round"
          :stroke-dasharray="CIRC"
          :stroke-dashoffset="dashOffset"
          :style="{ stroke: statusColor }"
        />
      </g>

      <text
        x="90" y="82"
        text-anchor="middle" dominant-baseline="middle"
        fill="currentColor" font-size="40" font-weight="700"
        class="t-primary"
      >{{ score }}</text>
      <text
        x="90" y="108"
        text-anchor="middle" dominant-baseline="middle"
        font-size="12" font-weight="600"
        :fill="statusColor"
      >{{ statusLabel }} · /100</text>
    </svg>
  </div>
</template>
