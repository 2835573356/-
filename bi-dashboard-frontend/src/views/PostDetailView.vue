<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import PageFooter from '@/components/layout/PageFooter.vue'

const route = useRoute()
const router = useRouter()
const store = useDashboardStore()

const post = ref(null)
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  if (!store.summary) {
    store.fetchAll()
  }
  const id = Number(route.params.id)
  if (id) {
    post.value = await store.fetchPostById(id)
  }
  loading.value = false
})

function goBack() {
  router.back()
}

const sentimentClass = (s) => {
  if (s === '消极') return 'chip-danger'
  if (s === '积极') return 'chip-ok'
  return ''
}
</script>

<template>
  <div>
  <TopNavBar :sample-count="store.summary?.sample_count || 0" />
  <main class="relative z-10 max-w-[1440px] mx-auto px-6 md:px-10 py-8 md:py-12">
    <div class="glass p-6 md:p-8 max-w-3xl mx-auto">
      <button class="btn btn-outline btn-sm mb-6" @click="goBack">← 返回列表</button>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-8">
        <div class="skeleton" style="height:200px;width:100%;"></div>
      </div>

      <div v-else-if="post">
        <div class="flex flex-wrap gap-2 mb-4">
          <span class="chip">📂 {{ post.category }}</span>
          <span class="chip" :class="sentimentClass(post.sentiment)">
            😐 {{ post.sentiment }}
          </span>
          <span :class="'badge-' + (post.priority || 'p2').toLowerCase()" class="px-2.5 py-1 rounded-lg text-xs font-semibold">
            {{ post.priority }}
          </span>
          <span class="chip">👁 {{ post.view_count }} 浏览</span>
          <span v-if="post.reply_count" class="chip">💬 {{ post.reply_count }} 回复</span>
        </div>

        <h1 class="text-2xl md:text-3xl font-semibold t-primary mb-4">{{ post.title }}</h1>

        <div class="text-sm t-secondary mb-6 space-y-1">
          <div>👤 作者：{{ post.author_name || '匿名用户' }}</div>
          <div>📅 发布于：{{ post.created_at || post.data_date || '未知日期' }}</div>
          <div v-if="post.source">📌 来源：{{ post.source }}</div>
        </div>

        <div class="p-4 rounded-xl text-sm t-secondary mb-6" style="background:rgba(241,245,249,0.5);">
          {{ post.content || '暂无详细内容' }}
        </div>

        <div v-if="post.tags && post.tags.length > 0" class="flex flex-wrap gap-2 mb-4">
          <span v-for="tag in post.tags" :key="tag" class="chip" style="font-size:11px;">🏷 {{ tag }}</span>
        </div>

        <div class="flex gap-2">
          <button class="btn btn-outline btn-sm" @click="navigator.clipboard.writeText(window.location.href)">🔗 复制链接</button>
          <button class="btn btn-outline btn-sm">⭐ 收藏</button>
        </div>
      </div>

      <div v-else class="text-center py-12 t-secondary">
        <div style="font-size:48px;margin-bottom:16px;">📝</div>
        <p>帖子不存在或已删除</p>
        <button class="btn btn-outline btn-sm mt-4" @click="goBack">返回列表</button>
      </div>
    </div>

    <PageFooter />
  </main>
  </div>
</template>
