<template>
  <div class="login-page">
    <!-- 左侧顶部品牌区 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="logo">
          <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#1E293B" />
            <path d="M14 24L20 18L14 12V24Z" fill="white" />
            <rect x="22" y="12" width="12" height="3" rx="1.5" fill="white" />
            <rect x="22" y="18" width="8" height="3" rx="1.5" fill="white" />
            <rect x="22" y="24" width="10" height="3" rx="1.5" fill="white" />
            <rect x="22" y="30" width="6" height="3" rx="1.5" fill="white" />
          </svg>
          <span class="logo-text">反诈助手</span>
        </div>
        <p class="brand-slogan">多模态智能反诈助手</p>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-section">
      <div class="login-container">
        <div class="login-header">
          <h2>欢迎回来</h2>
          <p>请登录您的账户使用反诈服务</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleLogin" class="login-form">
          <el-form-item prop="role" class="form-item">
            <div class="role-selector">
              <div class="role-option" :class="{ active: form.role === 'student' }" @click="form.role = 'student'">
                <span class="role-label">我是学生</span>
              </div>
              <div class="role-option" :class="{ active: form.role === 'admin' }" @click="form.role = 'admin'">
                <span class="role-label">我是管理员</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item prop="username" class="form-item">
            <label class="input-label">用户名</label>
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" :prefix-icon="User" />
          </el-form-item>

          <el-form-item prop="password" class="form-item">
            <label class="input-label">密码</label>
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password
              :prefix-icon="Lock" />
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <span class="forgot-link" @click="handleForgotPassword">忘记密码？</span>
          </div>

          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">
            登 录
          </el-button>
        </el-form>

        <div class="forgot-link">
          <router-link to="/forgot-password">忘记密码？</router-link>
        </div>

        <div class="login-footer">
          <span>还没有账户？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
  role: 'student'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleForgotPassword = () => {
  ElMessageBox.alert('请联系管理员重置密码', '忘记密码', {
    confirmButtonText: '我知道了',
    type: 'info',
  })
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await authStore.login(form.username, form.password, form.role)
      if (res.code === 200) {
        ElMessage.success('登录成功')
        router.push('/')
      } else {
        ElMessage.error(res.msg || '登录失败')
      }
    } catch (e) {
      ElMessage.error(e.response?.data?.msg || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

/* 左侧顶部品牌区 */
.brand-section {
  width: 420px;
  background: var(--color-bg-card);
  padding: 48px 48px 48px 96px;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
}

.brand-content {
  margin-top: 80px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

.brand-slogan {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 右侧登录区 */
.login-section {
  flex: 1;
  margin-left: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.login-container {
  width: 100%;
  max-width: 360px;
}

.login-header {
  margin-bottom: 40px;
}

.login-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.login-header p {
  font-size: 15px;
  color: var(--color-text-muted);
  margin: 0;
}

/* 表单样式 */
.login-form {
  margin-bottom: 24px;
}

.form-item {
  margin-bottom: 24px;
}

.input-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--color-border);
  transition: all 0.2s;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--color-text-muted);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--color-primary);
}

.login-form :deep(.el-input__inner) {
  font-size: 15px;
}

.login-form :deep(.el-input__prefix .el-icon) {
  color: var(--color-text-muted);
}

/* 选项 */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-options :deep(.el-checkbox__label) {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.forgot-link {
  font-size: 14px;
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

/* 角色选择器 */
.role-selector {
  display: flex;
  flex-wrap: nowrap;
  gap: 12px;
  margin-bottom: 8px;
}

.role-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 8px;
  background: var(--color-bg-card);
  border: 2px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.role-option:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg);
}

.role-option.active {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.role-option.active .role-label {
  color: var(--color-primary);
  font-weight: 600;
}

.role-icon {
  color: var(--color-text-muted);
  transition: color 0.2s;
}

.role-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.login-btn:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

/* 底部链接 */
.forgot-link {
  text-align: right;
  margin-bottom: 16px;
}

.forgot-link a {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 13px;
}

.forgot-link a:hover {
  color: var(--color-primary);
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.login-footer a {
  color: var(--color-primary);
  text-decoration: none;
  margin-left: 4px;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>
