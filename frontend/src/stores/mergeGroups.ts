import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiClient from '@/api/client'

export interface MergeGroup {
  id: string
  name: string
  description: string
  rss_token: string
  rss_slug: string | null
  rss_url: string
  max_items: number
  instance_ids: string[]
  instance_names: string[]
  created_at: string
  updated_at: string
}

export const useMergeGroupStore = defineStore('mergeGroups', () => {
  const groups = ref<MergeGroup[]>([])
  const currentGroup = ref<MergeGroup | null>(null)
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const res = await apiClient.get('/api/merge-groups')
      groups.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id: string) {
    loading.value = true
    try {
      const res = await apiClient.get(`/api/merge-groups/${id}`)
      currentGroup.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function create(data: { name: string; description: string; instance_ids: string[]; max_items: number }) {
    const res = await apiClient.post('/api/merge-groups', data)
    groups.value.unshift(res.data)
    return res.data
  }

  async function update(id: string, data: any) {
    const res = await apiClient.put(`/api/merge-groups/${id}`, data)
    const idx = groups.value.findIndex((g) => g.id === id)
    if (idx >= 0) groups.value[idx] = res.data
    currentGroup.value = res.data
    return res.data
  }

  async function remove(id: string) {
    await apiClient.delete(`/api/merge-groups/${id}`)
    groups.value = groups.value.filter((g) => g.id !== id)
    if (currentGroup.value?.id === id) currentGroup.value = null
  }

  return { groups, currentGroup, loading, fetchAll, fetchOne, create, update, remove }
})
