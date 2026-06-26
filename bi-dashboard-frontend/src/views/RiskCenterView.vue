<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { showToast } from '@/composables/useToast'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'

const store = useDashboardStore()

async function handleResolve(id) {
  const result = await store.markAlertResolved(id)
  if (result.ok) {
    showToast('告警已标记为已处理', 'success')
  } else {
    showToast(result.error || '操作失败', 'error')
  }
}

onMounted(() => {
  if (!store.riskAlerts) store.fetchAll()
})
</script>

<template>
  <div>
  <TopNavBar :sample-count="store.summary?.sample_count || 0" @refresh="store.fetchAll()" />
  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-10 py-8 md:py-12">
    <header class="mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight t-primary">⚠️ 风险中心</h1>
      <p class="t-secondary mt-2">全量告警列表、处理工作流与风险管理</p>
    </header>

    <div class="glass risk-card p-6 md:p-8 mb-6">
      <div class="flex items-center gap-3 mb-4">
        <span class="pulse-dot"></span>
        <h2 class="section-title text-xl">活跃告警列表</h2>
      </div>
      <div v-if="store.riskAlerts" class="space-y-3">
        <div v-for="(alert, i) in store.riskAlerts.alerts" :key="alert.id"
             class="mini-card" :class="{ 'risk-mini': alert.priority === 'P0', 'risk-mini-amber': alert.priority === 'P1' }"
             :style="{ animationDelay: i * 0.08 + 's', opacity: alert.status === 'resolved' ? 0.5 : 1 }">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;gap:12px;">
              <span :class="alert.priority === 'P0' ? 'badge-p0' : 'badge-p1'" class="px-2.5 py-1 rounded-lg text-xs font-semibold">{{ alert.priority }}</span>
              <div>
                <div class="font-medium t-primary" :style="{ textDecoration: alert.status === 'resolved' ? 'line-through' : 'none' }">{{ alert.title }}</div>
                <div class="text-xs t-tertiary">{{ alert.description }}</div>
              </div>
            </div>
            <div style="display:flex;gap:8px;">
              <button v-if="alert.status === 'active' && alert.id > 0" class="btn btn-sm btn-outline" @click="handleResolve(alert.id)">✅ 已处理</button>
              <span v-else-if="alert.status === 'active'" class="chip chip-warn" style="font-size:10px;">动态预警</span>
              <span v-else class="chip chip-ok" style="font-size:10px;">已解决</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <PageFooter />
  </main>
  </div>
</template>
