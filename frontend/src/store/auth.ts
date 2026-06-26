import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type { UserInfo } from '@/api/auth'

const TOKEN_KEY = 'sitp_access_token'

export const useAuthStore = defineStore('auth', () => {
  // ---- state ----
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<UserInfo | null>(null)
  const loading = ref(false)

  // ---- getters ----
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username ?? '')

  // ---- actions ----
  function setToken(newToken: string | null) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login({ email, password })
      setToken(res.data.access_token)
      user.value = {
        id: res.data.user.id,
        username: res.data.user.username,
        email: res.data.user.email,
        created_at: '',
      }
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.register({ username, email, password })
      setToken(res.data.access_token)
      user.value = {
        id: res.data.user.id,
        username: res.data.user.username,
        email: res.data.user.email,
        created_at: '',
      }
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    loading.value = true
    try {
      const res = await authApi.getMe()
      user.value = res.data
    } catch {
      // Token invalid or expired
      logout()
    } finally {
      loading.value = false
    }
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    username,
    login,
    register,
    fetchUser,
    logout,
    setToken,
  }
})
