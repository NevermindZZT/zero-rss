<template>
  <n-space align="center">
    <n-input
      :value="url"
      readonly
      :style="{ width: width + 'px' }"
      size="small"
    />
    <n-button size="small" @click="copyUrl">
      <template #icon><n-icon><Copy /></n-icon></template>
      复制
    </n-button>
    <n-button size="small" tag="a" :href="url" target="_blank" secondary>
      打开
    </n-button>
  </n-space>
</template>

<script setup lang="ts">
import { NIcon, useMessage } from 'naive-ui'
import { Copy } from '@vicons/carbon'

const props = defineProps<{
  url: string
  width?: number
}>()

const message = useMessage()

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(props.url)
    message.success('RSS 地址已复制到剪贴板')
  } catch {
    // Fallback
    const textarea = document.createElement('textarea')
    textarea.value = props.url
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    message.success('RSS 地址已复制到剪贴板')
  }
}
</script>
