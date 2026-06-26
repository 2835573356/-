<script setup>
import { watch, onMounted } from 'vue'
import { useChart } from '@/composables/useChart'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'

const props = defineProps({
  xAxisData: { type: Array, default: () => [] },
  seriesData: { type: Array, default: () => [] },
  showDataZoom: { type: Boolean, default: false }
})

const emit = defineEmits(['chart-ready'])

const { chartRef, setOption, getInstance, resize } = useChart()
const appStore = useAppStore()

function getTooltipStyle() {
  const isDark = appStore.isDark
  return {
    backgroundColor: isDark ? 'rgba(30,41,59,0.95)' : 'rgba(255,255,255,0.92)',
    borderColor: isDark ? 'rgba(71,85,105,0.8)' : 'rgba(226,232,240,1)',
    borderWidth: 1,
    textStyle: { color: isDark ? '#e2e8f0' : '#0f172a', fontSize: 12 },
    extraCssText: 'backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); border-radius: 12px; box-shadow: 0 8px 24px rgba(15,23,42,0.12);'
  }
}

function buildOption() {
  const isDark = appStore.isDark
  const cText = isDark ? '#e2e8f0' : '#0f172a'
  const cText2 = isDark ? '#94a3b8' : '#475569'
  const cText3 = isDark ? '#64748b' : '#94a3b8'
  const cAxis = isDark ? 'rgba(100,116,139,0.3)' : 'rgba(148,163,184,0.25)'

  const series = props.seriesData.map(s => ({
    name: s.name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: s.name === 'Bug / 系统异常' ? 7 : 6,
    data: s.data,
    lineStyle: { width: s.name === 'Bug / 系统异常' ? 3 : 2.5, color: s.color },
    itemStyle: { color: s.color, borderColor: '#fff', borderWidth: 1.5 },
    ...(s.name === 'Bug / 系统异常' ? {
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(239,68,68,0.28)' },
          { offset: 1, color: 'rgba(239,68,68,0)' }
        ])
      },
      markPoint: s.anomaly ? {
        symbol: 'pin', symbolSize: 50,
        itemStyle: { color: '#ef4444' },
        label: { color: '#fff', fontSize: 11, fontWeight: 600 },
        data: [{ name: '峰值', value: s.anomaly.peak_value, xAxis: 4, yAxis: s.anomaly.peak_value }]
      } : undefined
    } : {})
  }))

  const option = {
    grid: { left: 36, right: 24, top: 36, bottom: props.showDataZoom ? 60 : 36 },
    tooltip: { trigger: 'axis', ...getTooltipStyle() },
    legend: {
      data: props.seriesData.map(s => s.name),
      textStyle: { color: cText2, fontSize: 11 },
      top: 0, right: 0, itemGap: 14, icon: 'circle', itemWidth: 8, itemHeight: 8
    },
    xAxis: {
      type: 'category', data: props.xAxisData,
      axisLine: { lineStyle: { color: cAxis } },
      axisTick: { show: false },
      axisLabel: { color: cText3, fontSize: 11 }
    },
    yAxis: {
      type: 'value', axisLine: { show: false },
      splitLine: { lineStyle: { color: cAxis, type: 'dashed' } },
      axisLabel: { color: cText3, fontSize: 11 }
    },
    series
  }

  if (props.showDataZoom) {
    option.dataZoom = [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, height: 20, bottom: 10 }
    ]
  }

  return option
}

watch(() => [props.seriesData, props.xAxisData, appStore.isDark], () => {
  setOption(buildOption())
}, { deep: true })

onMounted(() => {
  setOption(buildOption())
  emit('chart-ready', getInstance())
})
</script>

<template>
  <div ref="chartRef" style="width:100%;height:320px;"></div>
</template>
