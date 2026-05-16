<template>
  <div class="main-layout">
    <!-- 顶部导航 -->
    <header class="top-header">
      <div class="header-left">
        <div class="logo">
          <div class="logo-icon">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <span class="logo-text">反诈助手</span>
        </div>
      </div>

      <nav class="header-nav">
        <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
          <span>首页</span>
        </router-link>
        <router-link to="/chat" class="nav-item" :class="{ active: route.path === '/chat' }">
          <span>AI反诈问答</span>
        </router-link>
        <router-link to="/detect" class="nav-item" :class="{ active: route.path === '/detect' }">
          <span>诈骗检测</span>
        </router-link>
        <router-link to="/cases" class="nav-item" :class="{ active: route.path === '/cases' }">
          <span>反诈案例</span>
        </router-link>
        <el-dropdown v-if="authStore.isAdmin" trigger="click" placement="bottom-start">
          <span class="nav-item dropdown-trigger" :class="{ active: route.path.startsWith('/admin') }">
            管理 <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item><router-link to="/admin/users" class="dropdown-nav-link">用户管理</router-link></el-dropdown-item>
              <el-dropdown-item><router-link to="/admin/settings" class="dropdown-nav-link">系统设置</router-link></el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>

      <div class="header-right">
        <el-dropdown trigger="click" placement="bottom-end">
          <div class="user-trigger">
            <div class="user-avatar">
              {{ (authStore.userInfo.realName || authStore.userInfo.username || 'U')[0] }}
            </div>
            <span class="user-name">{{ authStore.userInfo.realName || authStore.userInfo.username }}</span>
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/profile')">
                <el-icon><User /></el-icon>
                <span>个人中心</span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { User, ArrowDown, SwitchButton, Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = async () => {
  await ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: var(--color-bg);
}

.top-header {
  height: var(--header-height);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.95);
}

.header-left {
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 32px;
  flex: 1;
}

.nav-item {
  padding: 8px 12px;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  color: var(--color-text-primary);
  background: #FEE2E2;
}

.nav-item.active {
  color: #E53935;
  background: #FEE2E2;
}

.header-right {
  flex-shrink: 0;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.user-trigger:hover {
  background: var(--color-bg);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.arrow {
  font-size: 12px;
  color: var(--color-text-muted);
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.dropdown-nav-link {
  color: inherit;
  text-decoration: none;
  display: block;
  width: 100%;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
}

.main-content {
  padding: 24px;
  max-width: var(--content-max-width);
  margin: 0 auto;
}

@media (max-width: 768px) {
  .header-nav { display: none; }
  .user-name { display: none; }
  .top-header { padding: 0 16px; }
}
</style>
