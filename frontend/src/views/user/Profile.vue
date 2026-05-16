<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 左侧用户信息卡 -->
      <el-col :span="8">
        <div class="profile-card">
          <div class="avatar-section">
            <div class="avatar-wrap" @click="triggerAvatarUpload">
              <el-avatar :size="80" :src="userInfo.avatar" icon="UserFilled" />
              <div class="avatar-mask">
                <el-icon><Camera /></el-icon>
              </div>
            </div>
            <input type="file" ref="avatarInput" accept="image/*" style="display: none" @change="handleAvatarChange" />
            <h2 class="username">{{ userInfo.realName || userInfo.username || '用户' }}</h2>
            <el-tag :type="roleTagType" size="large">{{ roleLabel }}</el-tag>
          </div>
          <div class="stats-row">
            <div class="stat-item">
              <div class="stat-value">{{ stats.interviewCount }}</div>
              <div class="stat-label">面试次数</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.completedCount }}</div>
              <div class="stat-label">已完成</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.avgScore }}</div>
              <div class="stat-label">平均分</div>
            </div>
          </div>
        </div>

        <!-- 提建议卡片 -->
        <div class="feedback-card">
          <div class="feedback-header">
            <el-icon :size="20"><Message /></el-icon>
            <span>提建议</span>
          </div>
          <div class="feedback-body">
            <el-input
              v-model="feedbackContent"
              type="textarea"
              :rows="3"
              placeholder="请输入您的建议或问题..."
              resize="none"
            />
            <el-button type="primary" class="feedback-btn" @click="submitFeedback" :loading="feedbackLoading">
              <el-icon><Promotion /></el-icon>
              提交
            </el-button>
          </div>
        </div>
      </el-col>

      <!-- 右侧表单卡 -->
      <el-col :span="16">
        <!-- 个人信息 -->
        <div class="info-card">
          <div class="card-header">
            <span class="header-title">个人信息</span>
            <el-button v-if="!isEditing" type="primary" @click="handleEdit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <div v-else class="header-actions">
              <el-button @click="handleCancel">取消</el-button>
              <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
            </div>
          </div>
          <el-form :model="form" label-position="top" :disabled="!isEditing">
            <div class="form-grid">
              <el-form-item label="用户ID">
                <el-input :value="userInfo.id" disabled />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="form.username" disabled />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="请输入邮箱" />
              </el-form-item>
              <el-form-item label="真实姓名">
                <el-input v-model="form.realName" placeholder="请输入真实姓名" />
              </el-form-item>
              <el-form-item label="学校ID">
                <el-input v-model="form.schoolId" placeholder="请输入学校ID" />
              </el-form-item>
              <el-form-item label="角色">
                <el-tag :type="roleTagType">{{ roleLabel }}</el-tag>
              </el-form-item>
              <el-form-item label="注册时间">
                <span class="readonly-text">{{ form.createdAt || '—' }}</span>
              </el-form-item>
            </div>
          </el-form>
        </div>

        <!-- 修改密码 -->
        <div class="info-card mt-20">
          <div class="card-header">
            <span class="header-title">修改密码</span>
          </div>
          <el-form :model="passwordForm" label-position="top">
            <div class="form-grid">
              <el-form-item label="当前密码">
                <el-input v-model="passwordForm.currentPassword" type="password" show-password placeholder="请输入当前密码" />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
              </el-form-item>
              <el-form-item label="确认密码">
                <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
              </el-form-item>
            </div>
            <div class="form-actions">
              <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
                <el-icon><Key /></el-icon>
                修改密码
              </el-button>
            </div>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Message, Camera } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import request from '../../api/request'

const authStore = useAuthStore()
const isEditing = ref(false)
const saving = ref(false)
const changingPassword = ref(false)

const userInfo = computed(() => authStore.userInfo)

const form = reactive({
  username: '', email: '', realName: '', schoolId: '', createdAt: ''
})

const passwordForm = reactive({
  currentPassword: '', newPassword: '', confirmPassword: ''
})

const stats = reactive({
  interviewCount: 0, completedCount: 0, avgScore: 0
})

const feedbackContent = ref('')
const feedbackLoading = ref(false)
const avatarInput = ref(null)
const avatarUploading = ref(false)

const triggerAvatarUpload = () => {
  avatarInput.value.click()
}

const handleAvatarChange = async (e) => {
  const file = e.target.files[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }

  avatarUploading.value = true
  try {
    // 转换为 Base64
    const reader = new FileReader()
    reader.onload = async (event) => {
      const imageData = event.target.result
      try {
        const res = await request.post('/api/v1/auth/avatar/upload', {
          image: imageData
        })
        if (res.data.code === 200) {
          ElMessage.success('头像上传成功')
          // 更新本地用户信息
          authStore.userInfo.avatar = res.data.data.avatar
          localStorage.setItem('user_info', JSON.stringify(authStore.userInfo))
        } else {
          ElMessage.error(res.data.msg || '上传失败')
        }
      } catch (e) {
        ElMessage.error('上传失败')
      } finally {
        avatarUploading.value = false
      }
    }
    reader.readAsDataURL(file)
  } catch (e) {
    ElMessage.error('上传失败')
    avatarUploading.value = false
  }

  // 清空 input 以便重复选择同一文件
  e.target.value = ''
}

