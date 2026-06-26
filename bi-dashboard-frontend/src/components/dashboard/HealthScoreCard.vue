<script setup>
import ScoreRing from '@/components/dashboard/ScoreRing.vue'
import MiniCard from '@/components/common/MiniCard.vue'

const props = defineProps({
  summary: {
    type: Object,
    required: true
    // shape: { health_score, total_posts, daily_avg_posts, bug_ratio, negative_ratio, health_description }
  }
})

defineEmits(['click:detail', 'filter:category'])
</script>

<template>
  <div class="glass" style="padding: 24px;">
    <!-- Header -->
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary" style="margin-bottom: 2px;">社区健康度</div>
        <div class="section-title t-primary" style="font-size: 20px;">健康评分 · Health Score</div>
      </div>
    </div>

    <!-- Score Ring -->
    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
      <ScoreRing :score="summary.health_score" />
    </div>

    <!-- 2x2 Mini Stat Cards -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
      <MiniCard title="查看全部帖子" @click="$emit('click:detail', 'total_posts')">
        <div>
          <div class="t-tertiary mini-label">总帖子量 <span class="mini-arrow">↗</span></div>
          <div class="t-primary" style="font-size: 22px; font-weight: 700;">{{ summary.total_posts?.toLocaleString() }}</div>
        </div>
      </MiniCard>
      <MiniCard title="查看健康度评分明细" @click="$emit('click:detail', 'daily_avg')">
        <div>
          <div class="t-tertiary mini-label">日均帖子量 <span class="mini-arrow">↗</span></div>
          <div class="t-primary" style="font-size: 22px; font-weight: 700;">{{ summary.daily_avg_posts?.toLocaleString() }}</div>
        </div>
      </MiniCard>
      <MiniCard risk="danger" title="筛选 Bug / 系统异常 类帖子" @click="$emit('filter:category', 'bug')">
        <div>
          <div class="t-tertiary mini-label">Bug占比 <span class="mini-arrow">↗</span></div>
          <div class="t-danger" style="font-size: 22px; font-weight: 700;">{{ summary.bug_ratio }}%</div>
        </div>
      </MiniCard>
      <MiniCard risk="danger" title="筛选消极情绪帖子" @click="$emit('filter:category', 'negative')">
        <div>
          <div class="t-tertiary mini-label">消极情绪占比 <span class="mini-arrow">↗</span></div>
          <div class="t-danger" style="font-size: 22px; font-weight: 700;">{{ summary.negative_ratio }}%</div>
        </div>
      </MiniCard>
    </div>

    <!-- Assessment Text -->
    <div
      class="t-secondary"
      style="font-size: 13px; line-height: 1.7; padding: 12px 16px; background: rgba(148,163,184,0.08); border-radius: 12px;"
      v-html="summary.health_description"
    ></div>
  </div>
</template>

<style scoped>
.mini-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.mini-arrow {
  font-size: 12px;
  opacity: 0;
  transform: translateX(-2px);
  transition: opacity 200ms ease, transform 200ms ease;
}
/* 悬停所在卡片时显示跳转箭头，提示可点击 */
.mini-card:hover .mini-arrow {
  opacity: 0.7;
  transform: translateX(0);
}
</style>
