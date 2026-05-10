<template>
  <n-spin :show="loading">
    <template v-if="script">
      <n-space vertical :size="16">
        <n-flex justify="space-between" align="center">
          <n-h2 style="margin: 0">{{ script.name }}</n-h2>
          <n-space>
            <n-upload :default-upload="false" accept=".py" @change="handleReupload">
              <n-button>
                <template #icon><n-icon><Upload /></n-icon></template>
                重新上传文件
              </n-button>
            </n-upload>
            <n-button @click="showEditor = !showEditor">
              <template #icon><n-icon><Code /></n-icon></template>
              {{ showEditor ? '关闭编辑' : '编辑代码' }}
            </n-button>
            <n-popconfirm @positive-click="handleDelete">
              <template #trigger>
                <n-button type="error" secondary>
                  <template #icon><n-icon><TrashCan /></n-icon></template>
                  删除
                </n-button>
              </template>
              确定删除脚本「{{ script.name }}」吗？所有关联的实例也会被删除。
            </n-popconfirm>
          </n-space>
        </n-flex>

        <n-descriptions label-placement="left" bordered :column="2">
          <n-descriptions-item label="文件名">{{ script.filename }}</n-descriptions-item>
          <n-descriptions-item label="版本">{{ script.version }}</n-descriptions-item>
          <n-descriptions-item label="描述" :span="2">{{ script.description || '-' }}</n-descriptions-item>
          <n-descriptions-item label="作者">{{ script.author || '-' }}</n-descriptions-item>
          <n-descriptions-item label="实例数">{{ relatedInstances.length }}</n-descriptions-item>
        </n-descriptions>

        <!-- 参数定义 -->
        <n-card title="参数定义" :bordered="true" size="small">
          <n-empty v-if="paramsSchema.length === 0" description="此脚本没有可配置参数" />
          <n-table v-else size="small">
            <thead>
              <tr><th>参数名</th><th>标签</th><th>类型</th><th>必填</th><th>默认值</th><th>说明</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in paramsSchema" :key="p.name">
                <td><n-code>{{ p.name }}</n-code></td>
                <td>{{ p.label }}</td>
                <td><n-tag size="small">{{ p.type }}</n-tag></td>
                <td>{{ p.required ? '是' : '否' }}</td>
                <td>{{ p.default ?? '-' }}</td>
                <td>{{ p.description || '-' }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-card>

        <!-- 代码编辑器 -->
        <n-card v-if="showEditor" title="编辑代码" :bordered="true" size="small">
          <n-input
            v-model:value="editCode"
            type="textarea"
            :rows="20"
            :autosize="{ minRows: 10, maxRows: 30 }"
            style="font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 13px"
          />
          <n-button type="primary" style="margin-top: 12px" :loading="saving" @click="saveCode">
            保存
          </n-button>
        </n-card>

        <!-- 关联实例 -->
        <n-card title="关联实例" :bordered="true" size="small">
          <n-empty v-if="relatedInstances.length === 0" description="暂无实例" />
          <n-data-table
            v-else
            :columns="instanceColumns"
            :data="relatedInstances"
            :bordered="false"
            size="small"
          />
        </n-card>
      </n-space>
    </template>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, useMessage, useDialog } from 'naive-ui'
import { Code, TrashCan, Upload } from '@vicons/carbon'
import { useScriptStore } from '@/stores/scripts'
import { useInstanceStore } from '@/stores/instances'
import type { DataTableColumn } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const scriptStore = useScriptStore()
const instanceStore = useInstanceStore()

const loading = ref(true)
const showEditor = ref(false)
const saving = ref(false)
const editCode = ref('')
const script = computed(() => scriptStore.currentScript)
const paramsSchema = computed(() => (script.value?.params_schema as any[]) || [])
const relatedInstances = computed(() =>
  instanceStore.instances.filter((i) => i.script_id === route.params.id)
)

const instanceColumns: DataTableColumn[] = [
  { title: '名称', key: 'name' },
  { title: '状态', key: 'enabled', render: (row: any) => h('span', row.enabled ? '已启用' : '已禁用') },
  { title: '最后运行', key: 'last_run_at', render: (row: any) => row.last_run_at ? new Date(row.last_run_at).toLocaleString() : '-' },
  { title: '状态', key: 'last_run_status', render: (row: any) => h('span', {
    style: { color: row.last_run_status === 'success' ? '#18a058' : row.last_run_status === 'error' ? '#d03050' : '#888' }
  }, row.last_run_status || '-') },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h('a', {
      href: `#/instances/${row.id}`,
      style: { color: '#2080f0', cursor: 'pointer' }
    }, '查看'),
  },
]

import { h } from 'vue'

onMounted(async () => {
  const id = route.params.id as string
  await scriptStore.fetchOne(id)
  editCode.value = scriptStore.currentScript?.code || ''
  await instanceStore.fetchAll()
  loading.value = false
})

async function saveCode() {
  saving.value = true
  try {
    await scriptStore.updateScript(route.params.id as string, editCode.value)
    message.success('保存成功')
    showEditor.value = false
  } catch (e: any) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleReupload({ file }: { file: any }) {
  if (!file?.file) return
  if (!file.name?.endsWith('.py')) {
    message.error('只支持 .py 文件')
    return
  }
  try {
    const updated = await scriptStore.updateScriptByUpload(route.params.id as string, file.file)
    editCode.value = updated.code || ''
    message.success('脚本文件更新成功')
  } catch (e: any) {
    const detail = e.response?.data?.detail
    message.error(typeof detail === 'string' ? detail : '更新失败')
  }
}

async function handleDelete() {
  try {
    await scriptStore.deleteScript(route.params.id as string)
    message.success('删除成功')
    router.push('/scripts')
  } catch (e: any) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}
</script>
