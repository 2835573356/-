<script setup>
import LineChart from '@/components/charts/LineChart.vue'

const props = defineProps({
  trend: {
    type: Object,
    required: true
    // shape: { dates, series, anomaly_tags, description }
  }
})

defineEmits(['highlight:series'])
</script>

<template>
  <div class="glass" style="padding: 24px;">
    <!-- Header -->
    <div style="margin-bottom: 16px;">
      <div class="section-sub t-tertiary" style="margin-bottom: 2px;">TREND &amp; ANOMALY</div>
      <div class="section-title t-primary" style="font-size: 20px;">趋势与异常</div>
    </div>

    <!-- Anomaly Tags -->
    <div v-if="trend.anomaly_tags && trend.anomaly_tags.length" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;">
      <span
        v-for="(tag, idx) in trend.anomaly_tags"
        :key="idx"
        class="chip chip-clickable"
        :class="{
          'chip-danger': tag.type === 'danger',
          'chip-warn': tag.type === 'warn'
        }"
        @click="$emit('highlight:series', tag)"
      >
        {{ tag.label }}
      </span>
    </div>

    <!-- Line Chart -->
    <LineChart
      :x-axis-data="trend.dates"
      :series-data="trend.series"
      :show-data-zoom="false"
    />

    <!-- Description -->
    <p
      v-if="trend.description"
      class="t-secondary"
      style="font-size: 13px; line-height: 1.6; margin-top: 16px; padding: 0 4px;"
    >{{ trend.description }}</p>
  </div>
</template>
