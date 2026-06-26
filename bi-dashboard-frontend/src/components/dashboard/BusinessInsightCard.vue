<script setup>
const props = defineProps({
  insights: {
    type: Object,
    required: true,
    default: () => ({ insights: [] })
  }
})

const emit = defineEmits(['copy:insight'])

const badgeColors = ['#ef4444', '#f97316', '#8b5cf6', '#3b82f6', '#10b981']

function onCopy(index, event) {
  event.stopPropagation()
  emit('copy:insight', index)
}
</script>

<template>
  <div class="glass specular" style="padding: 24px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary">BUSINESS INSIGHT</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">关键业务洞察</div>
      </div>
      <span class="chip chip-info">5 条可执行结论</span>
    </div>

    <div style="display: flex; flex-direction: column; gap: 12px;">
      <div
        v-for="(insight, index) in insights.insights"
        :key="index"
        class="mini-card"
        style="padding: 16px; position: relative;"
      >
        <!-- Number badge -->
        <span
          style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 10px; color: #fff; font-size: 15px; font-weight: 700; margin-bottom: 10px;"
          :style="{ background: 'linear-gradient(135deg, ' + badgeColors[index] + ', ' + badgeColors[index] + 'cc)' }"
        >{{ index + 1 }}</span>

        <!-- Copy button -->
        <button
          class="copy-btn btn btn-sm btn-outline"
          style="position: absolute; top: 12px; right: 12px;"
          @click="onCopy(index, $event)"
          title="复制洞察"
        >📋</button>

        <!-- Title -->
        <div class="t-primary" style="font-size: 14px; font-weight: 600; margin-bottom: 6px; padding-right: 50px;">
          {{ insight.title }}
        </div>

        <!-- Impact -->
        <div v-if="insight.impact" style="margin-bottom: 6px;">
          <span class="t-tertiary" style="font-size: 11px;">影响：</span>
          <span class="t-warn" style="font-size: 13px;">{{ insight.impact }}</span>
        </div>

        <!-- Suggestion -->
        <div v-if="insight.suggestion">
          <span class="t-tertiary" style="font-size: 11px;">建议：</span>
          <span class="t-ok" style="font-size: 13px;">{{ insight.suggestion }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
