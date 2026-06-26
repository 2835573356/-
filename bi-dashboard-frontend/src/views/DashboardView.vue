<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { useAppStore } from '@/stores/app'
import { useWebSocket } from '@/composables/useWebSocket'
import { showToast } from '@/composables/useToast'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'
import HealthScoreCard from '@/components/dashboard/HealthScoreCard.vue'
import TodayVsYesterdayCard from '@/components/dashboard/TodayVsYesterdayCard.vue'
import P0RiskCard from '@/components/dashboard/P0RiskCard.vue'
import TrendChartCard from '@/components/dashboard/TrendChartCard.vue'
import SentimentChartCard from '@/components/dashboard/SentimentChartCard.vue'
import CategoryChartCard from '@/components/dashboard/CategoryChartCard.vue'
import PriorityDistributionCard from '@/components/dashboard/PriorityDistributionCard.vue'
import RootCauseCard from '@/components/dashboard/RootCauseCard.vue'
import BusinessInsightCard from '@/components/dashboard/BusinessInsightCard.vue'
import RiskAlertCard from '@/components/dashboard/RiskAlertCard.vue'
import HotPostsCard from '@/components/dashboard/HotPostsCard.vue'
import ExcelUploadCard from '@/components/dashboard/ExcelUploadCard.vue'
import Modal from '@/components/common/Modal.vue'

const router = useRouter()
const store = useDashboardStore()
const appStore = useAppStore()
const { connect: wsConnect, disconnect: wsDisconnect } = useWebSocket()

const showDateModal = ref(false)
const showHealthModal = ref(false)
const showComparisonModal = ref(false)
const showP0RiskModal = ref(false)
const showAlertModal = ref(false)
const modalTitle = ref('')
const modalContent = ref('')
const selectedAlert = ref(null)

const dpStart = ref('2026-06-20')
const dpEnd = ref('2026-06-25')

async function refreshData(showFeedback = false) {
  appStore.refreshData()
  await store.fetchAll({ start: appStore.dateRange.start, end: appStore.dateRange.end })
  if (store.error) {
    showToast(store.error, 'error')
  } else if (showFeedback) {
    showToast('数据已刷新', 'success', 2000)
  }
}

