<template>
  <div class="dashboard">
    <!-- 欢迎区 -->
    <div class="welcome-card">
      <div class="welcome-content">
        <h1>{{ greeting }}，{{ authStore.userInfo.realName || authStore.userInfo.username || '用户' }}</h1>
        <p>多模态智能反诈助手，守护您的财产安全</p>
      </div>
      <div class="welcome-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </div>

    <!-- 统计区 -->
    <div class="stats-grid">
      <div class="stat-card" @click="$router.push('/chat')">
        <div class="stat-icon primary">
          <el-icon :size="24"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.chatCount }}</div>
          <div class="stat-label">反诈咨询次数</div>
        </div>
      </div>
      <div class="stat-card" @click="$router.push('/detect')">
        <div class="stat-icon warning">
          <el-icon :size="24"><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.detectCount }}</div>
          <div class="stat-label">诈骗检测次数</div>
        </div>
      </div>
      <div class="stat-card" @click="$router.push('/cases')">
        <div class="stat-icon success">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.caseCount }}</div>
          <div class="stat-label">学习案例数</div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <section class="section">
      <h2 class="section-title">反诈工具</h2>
      <div class="action-cards">
        <div class="action-card primary" @click="$router.push('/chat')">
          <div class="action-icon">
            <el-icon :size="32"><ChatDotRound /></el-icon>
          </div>
          <div class="action-text">
            <h3>AI反诈问答</h3>
            <p>遇到可疑情况？向AI反诈助手咨询</p>
          </div>
          <div class="action-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="action-card" @click="$router.push('/detect')">
          <div class="action-icon">
            <el-icon :size="32"><Search /></el-icon>
          </div>
          <div class="action-text">
            <h3>诈骗检测</h3>
            <p>上传截图或文字，AI帮您识别诈骗</p>
          </div>
          <div class="action-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- 常见诈骗类型 -->
    <section class="section">
      <h2 class="section-title">常见诈骗类型</h2>
      <div class="fraud-types">
        <div v-for="type in fraudTypes" :key="type.key" class="fraud-type-tag" @click="$router.push('/cases?type=' + type.key)">
          <el-icon><Warning /></el-icon>
          <span>{{ type.label }}</span>
        </div>
      </div>
    </section>

    <!-- 反诈提醒 -->
    <section class="section">
      <div class="tips-card">
        <h3>牢记"三不一多"原则</h3>
        <div class="tips-grid">
          <div class="tip-item">
            <div class="tip-icon">🚫</div>
            <div class="tip-text">
              <strong>未知链接不点击</strong>
              <p>不随意点击陌生链接和二维码</p>
            </div>
          </div>
          <div class="tip-item">
            <div class="tip-icon">📞</div>
            <div class="tip-text">
              <strong>陌生来电不轻信</strong>
              <p>接到陌生电话要核实身份</p>
            </div>
          </div>
          <div class="tip-item">
            <div class="tip-icon">🔒</div>
            <div class="tip-text">
              <strong>个人信息不透露</strong>
              <p>银行卡号、密码、验证码绝不外泄</p>
            </div>
          </div>
          <div class="tip-item">
            <div class="tip-icon">💰</div>
            <div class="tip-text">
              <strong>转账汇款多核实</strong>
              <p>转账前务必电话确认对方身份</p>
            </div>
          </div>
        </div>
        <div class="emergency-line">
          <el-icon><Phone /></el-icon>
          <span>全国反诈专线：<strong>96110</strong></span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ChatDotRound, Warning, Document, ArrowRight, Search, Phone } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import request from '../../api/request'

const authStore = useAuthStore()

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const stats = reactive({
  chatCount: 0,
  detectCount: 0,
  caseCount: 0,
})

const fraudTypes = [
  { key: 'phishing', label: '钓鱼诈骗' },
  { key: 'investment', label: '投资理财' },
  { key: 'impersonation', label: '冒充公检法' },
  { key: 'romance', label: '杀猪盘' },
  { key: 'shopping', label: '网购退款' },
  { key: 'part_time', label: '刷单兼职' },
  { key: 'loan', label: '贷款诈骗' },
  { key: 'gaming', label: '游戏交易' },
]

const fetchStats = async () => {
  try {
    const [chatRes, detectRes, caseRes] = await Promise.all([
      request.get('/api/v1/af/chat/sessions').catch(() => ({ data: { data: [] } })),
      request.get('/api/v1/af/detect/history', { params: { page: 1, page_size: 1 } }).catch(() => ({ data: { data: { total: 0 } } })),
      request.get('/api/v1/af/case/types').catch(() => ({ data: { data: [] } })),
    ])
    stats.chatCount = (chatRes.data.data || []).length
    stats.detectCount = detectRes.data.data?.total || 0
    stats.caseCount = (caseRes.data.data || []).reduce((sum, t) => sum + t.count, 0)
  } catch (e) {
    console.error('获取统计失败:', e)
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.dashboard {
  padding: 24px 0;
}

.welcome-card {
  background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
  border-radius: var(--radius-xl);
  padding: 32px 40px;
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}

.welcome-content {
  position: relative;
  z-index: 1;
}

.welcome-content h1 {
  color: white;
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.welcome-content p {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  margin: 0;
}

.welcome-decoration {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 { width: 120px; height: 120px; right: 0; top: -60px; }
.circle-2 { width: 80px; height: 80px; right: 100px; top: 20px; }
.circle-3 { width: 40px; height: 40px; right: 60px; bottom: -20px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-light);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.primary { background: linear-gradient(135deg, #E53935 0%, #FF5252 100%); }
.stat-icon.warning { background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); }
.stat-icon.success { background: linear-gradient(135deg, #22C55E 0%, #4ADE80 100%); }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 16px 0;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.action-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-light);
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.action-card.primary {
  background: linear-gradient(135deg, #E53935 0%, #FF5252 100%);
  border: none;
}

.action-card.primary .action-icon,
.action-card.primary h3,
.action-card.primary p {
  color: white;
}

.action-card.primary .action-arrow {
  color: rgba(255, 255, 255, 0.7);
}

.action-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  background: #FEE2E2;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E53935;
  flex-shrink: 0;
}

.action-text {
  flex: 1;
}

.action-text h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.action-text p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.action-arrow {
  color: var(--color-text-muted);
  font-size: 20px;
}

.fraud-types {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.fraud-type-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 20px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.fraud-type-tag:hover {
  border-color: #E53935;
  color: #E53935;
  background: #FEE2E2;
}

.tips-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  padding: 32px;
  border: 1px solid var(--color-border-light);
}

.tips-card h3 {
  margin: 0 0 24px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.tip-item {
  text-align: center;
}

.tip-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.tip-text strong {
  display: block;
  font-size: 14px;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.tip-text p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.emergency-line {
  text-align: center;
  padding: 16px;
  background: #FEF2F2;
  border-radius: var(--radius-lg);
  color: #E53935;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.emergency-line strong {
  font-size: 20px;
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
  .action-cards { grid-template-columns: 1fr; }
  .tips-grid { grid-template-columns: repeat(2, 1fr); }
  .welcome-card { padding: 24px; }
  .welcome-decoration { display: none; }
}
</style>
