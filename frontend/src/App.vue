<template>
  <n-config-provider :theme="theme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { zhCN, dateZhCN, darkTheme } from 'naive-ui'
import type { GlobalTheme } from 'naive-ui'

const isDark = ref(false)
const theme = computed<GlobalTheme | null>(() => (isDark.value ? darkTheme : null))
</script>
