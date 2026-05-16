<template>
  <div class="case-page">
    <div class="case-header">
      <h1>反诈案例库</h1>
      <p>学习真实案例，提高防骗意识</p>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <div class="filter-types">
        <el-tag
          v-for="t in typeOptions"
          :key="t.value"
          :type="selectedType === t.value ? 'danger' : ''"
          :effect="selectedType === t.value ? 'dark' : 'plain'"
          @click="selectedType = selectedType === t.value ? '' : t.value"
          class="type-tag"
        >
          {{ t.label }}
        </el-tag>
      </div>
      <el-input
        v-model="keyword"
        placeholder="搜索案例..."
        clearable
        style="width: 240px"
        @keyup.enter="loadCases"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 案例列表 -->
    <div class="case-list" v-loading="loading">
      <div
        v-for="item in cases"
        :key="item.id"
        class="case-card"
        @click="openDetail(item)"
      >
        <div class="case-type-badge" :class="item.fraudType">
          {{ fraudTypeMap[item.fraudType] || '其他' }}
        </div>
        <h3 class="case-title">{{ item.title }}</h3>
        <p class="case-preview">{{ item.content }}</p>
        <div class="case-meta">
          <span v-if="item.source">来源：{{ item.source }}</span>
          <span>浏览：{{ item.viewCount }}</span>
        </div>
      </div>

      <div v-if="!cases.length && !loading" class="empty-state">
        <el-icon :size="48"><Document /></el-icon>
        <p>暂无案例数据</p>
        <el-button v-if="isAdmin" type="primary" @click="syncCases" :loading="syncing">
          从知识库导入案例
        </el-button>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadCases"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetail" :title="detailItem?.title" width="640px">
      <div class="detail-content" v-if="detailItem">
        <div class="detail-meta">
          <el-tag type="danger">{{ fraudTypeMap[detailItem.fraudType] || '其他' }}</el-tag>
          <span v-if="detailItem.source">来源：{{ detailItem.source }}</span>
        </div>
        <div class="detail-text" v-html="formatContent(detailItem.content)"></div>
        <div class="detail-tags" v-if="detailItem.tags">
          <el-tag v-for="tag in detailItem.tags.split(',')" :key="tag" size="small">{{ tag }}</el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Document } from '@element-plus/icons-vue'
import { getCaseList, getCaseDetail, syncCasesFromKnowledge } from '../../api/antiFraud'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const cases = ref([])
const loading = ref(false)
const syncing = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const selectedType = ref('')
const keyword = ref('')
const showDetail = ref(false)
const detailItem = ref(null)

const typeOptions = [
  { value: 'phishing', label: '钓鱼诈骗' },
  { value: 'investment', label: '投资理财' },
  { value: 'impersonation', label: '冒充公检法' },
  { value: 'romance', label: '杀猪盘' },
  { value: 'shopping', label: '网购退款' },
  { value: 'part_time', label: '刷单兼职' },
  { value: 'loan', label: '贷款诈骗' },
  { value: 'gaming', label: '游戏交易' },
]

const fraudTypeMap = {
  phishing: '钓鱼诈骗',
  investment: '投资理财',
  impersonation: '冒充公检法',
  romance: '杀猪盘',
  shopping: '网购退款',
  part_time: '刷单兼职',
  loan: '贷款诈骗',
  gaming: '游戏交易',
  other: '其他',
}

const loadCases = async () => {
  loading.value = true
  try {
    const res = await getCaseList({
      fraud_type: selectedType.value || undefined,
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    if (res.data.code === 200) {
      cases.value = res.data.data?.items || []
      total.value = res.data.data?.total || 0
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const openDetail = async (item) => {
  try {
    const res = await getCaseDetail(item.id)
    if (res.data.code === 200) {
      detailItem.value = res.data.data
      showDetail.value = true
    }
  } catch (e) { console.error(e) }
}

const syncCases = async () => {
  syncing.value = true
  try {
    const res = await syncCasesFromKnowledge()
    if (res.data.code === 200) {
      ElMessage.success(`成功导入 ${res.data.data.added} 条案例`)
      loadCases()
    }
  } catch (e) { ElMessage.error('导入失败') }
  finally { syncing.value = false }
}

const formatContent = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

watch(selectedType, () => { page.value = 1; loadCases() })

onMounted(() => {
  if (route.query.type) selectedType.value = route.query.type
  loadCases()
})
</script>

<style scoped>
.case-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 0;
}

.case-header {
  text-align: center;
  margin-bottom: 32px;
}

.case-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
}

.case-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-types {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.type-tag {
  cursor: pointer;
  transition: all var(--transition-fast);
}

.type-tag:hover {
  transform: scale(1.05);
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 200px;
}

.case-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.case-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
}

.case-type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  background: #FEE2E2;
  color: #DC2626;
}

.case-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.case-preview {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.case-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
}

.empty-state p {
  margin: 12px 0 20px 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.detail-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
}

.detail-tags {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
