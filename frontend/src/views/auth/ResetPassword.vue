<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>重置密码</h2>
      <p class="subtitle">请输入新密码</p>

      <el-form v-if="!done" :model="form" @submit.prevent="handleSubmit">
        <el-form-item>
          <el-input v-model="form.newPassword" type="password" show-password placeholder="新密码（至少6位）" size="large" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="确认新密码" size="large" prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleSubmit">
            重置密码
          </el-button>
        </el-form-item>
      </el-form>

      <div v-else class="success-msg">
        <el-icon :size="48" color="#22C55E"><CircleCheck /></el-icon>
        <p>密码重置成功</p>
        <el-button type="primary" @click="$router.push('/login')">去登录</el-button>
      </div>

      <div class="auth-links">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import { resetPassword } from '@/api/auth'

const route = useRoute()
const loading = ref(false)
const done = ref(false)
const form = reactive({ token: '', newPassword: '', confirmPassword: '' })

onMounted(() => {
  form.token = route.query.token || ''
})

const handleSubmit = async () => {
  if (!form.newPassword || form.newPassword.length < 6) return ElMessage.warning('密码长度不能少于6位')
  if (form.newPassword !== form.confirmPassword) return ElMessage.warning('两次密码不一致')

  loading.value = true
  try {
    const res = await resetPassword(form.token, form.newPassword)
    if (res.data.code === 200) {
      done.value = true
    } else {
      ElMessage.error(res.data.msg || '重置失败')
    }
  } catch (e) {
    ElMessage.error('重置失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--color-bg); }
.auth-card { background: var(--color-bg-card); border-radius: var(--radius-xl); padding: 40px; width: 400px; border: 1px solid var(--color-border-light); }
.auth-card h2 { margin: 0 0 8px 0; font-size: 22px; color: var(--color-text-primary); }
.subtitle { margin: 0 0 24px 0; font-size: 14px; color: var(--color-text-secondary); }
.success-msg { text-align: center; padding: 20px 0; }
.success-msg p { margin: 12px 0 16px; color: var(--color-text-primary); font-size: 16px; }
.auth-links { text-align: center; margin-top: 16px; }
.auth-links a { color: var(--color-primary); text-decoration: none; font-size: 14px; }
</style>
