<template>
  <div class="register-page">
    <!-- 左侧顶部品牌区 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="logo">
          <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#1E293B"/>
            <path d="M14 24L20 18L14 12V24Z" fill="white"/>
            <rect x="22" y="12" width="12" height="3" rx="1.5" fill="white"/>
            <rect x="22" y="18" width="8" height="3" rx="1.5" fill="white"/>
            <rect x="22" y="24" width="10" height="3" rx="1.5" fill="white"/>
            <rect x="22" y="30" width="6" height="3" rx="1.5" fill="white"/>
          </svg>
          <span class="logo-text">AI 智课</span>
        </div>
        <p class="brand-slogan">智能课程学习系统</p>
      </div>
    </div>

    <!-- 右侧注册区 -->
    <div class="register-section">
      <div class="register-container">
        <div class="register-header">
          <h2>创建账户</h2>
          <p>加入我们开始学习之旅</p>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="handleRegister" class="register-form">
          <el-form-item prop="username" class="form-item">
            <label class="input-label">用户名</label>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名（至少3个字符）"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="email" class="form-item">
            <label class="input-label">邮箱</label>
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱地址"
              size="large"
              :prefix-icon="Message"
            />
          </el-form-item>

          <el-form-item prop="password" class="form-item">
            <label class="input-label">密码</label>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码（至少6个字符）"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>

          <el-form-item prop="confirmPassword" class="form-item">
            <label class="input-label">确认密码</label>
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>

          <el-form-item prop="role" class="form-item">
            <label class="input-label">角色</label>
            <el-select v-model="form.role" placeholder="请选择角色" size="large" class="role-select">
              <el-option label="学生" value="student" />
            </el-select>
          </el-form-item>

          <el-form-item prop="realName" class="form-item">
            <label class="input-label">真实姓名（选填）</label>
            <el-input
              v-model="form.realName"
              placeholder="请输入真实姓名"
              size="large"
              :prefix-icon="UserFilled"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleRegister"
            class="register-btn"
          >
            注 册
          </el-button>
        </el-form>

        <div class="register-footer">
          <span>已有账户？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'student',
  realName: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const handleRegister = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await authStore.register({
        username: form.username,
        email: form.email,
        password: form.password,
        role: form.role,
        realName: form.realName || null
      })
      if (res.code === 200) {
        ElMessage.success('注册成功，请登录')
        router.push('/login')
      } else {
        ElMessage.error(res.msg || '注册失败')
      }
    } catch (e) {
      ElMessage.error(e.response?.data?.msg || '注册失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-page {
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

/* 右侧注册区 */
.register-section {
  flex: 1;
  margin-left: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  overflow-y: auto;
}

.register-container {
  width: 100%;
  max-width: 360px;
}

.register-header {
  margin-bottom: 32px;
}

.register-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.register-header p {
  font-size: 15px;
  color: var(--color-text-muted);
  margin: 0;
}

/* 表单样式 */
.register-form {
  margin-bottom: 24px;
}

.form-item {
  margin-bottom: 20px;
}

.input-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.register-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--color-border);
  transition: all 0.2s;
}

.register-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--color-text-muted);
}

.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--color-primary);
}

.register-form :deep(.el-input__inner) {
  font-size: 15px;
}

.register-form :deep(.el-input__prefix .el-icon) {
  color: var(--color-text-muted);
}

.role-select {
  width: 100%;
}

.role-select :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--color-border);
}

.role-select :deep(.el-select__caret) {
  color: var(--color-text-muted);
}

/* 注册按钮 */
.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: var(--color-primary);
  border-color: var(--color-primary);
  margin-top: 8px;
}

.register-btn:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

/* 底部链接 */
.register-footer {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.register-footer a {
  color: #2563EB;
  text-decoration: none;
  margin-left: 4px;
}

.register-footer a:hover {
  text-decoration: underline;
}
</style>
