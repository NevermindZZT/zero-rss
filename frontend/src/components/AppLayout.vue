<template>
  <n-layout position="absolute" has-sider>
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      native-scrollbar
      style="height: 100vh"
    >
      <div class="logo" :style="{ padding: collapsed ? '12px 0' : '16px' }">
        <n-h3 v-if="!collapsed" style="margin: 0; text-align: center">
          <n-gradient-text type="info">zero-rss</n-gradient-text>
        </n-h3>
        <n-h3 v-else style="margin: 0; text-align: center; font-size: 14px">
          ZR
        </n-h3>
      </div>
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered style="padding: 12px 24px; display: flex; align-items: center; justify-content: space-between">
        <n-breadcrumb>
          <n-breadcrumb-item>{{ pageTitle }}</n-breadcrumb-item>
        </n-breadcrumb>
        <n-space>
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button quaternary circle @click="toggleTheme">
                <template #icon><n-icon><Moon v-if="isDark" /><Sunny v-else /></n-icon></template>
              </n-button>
            </template>
            {{ isDark ? '亮色' : '暗色' }}主题
          </n-tooltip>
          <n-popconfirm @positive-click="handleLogout">
            <template #trigger>
              <n-button quaternary>退出</n-button>
            </template>
            确认退出登录？
          </n-popconfirm>
        </n-space>
      </n-layout-header>
      <n-layout-content content-style="padding: 24px; height: calc(100vh - 53px); overflow-y: auto">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon, useMessage } from 'naive-ui'
import {
  Dashboard,
  Code,
  Box,
  Moon,
  Sunny,
  Add,
} from '@vicons/carbon'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

const collapsed = ref(false)
const isDark = ref(false)

const emit = defineEmits<{ (e: 'theme-change', val: boolean): void }>()

function toggleTheme() {
  isDark.value = !isDark.value
  emit('theme-change', isDark.value)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
  message.success('已退出登录')
}

const pageTitle = computed(() => {
  const meta = route.meta
  return (meta?.title as string) || 'zero-rss'
})

const activeKey = computed(() => route.name as string)

const menuOptions = [
  {
    label: '仪表盘',
    key: 'Dashboard',
    icon: () => h(NIcon, null, { default: () => h(Dashboard) }),
  },
  {
    type: 'divider' as const,
    key: 'd1',
  },
  {
    label: '脚本管理',
    key: 'ScriptList',
    icon: () => h(NIcon, null, { default: () => h(Box) }),
  },
  {
    label: '实例管理',
    key: 'Instances',
    icon: () => h(NIcon, null, { default: () => h(Box) }),
    children: [
      {
        label: '实例列表',
        key: 'InstanceList',
        icon: () => h(NIcon, null, { default: () => h(Box) }),
      },
      {
        label: '创建实例',
        key: 'InstanceCreate',
        icon: () => h(NIcon, null, { default: () => h(Add) }),
      },
    ],
  },
]

function handleMenuClick(key: string) {
  if (key === 'Instances') return
  const routeName = key as string
  if (router.hasRoute(routeName)) {
    router.push({ name: routeName })
  }
}
</script>

<style scoped>
.logo {
  border-bottom: 1px solid var(--n-border-color);
}
</style>
