<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <aside class="session-sidebar">
      <div class="sidebar-header">
        <h3>反诈咨询</h3>
        <el-button type="primary" size="small" @click="createSession">
          <el-icon><Plus /></el-icon> 新会话
        </el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="selectSession(s.id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="session-title">{{ s.title }}</span>
          <span class="session-time">{{ s.updatedAt?.slice(5, 16) }}</span>
        </div>
        <div v-if="!sessions.length" class="empty-hint">暂无会话，点击新建</div>
      </div>
    </aside>

    <!-- 右侧聊天区 -->
    <main class="chat-main">
      <div class="chat-header" v-if="currentSessionId">
        <h3>{{ currentSession?.title || '反诈咨询' }}</h3>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!currentSessionId" class="welcome-area">
          <div class="welcome-icon">🛡️</div>
          <h2>AI反诈助手</h2>
          <p>遇到可疑情况？向我咨询，帮您识别诈骗风险</p>
          <div class="quick-questions">
            <div class="quick-q" v-for="q in quickQuestions" :key="q" @click="sendQuickQuestion(q)">
              {{ q }}
            </div>
          </div>
        </div>

        <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.role">
          <div class="message-avatar">
            <span v-if="msg.role === 'user'">{{ userInitial }}</span>
            <span v-else>🛡️</span>
          </div>
          <div class="message-bubble">
            <div class="message-content" v-html="formatMessage(msg.content)"></div>
            <div class="message-time">{{ msg.createdAt?.slice(11, 16) }}</div>
          </div>
        </div>

        <div v-if="sending" class="message-row assistant">
          <div class="message-avatar"><span>🛡️</span></div>
          <div class="message-bubble">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area" v-if="currentSessionId">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="描述您遇到的可疑情况，AI帮您分析..."
            @keydown.enter.ctrl="sendMessage"
            :disabled="sending"
          />
          <el-button type="primary" @click="sendMessage" :loading="sending" :disabled="!inputText.trim()">
            发送
          </el-button>
        </div>
        <div class="input-hint">Ctrl+Enter 发送 | 遇到紧急诈骗请直接拨打 96110</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { Plus, ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { getChatSessions, createChatSession, getChatMessages, sendChatMessage } from '../../api/antiFraud'

const authStore = useAuthStore()
const userInitial = computed(() => (authStore.userInfo.realName || authStore.userInfo.username || 'U')[0])

const sessions = ref([])
const currentSessionId = ref(null)
const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value))
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const messagesContainer = ref(null)

const quickQuestions = [
  '我收到一个退款电话，是不是诈骗？',
  '有人说我中奖了，要交手续费',
  '网上有人让我刷单返利，靠谱吗？',
  '冒充公检法要求转账到安全账户',
]

const loadSessions = async () => {
  try {
    const res = await getChatSessions()
    if (res.data.code === 200) sessions.value = res.data.data || []
  } catch (e) { console.error(e) }
}

const createSession = async () => {
  try {
    const res = await createChatSession()
    if (res.data.code === 200) {
      await loadSessions()
      currentSessionId.value = res.data.data.id
      messages.value = []
    }
  } catch (e) { console.error(e) }
}

const selectSession = async (id) => {
  currentSessionId.value = id
  try {
    const res = await getChatMessages(id)
    if (res.data.code === 200) messages.value = res.data.data || []
    await nextTick()
    scrollToBottom()
  } catch (e) { console.error(e) }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  if (!currentSessionId.value) {
    await createSession()
  }

  inputText.value = ''
  messages.value.push({ id: Date.now(), role: 'user', content: text, createdAt: new Date().toISOString() })
  await nextTick()
  scrollToBottom()

  sending.value = true
  try {
    const res = await sendChatMessage(currentSessionId.value, text)
    if (res.data.code === 200) {
      messages.value.push({
        id: res.data.data.replyId,
        role: 'assistant',
        content: res.data.data.reply,
        createdAt: new Date().toISOString(),
      })
    }
  } catch (e) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，AI服务暂时不可用。如有紧急情况请拨打96110反诈专线。',
      createdAt: new Date().toISOString(),
    })
  } finally {
    sending.value = false
    await nextTick()
    scrollToBottom()
  }
}

const sendQuickQuestion = (q) => {
  inputText.value = q
  sendMessage()
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

onMounted(loadSessions)
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - var(--header-height) - 48px);
  background: var(--color-bg);
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--color-border-light);
}

.session-sidebar {
  width: 260px;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border-light);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.session-item:hover {
  background: var(--color-bg);
}

.session-item.active {
  background: #FEE2E2;
  color: #E53935;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 11px;
  color: var(--color-text-muted);
}

.empty-hint {
  text-align: center;
  padding: 40px 16px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-card);
}

.chat-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-area {
  text-align: center;
  padding: 80px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-area h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--color-text-primary);
}

.welcome-area p {
  margin: 0 0 32px 0;
  color: var(--color-text-secondary);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.quick-q {
  padding: 10px 20px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 20px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-q:hover {
  border-color: #E53935;
  color: #E53935;
  background: #FEE2E2;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.message-row.user .message-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
}

.message-row.assistant .message-avatar {
  background: #FEE2E2;
  font-size: 18px;
}

.message-bubble {
  max-width: 70%;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-row.user .message-content {
  background: var(--color-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .message-content {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-light);
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.message-row.user .message-time {
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-light);
  background: var(--color-bg-card);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-hint {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 8px;
}

@media (max-width: 768px) {
  .session-sidebar { display: none; }
}
</style>
