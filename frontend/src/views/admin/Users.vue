<template>
  <div class="users-page">
    <!-- 页面标题 -->
    <div class="page-hero">
      <div class="hero-content">
        <h1 class="hero-title">用户管理</h1>
        <p class="hero-subtitle">管理系统中的用户信息，支持新增、编辑和删除操作</p>
      </div>
      <el-button type="primary" class="add-btn" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新增用户
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon blue">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ total }}</span>
          <span class="stat-label">用户总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ activeCount }}</span>
          <span class="stat-label">已启用</span>
        </div>
      </div>
    </div>

    <!-- 搜索过滤 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名/邮箱..."
        class="search-input"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <el-table :data="filteredUsers" style="width: 100%" v-loading="loading" class="custom-table">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="realName" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isActive" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isActive ? 'success' : 'danger'" size="small">
              {{ row.isActive ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-popconfirm
              title="确定删除该用户？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button size="small" type="danger" link>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredUsers.length === 0 && !loading" description="暂无用户数据" />

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchUsers"
          @size-change="fetchUsers"
        />
      </div>
    </div>

    <!-- 新增用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="form.realName" placeholder="可选" />
          </el-form-item>
        </div>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" style="width: 100%">
              <el-option label="学生" value="student" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
          <el-form-item label="学校">
            <el-select v-model="form.schoolId" placeholder="请选择学校" style="width: 100%" clearable filterable>
              <el-option v-for="s in schoolOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, User, CircleCheck, UserFilled, Edit, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'

const loading = ref(false)
const submitting = ref(false)
const allUsers = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const form = ref({
  username: '',
  email: '',
  password: '',
  realName: '',
  role: 'student',
  schoolId: '',
  isActive: true,
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const filteredUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return allUsers.value.slice(start, start + pageSize.value)
})

const total = computed(() => allUsers.value.length)
const activeCount = computed(() => allUsers.value.filter(u => u.isActive).length)

const roleLabel = (role) => {
  const map = { admin: '管理员', student: '学生' }
  return map[role] || role
}

const roleTagType = (role) => {
  const map = { admin: 'danger', student: 'success' }
  return map[role] || 'info'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await request.get('/api/v1/auth/users', { params })
    if (res.data.code === 200) {
      allUsers.value = res.data.data || []
    }
  } catch (e) {
    console.error('获取用户列表失败:', e)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleEdit = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = {
    username: row.username,
    email: row.email,
    password: '',
    realName: row.realName || '',
    role: row.role,
    schoolId: row.schoolId || '',
    isActive: row.isActive,
  }
  showCreateDialog.value = true
}

const handleDelete = async (row) => {
  try {
    await request.delete(`/api/v1/auth/users/${row.id}`)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '删除失败')
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  isEdit.value = false
  editingId.value = null
  form.value = {
    username: '',
    email: '',
    password: '',
    realName: '',
    role: 'student',
    schoolId: '',
    isActive: true,
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value) {
        const res = await request.put(`/api/v1/auth/users/${editingId.value}`, {
          email: form.value.email,
          realName: form.value.realName,
          role: form.value.role,
          schoolId: form.value.schoolId,
          isActive: form.value.isActive,
        })
        if (res.data.code === 200) {
          ElMessage.success('更新成功')
          closeDialog()
          fetchUsers()
        } else {
          ElMessage.error(res.data.msg || '更新失败')
        }
      } else {
        const res = await request.post('/api/v1/auth/register', form.value)
        if (res.data.code === 200) {
          ElMessage.success('创建成功')
          closeDialog()
          fetchUsers()
        } else {
          ElMessage.error(res.data.msg || '创建失败')
        }
      }
    } catch (e) {
      ElMessage.error(e.response?.data?.msg || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const schoolOptions = ref([])

const loadSchoolOptions = async () => {
  try {
    const res = await request.get('/api/v1/school/options')
    if (res.data.code === 200) {
      schoolOptions.value = res.data.data || []
    }
  } catch (e) {
    console.error('加载学校选项失败:', e)
  }
}

onMounted(() => {
  fetchUsers()
  loadSchoolOptions()
})
</script>

<style scoped>
.users-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 32px;
  background: white;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.hero-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.hero-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.add-btn {
  padding: 12px 24px;
  border-radius: 14px;
  font-weight: 500;
  background: #409eff;
  color: white;
  border: none;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: white;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue {
  background: #f0f7ff;
  color: #409eff;
}

.stat-icon.green {
  background: #f0fdf4;
  color: #67c23a;
}

.stat-icon.orange {
  background: #fff8f0;
  color: #e6a23c;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.filter-bar {
  margin-bottom: 20px;
}

.search-input {
  width: 320px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 4px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.table-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.custom-table :deep(.el-table__header th) {
  font-weight: 600;
  color: #475569;
  font-size: 13px;
}

.custom-table :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
