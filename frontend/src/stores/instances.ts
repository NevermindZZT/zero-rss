import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export interface Instance {
  id: string
  script_id: string
  script_name: string
  name: string
  description: string
  params: Record<string, any>
  schedule_type: string
  schedule_config: Record<string, any> | null
  rss_token: string
  rss_url: string
  enabled: boolean
  max_items: number
  created_at: string
  updated_at: string
  last_run_at: string | null
  last_run_status: string | null
  last_error: string | null
}

export interface InstanceForm {
  script_id: string
  name: string
  description: string
  params: Record<string, any>
  schedule_type: string
  schedule_config: Record<string, any> | null
  max_items: number
}

export interface RunHistory {
  id: string
  instance_id: string
  status: string
  items_count: number
  error_message: string | null
  duration_ms: number | null
  started_at: string | null
  completed_at: string | null
}

export interface RSSItem {
  id: string
  guid: string
  title: string
  description: string
  link: string
  author: string
  categories: string[]
  content: string
  image: string
  pub_date: string | null
  created_at: string
}

export const useInstanceStore = defineStore('instances', () => {
  const instances = ref<Instance[]>([])
  const currentInstance = ref<Instance | null>(null)
  const loading = ref(false)

  async function fetchAll(scriptId = '') {
    loading.value = true
    try {
      const params: Record<string, any> = {}
      if (scriptId) params.script_id = scriptId
      const res = await apiClient.get('/api/instances', { params })
      instances.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    try {
      const res = await apiClient.get(`/api/instances/${id}`)
      currentInstance.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function create(data: InstanceForm) {
    const res = await apiClient.post('/api/instances', data)
    instances.value.unshift(res.data)
    return res.data
  }

  async function update(id: string, data: Partial<InstanceForm & { enabled: boolean }>) {
    const res = await apiClient.put(`/api/instances/${id}`, data)
    const idx = instances.value.findIndex((i) => i.id === id)
    if (idx >= 0) {
      instances.value[idx] = { ...instances.value[idx], ...res.data }
    }
    currentInstance.value = res.data
    return res.data
  }

  async function remove(id: string) {
    await apiClient.delete(`/api/instances/${id}`)
    instances.value = instances.value.filter((i) => i.id !== id)
    if (currentInstance.value?.id === id) {
      currentInstance.value = null
    }
  }

  async function run(id: string) {
    const res = await apiClient.post(`/api/instances/${id}/run`)
    return res.data
  }

  async function testRun(id: string) {
    const res = await apiClient.post(`/api/instances/${id}/test`)
    return res.data
  }

  async function fetchHistory(id: string, page = 1, pageSize = 20): Promise<{ items: RunHistory[]; total: number }> {
    const res = await apiClient.get(`/api/instances/${id}/history`, {
      params: { page, page_size: pageSize },
    })
    return res.data
  }

  async function fetchItems(id: string, page = 1, pageSize = 20): Promise<{ items: RSSItem[]; total: number }> {
    const res = await apiClient.get(`/api/instances/${id}/items`, {
      params: { page, page_size: pageSize },
    })
    return res.data
  }

  return {
    instances,
    currentInstance,
    loading,
    fetchAll,
    fetchOne,
    create,
    update,
    remove,
    run,
    testRun,
    fetchHistory,
    fetchItems,
  }
})
