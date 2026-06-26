<script setup>
import { computed } from 'vue'
import HorizontalBarChart from '@/components/charts/HorizontalBarChart.vue'

const props = defineProps({
  categories: {
    type: Object,
    required: true,
    default: () => ({ categories: [], total: 0 })
  }
})

const emit = defineEmits(['filter:category'])

const list = computed(() => props.categories.categories || [])
const total = computed(() => props.categories.total || 0)
const hasData = computed(() => list.value.length > 0 && total.value > 0)

function onBarClick(categoryName) {
  emit('filter:category', categoryName)
}
</script>

<template>
  <div class="glass specular" style="padding: 24px; height: 100%;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
      <div>
        <div class="section-sub t-tertiary">ISSUE BREAKDOWN</div>
        <div class="section-title t-primary" style="font-size: 20px; margin-top: 4px;">问题结构分析</div>
      </div>
      <span v-if="hasData" class="chip chip-info">{{ list.length }} 类 · {{ total }} 条</span>
    </div>

    <div v-if="!hasData" class="empty-state">
      <div style="font-size: 40px; margin-bottom: 8px;">📊</div>
      <div class="t-secondary" style="font-size: 14px; font-weight: 500;">当前周期暂无分类数据</div>
      <div class="t-tertiary" style="font-size: 12px; margin-top: 4px;">试试切换数据周期</div>
    </div>

    <HorizontalBarChart
      v-else
      :categories="list"
      :total="total"
      @bar-click="onBarClick"
    />
  </div>
</template>
