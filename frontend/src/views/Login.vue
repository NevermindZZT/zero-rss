<template>
  <div class="login-container">
    <n-card style="width: 400px" :bordered="true">
      <n-h2 style="text-align: center">
        <n-gradient-text type="info">zero-rss</n-gradient-text>
      </n-h2>
      <n-p style="text-align: center; color: #888">
        私有化 RSS 订阅系统
      </n-p>
      <n-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <n-form-item path="token" label="访问令牌">
          <n-input
            v-model:value="form.token"
            type="password"
            show-password-on="click"
            placeholder="请输入部署时配置的 AUTH_TOKEN"
          />
        </n-form-item>
        <n-button
          type="primary"
          block
          :loading="loading"
          attr-type="submit"
        >
          登录
        </n-button>
      </n-form>
      <n-p style="text-align: center; font-size: 12px; color: #aaa; margin-top: 16px">
        Token 在部署时通过环境变量 AUTH_TOKEN 配置
      </n-p>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const message = useMessage()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  token: '',
})

const rules = {
  token: [{ required: true, message: '请输入访问令牌', trigger: 'blur' }],
}

async function handleLogin() {
  loading.value = true
  try {
    const result = await authStore.login(form.token)
    if (result.success) {
      message.success('登录成功')
      // 强制跳转到 dashboard
      window.location.hash = '#/dashboard'
    } else {
      message.error(result.message || 'Token 验证失败')
    }
  } catch (e: any) {
    message.error(e.response?.data?.detail || 'Token 验证失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