function extractImportedDates(result) {
  const rows = []
  const walk = (node) => {
    if (!node) return
    if (typeof node === 'string') {
      const text = node.trim()
      if (text.startsWith('[') || text.startsWith('{')) {
        try { walk(JSON.parse(text)) } catch { /* ignore */ }
      }
      return
    }
    if (Array.isArray(node)) {
      node.forEach(walk)
      return
    }
    if (typeof node === 'object') {
      const keys = Object.keys(node)
      const dateKey = keys.find(k => ['data_date', '日期', '数据日期', '发帖日期', '发布日期', '时间'].includes(k))
      if (dateKey && node[dateKey]) rows.push(String(node[dateKey]).slice(0, 10).replace(/\//g, '-'))
      Object.values(node).forEach(walk)
    }
  }
  walk(result)
  return [...new Set(rows)].filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort()
}

// Excel 上传完成后刷新看板；若能识别导入日期，自动切换到导入数据所在周期
async function onUploadSaved(payload) {
  const record = typeof payload === 'object' ? payload.record : null
  const dates = extractImportedDates(record?.result)
  if (dates.length) {
    appStore.setDateRange(dates[0], dates[dates.length - 1])
  }
  await refreshData(false)
}

function handleFilterCategory(category) {
  router.push({ path: '/posts', query: { category } })
}

// 健康度卡片的统计小卡跳转：把语义键映射为帖子列表的真实筛选条件
function handleHealthFilter(key) {
  if (key === 'bug') {
    router.push({ path: '/posts', query: { category: 'Bug / 系统异常' } })
  } else if (key === 'negative') {
    router.push({ path: '/posts', query: { sentiment: '消极' } })
  } else {
    router.push({ path: '/posts' })
  }
}

// 总帖子量 → 全部帖子列表；日均帖子量 → 健康度评分明细弹窗
function handleHealthMiniClick(key) {
  if (key === 'total_posts') {
    router.push({ path: '/posts' })
  } else {
    openHealthDetail()
  }
}

function handleFilterPriority(priority) {
  router.push({ path: '/posts', query: { priority } })
}

function handleSearchKeyword(keyword) {
  router.push({ path: '/posts', query: { keyword } })
}

function handleClickPost(postId) {
  router.push(`/posts/${postId}`)
}

function handleClickAlert(alertId) {
  const alert = store.riskAlerts?.alerts.find(a => a.id === alertId)
  if (alert) {
    selectedAlert.value = alert
    showAlertModal.value = true
  }
}

async function handleResolveAlert(id) {
  const result = await store.markAlertResolved(id)
  if (result.ok) {
    showToast('告警已标记为已处理', 'success')
    if (selectedAlert.value?.id === id) {
      selectedAlert.value.status = 'resolved'
    }
  } else {
    showToast(result.error || '操作失败', 'error')
  }
}

function handleCopyInsight(index) {
  const insight = store.insights?.insights.find(i => i.index === index)
  if (insight) {
    const text = `【洞察 #${insight.index}】${insight.title}\n影响：${insight.impact}\n建议：${insight.suggestion}`
    navigator.clipboard.writeText(text).then(() => {
      showToast('洞察已复制到剪贴板', 'success')
    })
  }
}

function openDatePicker() {
  // 打开时同步为当前生效的范围
  dpStart.value = appStore.dateRange.start
  dpEnd.value = appStore.dateRange.end
  showDateModal.value = true
}
function openHealthDetail() {
  modalTitle.value = '💚 健康度详情'
  modalContent.value = `
    <div style="margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
        <div style="font-size:48px;font-weight:700;color:#dc2626;">${store.summary?.health_score || 45}</div>
        <div style="font-size:20px;color:var(--t-secondary);">/ 100 · 高风险状态</div>
      </div>
      <div class="p-3 rounded-xl" style="background:rgba(254,226,226,0.5);margin-bottom:12px;">
        <strong class="t-danger">⚠️ 扣分项分析：</strong>
        <ul style="font-size:14px;margin-top:8px;list-style:none;padding:0;">
          <li>• Bug 占比 34.7% → <span class="t-danger">-13.9 分</span> (权重 40%)</li>
          <li>• 消极情绪 51.0% → <span class="t-danger">-17.9 分</span> (权重 35%)</li>
          <li>• P0 数量 6 → <span class="t-danger">-9.0 分</span> (权重 15%)</li>
          <li>• 异常信号数 → <span class="t-warn">-4.2 分</span> (权重 10%)</li>
        </ul>
      </div>
      <p class="t-secondary">建议：立即进入预警状态，冻结非必要发版，组织专项 hotfix。</p>
    </div>
  `
  showHealthModal.value = true
}

function openDailyComparison() {
  modalTitle.value = '📊 日环比详情'
  modalContent.value = `
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
        <span class="t-secondary">6/23 (昨日)</span><span style="font-weight:600;">28 条 Bug 类</span>
      </div>
      <div style="font-size:28px;font-weight:700;color:#dc2626;margin-bottom:12px;">→ 33 条 (+17.9%)</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:16px;">
        <span class="t-secondary">6/24 (今日)</span><span style="font-weight:600;">33 条 Bug 类</span>
      </div>
      <div class="bar-track" style="margin-bottom:16px;"><div class="bar-fill" style="width:72%;background:linear-gradient(90deg,#ef4444,#f59e0b);"></div></div>
      <p class="t-secondary">Bug 类问题在 6/24 达到周期峰值，主要驱动因素为"元素错位"类问题集中爆发。</p>
    </div>
  `
  showComparisonModal.value = true
}

function applyDateRange() {
  appStore.setDateRange(dpStart.value, dpEnd.value)
  showDateModal.value = false
  refreshData(true)
}

// Expose resolve handler to window for inline onclick
if (typeof window !== 'undefined') {
  window._markResolved = async (id) => {
    const result = await store.markAlertResolved(id)
    if (result.ok) showToast('告警已标记为已处理', 'success')
    else showToast(result.error || '操作失败', 'error')
    showHealthModal.value = false
  }
  window._closeModal = () => { showHealthModal.value = false; showComparisonModal.value = false; showP0RiskModal.value = false; showAlertModal.value = false }
}

onMounted(() => {
  refreshData()
  // Connect WebSocket for real-time updates
  setTimeout(() => wsConnect(), 500)
})

onUnmounted(() => {
  wsDisconnect()
})
</script>

<template>
  <div>
  <TopNavBar
    :sample-count="store.summary?.sample_count || 0"
    @refresh="refreshData(true)"
    @open-date-picker="openDatePicker"
  />

  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-12 py-8 md:py-14">
    <header class="mb-10 md:mb-14 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
      <div>
        <h1 class="text-3xl md:text-5xl font-semibold tracking-tight t-primary">
          社区数据简报
        </h1>
        <p class="t-secondary mt-3 text-sm md:text-base max-w-2xl leading-relaxed">
          监控 / 趋势 / 异常 / 归因 / 风险 — 面向产品与运营决策的社区健康透视。
        </p>
      </div>
      <div class="md:flex-shrink-0 md:pt-2 w-full md:w-auto md:max-w-[640px]">
        <ExcelUploadCard @saved="onUploadSaved" />
      </div>
    </header>

    <!-- Section 1: Health + Today vs Yesterday + P0 Risk -->
    <section class="grid grid-cols-12 gap-6 md:gap-8 mb-8 md:mb-10">
      <div class="col-span-12 lg:col-span-5">
        <HealthScoreCard
          v-if="store.summary"
          :summary="store.summary"
          @click:detail="handleHealthMiniClick"
          @filter:category="handleHealthFilter"
        />
      </div>
      <div class="col-span-6 lg:col-span-4">
        <P0RiskCard
          v-if="store.summary"
          :data="store.summary.p0_risk"
          @filter:priority="handleFilterPriority"
          @click:detail="showP0RiskModal = true"
        />
      </div>
      <div class="col-span-6 lg:col-span-3">
        <TodayVsYesterdayCard
          v-if="store.summary"
          :data="store.summary.today_vs_yesterday"
          @click="openDailyComparison"
        />
      </div>
    </section>

    <!-- Section 2: Trend + Sentiment -->
    <section class="grid grid-cols-12 gap-6 md:gap-8 mb-8 md:mb-10">
      <div class="col-span-12 lg:col-span-7">
        <TrendChartCard
          v-if="store.trend"
          :trend="store.trend"
        />
      </div>
      <div class="col-span-12 md:col-span-6 lg:col-span-5">
        <SentimentChartCard
          v-if="store.sentiment"
          :sentiment="store.sentiment"
        />
      </div>
    </section>

    <!-- Section 3: Issue Breakdown + Priority -->
    <section class="grid grid-cols-12 gap-6 md:gap-8 mb-8 md:mb-10">
      <div class="col-span-12 lg:col-span-7">
        <CategoryChartCard
          v-if="store.categories"
          :categories="store.categories"
          @filter:category="handleFilterCategory"
        />
      </div>
      <div class="col-span-12 lg:col-span-5">
        <PriorityDistributionCard
          v-if="store.priority"
          :p0-risk="store.priority.p0_risk"
          @filter:priority="handleFilterPriority"
        />
      </div>
    </section>

    <!-- Section 4: Root Cause + Insights -->
    <section class="grid grid-cols-12 gap-6 md:gap-8 mb-8 md:mb-10">
      <div class="col-span-12 lg:col-span-6">
        <RootCauseCard
          v-if="store.rootCause"
          :root-cause="store.rootCause"
          @search:keyword="handleSearchKeyword"
        />
      </div>
      <div class="col-span-12 lg:col-span-6">
        <BusinessInsightCard
          v-if="store.insights"
          :insights="store.insights"
          @copy:insight="handleCopyInsight"
        />
      </div>
    </section>

    <!-- Section 5: Risk + Hot Posts -->
    <section class="grid grid-cols-12 gap-6 md:gap-8 mb-8 md:mb-10">
      <div class="col-span-12 lg:col-span-7">
        <RiskAlertCard
          v-if="store.riskAlerts"
          :risk-alerts="store.riskAlerts"
          @click:alert="handleClickAlert"
          @resolve:alert="handleResolveAlert"
        />
      </div>
      <div class="col-span-12 lg:col-span-5">
        <HotPostsCard
          v-if="store.hotPosts"
          :hot-posts="store.hotPosts"
          @click:post="handleClickPost"
        />
      </div>
    </section>

    <PageFooter />
  </main>

  <!-- Modals -->
  <Modal :show="showDateModal" title="📅 数据周期设置" @close="showDateModal = false">
    <div style="display:flex;flex-direction:column;gap:12px;">
      <p class="text-sm t-secondary">选择数据周期范围：</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        <div><label class="text-xs t-tertiary">开始日期</label>
          <input v-model="dpStart" type="date" class="w-full px-3 py-2 rounded-xl border text-sm mt-1" style="outline:none;background:rgba(255,255,255,0.6);"></div>
        <div><label class="text-xs t-tertiary">结束日期</label>
          <input v-model="dpEnd" type="date" class="w-full px-3 py-2 rounded-xl border text-sm mt-1" style="outline:none;background:rgba(255,255,255,0.6);"></div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <span class="chip chip-clickable" @click="dpStart='2026-06-19';dpEnd='2026-06-25'">最近 7 天</span>
        <span class="chip chip-clickable" @click="dpStart='2026-05-26';dpEnd='2026-06-25'">最近 30 天</span>
        <span class="chip chip-clickable" @click="dpStart='2026-06-01';dpEnd='2026-06-25'">本月</span>
        <span class="chip chip-clickable" @click="dpStart='2026-05-01';dpEnd='2026-05-31'">上月</span>
      </div>
      <button class="btn btn-primary btn-sm" @click="applyDateRange">✅ 应用并刷新</button>
    </div>
  </Modal>

  <Modal :show="showHealthModal" title="💚 健康度详情" @close="showHealthModal = false">
    <div>
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
        <div style="font-size:48px;font-weight:700;color:#dc2626;">{{ store.summary?.health_score || '—' }}</div>
        <div style="font-size:20px;color:var(--t-secondary);">/ 100 · {{ store.summary?.health_status === 'high_risk' ? '高风险状态' : store.summary?.health_status === 'warning' ? '警告状态' : '健康状态' }}</div>
      </div>
      <div class="p-3 rounded-xl" style="background:rgba(254,226,226,0.5);margin-bottom:12px;">
        <strong class="t-danger">⚠️ 健康度明细：</strong>
        <ul style="font-size:14px;margin-top:8px;list-style:none;padding:0;">
          <li>• Bug 占比 {{ store.summary?.bug_ratio || 0 }}%</li>
          <li>• 消极情绪占比 {{ store.summary?.negative_ratio || 0 }}%</li>
          <li>• P0 数量 {{ store.summary?.p0_risk?.p0_count || 0 }}</li>
          <li>• 总帖子量 {{ store.summary?.total_posts || 0 }}</li>
        </ul>
      </div>
      <p class="t-secondary">{{ store.summary?.health_description || '' }}</p>
    </div>
  </Modal>

  <Modal :show="showComparisonModal" title="📊 日环比详情" @close="showComparisonModal = false">
    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
        <span class="t-secondary">变化类型</span>
        <span class="chip chip-danger">{{ store.summary?.today_vs_yesterday?.change_type === 'surge' ? '突增' : store.summary?.today_vs_yesterday?.change_type === 'increase' ? '上升' : store.summary?.today_vs_yesterday?.change_type === 'decrease' ? '下降' : '持平' }}</span>
      </div>
      <div style="font-size:28px;font-weight:700;color:#dc2626;margin-bottom:12px;">
        {{ (store.summary?.today_vs_yesterday?.change_percent || 0) > 0 ? '+' : '' }}{{ store.summary?.today_vs_yesterday?.change_percent || 0 }}%
      </div>
      <p class="t-secondary">{{ store.summary?.today_vs_yesterday?.description || '' }}</p>
      <div class="bar-track mt-4"><div class="bar-fill" :style="{ width: (store.summary?.today_vs_yesterday?.bar_percent || 0) + '%', background: 'linear-gradient(90deg,#ef4444,#f59e0b)' }"></div></div>
    </div>
  </Modal>

  <Modal :show="showP0RiskModal" title="🚨 P0 风险详情" @close="showP0RiskModal = false">
    <div>
      <p class="text-sm t-secondary" style="margin-bottom:16px;">
        当前共有 <span class="t-danger" style="font-weight:600;">{{ store.summary?.p0_risk?.p0_count || 0 }}</span> 条 P0 级别问题，紧急求助 {{ store.summary?.p0_risk?.emergency_count || 0 }} 条。
      </p>
      <div v-if="store.riskAlerts" style="display:flex;flex-direction:column;gap:8px;">
        <div v-for="alert in store.riskAlerts.alerts.filter(a => a.priority === 'P0')" :key="alert.id"
             class="mini-card risk-mini" style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div class="font-medium t-primary" style="font-size:14px;">{{ alert.title }}</div>
            <div class="text-xs t-tertiary">{{ alert.description }}</div>
          </div>
          <span class="badge-p0 px-2 py-0.5 rounded-md text-xs">P0</span>
        </div>
      </div>
    </div>
  </Modal>

  <!-- Alert detail modal -->
  <Modal :show="showAlertModal" title="🚨 告警详情" @close="showAlertModal = false">
    <div v-if="selectedAlert">
      <div style="margin-bottom:16px;display:flex;gap:8px;">
        <span :class="selectedAlert.priority === 'P0' ? 'badge-p0' : 'badge-p1'" class="px-2.5 py-1 rounded-lg text-xs font-semibold">{{ selectedAlert.priority }}</span>
        <span class="chip" :class="selectedAlert.is_systemic ? 'chip-danger' : 'chip-warn'">{{ selectedAlert.is_systemic ? '系统性风险' : '独立风险' }}</span>
        <span v-if="selectedAlert.status === 'resolved'" class="chip chip-ok">已解决</span>
      </div>
      <h3 style="font-size:18px;font-weight:600;margin-bottom:12px;" class="t-primary">{{ selectedAlert.title }}</h3>
      <p class="t-secondary" style="margin-bottom:16px;">{{ selectedAlert.description }}</p>
      <button v-if="selectedAlert.status === 'active' && selectedAlert.id > 0" class="btn btn-primary btn-sm" @click="handleResolveAlert(selectedAlert.id)">✅ 标记为已处理</button>
    </div>
  </Modal>
  </div>
</template>
