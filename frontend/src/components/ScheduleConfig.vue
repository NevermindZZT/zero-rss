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
          定时触发支持多个时间点。
          <br />支持 cron 表达式: <n-tag size="small">分 时 日 月 周</n-tag> 或 <n-tag size="small">秒 分 时 日 月 周</n-tag>
          <br />示例: <n-tag size="small">0 8 * * *</n-tag> 表示每天 8:00；<n-tag size="small">0 */5 * * * *</n-tag> 表示每 5 分钟触发
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
import { ref, watch } from 'vue'
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
const syncingFromProps = ref(false)

function modelSignature(val: { type: string; config: Record<string, any> | null } | undefined): string {
  const type = val?.type || 'interval'
  const config = val?.config || {}
  return `${type}|${JSON.stringify(config)}`
}

function applyFromModelValue(val: { type: string; config: Record<string, any> | null } | undefined) {
  const type = val?.type || 'interval'
  const config = val?.config || {}

  scheduleType.value = type

  if (type === 'interval') {
    intervalMinutes.value = Number(config.interval_minutes ?? 60)
  } else if (type === 'cron') {
    const exprs = Array.isArray(config.cron_expressions) ? config.cron_expressions : []
    cronExpressions.value = exprs.length ? [...exprs] : ['0 8 * * *']
  } else if (type === 'on_refresh') {
    refreshInterval.value = Number(config.refresh_interval_minutes ?? 30)
  }
}

// 从外部 modelValue 初始化
watch(
  () => modelSignature(props.modelValue),
  () => {
    syncingFromProps.value = true
    try {
      applyFromModelValue(props.modelValue)
    } finally {
      syncingFromProps.value = false
    }
  },
  { immediate: true }
)

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
  if (syncingFromProps.value) {
    return
  }
  const next = buildConfig()
  if (modelSignature(next) === modelSignature(props.modelValue)) {
    return
  }
  emit('update:modelValue', next)
}, { deep: true })

function addCron() {
  cronExpressions.value.push('0 12 * * *')
}

function removeCron(idx: number) {
  cronExpressions.value.splice(idx, 1)
}

function describeCron(expr: string): string {
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5 && parts.length !== 6) return '无效表达式'
  if (parts.length === 5) {
    const [min, hour] = parts
    if (min === '0' && hour !== '*') return `每天 ${hour.padStart(2, '0')}:00`
    if (min === '0' && hour === '*') return '每小时整点'
    return `分: ${min} 时: ${hour}`
  }
  const [sec, min, hour] = parts
  return `秒: ${sec} 分: ${min} 时: ${hour}`
}
</script>
