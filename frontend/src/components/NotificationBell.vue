<template>
  <el-dropdown trigger="click" placement="bottom-end" @visible-change="onDropdownChange">
    <div class="bell-trigger">
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
        <el-icon :size="20"><Bell /></el-icon>
      </el-badge>
    </div>
    <template #dropdown>
      <div class="notification-dropdown">
        <div class="dropdown-header">
          <span>通知</span>
          <el-button v-if="unreadCount > 0" type="primary" link size="small" @click.stop="handleMarkAllRead">
            全部已读
          </el-button>
        </div>

        <div class="notification-list" v-if="notifications.length">
          <div
            v-for="item in notifications"
            :key="item.id"
            class="notification-item"
            :class="{ unread: !item.isRead }"
            @click="handleClick(item)"
          >
            <div class="notif-content">
              <div class="notif-title">{{ item.title }}</div>
              <div class="notif-text" v-if="item.content">{{ item.content }}</div>
              <div class="notif-time">{{ item.createdAt }}</div>
            </div>
          </div>
        </div>
        <div v-else class="empty-notif">暂无通知</div>

        <div class="dropdown-footer">
          <router-link to="/notifications" @click.stop>查看全部</router-link>
        </div>
      </div>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from '@element-plus/icons-vue'
import { getNotifications, getUnreadCount, markAsRead, markAllAsRead } from '@/api/notification'

const router = useRouter()
const unreadCount = ref(0)
const notifications = ref([])

const fetchUnreadCount = async () => {
  try {
    const res = await getUnreadCount()
    if (res.data.code === 200) unreadCount.value = res.data.data.count
  } catch {}
}

const fetchNotifications = async () => {
  try {
    const res = await getNotifications({ page: 1, pageSize: 8, unreadFirst: true })
    if (res.data.code === 200) notifications.value = res.data.data.list || []
  } catch {}
}

const onDropdownChange = (visible) => {
  if (visible) fetchNotifications()
}

const handleMarkAllRead = async () => {
  try {
    await markAllAsRead()
    unreadCount.value = 0
    notifications.value.forEach(n => n.isRead = true)
  } catch {}
}

const handleClick = async (item) => {
  if (!item.isRead) {
    try {
      await markAsRead(item.id)
      item.isRead = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch {}
  }
  if (item.type === 'feedback_reply') {
    router.push('/profile')
  }
}

onMounted(fetchUnreadCount)

// 每 60 秒刷新未读数
setInterval(fetchUnreadCount, 60000)
</script>

<style scoped>
.bell-trigger {
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 6px;
  transition: background 0.2s;
}

.bell-trigger:hover {
  background: var(--color-bg);
}

.notification-dropdown {
  width: 340px;
  max-height: 420px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-light);
  font-weight: 600;
  font-size: 15px;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--color-border-light);
}

.notification-item:hover {
  background: var(--color-bg);
}

.notification-item.unread {
  background: var(--color-primary-bg);
}

.notif-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.notif-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notif-time {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.empty-notif {
  padding: 32px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
}

.dropdown-footer {
  padding: 8px 16px;
  text-align: center;
  border-top: 1px solid var(--color-border-light);
}

.dropdown-footer a {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 13px;
}
</style>
