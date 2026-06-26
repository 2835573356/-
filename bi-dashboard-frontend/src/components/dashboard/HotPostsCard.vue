<script setup>
import { computed } from 'vue'

const props = defineProps({
  hotPosts: {
    type: Array,
    required: true,
    default: () => []
  }
})

const emit = defineEmits(['click:post'])

const posts = computed(() => props.hotPosts || [])
const hasData = computed(() => posts.value.length > 0)
const maxViews = computed(() => Math.max(1, ...posts.value.map(p => p.view_count || 0)))

function truncateTitle(title) {
  if (!title) return ''
  return title.length > 38 ? title.slice(0, 38) + '…' : title
}

// Rank badge color: top 3 get accent colors.
function rankClass(i) {
  if (i === 0) return 'rank-1'
  if (i === 1) return 'rank-2'
  if (i === 2) return 'rank-3'
  return 'rank-n'
}

function onPostClick(postId) {
  emit('click:post', postId)
}
</script>

<template>
  <div class="glass specular" style="padding: 24px; height: 100%;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary">HOT POSTS</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">高浏览帖 TOP {{ posts.length || 8 }}</div>
      </div>
      <span v-if="hasData" class="chip chip-warn">舆论焦点</span>
    </div>

    <div v-if="!hasData" class="empty-state">
      <div style="font-size: 40px; margin-bottom: 8px;">🔥</div>
      <div class="t-secondary" style="font-size: 14px; font-weight: 500;">当前周期暂无热门帖</div>
      <div class="t-tertiary" style="font-size: 12px; margin-top: 4px;">试试切换数据周期</div>
    </div>

    <div v-else class="scroll-area hot-scroll">
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div
          v-for="(post, i) in posts"
          :key="post.id"
          class="mini-card hot-row"
          @click="onPostClick(post.id)"
        >
          <span class="rank-badge" :class="rankClass(i)">{{ i + 1 }}</span>
          <div style="flex: 1; min-width: 0;">
            <div class="t-primary" style="font-size: 14px; font-weight: 500; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ truncateTitle(post.title) }}
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span class="t-tertiary" style="font-size: 12px;">{{ post.category }} · {{ post.sentiment }}</span>
            </div>
            <!-- relative views bar -->
            <div class="bar-track" style="height: 4px;">
              <div class="bar-fill" :style="{ width: ((post.view_count || 0) / maxViews * 100) + '%', background: 'linear-gradient(90deg,#f59e0b,#ef4444)' }"></div>
            </div>
          </div>
          <span
            class="hot-views"
            :class="post.view_count > 300 ? 't-danger' : 't-secondary'"
          >
            👁 {{ (post.view_count || 0).toLocaleString() }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hot-scroll { max-height: 420px; }
.hot-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}
.rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 8px;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
  color: #fff;
}
.rank-1 { background: linear-gradient(135deg, #f59e0b, #ef4444); }
.rank-2 { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.rank-3 { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.rank-n { background: rgba(148,163,184,0.5); }
.hot-views {
  font-size: 14px; font-weight: 700; flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
</style>
