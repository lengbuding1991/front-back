<template>
  <div 
    class="font-inter h-screen flex flex-col overflow-hidden"
    :class="{ 
      'dark': isDarkMode,
      'bg-light text-dark': !isDarkMode,
      'bg-dark-bg text-light': isDarkMode 
    }"
  >
    <!-- 提示组件 -->
    <Toast ref="toastRef" />
    
    <!-- 登录弹窗 -->
    <LoginModal
      :show-login-modal="showLoginModal"
      @close-modal="showLoginModal = false"
      @login-success="handleLoginSuccess"
      @show-success="toast.success"
      @show-error="toast.error"
    />
    
    <!-- 主布局 -->
    <div class="flex h-full overflow-hidden">
      <!-- 侧边栏组件 -->
      <Sidebar
        :is-sidebar-collapsed="isSidebarCollapsed"
        :is-logged-in="isLoggedIn"
        :user-info="userInfo"
        :show-user-dropdown="showUserDropdown"
        :is-dark-mode="isDarkMode"
        :recent-chats="recentChats"
        :selected-chat-id="selectedChatId"
        :pagination="pagination"
        @toggle-sidebar="toggleSidebar"
        @new-chat="newChat"
        @select-chat="selectChat"
        @delete-chat="deleteChat"
        @open-login-modal="showLoginModal = true"
        @toggle-user-dropdown="toggleUserDropdown"
        @show-settings="showSettings"
        @show-help="showHelp"
        @toggle-theme="toggleTheme"
        @logout="handleLogout"
        @refresh-chats="refreshUserChats"
        @load-more-chats="loadMoreChats"
      />
      
      <!-- 主聊天区域组件 -->
      <ChatArea
        :current-chat-id="selectedChatId"
        :messages="currentMessages"
        :is-loading="isLoading"
        :input-message="inputMessage"
        :user-info="userInfo"
        :is-dark-mode="isDarkMode"
        :is-logged-in="isLoggedIn"
        @toggle-sidebar="toggleSidebar"
        @toggle-theme="toggleTheme"
        @show-settings="showSettings"
        @show-help="showHelp"
        @quick-start="handleQuickStart"
        @send-message="sendMessage"
        @copy-message="copyMessage"
        @regenerate-message="regenerateMessage"
        @clear-input="inputMessage = ''"
        @upload-file="uploadFile"
        @update:input-message="(value) => inputMessage = value"
        @show-login="showLoginModal = true"
      />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import Toast from './components/Toast.vue'
import Sidebar from './components/Sidebar.vue'
import ChatArea from './components/ChatArea.vue'
import LoginModal from './components/LoginModal.vue'
import { useToast } from './composables/useToast'
import { authAPI, chatAPI } from './services/api'

