<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { sentimentToEnglish } from '@/api/index'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'

const route = useRoute()
const router = useRouter()
const store = useDashboardStore()

const keyword = ref(route.query.keyword || '')
const category = ref(route.query.category || '')
const priority = ref(route.query.priority || '')
const sentiment = ref(route.query.sentiment || '')
const currentPage = ref(1)
const perPage = 20

// Sentiment display mapping
const sentimentClass = (s) => {
  if (s === '消极') return 'chip-danger'
  if (s === '积极') return 'chip-ok'
  return ''
}

function doSearch(page = 1) {
  currentPage.value = page
  store.fetchPosts({
    keyword: keyword.value || undefined,
    category: category.value || undefined,
    priority: priority.value || undefined,
    sentiment: sentiment.value ? sentimentToEnglish(sentiment.value) : undefined,
    page,
    page_size: perPage
  })
}

function clearFilters() {
  keyword.value = ''
  category.value = ''
  priority.value = ''
  sentiment.value = ''
  currentPage.value = 1
  doSearch(1)
}

function goToPage(page) {
  doSearch(page)
}

function viewPost(id) {
  router.push(`/posts/${id}`)
}

async function exportCSV() {
  const token = localStorage.getItem('token')
  const params = new URLSearchParams()
  if (keyword.value) params.set('keyword', keyword.value)
  if (category.value) params.set('category', category.value)
  if (priority.value) params.set('priority', priority.value)
  if (sentiment.value) params.set('sentiment', sentimentToEnglish(sentiment.value))
  params.set('format', 'csv')

  try {
    const resp = await fetch(`/api/v1/export/posts?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!resp.ok) throw new Error('导出失败')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'posts_export.csv'; a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export error:', e)
  }
}

// Watch route query changes
watch(() => route.query, (q) => {
  if (q.keyword !== undefined) keyword.value = q.keyword
  if (q.category !== undefined) category.value = q.category
  if (q.priority !== undefined) priority.value = q.priority
  if (q.sentiment !== undefined) sentiment.value = q.sentiment
  doSearch(1)
}, { immediate: false })

onMounted(() => {
  doSearch(1)
})
</script>

<template>
  <div>
  <TopNavBar :sample-count="store.postsTotal" @refresh="doSearch(currentPage)" />
  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-10 py-8 md:py-12">
    <header class="mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight t-primary">📋 帖子管理</h1>
      <p class="t-secondary mt-2">浏览、搜索与管理所有社区帖子</p>
    </header>

    <div class="glass p-6 md:p-8 mb-6">
      <!-- Filters -->
      <div class="flex flex-wrap gap-3 mb-6 items-center">
        <input v-model="keyword" type="text" placeholder="🔍 搜索帖子标题..."
               class="px-4 py-2 rounded-xl border text-sm flex-1 min-w-[200px]"
               style="outline:none;background:rgba(255,255,255,0.6);"
               @keyup.enter="doSearch(1)">
        <select v-model="category" @change="doSearch(1)"
                class="px-4 py-2 rounded-xl border text-sm" style="outline:none;background:rgba(255,255,255,0.6);">
          <option value="">全部类别</option>
          <option value="Bug / 系统异常">Bug / 系统异常</option>
          <option value="功能咨询">功能咨询</option>
          <option value="RPA执行问题">RPA执行问题</option>
          <option value="Excel数据问题">Excel数据问题</option>
          <option value="第三方系统问题">第三方系统问题</option>
          <option value="紧急求助">紧急求助</option>
        </select>
        <select v-model="priority" @change="doSearch(1)"
                class="px-4 py-2 rounded-xl border text-sm" style="outline:none;background:rgba(255,255,255,0.6);">
          <option value="">全部优先级</option>
          <option value="P0">P0</option>
          <option value="P1">P1</option>
          <option value="P2">P2</option>
        </select>
        <select v-model="sentiment" @change="doSearch(1)"
                class="px-4 py-2 rounded-xl border text-sm" style="outline:none;background:rgba(255,255,255,0.6);">
          <option value="">全部情绪</option>
          <option value="消极">消极</option>
          <option value="中性">中性</option>
          <option value="积极">积极</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="doSearch(1)">🔍 搜索</button>
        <button class="btn btn-outline btn-sm" @click="clearFilters">↺ 清除</button>
        <button class="btn btn-outline btn-sm" @click="exportCSV">📥 导出CSV</button>
        <span class="text-xs t-tertiary">共 {{ store.postsTotal }} 条结果</span>
      </div>

      <!-- Loading -->
      <div v-if="store.loading" class="text-center py-8 t-secondary">
        <div class="skeleton" style="height:200px;width:100%;"></div>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">ID</th>
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">标题</th>
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">分类</th>
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">情绪</th>
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">优先级</th>
              <th style="padding:12px;text-align:left;font-size:12px;color:var(--t-tertiary);">作者</th>
              <th style="padding:12px;text-align:right;font-size:12px;color:var(--t-tertiary);">浏览量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="post in store.posts" :key="post.id"
                class="cursor-pointer" style="border-bottom:1px solid rgba(148,163,184,0.08);"
                @click="viewPost(post.id)">
              <td style="padding:12px;font-size:13px;color:var(--t-tertiary);">#{{ post.id }}</td>
              <td style="padding:12px;font-size:14px;font-weight:500;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" class="t-primary">{{ post.title }}</td>
              <td style="padding:12px;font-size:13px;" class="t-secondary">{{ post.category }}</td>
              <td style="padding:12px;">
                <span class="chip" :class="sentimentClass(post.sentiment)" style="font-size:11px;">{{ post.sentiment }}</span>
              </td>
              <td style="padding:12px;">
                <span :class="'badge-' + (post.priority || 'p2').toLowerCase()" class="px-2 py-0.5 rounded-md text-[10px] font-semibold">{{ post.priority }}</span>
              </td>
              <td style="padding:12px;font-size:13px;color:var(--t-tertiary);">{{ post.author_name || '—' }}</td>
              <td style="padding:12px;text-align:right;font-weight:600;font-size:14px;" :class="post.view_count > 300 ? 't-danger' : 't-secondary'">{{ post.view_count }}</td>
            </tr>
            <tr v-if="store.posts.length === 0">
              <td colspan="7" style="text-align:center;padding:40px;color:var(--t-tertiary);">
                📭 暂无数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="store.postsTotalPages > 1" class="flex justify-center gap-2 mt-4">
        <span v-for="p in store.postsTotalPages" :key="p"
              class="chip chip-clickable" :class="{ 'chip-info': p === currentPage }"
              @click="goToPage(p)">{{ p }}</span>
      </div>
    </div>

    <PageFooter />
  </main>
  </div>
</template>
