<script setup>
const props = defineProps({
  riskAlerts: {
    type: Object,
    required: true,
    default: () => ({
      is_systemic_risk: false,
      urgent_action_required: false,
      suggestion: '',
      alerts: []
    })
  }
})

const emit = defineEmits(['click:alert', 'resolve:alert'])

function onAlertClick(alert) {
  emit('click:alert', alert.id)
}

function onResolve(alert, event) {
  event.stopPropagation()
  emit('resolve:alert', alert.id)
}
</script>

<template>
  <div class="glass specular risk-card" style="padding: 24px;">
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
      <span class="pulse-dot"></span>
      <div style="flex: 1;">
        <div class="section-sub" style="color: #b91c1c;">RISK ALERT</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">风险预警</div>
      </div>
      <span class="chip chip-danger">{{ riskAlerts.alerts.length }} 条预警</span>
    </div>

    <!-- Alerts grid -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
      <div
        v-for="(alert, index) in riskAlerts.alerts"
        :key="index"
        class="mini-card"
        :class="alert.priority === 'P0' ? 'risk-mini' : 'risk-mini-amber'"
        style="padding: 14px;"
        @click="onAlertClick(alert)"
      >
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
          <span
            :class="alert.priority === 'P0' ? 'badge-p0' : 'badge-p1'"
            style="display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;"
          >{{ alert.priority }}</span>
          <span class="t-primary" style="font-size: 13px; font-weight: 600;">{{ alert.title }}</span>
        </div>
        <div class="t-secondary" style="font-size: 12px; line-height: 1.5; margin-bottom: 10px;">
          {{ alert.description }}
        </div>
        <div v-if="alert.status === 'active' && alert.id > 0" style="display: flex; justify-content: flex-end;">
          <button
            class="btn btn-sm btn-outline"
            @click="onResolve(alert, $event)"
          >标记已处理</button>
        </div>
      </div>
    </div>

    <!-- Risk summary footer -->
    <div style="padding: 14px; border-radius: 12px; background: rgba(254, 226, 226, 0.5); border: 1px solid rgba(239, 68, 68, 0.2);">
      <div style="display: flex; align-items: flex-start; gap: 8px;">
        <span style="font-size: 16px; flex-shrink: 0;">⚠️</span>
        <div>
          <div class="t-primary" style="font-size: 13px; font-weight: 600; margin-bottom: 4px;">
            {{ riskAlerts.is_systemic_risk ? '存在系统性风险，需要重点关注并尽快采取行动。' : '未发现系统性风险，需持续关注预警项。' }}
          </div>
          <div v-if="riskAlerts.suggestion" class="t-secondary" style="font-size: 12px; line-height: 1.5;">
            {{ riskAlerts.suggestion }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
