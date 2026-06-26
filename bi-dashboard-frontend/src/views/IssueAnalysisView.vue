<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'
import HorizontalBarChart from '@/components/charts/HorizontalBarChart.vue'

const store = useDashboardStore()
const router = useRouter()

function handleBarClick(categoryName) {
  router.push({ path: '/posts', query: { category: categoryName } })
}

function handleSearchKeyword(keyword) {
  router.push({ path: '/posts', query: { keyword } })
}

onMounted(() => {
  if (!store.categories) store.fetchAll()
})
</script>

<template>
  <div>
  <TopNavBar :sample-count="store.summary?.sample_count || 0" @refresh="store.fetchAll()" />
  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-10 py-8 md:py-12">
    <header class="mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight t-primary">🔍 问题分析</h1>
      <p class="t-secondary mt-2">深入分析问题分类、根因聚类与优先级分布</p>
    </header>

    <div class="grid md:grid-cols-2 gap-5 mb-6">
      <div class="glass p-6 md:p-8">
        <h2 class="section-title text-xl mb-4">问题分类分布</h2>
        <HorizontalBarChart
          v-if="store.categories"
          :categories="store.categories.categories"
          :total="store.categories.total"
          @bar-click="handleBarClick"
        />
      </div>
      <div class="glass p-6 md:p-8">
        <h2 class="section-title text-xl mb-4">根因分析（详细）</h2>
        <div v-if="store.rootCause" class="space-y-3">
          <div v-for="(c, i) in store.rootCause.clusters" :key="i" class="mini-card clickable">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div class="font-medium t-primary">{{ c.name }}</div>
              <span class="chip chip-clickable" :class="'chip-' + c.priority">{{ c.count }} 条 · {{ c.percent }}%</span>
            </div>
            <div class="text-xs t-secondary mt-2">
              关键词：
              <span v-for="kw in c.keywords" :key="kw" class="chip chip-clickable" style="font-size:11px;" @click.stop="handleSearchKeyword(kw)">{{ kw }}</span><br/>
              <span class="t-primary font-medium">可能原因：</span>{{ c.possible_cause }}<br/>
              <span class="t-primary font-medium">建议：</span>{{ c.suggestion }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <PageFooter />
  </main>
  </div>
</template>