export default {
  name: 'App',
  components: {
    Toast,
    Sidebar,
    ChatArea,
    LoginModal
  },
  setup() {
    const toastRef = ref(null)
    const toast = useToast()
    
    // 立即设置Toast引用
    const setToastRef = () => {
      if (toastRef.value) {
        toast.setRef(toastRef.value)
      }
    }
    
    return {
      toastRef,
      toast,
      setToastRef
    }
  },
  data() {
    return {
      // 主题相关
      isDarkMode: false,
      
      // 侧边栏相关
      isSidebarCollapsed: false,
      showUserDropdown: false,
      
      // 用户认证相关
      isLoggedIn: false,
      userInfo: {
        username: '',
        email: '',
        avatar: '',
        plan: '个人版'
      },
      showLoginModal: false,
      
      // 聊天相关
      selectedChatId: null,
      recentChats: [], // 从服务器获取真实的历史对话
      currentMessages: [],
      // 消息缓存：存储每个对话的消息
      messagesCache: {},
      isLoading: false,
      inputMessage: '',
      
      // 其他状态
      // 分页相关数据
      pagination: {
        currentPage: 1,
        pageSize: 10,
        totalChats: 0,
        hasMore: false,
        isLoading: false
      },
      
    }
  },
  mounted() {
    // 设置提示组件引用
    this.setToastRef()
    this.$nextTick(() => {
      this.setToastRef()
    })
    
    // 检查本地存储的主题设置
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      this.isDarkMode = true
    }
    
    // 检查登录状态
    const savedUser = localStorage.getItem('userInfo')
    if (savedUser) {
      this.isLoggedIn = true
      this.userInfo = JSON.parse(savedUser)
      
      // 从本地存储恢复临时对话和消息缓存
      this.restoreTempChats()
      
      // 用户已登录，从服务器获取历史对话
      this.loadUserChats()
    }
    
    // 添加键盘事件监听
    this.setupKeyboardShortcuts()
  },
  methods: {
    // 侧边栏相关方法
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    },
    
    expandSidebar() {
      this.isSidebarCollapsed = false
    },
    
    toggleUserDropdown() {
      this.showUserDropdown = !this.showUserDropdown
    },
    
    // 聊天相关方法
    async newChat() {
      // 检查登录状态
      if (!this.isLoggedIn) {
        this.showLoginModal = true
        this.toast.info('请先登录后再创建新对话')
        return null
      }
      
      // 在前端生成临时对话ID（使用UUID格式）
      const generateTempChatId = () => {
        return 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      }
      
      const newChatId = generateTempChatId()
      
      // 随机颜色配置
      const colorConfigs = [
        { color: 'bg-blue-100', iconColor: 'text-blue-500' },
        { color: 'bg-green-100', iconColor: 'text-green-500' },
        { color: 'bg-yellow-100', iconColor: 'text-yellow-500' },
        { color: 'bg-red-100', iconColor: 'text-red-500' },
        { color: 'bg-purple-100', iconColor: 'text-purple-500' },
        { color: 'bg-pink-100', iconColor: 'text-pink-500' },
        { color: 'bg-indigo-100', iconColor: 'text-indigo-500' },
        { color: 'bg-teal-100', iconColor: 'text-teal-500' }
      ]
      const randomConfig = colorConfigs[Math.floor(Math.random() * colorConfigs.length)]
      
      // 在前端创建临时对话
      const tempChat = {
        id: newChatId,
        title: '新对话',
        time: '刚刚',
        color: randomConfig.color,
        iconColor: randomConfig.iconColor,
        isTemp: true // 标记为临时对话
      }
      
      // 添加到对话列表开头
      this.recentChats.unshift(tempChat)
      
      // 选择新创建的对话
      this.selectedChatId = newChatId
      this.currentMessages = []
      // 初始化新对话的消息缓存
      this.messagesCache[newChatId] = []
      
      // 保存临时对话到本地存储
      this.saveTempChats()
      
      this.toast.info('已创建新对话')
      
      return newChatId
    },
    
    selectChat(chatId) {
      // 检查登录状态
      if (!this.isLoggedIn) {
        this.showLoginModal = true
        this.toast.info('请先登录后再查看对话历史')
        return
      }
      
      this.selectedChatId = chatId
      
      // 检查是否为临时对话
      const currentChat = this.recentChats.find(chat => chat.id === chatId)
      
      // 如果是临时对话，不需要从服务器加载消息
      if (currentChat && currentChat.isTemp) {
        // 从缓存中加载消息
        this.currentMessages = this.messagesCache[chatId] || []
      } else {
        // 检查消息缓存中是否有该对话的消息
        if (this.messagesCache[chatId]) {
          // 从缓存中加载消息
          this.currentMessages = this.messagesCache[chatId]
        } else {
          // 从API加载消息并缓存
          this.loadChatMessages(chatId)
        }
      }
    },
    
    deleteChat(chatId) {
      const index = this.recentChats.findIndex(chat => chat.id === chatId)
      if (index !== -1) {
        const chat = this.recentChats[index]
        
        // 如果是临时对话，直接删除
        if (chat.isTemp) {
          this.recentChats.splice(index, 1)
          
          // 清理消息缓存
          delete this.messagesCache[chatId]
          
          if (this.selectedChatId === chatId) {
            this.selectedChatId = this.recentChats.length > 0 ? this.recentChats[0].id : null
            this.currentMessages = []
          }
          
          // 保存更新后的对话状态到本地存储
          this.saveTempChats()
          
          this.toast.success('对话已删除')
        } else {
          // TODO: 如果是已保存的对话，需要调用后端API删除
          this.toast.info('删除已保存对话功能开发中')
        }
      }
    },
    
    async loadChatMessages(chatId) {
      try {
        // 使用API服务获取聊天历史
        const response = await chatAPI.getChatMessages(chatId)
        
        if (response.success) {
          this.currentMessages = response.messages || []
          // 将消息存入缓存
          this.messagesCache[chatId] = this.currentMessages
        } else {
          this.currentMessages = []
          this.messagesCache[chatId] = []
        }
      } catch (error) {
        console.error('获取聊天历史失败:', error)
        this.currentMessages = []
        this.messagesCache[chatId] = []
      }
    },
    
    // 加载用户的所有对话（分页版本）
    async loadUserChats(loadMore = false) {
      if (!this.isLoggedIn || !this.userInfo?.id) {
        return
      }
      
      // 如果是加载更多，检查是否还有更多数据
      if (loadMore && !this.pagination.hasMore) {
        return
      }
      
      // 设置加载状态
      this.pagination.isLoading = true
      
      // 确定要加载的页码
      const targetPage = loadMore ? this.pagination.currentPage + 1 : 1
      
      // 检查是否有缓存（仅第一页使用缓存）
      if (!loadMore) {
        const cacheKey = `userChats_${this.userInfo.id}_page_${targetPage}`
        const cachedChats = localStorage.getItem(cacheKey)
        const cacheTime = localStorage.getItem(`${cacheKey}_time`)
        
        // 如果缓存存在且未过期（5分钟），使用缓存
        if (cachedChats && cacheTime && (Date.now() - parseInt(cacheTime)) < 5 * 60 * 1000) {
          try {
            const serverChats = JSON.parse(cachedChats)
            this.mergeChatsWithServerData(serverChats, targetPage, false)
            this.pagination.isLoading = false
            return
          } catch (error) {
            console.warn('缓存解析失败，重新加载对话', error)
          }
        }
      }
      
      try {
        const response = await chatAPI.getUserChatsPaginated(
          this.userInfo.id, 
          targetPage, 
          this.pagination.pageSize
        )
        
        if (response.success && response.chats) {
          // 缓存服务器返回的对话数据（仅第一页缓存）
          if (!loadMore) {
            const cacheKey = `userChats_${this.userInfo.id}_page_${targetPage}`
            localStorage.setItem(cacheKey, JSON.stringify(response.chats))
            localStorage.setItem(`${cacheKey}_time`, Date.now().toString())
          }
          
          this.mergeChatsWithServerData(response.chats, targetPage, loadMore, response.total_count)
        } else {
          // 如果服务器没有返回对话，保留前端的临时对话
          if (!loadMore) {
            this.recentChats = this.recentChats.filter(chat => chat.isTemp)
            this.saveTempChats()
          }
          this.toast.error('获取对话列表失败')
        }
      } catch (error) {
        console.error('获取用户对话失败:', error)
        // 出错时保留前端的临时对话
        if (!loadMore) {
          this.recentChats = this.recentChats.filter(chat => chat.isTemp)
          this.saveTempChats()
        }
        this.toast.error('获取对话列表失败')
      } finally {
        this.pagination.isLoading = false
      }
    },
    
    // 合并服务器对话和临时对话（分页版本）
    mergeChatsWithServerData(serverChats, page, loadMore = false, totalCount = 0) {
      // 生成随机颜色配置
      const colorConfigs = [
        { color: 'bg-blue-100', iconColor: 'text-blue-500' },
        { color: 'bg-green-100', iconColor: 'text-green-500' },
        { color: 'bg-yellow-100', iconColor: 'text-yellow-500' },
        { color: 'bg-red-100', iconColor: 'text-red-500' },
        { color: 'bg-purple-100', iconColor: 'text-purple-500' },
        { color: 'bg-pink-100', iconColor: 'text-pink-500' },
        { color: 'bg-indigo-100', iconColor: 'text-indigo-500' },
        { color: 'bg-teal-100', iconColor: 'text-teal-500' }
      ]
      
      // 格式化服务器返回的对话数据，前端随机生成颜色
      const formattedServerChats = serverChats.map((chat, index) => {
        const randomConfig = colorConfigs[Math.floor(Math.random() * colorConfigs.length)]
        return {
          id: chat.id,
          title: chat.title,
          time: this.formatTime(chat.created_at),
          color: randomConfig.color,
          iconColor: randomConfig.iconColor,
          isTemp: false // 标记为服务器对话
        }
      })
      
      // 更新分页信息
      this.pagination.currentPage = page
      this.pagination.totalChats = totalCount
      this.pagination.hasMore = totalCount > page * this.pagination.pageSize
      
      if (loadMore) {
        // 加载更多：将新对话添加到现有对话列表末尾
        this.recentChats = [...this.recentChats, ...formattedServerChats]
      } else {
        // 刷新或首次加载：保留临时对话，服务器对话替换现有服务器对话
        const tempChats = this.recentChats.filter(chat => chat.isTemp)
        this.recentChats = [...tempChats, ...formattedServerChats]
      }
      
      // 保存临时对话到本地存储
      this.saveTempChats()
      
      // 如果有对话，选择第一个对话并加载消息（仅首次加载时）
      if (!loadMore && this.recentChats.length > 0 && !this.selectedChatId) {
        this.selectedChatId = this.recentChats[0].id
        this.loadChatMessages(this.selectedChatId)
      } else if (this.selectedChatId) {
        // 如果已经有选中的对话，重新加载消息
        this.loadChatMessages(this.selectedChatId)
      }
    },
    
    // 刷新对话列表（手动刷新，不使用缓存）
    async refreshUserChats() {
      if (!this.isLoggedIn || !this.userInfo?.id) {
        return
      }
      
      try {
        const response = await chatAPI.getUserChatsPaginated(
          this.userInfo.id, 
          1, 
          this.pagination.pageSize
        )
        
        if (response.success && response.chats) {
          // 更新缓存（仅第一页）
          const cacheKey = `userChats_${this.userInfo.id}_page_1`
          localStorage.setItem(cacheKey, JSON.stringify(response.chats))
          localStorage.setItem(`${cacheKey}_time`, Date.now().toString())
          
          this.mergeChatsWithServerData(response.chats, 1, false, response.total_count)
          this.toast.success('对话列表已刷新')
        } else {
          this.toast.error('刷新对话列表失败')
        }
      } catch (error) {
        console.error('刷新对话列表失败:', error)
        this.toast.error('刷新对话列表失败')
      }
    },
    
    // 加载更多对话
    async loadMoreChats() {
      if (this.pagination.isLoading || !this.pagination.hasMore) {
        return
      }
      
      await this.loadUserChats(true)
    },
    
    // 保存临时对话到本地存储
    saveTempChats() {
      if (!this.isLoggedIn || !this.userInfo?.id) {
        return
      }
      
      const tempChats = this.recentChats.filter(chat => chat.isTemp)
      const cacheKey = `tempChats_${this.userInfo.id}`
      localStorage.setItem(cacheKey, JSON.stringify(tempChats))
    },
    
    // 从本地存储恢复临时对话
    restoreTempChats() {
      if (!this.isLoggedIn || !this.userInfo?.id) {
        return
      }
      
      const cacheKey = `tempChats_${this.userInfo.id}`
      const cachedTempChats = localStorage.getItem(cacheKey)
      
      if (cachedTempChats) {
        try {
          const tempChats = JSON.parse(cachedTempChats)
          // 将临时对话添加到对话列表开头
          this.recentChats = [...tempChats, ...this.recentChats.filter(chat => !chat.isTemp)]
        } catch (error) {
          console.warn('恢复临时对话失败:', error)
        }
      }
    },
    
    // 格式化时间显示
    formatTime(timestamp) {
      if (!timestamp) return ''
      
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / (1000 * 60))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      
      if (diffMins < 1) {
        return '刚刚'
      } else if (diffMins < 60) {
        return `${diffMins}分钟前`
      } else if (diffHours < 24) {
        return `${diffHours}小时前`
      } else if (diffDays < 7) {
        return `${diffDays}天前`
      } else {
        return date.toLocaleDateString()
      }
    },
    
    handleQuickStart(prompt) {
      this.inputMessage = prompt
      this.$nextTick(() => {
        this.sendMessage(prompt)
      })
    },
    
    copyMessage(content) {
      navigator.clipboard.writeText(content).then(() => {
        this.toast.success('消息已复制到剪贴板')
      }).catch(() => {
        this.toast.error('复制失败')
      })
    },
    
    regenerateMessage(messageId) {
      this.toast.info('重新生成功能开发中')
    },
    
    // 用户认证相关
    async handleLoginSuccess(userData) {
      this.isLoggedIn = true
      this.userInfo = { ...userData, plan: '个人版' }
      localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
      this.toast.success('登录成功')
      
      // 登录成功后自动加载对话列表
      await this.loadUserChats()
    },
    
    handleLogout() {
      // 清空所有对话相关数据
      this.recentChats = []
      this.currentMessages = []
      this.messagesCache = {}
      this.selectedChatId = null
      
      // 清空用户信息和登录状态
      this.isLoggedIn = false
      this.userInfo = { username: '', email: '', avatar: '', plan: '个人版' }
      this.showUserDropdown = false
      
      // 清理本地存储
      localStorage.removeItem('userInfo')
      // 清理所有用户的临时对话数据
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('tempChats_')) {
          localStorage.removeItem(key)
        }
      })
      
      this.toast.info('已退出登录')
    },
    
    // 主题相关
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode
      localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light')
    },
    
    // 其他功能
    showSettings() {
      this.toast.info('设置功能开发中')
    },
    
    showHelp() {
      this.toast.info('帮助与反馈功能开发中')
    },
    
    uploadFile() {
      this.toast.info('文件上传功能开发中')
    },
    
    // 键盘快捷键
    setupKeyboardShortcuts() {
      const handleKeydown = (event) => {
        // Ctrl/Cmd + K: 新建对话
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
          event.preventDefault()
          this.newChat()
        }
        
        // Ctrl/Cmd + ,: 打开设置
        if ((event.ctrlKey || event.metaKey) && event.key === ',') {
          event.preventDefault()
          this.showSettings()
        }
        
        // Ctrl/Cmd + L: 切换主题
        if ((event.ctrlKey || event.metaKey) && event.key === 'l') {
          event.preventDefault()
          this.toggleTheme()
        }
      }
      
      document.addEventListener('keydown', handleKeydown)
      
      // 在组件销毁时移除事件监听器
      this.$options.beforeUnmount = () => {
        document.removeEventListener('keydown', handleKeydown)
      }
    }
  }
}
</script>

<style scoped>
/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar-collapsed {
    width: 0 !important;
    min-width: 0 !important;
  }
  
  .sidebar-expanded {
    width: 100% !important;
    position: absolute;
    z-index: 30;
  }
}
</style>