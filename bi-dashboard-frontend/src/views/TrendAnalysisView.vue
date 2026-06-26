<script setup>
import { computed, onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useAppStore } from '@/stores/app'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'
import LineChart from '@/components/charts/LineChart.vue'

const store = useDashboardStore()
const appStore = useAppStore()

function fetchTrendPageData() {
  return store.fetchAll({
    start: appStore.dateRange.start,
    end: appStore.dateRange.end
  })
}

const totalByDate = computed(() => {
  const dates = store.trend?.dates || []
  const series = store.trend?.series || []
  return dates.map((date, index) => ({
    index,
    date,
    total: series.reduce((sum, item) => sum + Number(item.data?.[index] || 0), 0)
  }))
})

const activeDateRows = computed(() => totalByDate.value.filter(item => item.total > 0))

const anomalyItems = computed(() => {
  const trend = store.trend
  if (!trend?.series?.length) return []

  return trend.series
    .map(item => {
      const data = item.data || []
      const peakValue = data.length ? Math.max(...data) : 0
      const peakIndex = data.indexOf(peakValue)
      const activeIndexes = data
        .map((value, index) => ({ value: Number(value || 0), index }))
        .filter(point => point.value > 0)
      const latestPoint = activeIndexes.at(-1) || { value: 0, index: data.length - 1 }
      const previousPoint = activeIndexes.at(-2) || null
      const latest = latestPoint.value
      const previous = previousPoint?.value || 0
      const changePercent = previous > 0
        ? Number((((latest - previous) / previous) * 100).toFixed(1))
        : 0

      return {
        name: item.name,
        color: item.color,
        peakDate: trend.dates?.[peakIndex] || '-',
        peakValue,
        latestDate: trend.dates?.[latestPoint.index] || '-',
        previousDate: previousPoint ? trend.dates?.[previousPoint.index] || '-' : '-',
        latest,
        changePercent,
        anomaly: item.anomaly
      }
    })
    .sort((a, b) => {
      const aScore = a.anomaly ? 1 : 0
      const bScore = b.anomaly ? 1 : 0
      return bScore - aScore || Math.abs(b.changePercent) - Math.abs(a.changePercent)
    })
    .slice(0, 5)
})

const trendStats = computed(() => {
  const totals = totalByDate.value
  const active = activeDateRows.value
  const latestRow = active.at(-1) || totals.at(-1) || { date: '-', total: 0 }
  const previousRow = active.at(-2) || null
  const latest = latestRow.total
  const previous = previousRow?.total || 0
  const peak = totals.reduce((max, item) => item.total > max.total ? item : max, { date: '-', total: 0 })
  const changePercent = previous > 0
    ? Number((((latest - previous) / previous) * 100).toFixed(1))
    : 0

  return {
    latest,
    previous,
    latestDate: latestRow.date,
    previousDate: previousRow?.date || '-',
    peak,
    changePercent,
    anomalyCount: anomalyItems.value.filter(item => item.anomaly || Math.abs(item.changePercent) >= 50).length
  }
})

const comparisonRows = computed(() => {
  const series = store.trend?.series || []
  const activeIndexes = activeDateRows.value.map(item => item.index)
  const midpoint = Math.max(1, Math.floor(activeIndexes.length / 2))
  const previousIndexes = activeIndexes.slice(0, midpoint)
  const currentIndexes = activeIndexes.slice(midpoint)

  return series
    .map(item => {
      const data = item.data || []
      const previousTotal = previousIndexes.reduce((sum, index) => sum + Number(data[index] || 0), 0)
      const currentTotal = currentIndexes.reduce((sum, index) => sum + Number(data[index] || 0), 0)
      const changePercent = previousTotal > 0
        ? Number((((currentTotal - previousTotal) / previousTotal) * 100).toFixed(1))
        : 0

      return {
        name: item.name,
        color: item.color,
        previousTotal,
        currentTotal,
        changePercent
      }
    })
    .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
})

onMounted(() => {
  fetchTrendPageData()
})
</script>

