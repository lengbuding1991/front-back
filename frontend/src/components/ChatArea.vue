<template>
  <main class="flex-1 flex flex-col bg-gray-50 dark:bg-dark-bg">
    <!-- 顶部工具栏 -->
    <div class="bg-white dark:bg-dark-card border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <button
          @click="$emit('toggle-sidebar')"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg"
        >
          <i class="fas fa-bars text-gray-500 dark:text-gray-400"></i>
        </button>
        
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
            <i class="fas fa-brain text-white text-lg"></i>
          </div>
          <h1 class="text-xl font-bold text-primary">DeepSeek</h1>
        </div>
      </div>
      
      <div class="flex items-center space-x-3">
        <button
          @click="$emit('toggle-theme')"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg"
          :title="isDarkMode ? '切换到浅色模式' : '切换到深色模式'"
        >
          <i :class="isDarkMode ? 'fas fa-sun' : 'fas fa-moon'" class="text-gray-500 dark:text-gray-400"></i>
        </button>
        
        <button
          @click="$emit('show-settings')"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg"
          title="设置"
        >
          <i class="fas fa-cog text-gray-500 dark:text-gray-400"></i>
        </button>
        
        <button
          @click="$emit('show-help')"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg"
          title="帮助与反馈"
        >
          <i class="fas fa-question-circle text-gray-500 dark:text-gray-400"></i>
        </button>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <!-- 欢迎消息 -->
      <div v-if="!currentChatId" class="flex-1 flex items-center justify-center p-8">
        <div class="text-center max-w-2xl">
          <div class="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <i class="fas fa-brain text-primary text-3xl"></i>
          </div>
          <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-4">欢迎使用 DeepSeek</h2>
          <p class="text-lg text-gray-600 dark:text-gray-300 mb-8">
            我是您的AI助手，可以帮您解答问题、创作内容、分析文档等
          </p>
          
          <!-- 未登录提示 -->
          <div v-if="!isLoggedIn" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 mb-8">
            <div class="flex items-center justify-center mb-3">
              <i class="fas fa-exclamation-triangle text-yellow-500 text-xl mr-2"></i>
              <h3 class="text-lg font-semibold text-yellow-800 dark:text-yellow-200">请先登录</h3>
            </div>
            <p class="text-yellow-700 dark:text-yellow-300">登录后即可开始与AI助手对话，创建新对话并查看历史记录</p>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div 
              v-for="suggestion in suggestions" 
              :key="suggestion.id"
              @click="$emit('quick-start', suggestion.prompt)"
              class="bg-white dark:bg-dark-card rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer border border-gray-200 dark:border-gray-700"
              :class="{ 'opacity-50 cursor-not-allowed': !isLoggedIn }"
            >
              <div class="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mb-3">
                <i :class="suggestion.icon" class="text-primary"></i>
              </div>
              <h3 class="font-semibold text-gray-800 dark:text-white mb-2">{{ suggestion.title }}</h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">{{ suggestion.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 聊天消息区域 -->
      <div v-else class="flex-1 overflow-y-auto scrollbar-hide">
        <div class="max-w-4xl mx-auto px-4 py-6">
          <!-- 消息列表 -->
          <div v-for="message in messages" :key="message.id" class="mb-6">
            <!-- 用户消息 -->
            <div v-if="message.role === 'user'" class="flex justify-end mb-4">
              <div class="flex items-start space-x-3 max-w-3xl">
                <div class="flex-1">
                  <div class="bg-primary text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm">
                    <p class="text-sm whitespace-pre-wrap">{{ message.content }}</p>
                  </div>
                  <div class="flex items-center justify-end space-x-2 mt-1">
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatTime(message.timestamp) }}</span>
                    <button
                      @click="$emit('copy-message', message.content)"
                      class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      title="复制消息"
                    >
                      <i class="fas fa-copy text-xs"></i>
                    </button>
                  </div>
                </div>
                <img
                  :src="userInfo?.avatar || 'https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png'"
                  alt="用户头像"
                  class="w-8 h-8 rounded-full object-cover"
                />
              </div>
            </div>

            <!-- AI消息 -->
            <div v-else class="flex justify-start mb-4">
              <div class="flex items-start space-x-3 max-w-3xl">
                <div class="w-8 h-8 rounded-md bg-primary flex items-center justify-center flex-shrink-0">
                  <i class="fas fa-brain text-white text-sm"></i>
                </div>
                <div class="flex-1">
                  <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-gray-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                    <p class="text-sm text-gray-800 dark:text-white whitespace-pre-wrap">{{ message.content }}</p>
                  </div>
                  <div class="flex items-center space-x-2 mt-1">
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatTime(message.timestamp) }}</span>
                    <button
                      @click="$emit('copy-message', message.content)"
                      class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      title="复制消息"
                    >
                      <i class="fas fa-copy text-xs"></i>
                    </button>
                    <button
                      @click="$emit('regenerate-message', message.id)"
                      class="text-gray-400 hover:text-primary transition-colors"
                      title="重新生成"
                    >
                      <i class="fas fa-redo text-xs"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="flex justify-start mb-4">
            <div class="flex items-start space-x-3 max-w-3xl">
              <div class="w-8 h-8 rounded-md bg-primary flex items-center justify-center flex-shrink-0">
                <i class="fas fa-brain text-white text-sm"></i>
              </div>
              <div class="bg-white dark:bg-dark-card border border-gray-200 dark:border-gray-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
                <div class="flex items-center space-x-2">
                  <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                  <span class="text-sm text-gray-600 dark:text-gray-300">AI正在思考中...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-dark-card p-4">
        <div class="max-w-4xl mx-auto">
          <!-- 未登录状态提示 -->
          <div v-if="!isLoggedIn" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
            <div class="flex items-center">
              <i class="fas fa-exclamation-circle text-yellow-500 text-lg mr-3"></i>
              <div>
                <p class="text-yellow-700 dark:text-yellow-300 font-medium">请先登录以开始对话</p>
                <p class="text-yellow-600 dark:text-yellow-400 text-sm mt-1">登录后即可与AI助手进行对话</p>
              </div>
            </div>
          </div>
          
          <div class="flex items-end space-x-3">
            <div class="flex-1 relative">
              <textarea
                ref="messageInput"
                :value="localInputMessage"
                @input="updateLocalInputMessage"
                @keydown="handleKeydown"
                :placeholder="isLoggedIn ? '输入您的问题...' : '请先登录以开始对话'"
                :disabled="!isLoggedIn"
                :class="[
                  'w-full resize-none border rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:border-transparent',
                  isLoggedIn 
                    ? 'border-gray-300 dark:border-gray-600 focus:ring-primary bg-white dark:bg-dark-card text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400'
                    : 'border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                ]"
                :style="{ height: textareaHeight + 'px', minHeight: '52px', maxHeight: '200px' }"
              ></textarea>
              
              <!-- 输入框操作按钮 -->
              <div class="absolute right-3 bottom-3 flex items-center space-x-2">
                <button
                  @click="clearInput"
                  v-if="localInputMessage && isLoggedIn"
                  class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  title="清空输入"
                >
                  <i class="fas fa-times"></i>
                </button>
                <button
                  @click="$emit('upload-file')"
                  :disabled="!isLoggedIn"
                  :class="[
                    'transition-colors',
                    isLoggedIn 
                      ? 'text-gray-400 hover:text-primary'
                      : 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                  ]"
                  title="上传文件"
                >
                  <i class="fas fa-paperclip"></i>
                </button>
              </div>
            </div>
            
            <button
              @click="sendMessage"
              :disabled="!localInputMessage.trim() || isLoading || !isLoggedIn"
              :class="[
                'w-12 h-12 rounded-lg flex items-center justify-center transition-all',
                localInputMessage.trim() && !isLoading && isLoggedIn
                  ? 'bg-primary hover:bg-primary/90 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              ]"
              :title="isLoggedIn ? '发送消息' : '请先登录'"
            >
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
          
          <div v-if="isLoggedIn" class="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <span>按 Enter 发送，Shift + Enter 换行</span>
            </div>
            <div class="flex items-center space-x-2">
              <span>{{ localInputMessage.length }}/4000</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
