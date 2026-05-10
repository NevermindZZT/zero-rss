<template>
  <n-space vertical :size="16">
    <n-h2>创建实例</n-h2>

    <n-card :bordered="true">
      <n-steps :current="step" :status="stepStatus">
        <n-step title="选择脚本" />
        <n-step title="配置参数" />
        <n-step title="调度配置" />
        <n-step title="确认创建" />
      </n-steps>
    </n-card>

    <!-- 步骤 1: 选择脚本 -->
    <n-card v-if="step === 0" title="选择脚本" :bordered="true">
      <n-select
        v-model:value="form.script_id"
        :options="scriptOptions"
        placeholder="请选择脚本模板"
        filterable
        clearable
        @update:value="onScriptChange"
      />
      <n-p v-if="selectedScript" style="margin-top: 12px; color: #888">
        {{ selectedScript.description }}
      </n-p>
    </n-card>

    <!-- 步骤 2: 配置参数 -->
    <n-card v-if="step === 1" title="配置参数" :bordered="true">
      <template v-if="selectedScript && selectedScript.params_schema?.length > 0">
        <ParamForm
          ref="paramFormRef"
          :params="selectedScript.params_schema"
          v-model:model-value="form.params"
        />
      </template>
      <n-empty v-else description="此脚本无需配置参数" />
    </n-card>

    <!-- 步骤 3: 调度配置 -->
    <n-card v-if="step === 2" title="调度配置" :bordered="true">
      <n-form-item label="实例名称" required>
        <n-input v-model:value="form.name" placeholder="为此实例命名" />
      </n-form-item>
      <n-form-item label="描述">
        <n-input v-model:value="form.description" placeholder="可选描述" />
      </n-form-item>
      <n-form-item label="RSS 路径别名">
        <n-input v-model:value="form.rss_slug" placeholder="可选, 如 vue-releases (字母/数字/-/_组成)" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px">设置后 RSS 地址为 /rss/<b>{{ form.rss_slug || '...' }}</b>.xml, 不设置则自动生成随机字符串</n-text>
        </template>
      </n-form-item>
      <n-form-item label="最大条目数">
        <n-input-number v-model:value="form.max_items" :min="10" :max="500" style="width: 120px" />
      </n-form-item>
      <ScheduleConfig
        :model-value="{ type: form.schedule_type, config: form.schedule_config }"
        @update:model-value="onScheduleChange"
      />
    </n-card>

    <!-- 步骤 4: 确认 -->
    <n-card v-if="step === 3" title="确认信息" :bordered="true">
      <n-descriptions label-placement="left" bordered :column="1">
        <n-descriptions-item label="脚本">{{ selectedScript?.name }}</n-descriptions-item>
        <n-descriptions-item label="实例名称">{{ form.name }}</n-descriptions-item>
        <n-descriptions-item label="调度方式">{{ scheduleLabel }}</n-descriptions-item>
        <n-descriptions-item label="最大条目数">{{ form.max_items }}</n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-space justify="space-between">
      <n-button v-if="step > 0" @click="step--">上一步</n-button>
      <n-button v-if="step < 3" type="primary" @click="nextStep" :disabled="!canNext">
        下一步
      </n-button>
      <n-button v-else type="primary" :loading="submitting" @click="handleCreate">
        创建实例
      </n-button>
    </n-space>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useScriptStore } from '@/stores/scripts'
import { useInstanceStore } from '@/stores/instances'
import ParamForm from '@/components/ParamForm.vue'
import ScheduleConfig from '@/components/ScheduleConfig.vue'

const router = useRouter()
const message = useMessage()
const scriptStore = useScriptStore()
const instanceStore = useInstanceStore()

const step = ref(0)
const stepStatus = ref('process')
const submitting = ref(false)
const paramFormRef = ref()

const form = ref({
  script_id: '',
  name: '',
  description: '',
  params: {} as Record<string, any>,
  schedule_type: 'interval',
  schedule_config: { interval_minutes: 60 } as Record<string, any> | null,
  rss_slug: '',
  max_items: 100,
})

const selectedScript = computed(() =>
  scriptStore.scripts.find((s) => s.id === form.value.script_id) || null
)

const scriptOptions = computed(() =>
  scriptStore.scripts.map((s) => ({
    label: `${s.name} (${s.filename})`,
    value: s.id,
  }))
)

const scheduleLabel = computed(() => {
  const labels: Record<string, string> = {
    interval: '间隔触发',
    cron: '定时触发',
    on_refresh: '刷新触发',
    manual: '手动触发',
  }
  return labels[form.value.schedule_type] || form.value.schedule_type
})

const canNext = computed(() => {
  if (step.value === 0) return !!form.value.script_id
  if (step.value === 2) return !!form.value.name
  return true
})

onMounted(async () => {
  await scriptStore.fetchAll()
})

function onScriptChange(id: string) {
  if (!id) return
  const script = scriptStore.scripts.find((s) => s.id === id)
  if (script) {
    // 初始化参数默认值
    const defaults: Record<string, any> = {}
    for (const p of (script.params_schema || []) as any[]) {
      defaults[p.name] = p.default ?? (p.type === 'boolean' ? false : p.type === 'number' ? null : '')
    }
    form.value.params = defaults

    // 初始化调度配置
    if (script.default_schedule) {
      const ds = script.default_schedule as any
      form.value.schedule_type = ds.type || 'interval'
      form.value.schedule_config = ds.config || { ...ds }
    }
  }
}

function onScheduleChange(val: { type: string; config: Record<string, any> | null }) {
  form.value.schedule_type = val.type
  form.value.schedule_config = val.config
}

async function nextStep() {
  if (step.value < 3) {
    step.value++
  }
}

async function handleCreate() {
  if (!form.value.name) {
    message.error('请输入实例名称')
    return
  }
  submitting.value = true
  try {
    const instance = await instanceStore.create({
      script_id: form.value.script_id,
      name: form.value.name,
      description: form.value.description,
      params: form.value.params,
      schedule_type: form.value.schedule_type,
      schedule_config: form.value.schedule_config,
      rss_slug: form.value.rss_slug || undefined,
      max_items: form.value.max_items,
    })
    message.success('实例创建成功')
    router.push({ name: 'InstanceDetail', params: { id: instance.id } })
  } catch (e: any) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>
