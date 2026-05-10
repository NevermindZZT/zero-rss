<template>
  <n-space vertical>
    <n-radio-group v-model:value="scheduleType">
      <n-radio-button value="interval">间隔触发</n-radio-button>
      <n-radio-button value="cron">定时触发</n-radio-button>
      <n-radio-button value="on_refresh">刷新触发</n-radio-button>
      <n-radio-button value="manual">手动触发</n-radio-button>
    </n-radio-group>

    <n-card size="small" :bordered="true">
      <!-- 间隔触发 -->
      <template v-if="scheduleType === 'interval'">
        <n-form-item label="间隔时间">
          <n-input-number
            v-model:value="intervalMinutes"
            :min="1"
            :max="43200"
            style="width: 200px"
          >
            <template #suffix>分钟</template>
          </n-input-number>
        </n-form-item>
        <n-text depth="3">每隔 {{ intervalMinutes }} 分钟自动执行一次</n-text>
      </template>

      <!-- 定时触发 -->
      <template v-else-if="scheduleType === 'cron'">
        <n-alert type="info" :bordered="false" style="margin-bottom: 12px">
          定时触发支持多个时间点，使用 cron 表达式 (分 时 日 月 周)。
          <br />示例: <n-tag size="small">0 8 * * *</n-tag> 表示每天 8:00
        </n-alert>
        <div v-for="(expr, idx) in cronExpressions" :key="idx" style="margin-bottom: 8px">
          <n-space>
            <n-input
              v-model:value="cronExpressions[idx]"
              placeholder="0 8 * * *"
              style="width: 240px"
            />
            <n-button v-if="cronExpressions.length > 1" quaternary circle size="small" @click="removeCron(idx)">
              <template #icon><n-icon><Close /></n-icon></template>
            </n-button>
          </n-space>
          <n-text depth="3" style="font-size: 12px">
            {{ describeCron(expr) }}
          </n-text>
        </div>
        <n-button size="small" @click="addCron">
          <template #icon><n-icon><Add /></n-icon></template>
          添加时间点
        </n-button>
      </template>

      <!-- 刷新触发 -->
      <template v-else-if="scheduleType === 'on_refresh'">
        <n-form-item label="过期时间">
          <n-input-number
            v-model:value="refreshInterval"
            :min="1"
            :max="43200"
            style="width: 200px"
          >
            <template #suffix>分钟</template>
          </n-input-number>
        </n-form-item>
        <n-text depth="3">
          访问 RSS 时，如果距离上次更新超过 {{ refreshInterval }} 分钟，则自动触发更新
        </n-text>
      </template>

      <!-- 手动触发 -->
      <template v-else>
        <n-text depth="3">仅通过前端页面手动点击执行，不会自动运行</n-text>
      </template>
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { NIcon } from 'naive-ui'
import { Close, Add } from '@vicons/carbon'

const props = defineProps<{
  modelValue: { type: string; config: Record<string, any> | null }
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: { type: string; config: Record<string, any> | null }): void
}>()

const scheduleType = ref(props.modelValue?.type || 'interval')
const intervalMinutes = ref(60)
const cronExpressions = ref<string[]>(['0 8 * * *'])
const refreshInterval = ref(30)

// 从外部 modelValue 初始化
watch(() => props.modelValue, (val) => {
  if (val?.type) {
    scheduleType.value = val.type
    if (val.config) {
      if (val.type === 'interval' && val.config.interval_minutes) {
        intervalMinutes.value = val.config.interval_minutes
      }
      if (val.type === 'cron' && val.config.cron_expressions) {
        cronExpressions.value = [...val.config.cron_expressions]
      }
      if (val.type === 'on_refresh' && val.config.refresh_interval_minutes) {
        refreshInterval.value = val.config.refresh_interval_minutes
      }
    }
  }
}, { immediate: true })

// 输出配置
function buildConfig() {
  switch (scheduleType.value) {
    case 'interval':
      return { type: 'interval', config: { interval_minutes: intervalMinutes.value } }
    case 'cron':
      return { type: 'cron', config: { cron_expressions: cronExpressions.value.filter(Boolean) } }
    case 'on_refresh':
      return { type: 'on_refresh', config: { refresh_interval_minutes: refreshInterval.value } }
    default:
      return { type: 'manual', config: {} }
  }
}

// 任何变更时 emit
watch([scheduleType, intervalMinutes, cronExpressions, refreshInterval], () => {
  emit('update:modelValue', buildConfig())
}, { deep: true })

function addCron() {
  cronExpressions.value.push('0 12 * * *')
}

function removeCron(idx: number) {
  cronExpressions.value.splice(idx, 1)
}

function describeCron(expr: string): string {
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return '无效表达式'
  const [min, hour] = parts
  if (min === '0' && hour !== '*') return `每天 ${hour.padStart(2, '0')}:00`
  if (min === '0' && hour === '*') return '每小时整点'
  return `分: ${min} 时: ${hour}`
}
</script>