const submitFeedback = async () => {
  if (!feedbackContent.value.trim()) {
    ElMessage.warning('请输入建议内容')
    return
  }
  feedbackLoading.value = true
  try {
    await request.post('/api/v1/feedback', {
      content: feedbackContent.value,
      userId: String(userInfo.value.id || '1')
    })
    ElMessage.success('感谢您的建议！')
    feedbackContent.value = ''
  } catch (e) {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    feedbackLoading.value = false
  }
}

const roleLabel = computed(() => {
  const map = { admin: '管理员', student: '学生' }
  return map[userInfo.value.role] || '用户'
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', student: 'success' }
  return map[userInfo.value.role] || 'info'
})

const fetchUserInfo = async () => {
  try {
    const res = await request.get('/api/v1/auth/me')
    if (res.data.code === 200) {
      const data = res.data.data
      form.username = data.username || ''
      form.email = data.email || ''
      form.realName = data.realName || ''
      form.schoolId = data.schoolId || ''
      form.createdAt = data.createdAt || ''
    }
  } catch (e) {
    console.error('获取用户信息失败:', e)
  }
}

const fetchStats = async () => {
  try {
    const res = await request.get('/api/v1/interview/history')
    if (res.data.code === 200) {
      const list = res.data.data.list || []
      stats.interviewCount = list.length
      stats.completedCount = list.filter(s => s.status === 'completed').length
      const scoredSessions = list.filter(s => s.totalScore != null)
      if (scoredSessions.length > 0) {
        const total = scoredSessions.reduce((sum, s) => sum + (s.totalScore || 0), 0)
        stats.avgScore = Math.round(total / scoredSessions.length)
      }
    }
  } catch (e) {
    console.error('获取统计数据失败:', e)
  }
}

const handleEdit = () => { isEditing.value = true }
const handleCancel = () => { isEditing.value = false; fetchUserInfo() }

const handleSave = async () => {
  saving.value = true
  try {
    await request.post('/api/v1/auth/update-profile', {
      email: form.email, realName: form.realName, schoolId: form.schoolId
    })
    ElMessage.success('保存成功')
    isEditing.value = false
    authStore.fetchUserInfo()
  } catch (e) {
    ElMessage.error(e?.response?.data?.msg || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleChangePassword = async () => {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    ElMessage.error('密码长度不能少于6位')
    return
  }
  changingPassword.value = true
  try {
    await request.post('/api/v1/auth/change-password', {
      currentPassword: passwordForm.currentPassword, newPassword: passwordForm.newPassword
    })
    ElMessage.success('密码修改成功')
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (e) {
    ElMessage.error(e?.response?.data?.msg || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => { fetchUserInfo(); fetchStats() })
</script>

<style scoped>
.profile-page {
  padding: 24px;
  background: #f8fafc;
  min-height: calc(100vh - 60px);
}

/* 左侧用户卡片 */
.profile-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
  overflow: hidden;
}

.avatar-section {
  padding: 32px 24px 24px;
  text-align: center;
  background: #f8fafc;
  border-radius: 16px 16px 0 0;
  margin: -1px -1px 0;
}

.avatar-wrap {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.avatar-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  color: white;
  font-size: 20px;
  border-radius: 50%;
}

.avatar-wrap:hover .avatar-mask {
  opacity: 1;
}

.avatar-section :deep(.el-avatar) {
  width: 72px;
  height: 72px;
  background: #f0f7ff;
  color: #409eff;
  font-size: 32px;
}

.username {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
}

.avatar-section .el-tag {
  background: #f0f7ff;
  border-color: #e2e8f0;
  color: #1e293b;
}

.stats-row {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px 16px;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: #e2e8f0;
}

/* 提建议卡片 */
.feedback-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
  margin-top: 20px;
  overflow: hidden;
}

.feedback-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.feedback-body {
  padding: 16px 20px;
}

.feedback-body :deep(.el-textarea__inner) {
  border-radius: 10px;
  margin-bottom: 12px;
}

.feedback-btn {
  width: 100%;
  border-radius: 10px;
  padding: 10px;
}

/* 右侧信息卡片 */
.info-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
  padding: 24px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.form-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.form-actions .el-button {
  padding: 10px 24px;
  border-radius: 10px;
}

.readonly-text {
  color: #64748b;
  font-size: 14px;
}

.info-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #64748b;
}

.info-card :deep(.el-input__wrapper) {
  border-radius: 10px;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