export default {
  name: 'ChatArea',
  props: {
    currentChatId: {
      type: String,
      default: null
    },
    messages: {
      type: Array,
      default: () => []
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    inputMessage: {
      type: String,
      default: ''
    },
    userInfo: {
      type: Object,
      default: () => ({
        username: '',
        email: '',
        avatar: ''
      })
    },
    isDarkMode: {
      type: Boolean,
      default: false
    },
    isLoggedIn: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      textareaHeight: 52,
      localInputMessage: this.inputMessage,
      suggestions: [
        {
          id: 1,
          title: '代码助手',
          description: '帮我编写和优化代码',
          icon: 'fas fa-code',
          prompt: '请帮我编写一个Python函数，实现...'
        },
        {
          id: 2,
          title: '内容创作',
          description: '帮我写文章、邮件等',
          icon: 'fas fa-edit',
          prompt: '请帮我写一封工作邮件，内容是...'
        },
        {
          id: 3,
          title: '学习助手',
          description: '解答问题和解释概念',
          icon: 'fas fa-graduation-cap',
          prompt: '请解释一下什么是机器学习...'
        }
      ]
    }
  },
  methods: {
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    handleKeydown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault()
        if (this.localInputMessage.trim()) {
          this.sendMessage()
        }
      }
    },
    autoResize() {
      this.$nextTick(() => {
        const textarea = this.$refs.messageInput
        if (textarea) {
          textarea.style.height = 'auto'
          const newHeight = Math.min(textarea.scrollHeight, 200)
          this.textareaHeight = Math.max(newHeight, 52)
        }
      })
    },
    sendMessage() {
      if (!this.isLoggedIn) {
        this.$emit('show-login')
        return
      }
      
      if (this.localInputMessage.trim()) {
        this.$emit('send-message', this.localInputMessage)
        this.localInputMessage = ''
      }
    },
    clearInput() {
      this.localInputMessage = ''
      this.$emit('clear-input')
    },
    updateLocalInputMessage(event) {
      this.localInputMessage = event.target.value
      this.autoResize()
      this.$emit('update:input-message', event.target.value)
    }
  },
  watch: {
    inputMessage(newVal) {
      this.localInputMessage = newVal
    }
  },
  emits: [
    'toggle-sidebar',
    'toggle-theme',
    'show-settings',
    'show-help',
    'quick-start',
    'send-message',
    'copy-message',
    'regenerate-message',
    'clear-input',
    'upload-file',
    'update:input-message'
  ]
}
</script>