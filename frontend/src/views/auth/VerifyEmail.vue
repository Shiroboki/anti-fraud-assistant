<template>
  <div class="auth-page">
    <div class="auth-card">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="48" color="#6366F1"><Loading /></el-icon>
        <p>验证中...</p>
      </div>

      <div v-else-if="success" class="success-msg">
        <el-icon :size="48" color="#22C55E"><CircleCheck /></el-icon>
        <p>邮箱验证成功</p>
        <el-button type="primary" @click="$router.push('/login')">去登录</el-button>
      </div>

      <div v-else class="error-msg">
        <el-icon :size="48" color="#EF4444"><CircleClose /></el-icon>
        <p>{{ errorMsg }}</p>
        <el-button @click="$router.push('/login')">返回登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue'
import { verifyEmail } from '@/api/auth'

const route = useRoute()
const loading = ref(true)
const success = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    loading.value = false
    errorMsg.value = '缺少验证令牌'
    return
  }
  try {
    const res = await verifyEmail(token)
    success.value = res.data.code === 200
    if (!success.value) errorMsg.value = res.data.msg || '验证失败'
  } catch {
    errorMsg.value = '验证失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--color-bg); }
.auth-card { background: var(--color-bg-card); border-radius: var(--radius-xl); padding: 48px; text-align: center; border: 1px solid var(--color-border-light); }
.loading-state p, .success-msg p, .error-msg p { margin: 16px 0; font-size: 16px; color: var(--color-text-primary); }
</style>
