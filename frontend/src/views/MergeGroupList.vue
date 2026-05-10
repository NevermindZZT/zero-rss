<template>
  <n-space vertical :size="16">
    <n-flex justify="space-between" align="center">
      <n-h2 style="margin: 0">合并源管理</n-h2>
      <n-button type="primary" @click="openCreateModal">
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
  <n-modal v-model:show="showCreateModal" :title="editingId ? '编辑合并源' : '创建合并源'" preset="card" style="width: 600px">
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
      <n-form-item label="RSS 路径别名">
        <n-input v-model:value="form.rss_slug" placeholder="可选, 如 all-news (字母/数字/-/_组成)" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px">设置后 RSS 地址为 /rss/merge/<b>{{ form.rss_slug || '...' }}</b>.xml</n-text>
        </template>
      </n-form-item>
      <n-form-item label="最大条目数">
        <n-input-number v-model:value="form.max_items" :min="10" :max="500" style="width: 120px" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="closeModal">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">{{ editingId ? '保存' : '创建' }}</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, h, onMounted, reactive } from 'vue'
import { NIcon, useMessage, useDialog, NTag, NButton, NSpace } from 'naive-ui'
import { Add, TrashCan, Edit } from '@vicons/carbon'
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
const editingId = ref<string | null>(null)

const form = reactive({
  name: '',
  description: '',
  instance_ids: [] as string[],
  rss_slug: '',
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
    title: '别名',
    key: 'rss_slug',
    width: 100,
    render: (row: any) => row.rss_slug || '-',
  },
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
    width: 140,
    render: (row: any) => h(NSpace, { size: 2 }, {
      default: () => [
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          onClick: () => openEditModal(row),
        }, { default: () => '编辑', icon: () => h(NIcon, null, { default: () => h(Edit) }) }),
        h(NButton, {
          size: 'tiny',
          type: 'error',
          quaternary: true,
          onClick: () => handleDelete(row),
        }, { default: () => '删除', icon: () => h(NIcon, null, { default: () => h(TrashCan) }) }),
      ],
    }),
  },
]

function resetForm() {
  editingId.value = null
  form.name = ''
  form.description = ''
  form.instance_ids = []
  form.rss_slug = ''
  form.max_items = 100
}

function openCreateModal() {
  resetForm()
  showCreateModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  resetForm()
}

function openEditModal(group: MergeGroup) {
  editingId.value = group.id
  form.name = group.name
  form.description = group.description || ''
  form.instance_ids = [...(group.instance_ids || [])]
  form.rss_slug = group.rss_slug || ''
  form.max_items = group.max_items || 100
  showCreateModal.value = true
}

async function handleSubmit() {
  if (!form.name) { message.error('请输入名称'); return }
  if (!form.instance_ids.length) { message.error('请选择至少一个实例'); return }
  submitting.value = true
  try {
    if (editingId.value) {
      await mergeStore.update(editingId.value, { ...form })
      message.success('更新成功')
    } else {
      await mergeStore.create({ ...form })
      message.success('创建成功')
    }
    showCreateModal.value = false
    groups.value = mergeStore.groups
    resetForm()
  } catch (e: any) {
    message.error(e.response?.data?.detail || (editingId.value ? '更新失败' : '创建失败'))
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
