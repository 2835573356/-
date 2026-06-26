<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { uploadExcel, fetchUploadStatus, fetchUploadRecords, deleteUploadRecord } from '@/api/upload'
import { showToast } from '@/composables/useToast'
import Modal from '@/components/common/Modal.vue'

const emit = defineEmits(['saved'])

const fileInput = ref(null)
const uploading = ref(false)        // 整个流程进行中（上传+轮询）
const progressText = ref('')        // 动态进度文案
const elapsed = ref(0)              // 已用秒数
const records = ref([])
const showPanel = ref(false)
const activeRecord = ref(null)
const deletingId = ref(null)        // 正在删除的记录 id

let pollTimer = null
let elapsedTimer = null

const latest = computed(() => records.value[0] || null)

function recordStatusLabel(rec) {
  if (!rec) return '未知'
  if (rec.status === 'success') return `${rec.row_count || 0}条`
  if (rec.status === 'failed') return '失败'
  if (rec.status === 'running' || rec.status === 'pending') return '处理中'
  return rec.status || '处理中'
}

// 从结果中尽力抽出一个数据行数组用于表格展示
const tableRows = computed(() => {
  const r = activeRecord.value
  if (!r || !r.result) return []
  return extractRows(r.result)
})

const tableColumns = computed(() => {
  const rows = tableRows.value
  if (!rows.length) return []
  const keys = new Set()
  rows.slice(0, 50).forEach(row => Object.keys(row).forEach(k => keys.add(k)))
  return Array.from(keys)
})

function extractRows(node) {
  if (typeof node === 'string') {
    const s = node.trim()
    if (s.startsWith('[') || s.startsWith('{')) {
      try { return extractRows(JSON.parse(s)) } catch { return [] }
    }
    return []
  }
  if (Array.isArray(node)) {
    if (node.length && node.every(x => x && typeof x === 'object' && !Array.isArray(x))) return node
    for (const item of node) {
      const found = extractRows(item)
      if (found.length) return found
    }
  } else if (node && typeof node === 'object') {
    for (const key of ['rows', 'data', 'result', 'output', 'list', 'items', 'records']) {
      if (key in node) {
        const found = extractRows(node[key])
        if (found.length) return found
      }
    }
    for (const v of Object.values(node)) {
      const found = extractRows(v)
      if (found.length) return found
    }
  }
  return []
}

function triggerPick() {
  fileInput.value?.click()
}

