import axios from 'axios'
  import { ElMessage } from 'element-plus'
  import router from '../router'

  const request = axios.create({
    baseURL: 'http://localhost:8000',
    // baseURL: 'http://39.97.237.70:8000',
    timeout: 120000
  })

  let isRedirecting = false
  let lastErrorMsg = ''
  let lastErrorTime = 0
  const ERROR_DEBOUNCE = 3000

  function showError(msg) {
    const now = Date.now()
    if (msg === lastErrorMsg && now - lastErrorTime < ERROR_DEBOUNCE) {
      return
    }
    lastErrorMsg = msg
    lastErrorTime = now
    ElMessage.error(msg)
  }

  let isRefreshing = false
  let refreshSubscribers = []

  function subscribeTokenRefresh(cb) {
    refreshSubscribers.push(cb)
  }

  function onTokenRefreshed(newToken) {
    refreshSubscribers.forEach(cb => cb(newToken))
    refreshSubscribers = []
  }

  function getTokenExpireTime(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp ? payload.exp * 1000 : null
    } catch {
      return null
    }
  }

  function isTokenExpiringSoon(token) {
    const expireTime = getTokenExpireTime(token)
    if (!expireTime) return false
    const now = Date.now()
    return expireTime - now < 5 * 60 * 1000
  }

  function isSuccess(code) {
    return code === 200 || code === '00000'
  }

  request.interceptors.request.use(
    config => {
      const token = localStorage.getItem('access_token')
      if (token) {
        if (isTokenExpiringSoon(token) && !isRefreshing && config.method === 'get') {
          isRefreshing = true
          return request.post('/api/v1/auth/refresh', {}, {
            headers: { Authorization: `Bearer ${token}` },
            timeout: 10000
          }).then(res => {
            if (isSuccess(res.data.code)) {
              const newToken = res.data.data.accessToken
              localStorage.setItem('access_token', newToken)
              onTokenRefreshed(newToken)
              config.headers.Authorization = `Bearer ${newToken}`
            } else {
              throw new Error('token refresh failed')
            }
            isRefreshing = false
            return config
          }).catch(() => {
            isRefreshing = false
            localStorage.removeItem('access_token')
            localStorage.removeItem('user_info')
            return config
          })
        }
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    error => Promise.reject(error)
  )

  request.interceptors.response.use(
    response => response,
    error => {
      if (error.response) {
        const { status, data } = error.response

        if (data?.code !== undefined && isSuccess(data?.code)) {
          // 成功，不提示错误
        } else if (data?.code !== undefined) {
          const msg = data?.msg || '操作失败'
          showError(msg)
        } else if (status === 401) {
          if (!isRedirecting) {
            isRedirecting = true
            localStorage.removeItem('access_token')
            localStorage.removeItem('user_info')
            router.push('/login').finally(() => {
              isRedirecting = false
            })
            showError('登录已过期，请重新登录')
          }
        } else if (status === 403) {
          showError(data?.msg || '权限不足')
        } else if (status >= 500) {
          showError('服务器错误，请稍后重试')
        } else if (status >= 400) {
          showError(data?.msg || '请求失败')
        }
      } else {
        if (error.code === 'ECONNABORTED') {
          showError('请求超时，请稍后重试')
        } else if (error.message?.includes('Network Error')) {
          showError('网络连接失败，请检查网络')
        } else {
          showError('网络错误，请检查连接')
        }
      }
      return Promise.reject(error)
    }
  )

  export default request