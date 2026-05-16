<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <div v-loading="loading" class="settings-content">
      <!-- LLM配置 -->
      <div class="settings-section">
        <h3>大模型配置</h3>
        <p class="section-desc">配置面试评估使用的AI大模型服务</p>

        <el-form label-width="140px" class="settings-form">
          <el-form-item label="服务提供商">
            <el-radio-group v-model="form.chat_provider">
              <el-radio value="tongyi">通义千问（阿里云）</el-radio>
              <el-radio value="openai_compatible">OpenAI 兼容</el-radio>
              <el-radio value="ollama">Ollama（本地）</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 通义千问 -->
          <el-form-item label="通义千问API Key" v-if="form.chat_provider === 'tongyi'">
            <el-input
              v-model="form.dashscope_api_key"
              type="password"
              placeholder="请输入DASHSCOPE_API_KEY"
              show-password
              style="max-width: 400px"
            />
          </el-form-item>

          <el-form-item label="云端模型名称" v-if="form.chat_provider === 'tongyi'">
            <el-select v-model="form.chat_model_cloud" style="width: 200px">
              <el-option value="qwen-max" label="qwen-max（最强）" />
              <el-option value="qwen-plus" label="qwen-plus" />
              <el-option value="qwen-turbo" label="qwen-turbo（最快）" />
            </el-select>
          </el-form-item>

          <!-- OpenAI 兼容 -->
          <template v-if="form.chat_provider === 'openai_compatible'">
            <el-form-item label="快速选择">
              <div class="preset-btns">
                <el-button v-for="p in openaiPresets" :key="p.name" size="small" @click="applyPreset(p)">
                  {{ p.name }}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item label="API Key">
              <el-input
                v-model="form.openai_api_key"
                type="password"
                placeholder="sk-..."
                show-password
                style="max-width: 400px"
              />
            </el-form-item>

            <el-form-item label="Base URL">
              <el-input
                v-model="form.openai_base_url"
                placeholder="https://api.openai.com/v1"
                style="max-width: 400px"
              />
            </el-form-item>

            <el-form-item label="模型名称">
              <el-input
                v-model="form.chat_model_openai"
                placeholder="gpt-4o-mini"
                style="max-width: 200px"
              />
            </el-form-item>
          </template>

          <!-- Ollama -->
          <el-form-item label="Ollama地址" v-if="form.chat_provider === 'ollama'">
            <el-input
              v-model="form.ollama_url"
              placeholder="http://localhost:11434"
              style="max-width: 300px"
            />
          </el-form-item>

          <el-form-item label="Ollama模型" v-if="form.chat_provider === 'ollama'">
            <el-input
              v-model="form.chat_model_ollama"
              placeholder="qwen3.5:9b"
              style="max-width: 200px"
            />
          </el-form-item>

          <el-form-item label="最大并发数">
            <el-input-number v-model="form.llm_max_concurrent" :min="1" :max="20" />
            <div class="form-tip">同时进行的LLM调用数量，建议5-10，避免API限流</div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="success"
              @click="handleTestLLM"
              :loading="testing"
            >
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            <span v-if="testResult" :class="['test-result', testResult.ok ? 'success' : 'fail']">
              {{ testResult.msg }}
            </span>
          </el-form-item>
        </el-form>
      </div>

      <!-- 面试配置 -->
      <div class="settings-section">
        <h3>面试参数</h3>

        <el-form label-width="140px" class="settings-form">
          <el-form-item label="系统名称">
            <el-input v-model="form.system_name" placeholder="AI模拟面试平台" style="max-width: 300px" />
          </el-form-item>

          <el-form-item label="默认面试时长">
            <el-input-number v-model="form.interview_default_time_limit" :min="5" :max="120" />
            <span class="unit">分钟</span>
          </el-form-item>

          <el-form-item label="默认题目数量">
            <el-input-number v-model="form.interview_default_question_count" :min="3" :max="20" />
            <span class="unit">道</span>
          </el-form-item>

          <el-form-item label="启用数字人">
            <el-switch v-model="form.digital_human_enabled" />
            <div class="form-tip">开启后在职位列表页可选择数字人面试模式</div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 保存按钮 -->
      <div class="settings-footer">
        <el-button @click="loadSettings">重置</el-button>
        <el-button type="primary" @click="saveSettings" :loading="saving">
          保存设置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'
import { getSettings, updateSetting, batchUpdateSettings, testLLMConnection } from '@/api/settings'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const form = reactive({
  chat_provider: 'tongyi',
  dashscope_api_key: '',
  chat_model_cloud: 'qwen-max',
  chat_model_ollama: 'qwen3.5:9b',
  ollama_url: 'http://localhost:11434',
  openai_api_key: '',
  openai_base_url: 'https://api.openai.com/v1',
  chat_model_openai: 'gpt-4o-mini',
  llm_max_concurrent: 5,
  system_name: 'AI模拟面试与能力提升平台',
  interview_default_time_limit: 30,
  interview_default_question_count: 5,
  digital_human_enabled: false,
})

