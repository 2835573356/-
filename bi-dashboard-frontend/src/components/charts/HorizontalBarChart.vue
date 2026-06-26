<script setup>
import { watch, onMounted, computed, nextTick } from 'vue'
import { useChart } from '@/composables/useChart'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  total: { type: Number, default: 314 }
})

const emit = defineEmits(['bar-click'])
const { chartRef, setOption, getInstance, resize } = useChart()
const appStore = useAppStore()

// Adapt height to row count so the chart isn't cramped or empty.
const chartHeight = computed(() => {
  const n = props.categories.length || 1
  return Math.min(360, Math.max(140, n * 46 + 40))
})

function buildOption() {
  const isDark = appStore.isDark
  const cText = isDark ? '#e2e8f0' : '#0f172a'
  const cText2 = isDark ? '#94a3b8' : '#475569'
  const cText3 = isDark ? '#64748b' : '#94a3b8'
  const cAxis = isDark ? 'rgba(100,116,139,0.3)' : 'rgba(148,163,184,0.25)'
  const tooltipBg = isDark ? 'rgba(30,41,59,0.95)' : 'rgba(255,255,255,0.92)'
  const tooltipBorder = isDark ? 'rgba(71,85,105,0.8)' : 'rgba(226,232,240,1)'

  const names = props.categories.map(c => c.name).reverse()
  const reversed = [...props.categories].reverse()

  return {
    grid: { left: 130, right: 60, top: 16, bottom: 16 },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: tooltipBg, borderColor: tooltipBorder, borderWidth: 1,
      textStyle: { color: cText, fontSize: 12 },
      extraCssText: 'backdrop-filter: blur(20px); border-radius: 12px;',
      formatter: (p) => {
        const o = p[0]
        return `${o.name}<br/>${o.value} 条 · ${(o.value / props.total * 100).toFixed(1)}%`
      }
    },
    xAxis: {
      type: 'value', axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: cAxis, type: 'dashed' } },
      axisLabel: { color: cText3, fontSize: 11 }
    },
    yAxis: {
      type: 'category', data: names,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: cText, fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: reversed.map(c => ({
        value: c.count,
        itemStyle: {
          borderRadius: [0, 10, 10, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: c.color + '99' },
            { offset: 1, color: c.color }
          ])
        }
      })),
      barWidth: 16,
      label: {
        show: true, position: 'right', color: cText2, fontSize: 11,
        formatter: (p) => `${p.value} · ${(p.value / props.total * 100).toFixed(1)}%`
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } }
    }]
  }
}

watch(() => [props.categories, appStore.isDark], async () => {
  setOption(buildOption())
  await nextTick()
  resize()
}, { deep: true })

onMounted(() => {
  setOption(buildOption())
  const inst = getInstance()
  if (inst) {
    inst.on('click', (params) => {
      if (params.componentType === 'series') {
        emit('bar-click', params.name)
      }
    })
  }
})
</script>

<template>
  <div ref="chartRef" :style="{ width: '100%', height: chartHeight + 'px' }"></div>
</template>
