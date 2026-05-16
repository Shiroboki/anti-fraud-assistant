<template>
  <div class="detect-page">
    <div class="detect-header">
      <h1>诈骗检测</h1>
      <p>上传截图或粘贴文字，AI帮您识别是否为诈骗</p>
    </div>

    <div class="detect-content">
      <!-- 输入区 -->
      <div class="input-section">
        <el-tabs v-model="detectType">
          <el-tab-pane label="文本检测" name="text">
            <el-input
              v-model="textContent"
              type="textarea"
              :rows="6"
              placeholder="粘贴可疑的短信、聊天记录、邮件内容等..."
            />
          </el-tab-pane>
          <el-tab-pane label="图片检测" name="image">
            <el-upload
              class="image-upload"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :limit="1"
              accept="image/*"
            >
              <el-icon :size="48"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽图片到此处，或<em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">支持 JPG/PNG 格式截图</div>
              </template>
            </el-upload>
            <el-input
              v-model="imageDesc"
              type="textarea"
              :rows="2"
              placeholder="补充描述（可选）：这张图片的来源、上下文等"
              style="margin-top: 12px"
            />
          </el-tab-pane>
        </el-tabs>

        <el-button
          type="danger"
          size="large"
          @click="startDetect"
          :loading="detecting"
          :disabled="!canDetect"
          style="width: 100%; margin-top: 16px"
        >
          <el-icon><Search /></el-icon>
          开始检测
        </el-button>
      </div>

      <!-- 结果区 -->
      <div class="result-section" v-if="result">
        <div class="result-card" :class="result.risk_level">
          <div class="result-header">
            <div class="risk-badge" :class="result.risk_level">
              {{ riskLevelMap[result.risk_level] || '未知' }}
            </div>
            <div class="confidence">
              置信度：{{ Math.round((result.confidence || 0) * 100) }}%
            </div>
          </div>

          <div class="result-body">
            <div class="result-label">分析结果</div>
            <p class="result-text">{{ result.analysis }}</p>

            <template v-if="result.fraud_type && result.fraud_type !== 'null'">
              <div class="result-label">诈骗类型</div>
              <el-tag type="danger" size="large">{{ fraudTypeMap[result.fraud_type] || result.fraud_type }}</el-tag>
            </template>

            <div class="result-label" v-if="result.suggestions?.length">防范建议</div>
            <ul class="suggestions" v-if="result.suggestions?.length">
              <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
            </ul>
          </div>

          <div class="result-footer" v-if="result.risk_level === 'high' || result.risk_level === 'critical'">
            <el-icon><Warning /></el-icon>
            <span>检测到高风险！如已转账请立即拨打 <strong>110</strong> 报警，或拨打 <strong>96110</strong> 反诈专线</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 检测历史 -->
    <div class="history-section" v-if="history.length">
      <h2>检测历史</h2>
      <div class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item">
          <div class="history-type">
            <el-icon v-if="item.detectionType === 'image'"><Picture /></el-icon>
            <el-icon v-else><Document /></el-icon>
            {{ item.detectionType === 'image' ? '图片检测' : '文本检测' }}
          </div>
          <div class="history-content">{{ item.inputContent }}</div>
          <div class="history-risk" :class="item.riskLevel">
            {{ riskLevelMap[item.riskLevel] || '未知' }}
          </div>
          <div class="history-time">{{ item.createdAt }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Warning, UploadFilled, Picture, Document } from '@element-plus/icons-vue'
import { detectText, detectImage, getDetectionHistory } from '../../api/antiFraud'
import { ElMessage } from 'element-plus'

const detectType = ref('text')
const textContent = ref('')
const imageFile = ref(null)
const imageDesc = ref('')
const detecting = ref(false)
const result = ref(null)
const history = ref([])

const canDetect = computed(() => {
  if (detectType.value === 'text') return textContent.value.trim().length > 0
  return !!imageFile.value
})

const riskLevelMap = {
  safe: '安全',
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '极高风险',
}

const fraudTypeMap = {
  phishing: '钓鱼诈骗',
  investment: '投资理财诈骗',
  impersonation: '冒充公检法',
  romance: '杀猪盘/网恋诈骗',
  shopping: '网购退款诈骗',
  part_time: '刷单兼职诈骗',
  loan: '贷款诈骗',
  gaming: '游戏交易诈骗',
  other: '其他类型',
}

const handleFileChange = (file) => {
  imageFile.value = file.raw
}

const startDetect = async () => {
  detecting.value = true
  result.value = null
  try {
    let res
    if (detectType.value === 'text') {
      res = await detectText(textContent.value)
    } else {
      res = await detectImage(imageFile.value, imageDesc.value)
    }
    if (res.data.code === 200) {
      result.value = res.data.data
      loadHistory()
    }
  } catch (e) {
    ElMessage.error('检测失败，请稍后重试')
  } finally {
    detecting.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await getDetectionHistory(1, 10)
    if (res.data.code === 200) history.value = res.data.data?.items || []
  } catch (e) { console.error(e) }
}

onMounted(loadHistory)
</script>

<style scoped>
.detect-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 0;
}

.detect-header {
  text-align: center;
  margin-bottom: 32px;
}

.detect-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.detect-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.detect-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 40px;
}

.input-section {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  padding: 24px;
  border: 1px solid var(--color-border-light);
}

.image-upload {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
}

.result-section {
  min-height: 200px;
}

.result-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  border: 2px solid var(--color-border-light);
  overflow: hidden;
}

.result-card.safe { border-color: #22C55E; }
.result-card.low { border-color: #FBBF24; }
.result-card.medium { border-color: #F59E0B; }
.result-card.high { border-color: #EF4444; }
.result-card.critical { border-color: #DC2626; }

.result-header {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border-light);
}

.risk-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.risk-badge.safe { background: #DCFCE7; color: #16A34A; }
.risk-badge.low { background: #FEF9C3; color: #A16207; }
.risk-badge.medium { background: #FEF3C7; color: #D97706; }
.risk-badge.high { background: #FEE2E2; color: #DC2626; }
.risk-badge.critical { background: #FEE2E2; color: #991B1B; }

.confidence {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.result-body {
  padding: 20px;
}

.result-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 16px 0 8px 0;
}

.result-label:first-child {
  margin-top: 0;
}

.result-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
  margin: 0;
}

.suggestions {
  margin: 0;
  padding-left: 20px;
}

.suggestions li {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

.result-footer {
  padding: 12px 20px;
  background: #FEF2F2;
  color: #DC2626;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-footer strong {
  font-size: 16px;
}

.history-section {
  margin-top: 40px;
}

.history-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--color-border-light);
}

.history-type {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.history-content {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-risk {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.history-risk.safe { background: #DCFCE7; color: #16A34A; }
.history-risk.low { background: #FEF9C3; color: #A16207; }
.history-risk.medium { background: #FEF3C7; color: #D97706; }
.history-risk.high { background: #FEE2E2; color: #DC2626; }
.history-risk.critical { background: #FEE2E2; color: #991B1B; }

.history-time {
  font-size: 12px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .detect-content { grid-template-columns: 1fr; }
}
</style>