const openaiPresets = [
  { name: 'OpenAI', url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { name: 'DeepSeek', url: 'https://api.deepseek.com', model: 'deepseek-chat' },
  { name: 'Moonshot', url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { name: '智谱 GLM', url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { name: '通义千问(兼容)', url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
]

const applyPreset = (preset) => {
  form.openai_base_url = preset.url
  form.chat_model_openai = preset.model
}

// 将后端返回的key映射到表单字段
const keyMap = {
  chat_provider: 'chat_provider',
  dashscope_api_key: 'dashscope_api_key',
  chat_model_cloud: 'chat_model_cloud',
  chat_model_ollama: 'chat_model_ollama',
  ollama_url: 'ollama_url',
  openai_api_key: 'openai_api_key',
  openai_base_url: 'openai_base_url',
  chat_model_openai: 'chat_model_openai',
  llm_max_concurrent: 'llm_max_concurrent',
  system_name: 'system_name',
  interview_default_time_limit: 'interview_default_time_limit',
  interview_default_question_count: 'interview_default_question_count',
  digital_human_enabled: 'digital_human_enabled',
}

const reverseKeyMap = Object.fromEntries(
  Object.entries(keyMap).map(([k, v]) => [v, k])
)

const loadSettings = async () => {
  loading.value = true
  try {
    const res = await getSettings()
    if (res.data.code === 200) {
      const settings = res.data.data
      for (const s of settings) {
        const field = keyMap[s.key]
        if (field) {
          let val = s.value
          // 类型转换
          if (field === 'llm_max_concurrent' || field === 'interview_default_time_limit' || field === 'interview_default_question_count') {
            val = parseInt(val) || 0
          } else if (field === 'digital_human_enabled') {
            val = val === 'true'
          }
          form[field] = val
        }
      }
    }
  } catch (e) {
    console.error('加载设置失败:', e)
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    // 构建要保存的key-value对（用后端key）
    const toSave = {}
    for (const [field, key] of Object.entries(reverseKeyMap)) {
      let val = form[field]
      // 跳过API Key（敏感字段，单个更新）
      if (key === 'dashscope_api_key' || key === 'openai_api_key') continue
      if (typeof val === 'boolean') val = val ? 'true' : 'false'
      if (typeof val === 'number') val = String(val)
      toSave[key] = val
    }

    const res = await batchUpdateSettings(toSave)
    if (res.data.code === 200) {
      ElMessage.success('设置已保存')

      // 敏感字段单独更新
      if (form.dashscope_api_key && form.dashscope_api_key !== '******') {
        await updateSetting('dashscope_api_key', form.dashscope_api_key)
      }
      if (form.openai_api_key && form.openai_api_key !== '******') {
        await updateSetting('openai_api_key', form.openai_api_key)
      }
      ElMessage.success('全部设置已保存，重启服务后生效')
    }
  } catch (e) {
    console.error('保存设置失败:', e)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleTestLLM = async () => {
  testing.value = true
  testResult.value = null
  try {
    const res = await testLLMConnection({
      chat_provider: form.chat_provider,
      dashscope_api_key: form.dashscope_api_key,
      chat_model_cloud: form.chat_model_cloud,
      chat_model_ollama: form.chat_model_ollama,
      ollama_url: form.ollama_url,
      openai_api_key: form.openai_api_key,
      openai_base_url: form.openai_base_url,
      chat_model_openai: form.chat_model_openai,
    })
    if (res.data.code === 200) {
      testResult.value = { ok: true, msg: `连接成功 - ${res.data.data?.reply || ''}` }
    } else {
      testResult.value = { ok: false, msg: res.data.msg || '连接失败' }
    }
  } catch (e) {
    testResult.value = { ok: false, msg: '连接失败: ' + (e.response?.data?.msg || e.message) }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
}

.settings-page h2 {
  margin: 0 0 24px 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.settings-content {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.settings-section {
  padding: 24px;
  border-bottom: 1px solid var(--color-border-light);
}

.settings-section:last-of-type {
  border-bottom: none;
}

.settings-section h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-desc {
  margin: 0 0 20px 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.settings-form {
  max-width: 600px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.unit {
  margin-left: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.settings-footer {
  padding: 20px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--color-border-light);
}

.preset-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.test-result {
  margin-left: 12px;
  font-size: 13px;
  font-weight: 500;
}

.test-result.success {
  color: #22C55E;
}

.test-result.fail {
  color: #EF4444;
}
</style>
