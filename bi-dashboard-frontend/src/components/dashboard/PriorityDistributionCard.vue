<script setup>
import { computed } from 'vue'

const props = defineProps({
  p0Risk: {
    type: Object,
    required: true,
    default: () => ({ p0_count: 0, p1_count: 0, p2_count: 0 })
  }
})

const emit = defineEmits(['filter:priority'])

const total = computed(() => {
  const { p0_count = 0, p1_count = 0, p2_count = 0 } = props.p0Risk
  return p0_count + p1_count + p2_count
})

// Store ALL priority rows here. The template renders every row into a
// scroll container that is capped to ~3 rows tall; the rest scroll.
const items = computed(() => {
  const { p0_count = 0, p1_count = 0, p2_count = 0 } = props.p0Risk
  const t = total.value || 1
  const defs = [
    { priority: 'P0', badgeClass: 'badge-p0', subtitle: '系统不可用 / 大面积 / 紧急求助', examples: '登录失败、批量数据抓取BUG、多电脑元素错位', count: p0_count, countClass: 't-danger', grad: 'linear-gradient(135deg, #ef4444, #dc2626)' },
    { priority: 'P1', badgeClass: 'badge-p1', subtitle: '功能异常但可绕过', examples: 'Bug / 系统异常 + RPA执行 + Excel + 第三方', count: p1_count, countClass: 't-warn', grad: 'linear-gradient(135deg, #f59e0b, #d97706)' },
    { priority: 'P2', badgeClass: 'badge-p2', subtitle: '咨询 / 使用问题', examples: '功能咨询、新手入门、闲聊讨论', count: p2_count, countClass: 't-info', grad: 'linear-gradient(135deg, #3b82f6, #2563eb)' }
  ]
  return defs.map(d => {
    const percent = (d.count / t * 100).toFixed(1)
    return { ...d, percent, fillStyle: { width: percent + '%', background: d.grad } }
  })
})

const VISIBLE = 3
const scrollable = computed(() => items.value.length > VISIBLE)

function onPriorityClick(priority) {
  emit('filter:priority', priority)
}
</script>

<template>
  <div class="glass specular" style="padding: 24px; height: 100%;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary">PRIORITY</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">问题优先级分布</div>
      </div>
      <span class="chip" :class="scrollable ? 'chip-info' : 'chip-warn'">
        {{ scrollable ? `共 ${items.length} 级 · 滚动查看` : 'P1 占比偏高' }}
      </span>
    </div>

    <!-- Scroll area: shows ~3 rows, the rest scroll -->
    <div class="scroll-area priority-scroll" :class="{ 'is-scrollable': scrollable }">
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div
          v-for="item in items"
          :key="item.priority"
          class="mini-card priority-row"
          @click="onPriorityClick(item.priority)"
        >
          <span :class="item.badgeClass" class="priority-badge">{{ item.priority }}</span>
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
              <span class="t-primary" style="font-size: 14px; font-weight: 500;">{{ item.subtitle }}</span>
              <span :class="item.countClass" style="font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums;">{{ item.count }}</span>
            </div>
            <div class="t-tertiary" style="font-size: 12px; margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ item.examples }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="item.fillStyle"></div>
            </div>
            <div class="t-tertiary" style="font-size: 11px; margin-top: 4px; text-align: right; font-variant-numeric: tabular-nums;">{{ item.percent }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Cap the visible area to ~3 rows (each row ≈ 104px incl. 12px gap). */
.priority-scroll.is-scrollable {
  max-height: 336px;
}
.priority-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
}
.priority-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}
</style>
