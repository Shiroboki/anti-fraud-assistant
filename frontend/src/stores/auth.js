import { defineStore } from 'pinia'
  import { ref, computed } from 'vue'
  import request from '../api/request'

  export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('access_token') || '')
    const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => userInfo.value.role === 'admin')
    const userRole = computed(() => userInfo.value.role || '')

    const isSuccess = (code) => code === 200 || code === '00000'

    async function login(username, password, role) {
      const res = await request.post('/api/v1/auth/login/json', {
        username,
        password,
        role
      })

      if (isSuccess(res.data.code)) {
        token.value = res.data.data.accessToken
        userInfo.value = res.data.data.userInfo
        localStorage.setItem('access_token', token.value)
        localStorage.setItem('user_info', JSON.stringify(userInfo.value))
      }
      return res.data
    }

    async function register(userData) {
      const res = await request.post('/api/v1/auth/register', userData)
      return res.data
    }

    async function fetchUserInfo() {
      try {
        const res = await request.get('/api/v1/auth/me')
        if (isSuccess(res.data.code)) {
          userInfo.value = res.data.data
          localStorage.setItem('user_info', JSON.stringify(userInfo.value))
        }
      } catch (e) {
        logout()
      }
    }

    function logout() {
      token.value = ''
      userInfo.value = {}
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
    }

    function hasPermission(resource, action) {
      if (isAdmin.value) return true
      const permissions = userInfo.value.permissions || []
      return permissions.some(p =>
        p === `${resource}:${action}` ||
        p === '*:*' ||
        p === `${resource}:*`
      )
    }

    function hasRole(roles) {
      if (!Array.isArray(roles)) roles = [roles]
      return roles.includes(userRole.value)
    }

    return {
      token,
      userInfo,
      isLoggedIn,
      isAdmin,
      userRole,
      login,
      register,
      fetchUserInfo,
      logout,
      hasPermission,
      hasRole
    }
  })