<template>
  <n-spin :show="loading">
    <template v-if="instance">
      <n-space vertical :size="16">
        <!-- 标题栏 -->
        <n-flex justify="space-between" align="center">
          <n-space align="center">
            <n-h2 style="margin: 0">{{ instance.name }}</n-h2>
            <n-tag v-if="instance.enabled" type="success" size="small" :bordered="false">已启用</n-tag>
            <n-tag v-else type="warning" size="small" :bordered="false">已禁用</n-tag>
          </n-space>
          <n-space>
            <n-button @click="handleToggleEnabled">
              {{ instance.enabled ? '禁用' : '启用' }}
            </n-button>
            <n-button type="primary" :loading="running" @click="handleRun">
              <template #icon><n-icon><PlayFilledAlt /></n-icon></template>
              运行
            </n-button>
            <n-popconfirm @positive-click="handleDelete">
              <template #trigger>
                <n-button type="error" secondary>
                  <template #icon><n-icon><TrashCan /></n-icon></template>
                  删除
                </n-button>
              </template>
              确定删除实例「{{ instance.name }}」吗？
            </n-popconfirm>
          </n-space>
        </n-flex>

        <!-- 基本信息 -->
        <n-card title="基本信息" :bordered="true" size="small">
          <n-descriptions label-placement="left" bordered :column="2">
            <n-descriptions-item label="所属脚本">{{ instance.script_name }}</n-descriptions-item>
            <n-descriptions-item label="调度方式">{{ scheduleLabel }}</n-descriptions-item>
            <n-descriptions-item label="最后运行">{{ instance.last_run_at ? new Date(instance.last_run_at).toLocaleString() : '从未运行' }}</n-descriptions-item>
            <n-descriptions-item label="运行状态">
              <n-tag v-if="instance.last_run_status" :type="instance.last_run_status === 'success' ? 'success' : 'error'" size="small" :bordered="false">
                {{ instance.last_run_status === 'success' ? '成功' : '失败' }}
              </n-tag>
              <span v-else>-</span>
            </n-descriptions-item>
            <n-descriptions-item v-if="instance.last_error" label="错误信息" :span="2">
              <n-text type="error" style="font-size: 13px">{{ instance.last_error }}</n-text>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- RSS 订阅地址 -->
        <n-card title="RSS 订阅地址" :bordered="true" size="small">
          <RSSLinkDisplay :url="instance.rss_url" :width="500" />
        </n-card>

        <!-- 参数配置 -->
        <n-card title="参数配置" :bordered="true" size="small">
          <n-empty v-if="Object.keys(instance.params).length === 0" description="无配置参数" />
          <n-descriptions v-else label-placement="left" bordered :column="1">
            <n-descriptions-item v-for="(val, key) in instance.params" :key="key" :label="key">
              {{ typeof val === 'object' ? JSON.stringify(val) : String(val) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 运行历史 -->
        <n-card title="运行历史" :bordered="true" size="small">
          <n-data-table
            :columns="historyColumns"
            :data="history"
            :loading="historyLoading"
            :bordered="false"
            size="small"
            :max-height="300"
          />
        </n-card>

        <!-- RSS 条目预览 -->
        <n-card title="RSS 条目预览" :bordered="true" size="small">
          <n-data-table
            :columns="itemColumns"
            :data="items"
            :loading="itemsLoading"
            :bordered="false"
            size="small"
            :max-height="400"
          />
        </n-card>
      </n-space>
    </template>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui'
import { PlayFilledAlt, TrashCan } from '@vicons/carbon'
import type { DataTableColumn } from 'naive-ui'
import { useInstanceStore } from '@/stores/instances'
import type { Instance, RunHistory, RSSItem } from '@/stores/instances'
import RSSLinkDisplay from '@/components/RSSLinkDisplay.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const instanceStore = useInstanceStore()

const loading = ref(true)
const running = ref(false)
const historyLoading = ref(false)
const itemsLoading = ref(false)
const instance = ref<Instance | null>(null)
const history = ref<RunHistory[]>([])
const items = ref<RSSItem[]>([])

const scheduleLabel = computed(() => {
  const labels: Record<string, string> = { interval: '间隔触发', cron: '定时触发', on_refresh: '刷新触发', manual: '手动触发' }
  return labels[instance.value?.schedule_type || ''] || instance.value?.schedule_type
})

onMounted(async () => {
  const id = route.params.id as string
  instance.value = await instanceStore.fetchOne(id)
  loading.value = false
  await loadHistory()
  await loadItems()
})

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await instanceStore.fetchHistory(route.params.id as string)
    history.value = res.items
  } finally {
    historyLoading.value = false
  }
}

async function loadItems() {
  itemsLoading.value = true
  try {
    const res = await instanceStore.fetchItems(route.params.id as string)
    items.value = res.items
  } finally {
    itemsLoading.value = false
  }
}

async function handleRun() {
  running.value = true
  try {
    await instanceStore.run(route.params.id as string)
    message.success('已触发运行')
    // Refresh
    instance.value = await instanceStore.fetchOne(route.params.id as string)
    await loadHistory()
    await loadItems()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '运行失败')
  } finally {
    running.value = false
  }
}

async function handleToggleEnabled() {
  if (!instance.value) return
  try {
    instance.value = await instanceStore.update(instance.value.id, {
      enabled: !instance.value.enabled,
    })
    message.success(instance.value.enabled ? '已启用' : '已禁用')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  }
}

function handleDelete() {
  dialog.warning({
    title: '确认删除',
    content: `确定删除实例「${instance.value?.name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await instanceStore.remove(route.params.id as string)
        message.success('删除成功')
        router.push('/instances')
      } catch (e: any) {
        message.error(e.response?.data?.detail || '删除失败')
      }
    },
  })
}

const historyColumns: DataTableColumn[] = [
  { title: '时间', key: 'started_at', width: 160, render: (row: any) => row.started_at ? new Date(row.started_at).toLocaleString() : '-' },
  { title: '状态', key: 'status', width: 80, render: (row: any) => h(NTag, { type: row.status === 'success' ? 'success' : row.status === 'error' ? 'error' : 'warning', size: 'small', bordered: false }, { default: () => row.status === 'success' ? '成功' : row.status === 'error' ? '失败' : '运行中' }) },
  { title: '条目数', key: 'items_count', width: 70 },
  { title: '耗时(ms)', key: 'duration_ms', width: 90, render: (row: any) => row.duration_ms ?? '-' },
  { title: '错误信息', key: 'error_message', ellipsis: { tooltip: true }, render: (row: any) => row.error_message || '-' },
]

const itemColumns: DataTableColumn[] = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true }, width: 300, render: (row: any) => row.link ? h('a', { href: row.link, target: '_blank', style: { color: '#2080f0' } }, row.title || '(无标题)') : row.title || '(无标题)' },
  { title: '发布时间', key: 'pub_date', width: 160, render: (row: any) => row.pub_date ? new Date(row.pub_date).toLocaleString() : '-' },
  { title: '作者', key: 'author', width: 120, render: (row: any) => row.author || '-' },
]
</script>
