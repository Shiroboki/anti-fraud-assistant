<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>忘记密码</h2>
      <p class="subtitle">输入您的注册邮箱，我们将发送重置链接</p>

      <el-form v-if="!sent" :model="form" @submit.prevent="handleSubmit">
        <el-form-item>
          <el-input v-model="form.email" placeholder="邮箱地址" size="large" prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleSubmit">
            发送重置邮件
          </el-button>
        </el-form-item>
      </el-form>

      <div v-else class="success-msg">
        <el-icon :size="48" color="#22C55E"><CircleCheck /></el-icon>
        <p>重置邮件已发送到 <strong>{{ form.email }}</strong></p>
        <p class="hint">请查收邮件并点击链接重置密码（1小时内有效）</p>
        <el-button @click="sent = false">重新发送</el-button>
      </div>

      <div class="auth-links">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import { forgotPassword } from '@/api/auth'

const loading = ref(false)
const sent = ref(false)
const form = reactive({ email: '' })

const handleSubmit = async () => {
  if (!form.email) return ElMessage.warning('请输入邮箱地址')
  loading.value = true
  try {
    const res = await forgotPassword(form.email)
    if (res.data.code === 200) {
      sent.value = true
    } else {
      ElMessage.error(res.data.msg || '发送失败')
    }
  } catch (e) {
    ElMessage.error('发送失败')
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
.success-msg p { margin: 12px 0 4px; color: var(--color-text-primary); }
.success-msg .hint { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 16px; }
.auth-links { text-align: center; margin-top: 16px; }
.auth-links a { color: var(--color-primary); text-decoration: none; font-size: 14px; }
</style>
