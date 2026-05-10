<template>
  <n-space vertical :size="16">
    <n-flex justify="space-between" align="center">
      <n-h2 style="margin: 0">实例管理</n-h2>
      <n-button type="primary" @click="$router.push({ name: 'InstanceCreate' })">
        <template #icon><n-icon><Add /></n-icon></template>
        创建实例
      </n-button>
    </n-flex>

    <n-data-table
      :columns="columns"
      :data="instances"
      :loading="loading"
      :bordered="true"
      :row-key="(row: any) => row.id"
      size="small"
      @update:page="handlePageChange"
    />

    <n-empty v-if="!loading && instances.length === 0" description="暂无实例" />
  </n-space>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NIcon, useMessage, useDialog, NTag, NSpace, NButton } from 'naive-ui'
import { Add, PlayFilledAlt, TrashCan } from '@vicons/carbon'
import type { DataTableColumn } from 'naive-ui'
import { useInstanceStore } from '@/stores/instances'
import type { Instance } from '@/stores/instances'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const instanceStore = useInstanceStore()

const loading = ref(true)
const instances = ref<Instance[]>([])

onMounted(async () => {
  loading.value = true
  await instanceStore.fetchAll()
  instances.value = instanceStore.instances
  loading.value = false
})

const columns: DataTableColumn[] = [
  {
    title: '名称',
    key: 'name',
    width: 180,
    render: (row: any) => h('a', {
      href: `#/instances/${row.id}`,
      style: { color: '#2080f0', cursor: 'pointer', fontWeight: 500 },
    }, row.name),
  },
  {
    title: '所属脚本',
    key: 'script_name',
    width: 140,
  },
  {
    title: '别名',
    key: 'rss_slug',
    width: 100,
    render: (row: any) => row.rss_slug || '-',
  },
  {
    title: '调度方式',
    key: 'schedule_type',
    width: 100,
    render: (row: any) => {
      const labels: Record<string, string> = {
        interval: '间隔触发',
        cron: '定时触发',
        on_refresh: '刷新触发',
        manual: '手动触发',
      }
      return h(NTag, { size: 'small', bordered: false }, { default: () => labels[row.schedule_type] || row.schedule_type })
    },
  },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render: (row: any) => h(NTag, {
      type: row.enabled ? 'success' : 'warning',
      size: 'small',
      bordered: false,
    }, { default: () => row.enabled ? '已启用' : '已禁用' }),
  },
  {
    title: '最后运行',
    key: 'last_run_at',
    width: 160,
    render: (row: any) => row.last_run_at ? new Date(row.last_run_at).toLocaleString() : '-',
  },
  {
    title: '运行状态',
    key: 'last_run_status',
    width: 90,
    render: (row: any) => {
      if (!row.last_run_status) return '-'
      const type = row.last_run_status === 'success' ? 'success' : 'error'
      return h(NTag, { type, size: 'small', bordered: false }, { default: () => row.last_run_status === 'success' ? '成功' : '失败' })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render: (row: any) => h(NSpace, null, {
      default: () => [
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          onClick: () => handleRun(row.id),
        }, { default: () => '运行', icon: () => h(NIcon, null, { default: () => h(PlayFilledAlt) }) }),
        h(NButton, {
          size: 'tiny',
          type: 'error',
          quaternary: true,
          onClick: () => handleDelete(row.id, row.name),
        }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(TrashCan) }) }),
      ],
    }),
  },
]

async function handleRun(id: string) {
  try {
    await instanceStore.run(id)
    message.success('已触发运行')
    // Refresh data
    await instanceStore.fetchAll()
    instances.value = instanceStore.instances
  } catch (e: any) {
    message.error(e.response?.data?.detail || '运行失败')
  }
}

function handleDelete(id: string, name: string) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除实例「${name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await instanceStore.remove(id)
        message.success('删除成功')
        instances.value = instanceStore.instances
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

function handlePageChange(page: number) {
  // 暂时只显示全部数据
}
</script>
