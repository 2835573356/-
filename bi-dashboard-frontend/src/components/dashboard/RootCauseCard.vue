<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  rootCause: {
    type: Object,
    required: true,
    default: () => ({ clusters: [] })
  }
})

const emit = defineEmits(['search:keyword'])

const clusters = computed(() => props.rootCause.clusters || [])
const hasData = computed(() => clusters.value.length > 0)

const expandedIndex = ref(null)

function toggleCluster(index) {
  expandedIndex.value = expandedIndex.value === index ? null : index
}

// Backend already provides `priority` ('danger'|'warn'|'info'); fall back to percent.
function chipLabel(cluster) {
  if (cluster.priority) return cluster.priority
  if (cluster.percent > 10) return 'danger'
  if (cluster.percent >= 5) return 'warn'
  return 'info'
}

// Support both `name` (backend) and legacy `title`.
function clusterTitle(cluster) {
  return cluster.name || cluster.title || '未命名簇'
}

function onKeywordClick(keyword) {
  emit('search:keyword', keyword)
}

const VISIBLE = 3
const scrollable = computed(() => clusters.value.length > VISIBLE)
</script>

<template>
  <div class="glass specular" style="padding: 24px; height: 100%;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary">ROOT CAUSE</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">根因分析（语义聚类）</div>
      </div>
      <span v-if="hasData" class="chip chip-info">{{ clusters.length }} 个高频簇</span>
    </div>

    <div v-if="!hasData" class="empty-state">
      <div style="font-size: 40px; margin-bottom: 8px;">🧩</div>
      <div class="t-secondary" style="font-size: 14px; font-weight: 500;">当前周期暂无聚类结果</div>
      <div class="t-tertiary" style="font-size: 12px; margin-top: 4px;">试试切换数据周期</div>
    </div>

    <div v-else class="scroll-area" :class="{ 'rc-scroll': scrollable }">
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div
          v-for="(cluster, index) in clusters"
          :key="index"
          class="mini-card"
          style="padding: 16px;"
          @click="toggleCluster(index)"
        >
          <!-- Title row -->
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
              <span class="rc-index">{{ index + 1 }}</span>
              <span class="t-primary" style="font-size: 14px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ clusterTitle(cluster) }}</span>
            </div>
            <span class="chip" :class="'chip-' + chipLabel(cluster)" style="flex-shrink: 0;">{{ cluster.count }} · {{ cluster.percent }}%</span>
          </div>

          <!-- Expandable detail -->
          <div v-if="expandedIndex === index" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(148, 163, 184, 0.2);">
            <div v-if="cluster.keywords && cluster.keywords.length" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
              <span
                v-for="keyword in cluster.keywords"
                :key="keyword"
                class="chip chip-clickable"
                @click.stop="onKeywordClick(keyword)"
              >{{ keyword }}</span>
            </div>
            <div v-if="cluster.possible_cause" style="margin-bottom: 10px;">
              <div class="t-tertiary" style="font-size: 11px; margin-bottom: 4px;">可能原因</div>
              <div class="t-secondary" style="font-size: 13px; line-height: 1.5;">{{ cluster.possible_cause }}</div>
            </div>
            <div v-if="cluster.suggestion">
              <div class="t-tertiary" style="font-size: 11px; margin-bottom: 4px;">改进建议</div>
              <div class="t-info" style="font-size: 13px; line-height: 1.5;">{{ cluster.suggestion }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rc-scroll { max-height: 380px; }
.rc-index {
  display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; font-size: 13px; font-weight: 700; flex-shrink: 0;
}
</style>
