<template>
  <div class="assistant-view">
    <AppHeader title="环保小助手" show-back />

    <div class="chat-container">
      <div class="welcome-card">
        <div class="welcome-header">
          <h2>
            <el-icon><ChatDotRound /></el-icon>
            环保小助手
          </h2>
          <el-radio-group v-model="assistantMode" size="small" class="mode-switch">
            <el-radio-button value="langchain">LangChain（推荐）</el-radio-button>
            <el-radio-button value="langchain4j">LangChain4j</el-radio-button>
          </el-radio-group>
        </div>
        <p>{{ currentModeConfig.description }}</p>
        <div class="welcome-tags">
          <el-tag v-if="assistantMode === 'langchain'" type="success" effect="plain">成熟Agent</el-tag>
          <el-tag v-if="assistantMode === 'langchain'" type="success" effect="plain">多工具编排</el-tag>
          <el-tag v-if="assistantMode === 'langchain'" type="success" effect="plain">对话记忆</el-tag>
          <el-tag type="success" effect="plain">工具调用</el-tag>
          <el-tag type="success" effect="plain">知识问答</el-tag>
          <el-tag type="success" effect="plain">流式输出</el-tag>
        </div>
        <div class="mode-info">
          <el-tag size="small" :type="assistantMode === 'langchain' ? 'success' : 'warning'">
            当前模式：{{ currentModeConfig.title }}
          </el-tag>
        </div>
      </div>

      <div class="chat-area">
        <div class="chat-header">
          <div class="assistant-avatar">
            <el-icon><Service /></el-icon>
          </div>
          <div class="assistant-info">
            <h3>环保小助手</h3>
            <p>{{ currentModeConfig.subtitle }}</p>
          </div>
          <div class="status-dot"></div>
        </div>

        <div class="message-list" ref="messageList">
          <div class="empty-state" v-if="messages.length === 0">
            <el-icon><ChatLineRound /></el-icon>
            <h3>开始对话</h3>
            <p>{{ currentModeConfig.emptyTip }}</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index"
               :class="['message-item', msg.role]">
            <div class="message-avatar">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-bubble" v-html="formatMessage(msg.content)"></div>

              <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-info">
                <el-icon><Connection /></el-icon>
                已调用 {{ msg.toolCalls.join('、') }} 工具
              </div>

              <div v-if="msg.references && msg.references.length > 0" class="reference-section">
                <h4>
                  <el-icon><Reading /></el-icon>
                  参考来源
                </h4>
                <p v-for="(ref, rIndex) in msg.references" :key="rIndex">
                  {{ rIndex + 1 }}. {{ ref }}
                </p>
              </div>

              <span class="message-time">{{ msg.time }}</span>
            </div>
          </div>

          <div v-if="isLoading" class="message-item assistant">
            <div class="message-avatar">
              <el-icon><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="quick-questions" v-if="messages.length === 0">
            <el-tag v-for="q in currentModeConfig.quickQuestions" :key="q"
                    type="info" effect="plain"
                    @click="handleQuickQuestion(q)">
              {{ q }}
            </el-tag>
          </div>

          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              :placeholder="currentModeConfig.inputPlaceholder"
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="isLoading"
            />
            <el-button type="success"
                       class="send-btn"
                       :disabled="!inputMessage.trim() || isLoading"
                       :loading="isLoading"
                       @click="sendMessage">
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'

const router = useRouter()

const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const messageList = ref(null)
const assistantMode = ref('langchain')

const MODE_CONFIG = {
  langchain: {
    title: 'LangChain（默认）',
    subtitle: 'Python Agent（更完善，推荐）',
    description: '当前默认使用 LangChain Agent 模式，支持更完整的工具编排、记忆与多轮推理，更接近成熟 Agent 体验。',
    emptyTip: '输入问题后，LangChain Agent 会调用知识库与工具链为你解答',
    inputPlaceholder: '输入环保问题，按 Enter 发送，Shift+Enter 换行...',
    apiPath: '/environment/api/assistant/langchain/stream',
    mode: 'agent',
    quickQuestions: [
      '请解释 PM2.5 与 PM10 的区别，并给出防护建议',
      '结合环保法规，企业废水排放一般要关注哪些指标？',
      '帮我整理一份垃圾分类科普的讲解提纲',
      '现在给我一套节能减排的家庭实践清单'
    ]
  },
  langchain4j: {
    title: 'LangChain4j（独立）',
    subtitle: 'Java RAG 助手',
    description: 'LangChain4j 页面独立保留，适合验证 Java 端 RAG 能力，和 LangChain Agent 完全分开。',
    emptyTip: '输入问题后，LangChain4j 助手会基于 Java 侧知识检索进行回答',
    inputPlaceholder: '输入问题，按 Enter 发送，Shift+Enter 换行...',
    apiPath: '/environment/api/assistant/langchain4j/chat',
    mode: 'rag',
    quickQuestions: [
      '什么是温室气体排放核算？',
      '环保法对企业信息公开有什么要求？',
      '大气污染防治常见措施有哪些？',
      '工业废气治理有哪些常用技术？'
    ]
  }
}

