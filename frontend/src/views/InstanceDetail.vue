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
            <n-button @click="openEditModal">编辑配置</n-button>
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

  <n-modal v-model:show="showEditModal" preset="card" title="编辑实例" style="width: 760px">
    <n-space vertical :size="12">
      <n-form-item label="实例名称" required>
        <n-input v-model:value="editForm.name" placeholder="实例名称" />
      </n-form-item>
      <n-form-item label="描述">
        <n-input v-model:value="editForm.description" placeholder="可选描述" />
      </n-form-item>
      <n-form-item label="RSS 路径别名">
        <n-input v-model:value="editForm.rss_slug" placeholder="可选, 如 vue-releases" />
      </n-form-item>
      <n-form-item label="最大条目数">
        <n-input-number v-model:value="editForm.max_items" :min="10" :max="500" style="width: 140px" />
      </n-form-item>

      <n-card size="small" title="参数配置" :bordered="true">
        <ParamForm
          v-if="selectedScript && selectedScript.params_schema?.length > 0"
          :params="selectedScript.params_schema"
          v-model:model-value="editForm.params"
        />
        <n-empty v-else description="此脚本没有可配置参数" />
      </n-card>

      <n-card size="small" title="调度配置" :bordered="true">
        <ScheduleConfig
          :model-value="{ type: editForm.schedule_type, config: editForm.schedule_config }"
          @update:model-value="onEditScheduleChange"
        />
      </n-card>
    </n-space>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" :loading="savingEdit" @click="handleSaveEdit">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui'
import { PlayFilledAlt, TrashCan } from '@vicons/carbon'
import type { DataTableColumn } from 'naive-ui'
import { useInstanceStore } from '@/stores/instances'
import { useScriptStore } from '@/stores/scripts'
import type { Instance, RunHistory, RSSItem } from '@/stores/instances'
import RSSLinkDisplay from '@/components/RSSLinkDisplay.vue'
import ParamForm from '@/components/ParamForm.vue'
import ScheduleConfig from '@/components/ScheduleConfig.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const instanceStore = useInstanceStore()
const scriptStore = useScriptStore()

const loading = ref(true)
const running = ref(false)
const historyLoading = ref(false)
const itemsLoading = ref(false)
const showEditModal = ref(false)
const savingEdit = ref(false)
const instance = ref<Instance | null>(null)
const history = ref<RunHistory[]>([])
const items = ref<RSSItem[]>([])
const selectedScript = computed(() => scriptStore.currentScript)

const editForm = ref({
  name: '',
  description: '',
  params: {} as Record<string, any>,
  schedule_type: 'interval',
  schedule_config: { interval_minutes: 60 } as Record<string, any> | null,
  rss_slug: '',
  max_items: 100,
})

const scheduleLabel = computed(() => {
  const labels: Record<string, string> = { interval: '间隔触发', cron: '定时触发', on_refresh: '刷新触发', manual: '手动触发' }
  return labels[instance.value?.schedule_type || ''] || instance.value?.schedule_type
})

onMounted(async () => {
  const id = route.params.id as string
  instance.value = await instanceStore.fetchOne(id)
  if (instance.value?.script_id) {
    await scriptStore.fetchOne(instance.value.script_id)
  }
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
  const currentInstance = instance.value
  if (!currentInstance) return
  try {
    const updatedInstance = await instanceStore.update(currentInstance.id, {
      enabled: !currentInstance.enabled,
    })
    instance.value = updatedInstance
    message.success(updatedInstance.enabled ? '已启用' : '已禁用')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '操作失败')
  }
}

function openEditModal() {
  if (!instance.value) return
  editForm.value = {
    name: instance.value.name,
    description: instance.value.description || '',
    params: { ...(instance.value.params || {}) },
    schedule_type: instance.value.schedule_type || 'interval',
    schedule_config: instance.value.schedule_config ? { ...instance.value.schedule_config } : { interval_minutes: 60 },
    rss_slug: instance.value.rss_slug || '',
    max_items: instance.value.max_items || 100,
  }
  showEditModal.value = true
}

function onEditScheduleChange(val: { type: string; config: Record<string, any> | null }) {
  editForm.value.schedule_type = val.type
  editForm.value.schedule_config = val.config
}

async function handleSaveEdit() {
  if (!instance.value) return
  if (!editForm.value.name.trim()) {
    message.error('实例名称不能为空')
    return
  }

  savingEdit.value = true
  try {
    const updated = await instanceStore.update(instance.value.id, {
      name: editForm.value.name.trim(),
      description: editForm.value.description,
      params: editForm.value.params,
      schedule_type: editForm.value.schedule_type,
      schedule_config: editForm.value.schedule_config,
      rss_slug: editForm.value.rss_slug,
      max_items: editForm.value.max_items,
    })
    instance.value = updated
    showEditModal.value = false
    message.success('实例更新成功')
    await loadItems()
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') {
      message.error(detail)
    } else if (detail?.message) {
      message.error(detail.message)
    } else {
      message.error('更新失败')
    }
  } finally {
    savingEdit.value = false
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
        const detail = e.response?.data?.detail
        if (typeof detail === 'string') {
          message.error(detail)
        } else if (detail?.message) {
          const groups = Array.isArray(detail.merge_groups) ? detail.merge_groups.join('、') : ''
          message.error(groups ? `${detail.message}: ${groups}` : detail.message)
        } else {
          message.error('删除失败')
        }
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