function stopTimers() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null }
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  elapsed.value = 0
  progressText.value = '正在上传文件到影刀…'
  showPanel.value = true
  activeRecord.value = null

  elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)

  try {
    const record = await uploadExcel(file)
    progressText.value = '文件已上传，流程开始执行…'
    activeRecord.value = record
    await loadRecords()
    pollStatus(record.id)   // 开始轮询
  } catch (err) {
    progressText.value = `上传请求暂未确认，可能仍在处理中…（${err.message || '网络异常'}）`
    showToast('上传请求暂未确认，请稍后查看处理结果', 'warn', 6000)
    await loadRecords()
    stopTimers()
    uploading.value = false
    showPanel.value = true
  } finally {
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function pollStatus(id) {
  try {
    const rec = await fetchUploadStatus(id)
    activeRecord.value = rec

    if (rec.status === 'success') {
      stopTimers()
      uploading.value = false
      const n = extractRows(rec.result).length
      const saved = rec.saved_count ?? 0
      progressText.value = ''
      showToast(
        saved > 0
          ? `处理完成，解析 ${n} 条，入库 ${saved} 条，已刷新分析`
          : `处理完成，解析 ${n} 条，入库 0 条，请检查表头字段是否匹配`,
        saved > 0 ? 'success' : 'warn',
        6000
      )
      await loadRecords()
      emit('saved', { saved, parsed: n, record: rec })
      return
    }
    if (rec.status === 'failed') {
      stopTimers()
      uploading.value = false
      progressText.value = ''
      showToast(rec.error || '流程执行失败', 'error', 6000)
      await loadRecords()
      return
    }
    progressText.value = `流程执行中，请稍候…（已等待 ${elapsed.value} 秒）`
    pollTimer = setTimeout(() => pollStatus(id), 3000)
  } catch (err) {
    progressText.value = `查询进度中…（已等待 ${elapsed.value} 秒）`
    pollTimer = setTimeout(() => pollStatus(id), 3000)
  }
}

async function loadRecords() {
  try {
    records.value = await fetchUploadRecords(20)
  } catch { /* ignore */ }
}

function openRecord(rec) {
  if (uploading.value) return
  activeRecord.value = rec
  showPanel.value = true
}

function closePanel() {
  if (uploading.value) return   // 处理中不允许关闭，避免误中断进度查看
  showPanel.value = false
}

async function removeRecord(rec) {
  if (deletingId.value) return
  if (!window.confirm(`确定删除记录「${rec.filename}」吗？此操作不可恢复。`)) return
  deletingId.value = rec.id
  try {
    await deleteUploadRecord(rec.id)
    records.value = records.value.filter(r => r.id !== rec.id)
    // 若删除的是当前查看的记录，切换到下一条或清空
    if (activeRecord.value && activeRecord.value.id === rec.id) {
      activeRecord.value = records.value[0] || null
    }
    showToast('记录已删除', 'success')
  } catch (err) {
    showToast(err.message || '删除失败', 'error', 5000)
  } finally {
    deletingId.value = null
  }
}

function fmtTime(t) {
  if (!t) return '—'
  return new Date(t).toLocaleString('zh-CN')
}

function cellText(v) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

onMounted(loadRecords)
onUnmounted(stopTimers)
</script>

<template>
  <div class="upload-widget">
    <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" style="display:none" @change="onFileChange" />

    <div class="upload-actions">
      <button class="btn btn-primary" :disabled="uploading" @click="triggerPick">
        <span v-if="uploading" class="upload-spin">⏳</span>
        <span v-else>📤</span>
        {{ uploading ? `处理中 ${elapsed}s` : '上传 Excel' }}
      </button>
      <button v-if="records.length" class="btn btn-outline" @click="showPanel = !showPanel">
        📋 处理结果 ({{ records.length }})
      </button>
    </div>
    <p class="upload-hint t-tertiary">若数据量大，解析需要等待</p>

    <!-- Result modal -->
    <Modal :show="showPanel || uploading" title="📊 Excel 处理结果" @close="closePanel">
      <!-- Live progress (running) -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-spinner"></div>
        <div style="flex:1; min-width:0;">
          <div class="t-primary" style="font-size:14px; font-weight:600;">{{ progressText || '处理中…' }}</div>
          <div class="t-tertiary" style="font-size:12px; margin-top:2px;">已用时 {{ elapsed }} 秒 · 流程在影刀云端执行，请勿关闭页面</div>
        </div>
        <div class="progress-bar-indeterminate"><span></span></div>
      </div>

      <!-- Records selector -->
      <div v-if="records.length" class="record-chips">
        <span
          v-for="rec in records"
          :key="rec.id"
          class="record-chip chip"
          :class="{
            'chip-info': activeRecord && activeRecord.id === rec.id,
            'chip-danger': rec.status === 'failed',
            'chip-warn': rec.status === 'running' || rec.status === 'pending'
          }"
        >
          <span class="chip-clickable record-chip-label" @click="openRecord(rec)">
            {{ rec.filename }} · {{ recordStatusLabel(rec) }}
          </span>
          <button
            class="record-del-btn"
            :disabled="deletingId === rec.id"
            title="删除此记录"
            @click.stop="removeRecord(rec)"
          >{{ deletingId === rec.id ? '⏳' : '✕' }}</button>
        </span>
      </div>

      <div v-if="!records.length && !uploading" class="t-tertiary" style="font-size:13px; padding:20px 0; text-align:center;">
        暂无处理记录
      </div>

      <template v-if="activeRecord">
        <div class="record-meta t-tertiary">
          <span>文件：{{ activeRecord.filename }} ｜ 状态：{{ recordStatusLabel(activeRecord) }} ｜ 上传人：{{ activeRecord.created_by || '—' }} ｜ 入库：{{ activeRecord.saved_count ?? 0 }} 条 ｜ 时间：{{ fmtTime(activeRecord.created_at) }}</span>
          <button
            class="btn btn-outline btn-sm record-del-current"
            :disabled="deletingId === activeRecord.id"
            @click="removeRecord(activeRecord)"
          >🗑️ 删除此记录</button>
        </div>

        <div v-if="activeRecord.status === 'failed'" class="t-danger" style="font-size:13px; padding:12px; background:rgba(239,68,68,0.08); border-radius:10px;">
          ⚠️ {{ activeRecord.error }}
        </div>

        <div v-else-if="activeRecord.status === 'running' || activeRecord.status === 'pending'" class="t-secondary" style="font-size:13px; padding:12px; background:rgba(59,130,246,0.08); border-radius:10px;">
          流程仍在处理中，系统会继续轮询。{{ activeRecord.error || '' }}
        </div>

        <!-- Data table -->
        <div v-else-if="tableRows.length" class="scroll-area" style="max-height:420px; border-radius:12px;">
          <table class="upload-table">
            <thead>
              <tr>
                <th>#</th>
                <th v-for="col in tableColumns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in tableRows" :key="i">
                <td class="t-tertiary">{{ i + 1 }}</td>
                <td v-for="col in tableColumns" :key="col">{{ cellText(row[col]) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Raw JSON fallback -->
        <div v-else>
          <div class="t-tertiary" style="font-size:12px; margin-bottom:6px;">原始返回结果：</div>
          <pre class="upload-json">{{ JSON.stringify(activeRecord.result, null, 2) }}</pre>
        </div>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.upload-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.upload-hint { margin-top: 6px; font-size: 12px; text-align: right; }
.upload-spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Record chips with inline delete */
.record-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.record-chip { display: inline-flex; align-items: center; gap: 6px; padding-right: 4px; }
.record-chip-label { cursor: pointer; }
.record-del-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; flex-shrink: 0;
  border: none; border-radius: 50%; cursor: pointer;
  font-size: 11px; line-height: 1;
  color: var(--t-secondary); background: rgba(148,163,184,0.2);
  transition: background 0.15s, color 0.15s;
}
.record-del-btn:hover:not(:disabled) { background: #ef4444; color: #fff; }
.record-del-btn:disabled { cursor: default; opacity: 0.6; }
.record-meta {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  flex-wrap: wrap; font-size: 12px; margin-bottom: 12px;
}
.record-del-current { flex-shrink: 0; }

/* Live progress block */
.upload-progress {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; margin-bottom: 14px;
  border-radius: 14px;
  background: rgba(59,130,246,0.08);
  border: 1px solid rgba(59,130,246,0.2);
}
.progress-spinner {
  width: 28px; height: 28px; flex-shrink: 0;
  border: 3px solid rgba(59,130,246,0.25);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
.progress-bar-indeterminate {
  position: relative; width: 120px; height: 6px; flex-shrink: 0;
  background: rgba(59,130,246,0.15); border-radius: 999px; overflow: hidden;
}
.progress-bar-indeterminate span {
  position: absolute; left: 0; top: 0; height: 100%; width: 40%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  border-radius: 999px;
  animation: indeterminate 1.2s ease-in-out infinite;
}
@keyframes indeterminate {
  0% { left: -40%; }
  100% { left: 100%; }
}

.upload-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.upload-table th, .upload-table td {
  padding: 8px 12px; text-align: left; white-space: nowrap;
  border-bottom: 1px solid rgba(148,163,184,0.18);
}
.upload-table th {
  position: sticky; top: 0;
  background: rgba(248,250,252,0.95); backdrop-filter: blur(8px);
  font-weight: 600; color: var(--t-secondary); font-size: 12px;
}
.upload-table tbody tr:hover { background: rgba(59,130,246,0.05); }
body.dark .upload-table th { background: rgba(30,41,59,0.95); }

.upload-json {
  font-size: 12px; line-height: 1.5; max-height: 360px; overflow: auto;
  padding: 12px; border-radius: 10px;
  background: rgba(148,163,184,0.1); color: var(--t-secondary);
  white-space: pre-wrap; word-break: break-all;
}
</style>
