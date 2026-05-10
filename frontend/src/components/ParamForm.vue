<template>
  <n-form :model="formValue" :rules="formRules" label-placement="left" label-width="auto">
    <n-form-item
      v-for="param in params"
      :key="param.name"
      :path="param.name"
      :label="param.label"
      :rule="{
        required: param.required,
        message: `${param.label} 为必填项`,
        trigger: ['blur', 'change'],
      }"
    >
      <template v-if="param.type === 'boolean'">
        <n-switch v-model:value="formValue[param.name]" />
      </template>
      <template v-else-if="param.type === 'select' && param.options">
        <n-select
          v-model:value="formValue[param.name]"
          :options="param.options"
          :placeholder="param.description || `请选择${param.label}`"
          clearable
        />
      </template>
      <template v-else-if="param.type === 'multiline'">
        <n-input
          v-model:value="formValue[param.name]"
          type="textarea"
          :rows="3"
          :placeholder="param.description || `请输入${param.label}`"
        />
      </template>
      <template v-else-if="param.type === 'password'">
        <n-input
          v-model:value="formValue[param.name]"
          type="password"
          show-password-on="click"
          :placeholder="param.description || `请输入${param.label}`"
        />
      </template>
      <template v-else-if="param.type === 'number'">
        <n-input-number
          v-model:value="formValue[param.name]"
          :placeholder="param.description || `请输入${param.label}`"
          style="width: 100%"
        />
      </template>
      <template v-else>
        <n-input
          v-model:value="formValue[param.name]"
          :placeholder="param.description || `请输入${param.label}`"
        />
      </template>
      <template v-if="param.description && param.type !== 'multiline' && param.type !== 'password' && param.type !== 'select'">
        <n-text depth="3" style="font-size: 12px; margin-top: 4px">
          {{ param.description }}
        </n-text>
      </template>
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { ParamDef } from '@/stores/scripts'

const props = defineProps<{
  params: ParamDef[]
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

// 构建默认值
const defaultValues: Record<string, any> = {}
for (const p of props.params) {
  defaultValues[p.name] = p.default ?? (p.type === 'boolean' ? false : p.type === 'number' ? null : '')
}

const formValue = reactive<Record<string, any>>({ ...defaultValues, ...props.modelValue })

watch(formValue, (val) => {
  emit('update:modelValue', { ...val })
}, { deep: true })

watch(() => props.modelValue, (val) => {
  Object.assign(formValue, { ...defaultValues, ...val })
}, { deep: true })

const formRules: Record<string, any> = {}
for (const p of props.params) {
  if (p.required) {
    formRules[p.name] = {
      required: true,
      message: `${p.label} 为必填项`,
      trigger: ['blur', 'change'],
    }
  }
}

defineExpose({ formValue })
</script>
