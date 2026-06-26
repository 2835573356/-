<script setup>
import { watch, onMounted } from 'vue'
import { useChart } from '@/composables/useChart'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'

const props = defineProps({
  data: { type: Array, default: () => [] },
  centerText: { type: String, default: '消极主导' },
  centerValue: { type: String, default: '51.0%' }
})

const { chartRef, setOption } = useChart()
const appStore = useAppStore()

function buildOption() {
  const isDark = appStore.isDark
  const tooltipBg = isDark ? 'rgba(30,41,59,0.95)' : 'rgba(255,255,255,0.92)'
  const tooltipBorder = isDark ? 'rgba(71,85,105,0.8)' : 'rgba(226,232,240,1)'
  const cText = isDark ? '#e2e8f0' : '#0f172a'

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      borderWidth: 1,
      textStyle: { color: cText, fontSize: 12 },
      extraCssText: 'backdrop-filter: blur(20px); border-radius: 12px;',
      formatter: '{b}<br/>{c} 条 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['62%', '88%'],
      avoidLabelOverlap: false,
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
      label: { show: false },
      labelLine: { show: false },
      emphasis: { scale: true, scaleSize: 10, focus: 'self' },
      data: props.data.map(d => ({
        value: d.value,
        name: d.name,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: d.color },
            { offset: 1, color: d.color + 'cc' }
          ])
        }
      }))
    }],
    graphic: [
      { type: 'text', left: 'center', top: '42%',
        style: { text: props.centerText, fill: cText, fontSize: 14, fontWeight: 600, textAlign: 'center' } },
      { type: 'text', left: 'center', top: '56%',
        style: { text: props.centerValue, fill: '#dc2626', fontSize: 18, fontWeight: 700, textAlign: 'center' } }
    ]
  }
}

watch(() => [props.data, appStore.isDark], () => {
  setOption(buildOption())
}, { deep: true })

onMounted(() => {
  setOption(buildOption())
})
</script>

<template>
  <div ref="chartRef" style="width:180px;height:180px;"></div>
</template>
