<template>
  <n-space vertical :size="16">
    <n-flex justify="space-between" align="center">
      <n-h2 style="margin: 0">脚本管理</n-h2>
      <n-upload
        :default-upload="false"
        accept=".py"
        @change="handleUpload"
      >
        <n-button type="primary">
          <template #icon><n-icon><Upload /></n-icon></template>
          上传脚本
        </n-button>
      </n-upload>
    </n-flex>

    <n-input
      v-model:value="search"
      placeholder="搜索脚本名称或文件名..."
      clearable
      @input="handleSearch"
    >
      <template #prefix>
        <n-icon><Search /></n-icon>
      </template>
    </n-input>

    <n-spin :show="loading">
      <n-empty v-if="!loading && scripts.length === 0" description="暂无脚本，点击上方按钮上传">
        <template #icon><n-icon size="48"><Code /></n-icon></template>
      </n-empty>

      <n-grid v-else :cols="3" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi v-for="script in scripts" :key="script.id">
          <n-card
            :title="script.name"
            :bordered="true"
            hoverable
            @click="$router.push({ name: 'ScriptDetail', params: { id: script.id } })"
            style="cursor: pointer"
          >
            <template #header-extra>
              <n-tag size="small" :bordered="false">{{ script.version }}</n-tag>
            </template>
            <p style="color: #888; font-size: 13px; margin: 0; min-height: 40px">
              {{ script.description || '暂无描述' }}
            </p>
            <template #footer>
              <n-space justify="space-between">
                <n-text depth="3" style="font-size: 12px">{{ script.filename }}</n-text>
                <n-text depth="3" style="font-size: 12px">{{ script.instance_count || 0 }} 个实例</n-text>
              </n-space>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NIcon, useMessage, useDialog } from 'naive-ui'
import { Upload, Search, Code } from '@vicons/carbon'
import { useScriptStore } from '@/stores/scripts'

const message = useMessage()
const dialog = useDialog()
const scriptStore = useScriptStore()

const loading = ref(false)
const search = ref('')
const scripts = ref<any[]>([])

onMounted(async () => {
  await loadScripts()
})

async function loadScripts() {
  loading.value = true
  try {
    await scriptStore.fetchAll(search.value)
    scripts.value = scriptStore.scripts
  } finally {
    loading.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout>
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadScripts, 300)
}

async function handleUpload({ file }: { file: any }) {
  if (!file.file) return
  if (!file.name?.endsWith('.py')) {
    message.error('只支持 .py 文件')
    return
  }
  try {
    await scriptStore.uploadScript(file.file)
    message.success('脚本上传成功')
    await loadScripts()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '上传失败')
  }
}
</script>