<template>
  <div>
  <TopNavBar
    :sample-count="store.summary?.sample_count || 0"
    @refresh="fetchTrendPageData"
  />
  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-10 py-8 md:py-12">
    <header class="mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight t-primary">📈 趋势分析</h1>
      <p class="t-secondary mt-2">详细的每日帖子量趋势与异常检测分析</p>
    </header>

    <div class="glass p-6 md:p-8 mb-6">
      <h2 class="section-title text-xl mb-4">帖子量趋势（完整视图）</h2>
      <LineChart
        v-if="store.trend"
        :x-axis-data="store.trend.dates"
        :series-data="store.trend.series"
        :show-data-zoom="true"
        style="height:420px;"
      />
      <div class="mt-4 text-sm t-secondary">
        本页展示完整的趋势数据。可拖拽底部滑块缩放时间范围，或使用鼠标滚轮放大/缩小。
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-5">
      <div class="glass p-6 md:p-7">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:18px;">
          <div>
            <div class="section-sub t-tertiary" style="margin-bottom:2px;">ANOMALY DETAIL</div>
            <h3 class="section-title text-lg">异常检测详情</h3>
          </div>
          <span class="chip" :class="trendStats.anomalyCount ? 'chip-danger' : 'chip-ok'">
            {{ trendStats.anomalyCount ? `${trendStats.anomalyCount} 个波动项` : '暂无明显波动' }}
          </span>
        </div>

        <div class="trend-stat-grid mb-4">
          <div class="mini-card">
            <div class="text-xs t-tertiary">最新总量</div>
            <div class="trend-stat-value t-primary">{{ trendStats.latest }}</div>
            <div class="text-xs t-tertiary">{{ trendStats.latestDate }}</div>
          </div>
          <div class="mini-card">
            <div class="text-xs t-tertiary">周期峰值</div>
            <div class="trend-stat-value t-danger">{{ trendStats.peak.total }}</div>
            <div class="text-xs t-tertiary">{{ trendStats.peak.date }}</div>
          </div>
          <div class="mini-card">
            <div class="text-xs t-tertiary">较上一有效日</div>
            <div class="trend-stat-value" :class="trendStats.changePercent >= 0 ? 't-danger' : 't-info'">
              {{ trendStats.changePercent >= 0 ? '+' : '' }}{{ trendStats.changePercent }}%
            </div>
            <div class="text-xs t-tertiary">{{ trendStats.previousDate }} → {{ trendStats.latestDate }}</div>
          </div>
        </div>

        <div v-if="anomalyItems.length" class="trend-list">
          <div v-for="item in anomalyItems" :key="item.name" class="mini-card trend-row">
            <div class="trend-row-main">
              <span class="trend-dot" :style="{ background: item.color }"></span>
              <div>
                <div class="font-medium t-primary">{{ item.name }}</div>
                <div class="text-xs t-tertiary">
                  峰值 {{ item.peakValue }} 条 · {{ item.peakDate }} · 最新 {{ item.latest }} 条（{{ item.latestDate }}）
                </div>
              </div>
            </div>
            <span class="chip" :class="item.anomaly ? 'chip-danger' : 'chip-info'">
              {{ item.changePercent >= 0 ? '+' : '' }}{{ item.changePercent }}%
            </span>
          </div>
        </div>
        <div v-else class="empty-state" style="min-height:160px;">
          <div style="font-size:36px;margin-bottom:8px;">🔬</div>
          <p class="text-sm t-secondary">暂无趋势数据</p>
        </div>
      </div>

      <div class="glass p-6 md:p-7">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:18px;">
          <div>
            <div class="section-sub t-tertiary" style="margin-bottom:2px;">PERIOD COMPARE</div>
            <h3 class="section-title text-lg">对比分析</h3>
          </div>
          <span class="chip chip-info">{{ comparisonRows.length }} 类目</span>
        </div>

        <p class="text-xs t-tertiary mb-3">按有数据的日期切分前后两段，避免空日期干扰对比。</p>

        <div class="trend-compare-summary mini-card mb-4">
          <div>
            <div class="text-xs t-tertiary">上一段合计</div>
            <div class="trend-stat-value t-primary">
              {{ comparisonRows.reduce((sum, item) => sum + item.previousTotal, 0) }}
            </div>
          </div>
          <div>
            <div class="text-xs t-tertiary">当前段合计</div>
            <div class="trend-stat-value t-primary">
              {{ comparisonRows.reduce((sum, item) => sum + item.currentTotal, 0) }}
            </div>
          </div>
          <div>
            <div class="text-xs t-tertiary">最新日期</div>
            <div class="trend-stat-value t-info">{{ trendStats.latestDate }}</div>
          </div>
        </div>

        <div v-if="comparisonRows.length" class="trend-list">
          <div v-for="row in comparisonRows" :key="row.name" class="trend-compare-row">
            <div class="trend-row-main">
              <span class="trend-dot" :style="{ background: row.color }"></span>
              <span class="font-medium t-primary">{{ row.name }}</span>
            </div>
            <div class="trend-progress-track">
              <div
                class="trend-progress-fill"
                :style="{
                  width: Math.min(100, Math.max(6, row.currentTotal / Math.max(1, row.currentTotal + row.previousTotal) * 100)) + '%',
                  background: row.color
                }"
              ></div>
            </div>
            <div class="trend-compare-meta">
              <span class="text-xs t-tertiary">前期 {{ row.previousTotal }} · 当前 {{ row.currentTotal }}</span>
              <span class="chip" :class="row.changePercent >= 0 ? 'chip-warn' : 'chip-ok'">
                {{ row.changePercent >= 0 ? '+' : '' }}{{ row.changePercent }}%
              </span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state" style="min-height:160px;">
          <div style="font-size:36px;margin-bottom:8px;">📊</div>
          <p class="text-sm t-secondary">暂无对比数据</p>
        </div>
      </div>
    </div>

    <PageFooter />
  </main>
  </div>
</template>

<style scoped>
.trend-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.trend-stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row,
.trend-compare-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.trend-row-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.trend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex: 0 0 auto;
  box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.12);
}

.trend-compare-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.trend-progress-track {
  height: 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  overflow: hidden;
}

.trend-progress-fill {
  height: 100%;
  border-radius: inherit;
  opacity: 0.85;
}

.trend-compare-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

@media (max-width: 640px) {
  .trend-stat-grid,
  .trend-compare-summary {
    grid-template-columns: 1fr;
  }

  .trend-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
