<template>
  <n-space vertical :size="24">
    <n-h2>仪表盘</n-h2>

    <n-grid :cols="4" :x-gap="16">
      <n-gi>
        <n-card :bordered="true">
          <n-statistic label="脚本模板" :value="stats.total_scripts">
            <template #prefix>
              <n-icon><Code /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="true">
          <n-statistic label="实例总数" :value="stats.total_instances">
            <template #prefix>
              <n-icon><Box /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="true">
          <n-statistic label="运行中实例" :value="stats.enabled_instances">
            <template #prefix>
              <n-icon><PlayFilledAlt /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="true">
          <n-statistic label="总条目数" :value="stats.total_items">
            <template #prefix>
              <n-icon><Document /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16">
      <n-gi>
        <n-card title="快速操作" :bordered="true">
          <n-space vertical>
            <n-button type="primary" @click="$router.push('/scripts')">
              <template #icon><n-icon><Code /></n-icon></template>
              管理脚本
            </n-button>
            <n-button @click="$router.push('/instances/create')">
              <template #icon><n-icon><Add /></n-icon></template>
              创建实例
            </n-button>
            <n-button @click="$router.push('/instances')">
              <template #icon><n-icon><Box /></n-icon></template>
              查看实例
            </n-button>
          </n-space>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="系统信息" :bordered="true">
          <n-descriptions :column="1">
            <n-descriptions-item label="系统状态">
              <n-tag type="success" :bordered="false">运行中</n-tag>
            </n-descriptions-item>
              <n-descriptions-item label="版本">{{ appVersion }}</n-descriptions-item>
            <n-descriptions-item label="最近错误">{{ stats.recent_errors }} 次</n-descriptions-item>
            <n-descriptions-item label="数据持久化">SQLite 本地存储</n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NIcon } from 'naive-ui'
import { Code, Box, PlayFilledAlt, Document, Add } from '@vicons/carbon'
import apiClient from '@/api/client'

const stats = ref({
  total_scripts: 0,
  total_instances: 0,
  total_items: 0,
  enabled_instances: 0,
  recent_errors: 0,
})
const appVersion = ref('unknown')

onMounted(async () => {
  try {
    const [statsRes, healthRes] = await Promise.all([
      apiClient.get('/api/system/stats'),
      apiClient.get('/api/system/health'),
    ])
    stats.value = statsRes.data
    appVersion.value = healthRes.data?.version || 'unknown'
  } catch {
    // ignore
  }
})
</script>
