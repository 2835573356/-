<script setup>
import DonutChart from '@/components/charts/DonutChart.vue'
import Chip from '@/components/common/Chip.vue'
import { computed } from 'vue'

const props = defineProps({
  sentiment: {
    type: Object,
    required: true
    // backend shape: { items:[{name,value,percent,color}], dominant:'negative'|'neutral'|'positive', description }
  }
})

defineEmits(['highlight:sentiment'])

// Map English dominant value -> Chinese label
const dominantLabel = computed(() => {
  const map = { negative: '消极', neutral: '中性', positive: '积极' }
  return map[props.sentiment.dominant] || props.sentiment.dominant || ''
})

const items = computed(() => props.sentiment.items || [])

const total = computed(() => items.value.reduce((sum, i) => sum + (i.value || 0), 0))

const hasData = computed(() => total.value > 0)

const donutData = computed(() =>
  items.value.map(item => ({ name: item.name, value: item.value, color: item.color }))
)

const dominantItem = computed(() => items.value.find(i => i.name === dominantLabel.value))

const centerValue = computed(() => {
  if (!dominantItem.value || total.value === 0) return ''
  return ((dominantItem.value.value / total.value) * 100).toFixed(1) + '%'
})

const dominantChipType = computed(() => {
  const map = { '消极': 'danger', '中性': 'warn', '积极': 'ok' }
  return map[dominantLabel.value] || 'default'
})

function getDotColor(name) {
  const map = { '消极': 'var(--c-danger)', '中性': 'var(--c-warn)', '积极': 'var(--c-ok)' }
  return map[name] || 'var(--t-tertiary)'
}

function getBarColor(name) {
  const map = {
    '消极': 'linear-gradient(90deg, #ef4444, #f87171)',
    '中性': 'linear-gradient(90deg, #f59e0b, #fbbf24)',
    '积极': 'linear-gradient(90deg, #10b981, #34d399)'
  }
  return map[name] || 'linear-gradient(90deg, #3b82f6, #60a5fa)'
}

function pct(item) {
  return total.value > 0 ? ((item.value / total.value) * 100).toFixed(1) : '0.0'
}
</script>

<template>
  <div class="glass" style="padding: 24px; height: 100%;">
    <!-- Header -->
    <div style="margin-bottom: 16px;">
      <div class="section-sub t-tertiary" style="margin-bottom: 2px;">SENTIMENT</div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="section-title t-primary" style="font-size: 20px;">舆情情绪</span>
        <Chip v-if="hasData && dominantLabel" :type="dominantChipType">{{ dominantLabel }}主导</Chip>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!hasData" class="empty-state">
      <div style="font-size: 40px; margin-bottom: 8px;">🫧</div>
      <div class="t-secondary" style="font-size: 14px; font-weight: 500;">当前周期暂无情绪数据</div>
      <div class="t-tertiary" style="font-size: 12px; margin-top: 4px;">试试切换数据周期</div>
    </div>

    <!-- Donut Chart + Sentiment Bars -->
    <template v-else>
      <div style="display: flex; align-items: center; gap: 24px; margin-bottom: 16px;">
        <DonutChart
          v-if="donutData.length"
          :data="donutData"
          :center-text="dominantLabel + '主导'"
          :center-value="centerValue"
        />

        <div style="flex: 1; display: flex; flex-direction: column; gap: 14px;">
          <div
            v-for="item in items"
            :key="item.name"
            style="cursor: pointer;"
            @click="$emit('highlight:sentiment', item)"
          >
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span style="width: 8px; height: 8px; border-radius: 50%; display: inline-block;" :style="{ background: getDotColor(item.name) }"></span>
                <span class="t-secondary" style="font-size: 13px; font-weight: 500;">{{ item.name }}</span>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="t-primary" style="font-size: 14px; font-weight: 600; font-variant-numeric: tabular-nums;">{{ item.value?.toLocaleString() }}</span>
                <span class="t-tertiary" style="font-size: 12px; font-variant-numeric: tabular-nums;">{{ pct(item) }}%</span>
              </div>
            </div>
            <div class="bar-track" style="height: 6px;">
              <div class="bar-fill" :style="{ width: pct(item) + '%', background: getBarColor(item.name) }"></div>
            </div>
          </div>
        </div>
      </div>

      <p v-if="sentiment.description" class="t-secondary" style="font-size: 13px; line-height: 1.6; padding: 0 4px;">
        {{ sentiment.description }}
      </p>
    </template>
  </div>
</template>
