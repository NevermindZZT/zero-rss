import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token') || '')
  const isAuthenticated = computed(() => !!token.value)

  async function login(t: string) {
    const res = await apiClient.post('/api/system/auth', { token: t })
    if (res.data.success) {
      token.value = t
      localStorage.setItem('auth_token', t)
    }
    return res.data
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('auth_token')
  }

  return { token, isAuthenticated, login, logout }
})
