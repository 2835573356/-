<script setup>
import Chip from '@/components/common/Chip.vue'
import MiniCard from '@/components/common/MiniCard.vue'

const props = defineProps({
  data: {
    type: Object,
    required: true
    // shape: { level, emergency_count, systemic_bug_count, p0_count, p1_count, p2_count }
  }
})

defineEmits(['filter:priority', 'click:detail'])
</script>

<template>
  <div class="glass risk-card" style="padding: 24px;">
    <!-- Header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
      <div class="section-sub t-danger" style="margin-bottom: 0;">P0 风险</div>
      <Chip type="danger">
        <span class="pulse-dot" style="margin-right: 4px;"></span>
        {{ data.level }}
      </Chip>
    </div>

    <!-- Emergency + Systemic Bug Counts -->
    <div style="display: flex; gap: 16px; margin-bottom: 16px;">
      <div style="flex: 1;">
        <div class="t-tertiary" style="font-size: 11px; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 2px;">紧急数</div>
        <div class="t-danger" style="font-size: 24px; font-weight: 700;">{{ data.emergency_count }}</div>
      </div>
      <div style="flex: 1;">
        <div class="t-tertiary" style="font-size: 11px; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 2px;">系统性Bug数</div>
        <div class="t-danger" style="font-size: 24px; font-weight: 700;">{{ data.systemic_bug_count }}</div>
      </div>
    </div>

    <!-- P0 / P1 / P2 Mini Cards -->
    <div style="display: flex; flex-direction: column; gap: 10px;">
      <MiniCard risk="danger" @click="$emit('filter:priority', 'P0')">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span style="font-weight: 600; font-size: 14px;">P0 · 最高优先级</span>
          <span class="t-danger" style="font-size: 22px; font-weight: 700;">{{ data.p0_count }}</span>
        </div>
      </MiniCard>
      <MiniCard risk="amber" @click="$emit('filter:priority', 'P1')">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="t-warn" style="font-weight: 600; font-size: 14px;">P1 · 紧急</span>
          <span class="t-warn" style="font-size: 22px; font-weight: 700;">{{ data.p1_count }}</span>
        </div>
      </MiniCard>
      <MiniCard @click="$emit('filter:priority', 'P2')">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="t-info" style="font-weight: 600; font-size: 14px;">P2 · 一般</span>
          <span class="t-info" style="font-size: 22px; font-weight: 700;">{{ data.p2_count }}</span>
        </div>
      </MiniCard>
    </div>
  </div>
</template>
