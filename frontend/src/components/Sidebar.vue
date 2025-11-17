<template>
  <aside
    :class="[
      'bg-white dark:bg-dark-card border-r border-gray-200 dark:border-gray-700 flex flex-col transition-all duration-300 ease-in-out z-20',
      isSidebarCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- 侧边栏顶部logo -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <div class="flex items-center space-x-2" v-if="!isSidebarCollapsed">
        <div class="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
          <i class="fas fa-brain text-white text-lg"></i>
        </div>
        <h1 class="text-xl font-bold text-primary">DeepSeek</h1>
      </div>
      <button
        @click="$emit('toggle-sidebar')"
        class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg"
      >
        <i 
          :class="[
            'fas text-gray-500 dark:text-gray-400',
            isSidebarCollapsed ? 'fa-bars' : 'fa-chevron-left'
          ]"
        ></i>
      </button>
    </div>

    <!-- 侧边栏对话列表 -->
    <div class="flex-1 overflow-y-auto scrollbar-hide p-2">
      <div class="mb-4">
        <button
          @click="$emit('new-chat')"
          class="w-full flex items-center justify-center space-x-2 bg-primary/10 hover:bg-primary/20 text-primary py-2.5 px-4 rounded-lg transition-bg font-medium"
        >
          <i class="fas fa-plus"></i>
          <span v-if="!isSidebarCollapsed">新对话</span>
        </button>
      </div>
      
      <div class="space-y-1" v-if="!isSidebarCollapsed">
        <div class="flex items-center justify-between mb-2 px-3">
          <div class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            最近对话
          </div>
          <button
            @click="$emit('refresh-chats')"
            class="text-xs text-gray-500 hover:text-primary dark:text-gray-400 dark:hover:text-primary transition-colors"
            title="刷新对话列表"
          >
            <i class="fas fa-sync-alt"></i>
          </button>
        </div>
        
        <!-- 对话项 -->
        <div
          v-for="chat in recentChats"
          :key="chat.id"
          @click="$emit('select-chat', chat.id)"
          :class="[
            'chat-item flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg cursor-pointer',
            { 'bg-gray-100 dark:bg-dark-hover': selectedChatId === chat.id }
          ]"
        >
          <div :class="`w-8 h-8 rounded-md ${chat.color} flex items-center justify-center flex-shrink-0`">
            <i :class="`fas fa-comment ${chat.iconColor}`"></i>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{{ chat.title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ chat.time }}</p>
          </div>
          <button
            @click.stop="$emit('delete-chat', chat.id)"
            class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 p-1 opacity-0 hover:opacity-100 transition-opacity"
            title="删除对话"
          >
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
        
        <!-- 加载更多按钮 -->
        <div v-if="pagination.hasMore && !isSidebarCollapsed" class="mt-2">
          <button
            @click="$emit('load-more-chats')"
            :disabled="pagination.isLoading"
            :class="[
              'w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg transition-bg font-medium',
              pagination.isLoading 
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-dark-hover dark:hover:bg-dark-card dark:text-gray-300'
            ]"
          >
            <i v-if="pagination.isLoading" class="fas fa-spinner fa-spin"></i>
            <span v-else>加载更多</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 侧边栏底部用户信息 -->
    <div class="p-3 border-t border-gray-200 dark:border-gray-700">
      <div class="relative">
        <!-- 未登录状态：显示登录按钮 -->
        <div v-if="!isLoggedIn" class="flex items-center justify-center">
          <button
            @click="$emit('open-login-modal')"
            class="w-full flex items-center justify-center space-x-2 bg-primary hover:bg-primary/90 text-white py-2.5 px-4 rounded-lg transition-bg font-medium"
          >
            <i class="fas fa-sign-in-alt"></i>
            <span v-if="!isSidebarCollapsed">登录</span>
          </button>
        </div>
        
        <!-- 已登录状态：显示用户信息 -->
        <div v-else>
          <!-- 用户信息区域 -->
          <div 
            @click="$emit('toggle-user-dropdown')"
            class="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg cursor-pointer"
          >
            <img
              :src="userInfo?.avatar || 'https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png'"
              alt="用户头像"
              class="w-8 h-8 rounded-full object-cover"
            />
            <div class="flex-1 min-w-0" v-if="!isSidebarCollapsed">
              <p class="text-sm font-medium truncate text-gray-800 dark:text-white">{{ userInfo?.username || '用户' }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ userInfo?.plan || '个人版' }}</p>
            </div>
            <i class="fas fa-chevron-down text-xs text-gray-500 dark:text-gray-400"></i>
          </div>
          
          <!-- 用户下拉菜单 -->
          <div 
            v-if="showUserDropdown"
            class="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-dark-card rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10"
          >
            <button
              @click="$emit('show-settings')"
              class="w-full flex items-center space-x-3 p-2 hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg text-left"
            >
              <i class="fas fa-cog text-gray-500 dark:text-gray-400 w-5 text-center"></i>
              <span class="text-sm">设置</span>
            </button>
            <button
              @click="$emit('show-help')"
              class="w-full flex items-center space-x-3 p-2 hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg text-left"
            >
              <i class="fas fa-question-circle text-gray-500 dark:text-gray-400 w-5 text-center"></i>
              <span class="text-sm">帮助与反馈</span>
            </button>
            <div class="border-t border-gray-200 dark:border-gray-700 my-1"></div>
            <button
              @click="$emit('toggle-theme')"
              class="w-full flex items-center space-x-3 p-2 hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg text-left"
            >
              <i :class="isDarkMode ? 'fas fa-sun' : 'fas fa-moon'" class="text-gray-500 dark:text-gray-400 w-5 text-center"></i>
              <span class="text-sm">{{ isDarkMode ? '浅色模式' : '深色模式' }}</span>
            </button>
            <div class="border-t border-gray-200 dark:border-gray-700 my-1"></div>
            <button
              @click="$emit('logout')"
              class="w-full flex items-center space-x-3 p-2 hover:bg-gray-100 dark:hover:bg-dark-hover transition-bg text-left"
            >
              <i class="fas fa-sign-out-alt text-gray-500 dark:text-gray-400 w-5 text-center"></i>
              <span class="text-sm">退出登录</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    isSidebarCollapsed: {
      type: Boolean,
      default: false
    },
    isLoggedIn: {
      type: Boolean,
      default: false
    },
    userInfo: {
      type: Object,
      default: () => ({
        username: '',
        email: '',
        avatar: ''
      })
    },
    showUserDropdown: {
      type: Boolean,
      default: false
    },
    isDarkMode: {
      type: Boolean,
      default: false
    },
    recentChats: {
      type: Array,
      default: () => []
    },
    selectedChatId: {
      type: Number,
      default: 1
    },
    // 分页相关props
    pagination: {
      type: Object,
      default: () => ({
        currentPage: 1,
        pageSize: 10,
        totalChats: 0,
        hasMore: false,
        isLoading: false
      })
    }
  },
  emits: [
    'toggle-sidebar',
    'new-chat',
    'select-chat',
    'delete-chat',
    'open-login-modal',
    'toggle-user-dropdown',
    'show-settings',
    'show-help',
    'toggle-theme',
    'logout',
    'refresh-chats',
    'load-more-chats'
  ]
}
</script>