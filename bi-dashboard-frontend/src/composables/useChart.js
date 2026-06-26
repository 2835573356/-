import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

export function useChart(options = {}) {
  const chartRef = ref(null)
  let chartInstance = null

  function initChart() {
    if (chartRef.value) {
      chartInstance = echarts.init(chartRef.value)
      if (options.option) {
        chartInstance.setOption(options.option)
      }
    }
  }

  function setOption(option, opts = {}) {
    if (chartInstance && !chartInstance.isDisposed()) {
      chartInstance.setOption(option, { notMerge: true, ...opts })
    }
  }

  function resize() {
    if (chartInstance && !chartInstance.isDisposed()) {
      chartInstance.resize()
    }
  }

  function getInstance() {
    return chartInstance
  }

  function dispose() {
    if (chartInstance && !chartInstance.isDisposed()) {
      chartInstance.dispose()
    }
  }

  onMounted(() => {
    initChart()
    window.addEventListener('resize', resize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    dispose()
  })

  return { chartRef, setOption, resize, getInstance, initChart }
}
