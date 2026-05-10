<template>
  <n-space vertical :size="16">
    <n-flex justify="space-between" align="center">
      <n-h2 style="margin: 0">合并源管理</n-h2>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon><n-icon><Add /></n-icon></template>
        创建合并源
      </n-button>
    </n-flex>

    <n-data-table
      :columns="columns"
      :data="groups"
      :loading="loading"
      :bordered="true"
      size="small"
    />
    <n-empty v-if="!loading && groups.length === 0" description="暂无合并源" />
  </n-space>

  <!-- 创建/编辑对话框 -->
  <n-modal v-model:show="showCreateModal" title="创建合并源" preset="card" style="width: 600px">
    <n-form>
      <n-form-item label="名称" required>
        <n-input v-model:value="form.name" placeholder="合并源名称" />
      </n-form-item>
      <n-form-item label="描述">
        <n-input v-model:value="form.description" placeholder="可选描述" />
      </n-form-item>
      <n-form-item label="选择实例" required>
        <n-select v-model:value="form.instance_ids" :options="instanceOptions" multiple filterable placeholder="选择要合并的实例" />
      </n-form-item>
      <n-form-item label="最大条目数">
        <n-input-number v-model:value="form.max_items" :min="10" :max="500" style="width: 120px" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleCreate">创建</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, h, onMounted, reactive } from 'vue'
import { NIcon, useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui'
import { Add, TrashCan } from '@vicons/carbon'
import type { DataTableColumn } from 'naive-ui'
import { useMergeGroupStore } from '@/stores/mergeGroups'
import { useInstanceStore } from '@/stores/instances'
import type { MergeGroup } from '@/stores/mergeGroups'
import RSSLinkDisplay from '@/components/RSSLinkDisplay.vue'

const message = useMessage()
const dialog = useDialog()
const mergeStore = useMergeGroupStore()
const instanceStore = useInstanceStore()

const loading = ref(true)
const submitting = ref(false)
const showCreateModal = ref(false)
const groups = ref<MergeGroup[]>([])

const form = reactive({
  name: '',
  description: '',
  instance_ids: [] as string[],
  max_items: 100,
})

const instanceOptions = ref<{ label: string; value: string }[]>([])

onMounted(async () => {
  await Promise.all([mergeStore.fetchAll(), instanceStore.fetchAll()])
  groups.value = mergeStore.groups
  instanceOptions.value = instanceStore.instances.map((i) => ({
    label: `${i.name} (${i.script_name})`,
    value: i.id,
  }))
  loading.value = false
})

const columns: DataTableColumn[] = [
  { title: '名称', key: 'name', ellipsis: { tooltip: true } },
  {
    title: '实例数',
    key: 'instance_ids',
    width: 80,
    render: (row: any) => row.instance_ids?.length || 0,
  },
  {
    title: 'RSS 地址',
    key: 'rss_url',
    width: 400,
    render: (row: any) => h(RSSLinkDisplay, { url: row.rss_url, width: 320 }),
  },
  {
    title: '最大条目',
    key: 'max_items',
    width: 80,
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: any) => h(NButton, {
      size: 'tiny',
      type: 'error',
      quaternary: true,
      onClick: () => handleDelete(row),
    }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(TrashCan) }) }),
  },
]

async function handleCreate() {
  if (!form.name) { message.error('请输入名称'); return }
  if (!form.instance_ids.length) { message.error('请选择至少一个实例'); return }
  submitting.value = true
  try {
    await mergeStore.create({ ...form })
    message.success('创建成功')
    showCreateModal.value = false
    groups.value = mergeStore.groups
    form.name = ''
    form.description = ''
    form.instance_ids = []
    form.max_items = 100
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

function handleDelete(group: MergeGroup) {
  dialog.warning({
    title: '确认删除',
    content: `确定删除合并源「${group.name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await mergeStore.remove(group.id)
        message.success('删除成功')
        groups.value = mergeStore.groups
      } catch (e: any) {
        message.error(e.response?.data?.detail || '删除失败')
      }
    },
  })
}
</script>