const currentModeConfig = computed(() => {
  return MODE_CONFIG[assistantMode.value]
})

const checkLogin = () => {
  const token = localStorage.getItem('token')
  const userInfo = localStorage.getItem('userInfo')

  if (!token || !userInfo) {
    ElMessage.warning('请先登录')
    setTimeout(() => {
      router.push('/')
    }, 1500)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

const getCurrentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const createSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
}

const getSessionId = () => {
  const key = `chatSessionId:${assistantMode.value}`
  let sessionId = localStorage.getItem(key)
  if (!sessionId) {
    sessionId = createSessionId()
    localStorage.setItem(key, sessionId)
  }
  return sessionId
}

const escapeHtml = (text) => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

const renderInlineMarkdown = (line) => {
  let text = line
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
  return text
}

const formatMessage = (content) => {
  if (!content) return ''
  const codeBlocks = []
  let text = content.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const token = `__CODE_BLOCK_${codeBlocks.length}__`
    const languageClass = lang ? ` class="lang-${lang}"` : ''
    codeBlocks.push(`<pre><code${languageClass}>${escapeHtml(code)}</code></pre>`)
    return token
  })

  text = escapeHtml(text).replace(/\r\n/g, '\n')
  const lines = text.split('\n')
  const htmlParts = []
  let inUl = false
  let inOl = false

  const closeLists = () => {
    if (inUl) {
      htmlParts.push('</ul>')
      inUl = false
    }
    if (inOl) {
      htmlParts.push('</ol>')
      inOl = false
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim()

    if (line.startsWith('__CODE_BLOCK_')) {
      closeLists()
      htmlParts.push(line)
      continue
    }

    if (!line) {
      closeLists()
      continue
    }

    const ulMatch = line.match(/^[-*]\s+(.+)/)
    if (ulMatch) {
      if (!inUl) {
        closeLists()
        htmlParts.push('<ul>')
        inUl = true
      }
      htmlParts.push(`<li>${renderInlineMarkdown(ulMatch[1])}</li>`)
      continue
    }

    const olMatch = line.match(/^\d+\.\s+(.+)/)
    if (olMatch) {
      if (!inOl) {
        closeLists()
        htmlParts.push('<ol>')
        inOl = true
      }
      htmlParts.push(`<li>${renderInlineMarkdown(olMatch[1])}</li>`)
      continue
    }

    closeLists()

    if (line.startsWith('### ')) {
      htmlParts.push(`<h3>${renderInlineMarkdown(line.substring(4))}</h3>`)
      continue
    }
    if (line.startsWith('## ')) {
      htmlParts.push(`<h2>${renderInlineMarkdown(line.substring(3))}</h2>`)
      continue
    }
    if (line.startsWith('# ')) {
      htmlParts.push(`<h1>${renderInlineMarkdown(line.substring(2))}</h1>`)
      continue
    }
    if (line.startsWith('&gt;')) {
      htmlParts.push(`<blockquote>${renderInlineMarkdown(line.substring(4).trim())}</blockquote>`)
      continue
    }

    htmlParts.push(`<p>${renderInlineMarkdown(line)}</p>`)
  }

  closeLists()
  let html = htmlParts.join('')
  html = html.replace(/__CODE_BLOCK_(\d+)__/g, (_, index) => codeBlocks[Number(index)] || '')
  return html
}

const pushAssistantMessageIfNeeded = (assistantIndex, content, meta = {}) => {
  let index = assistantIndex
  if (index === -1) {
    index = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      time: getCurrentTime(),
      toolCalls: [],
      references: []
    })
  }

  const target = messages.value[index]
  if (meta.replace) {
    target.content = content
  } else {
    target.content += content
  }

  if (meta.toolCalls && meta.toolCalls.length > 0) {
    const toolSet = new Set([...(target.toolCalls || []), ...meta.toolCalls])
    target.toolCalls = Array.from(toolSet)
  }
  if (meta.references && meta.references.length > 0) {
    target.references = meta.references
  }

  return index
}

const parseSseEvent = (eventBlock) => {
  const lines = eventBlock
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.startsWith('data:'))
    .map(line => line.slice(5).trim())

  if (lines.length === 0) return null

  const payload = lines.join('\n')
  if (!payload || payload === '[DONE]') {
    return { done: true }
  }

  try {
    const parsed = JSON.parse(payload)

    if (parsed.error) {
      return { error: parsed.error }
    }

    if (typeof parsed.content === 'string') {
      return {
        content: parsed.content,
        toolCalls: parsed.tool_calls || parsed.toolCalls || [],
        references: parsed.references || []
      }
    }

    if (typeof parsed.answer === 'string') {
      return {
        content: parsed.answer,
        replace: true,
        toolCalls: parsed.tool_calls || parsed.toolCalls || [],
        references: parsed.references || []
      }
    }
  } catch (_) {
    return { content: payload }
  }

  return null
}

