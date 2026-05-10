import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export interface Script {
  id: string
  name: string
  description: string
  version: string
  author: string
  filename: string
  params_schema: ParamDef[]
  default_schedule: Record<string, any> | null
  code?: string
  created_at: string
  updated_at: string
  instance_count?: number
}

export interface ParamDef {
  name: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiline' | 'password'
  default?: any
  required?: boolean
  description?: string
  options?: { label: string; value: any }[]
}

export const useScriptStore = defineStore('scripts', () => {
  const scripts = ref<Script[]>([])
  const currentScript = ref<Script | null>(null)
  const loading = ref(false)

  async function fetchAll(search = '') {
    loading.value = true
    try {
      const params = search ? { search } : {}
      const res = await apiClient.get('/api/scripts', { params })
      scripts.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    try {
      const res = await apiClient.get(`/api/scripts/${id}`)
      currentScript.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function uploadScript(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.post('/api/scripts', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    scripts.value.unshift(res.data)
    return res.data
  }

  async function updateScript(id: string, code: string) {
    const res = await apiClient.put(`/api/scripts/${id}`, { code })
    const idx = scripts.value.findIndex((s) => s.id === id)
    if (idx >= 0) {
      scripts.value[idx] = { ...scripts.value[idx], ...res.data }
    }
    currentScript.value = res.data
    return res.data
  }

  async function updateScriptByUpload(id: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.put(`/api/scripts/${id}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const idx = scripts.value.findIndex((s) => s.id === id)
    if (idx >= 0) {
      scripts.value[idx] = { ...scripts.value[idx], ...res.data }
    }
    currentScript.value = res.data
    return res.data
  }

  async function deleteScript(id: string) {
    await apiClient.delete(`/api/scripts/${id}`)
    scripts.value = scripts.value.filter((s) => s.id !== id)
    if (currentScript.value?.id === id) {
      currentScript.value = null
    }
  }

  return {
    scripts,
    currentScript,
    loading,
    fetchAll,
    fetchOne,
    uploadScript,
    updateScript,
    updateScriptByUpload,
    deleteScript,
  }
})