const readSseStream = async (response, onChunk) => {
  if (!response.body) throw new Error('响应体为空')

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const eventBlock of events) {
      const result = parseSseEvent(eventBlock)
      if (result) onChunk(result)
    }
  }

  if (buffer.trim()) {
    const finalResult = parseSseEvent(buffer)
    if (finalResult) onChunk(finalResult)
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  messages.value.push({
    role: 'user',
    content: message,
    time: getCurrentTime()
  })

  inputMessage.value = ''
  scrollToBottom()

  isLoading.value = true
  let assistantIndex = -1

  try {
    const token = localStorage.getItem('token')
    const response = await fetch(currentModeConfig.value.apiPath, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question: message,
        message,
        mode: currentModeConfig.value.mode,
        sessionId: getSessionId()
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    await readSseStream(response, (event) => {
      if (event.done) return
      if (event.error) throw new Error(event.error)
      if (!event.content) return

      if (assistantIndex === -1) {
        isLoading.value = false
      }
      assistantIndex = pushAssistantMessageIfNeeded(assistantIndex, event.content, {
        replace: event.replace,
        toolCalls: event.toolCalls,
        references: event.references
      })
      scrollToBottom()
    })

    if (assistantIndex === -1) {
      messages.value.push({
        role: 'assistant',
        content: '请求已完成，但未返回可展示内容。',
        time: getCurrentTime(),
        toolCalls: [],
        references: []
      })
    }

  } catch (error) {
    console.error('发送消息失败', error)
    ElMessage.error('网络错误，请重试')
    if (assistantIndex === -1) {
      messages.value.push({
        role: 'assistant',
        content: '抱歉，网络连接出现问题，请检查网络后重试。',
        time: getCurrentTime(),
        toolCalls: [],
        references: []
      })
    } else if (messages.value[assistantIndex]) {
      messages.value[assistantIndex].content = '抱歉，网络连接出现问题，请检查网络后重试。'
      messages.value[assistantIndex].toolCalls = []
      messages.value[assistantIndex].references = []
    }
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const handleQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

onMounted(() => {
  checkLogin()
})
</script>

<style scoped>
.assistant-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  padding: 84px 24px 24px;
}

.welcome-card {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e9 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid #d1edc4;
}

.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.welcome-card h2 {
  color: #2e7d32;
  font-size: 20px;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-switch {
  flex-shrink: 0;
}

.mode-info {
  margin-top: 12px;
  display: flex;
  align-items: center;
}

.welcome-card p {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.welcome-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.chat-area {
  flex: 1;
  background-color: #fff;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 500px;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: #fafafa;
}

.chat-header .assistant-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #67c23a, #4caf50);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-header .assistant-avatar .el-icon {
  color: #fff;
  font-size: 20px;
}

.chat-header .assistant-info h3 {
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.chat-header .assistant-info p {
  font-size: 12px;
  color: #909399;
}

.chat-header .status-dot {
  width: 8px;
  height: 8px;
  background-color: #67c23a;
  border-radius: 50%;
  margin-left: auto;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-item.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.message-item.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background-color: #409eff;
}

.message-item.assistant .message-avatar {
  background: linear-gradient(135deg, #67c23a, #4caf50);
}

.message-avatar .el-icon {
  color: #fff;
  font-size: 18px;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-item.user .message-bubble {
  background-color: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-bubble {
  background-color: #f5f7fa;
  color: #303133;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.reference-section {
  margin-top: 12px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #67c23a;
}

.reference-section h4 {
  font-size: 13px;
  color: #67c23a;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reference-section p {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.tool-info {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #ecf5ff;
  border-radius: 6px;
  font-size: 12px;
  color: #409eff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  background-color: #fff;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  font-size: 14px;
}

.send-btn {
  height: 40px;
  padding: 0 24px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.quick-questions .el-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.quick-questions .el-tag:hover {
  background-color: #67c23a;
  color: #fff;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  padding: 40px;
}

.empty-state .el-icon {
  font-size: 64px;
  color: #dcdfe6;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: #606266;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
}

.message-bubble pre {
  background-color: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
}

.message-bubble code {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-item.user .message-bubble code {
  background-color: rgba(255, 255, 255, 0.2);
}

.message-bubble ul, .message-bubble ol {
  padding-left: 20px;
  margin: 8px 0;
}

.message-bubble li {
  margin: 4px 0;
}

.message-bubble p {
  margin: 0 0 8px;
}

.message-bubble h1,
.message-bubble h2,
.message-bubble h3 {
  margin: 8px 0;
  color: #1f2d3d;
}

.message-bubble h1 { font-size: 18px; }
.message-bubble h2 { font-size: 16px; }
.message-bubble h3 { font-size: 15px; }

.message-bubble blockquote {
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 3px solid #67c23a;
  background-color: #f7fbf4;
  color: #606266;
}

.message-bubble a {
  color: #409eff;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .chat-container {
    padding: 76px 12px 12px;
  }

  .welcome-card {
    padding: 16px;
  }

  .welcome-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .welcome-card h2 {
    font-size: 18px;
    margin-bottom: 0;
  }

  .mode-switch {
    width: 100%;
  }

  .chat-area {
    min-height: 400px;
  }

  .message-item {
    max-width: 90%;
  }

  .quick-questions {
    display: none;
  }
}
</style>
