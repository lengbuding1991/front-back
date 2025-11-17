<template>
  <transition name="modal">
    <div 
      v-if="showLoginModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="$emit('close-modal')"
    >
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <!-- 弹窗头部 -->
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ isLoginMode ? '登录' : '注册' }}
          </h3>
          <button
            @click="$emit('close-modal')"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- 弹窗内容 -->
        <div class="p-6">
          <!-- 登录/注册切换 -->
          <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 mb-6">
            <button
              @click="isLoginMode = true"
              :class="[
                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                isLoginMode 
                  ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              ]"
            >
              登录
            </button>
            <button
              @click="isLoginMode = false"
              :class="[
                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                !isLoginMode 
                  ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              ]"
            >
              注册
            </button>
          </div>

          <!-- 登录表单 -->
          <form v-if="isLoginMode" @submit.prevent="handleLogin" class="space-y-4">
            <div>
              <label for="loginIdentifier" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                用户名或邮箱
              </label>
              <input
                id="loginIdentifier"
                v-model="loginForm.identifier"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请输入用户名或邮箱地址"
              />
            </div>

            <div>
              <label for="loginPassword" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                密码
              </label>
              <input
                id="loginPassword"
                v-model="loginForm.password"
                type="password"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请输入密码"
              />
            </div>

            <div class="flex items-center justify-between">
              <label class="flex items-center">
                <input
                  v-model="loginForm.rememberMe"
                  type="checkbox"
                  class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">记住我</span>
              </label>
              <button type="button" class="text-sm text-primary hover:text-primary/80 transition-colors">
                忘记密码？
              </button>
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              :class="[
                'w-full py-3 px-4 rounded-lg font-medium transition-colors',
                isLoading 
                  ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed' 
                  : 'bg-primary hover:bg-primary/90 text-white'
              ]"
            >
              <span v-if="!isLoading">登录</span>
              <span v-else class="flex items-center justify-center">
                <i class="fas fa-spinner fa-spin mr-2"></i>
                登录中...
              </span>
            </button>
          </form>

          <!-- 注册表单 -->
          <form v-else @submit.prevent="handleRegister" class="space-y-4">
            <div>
              <label for="registerUsername" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                用户名
              </label>
              <input
                id="registerUsername"
                v-model="registerForm.username"
                type="text"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <label for="registerEmail" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                邮箱地址
              </label>
              <input
                id="registerEmail"
                v-model="registerForm.email"
                type="email"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请输入邮箱地址"
              />
            </div>

            <div>
              <label for="registerPassword" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                密码
              </label>
              <input
                id="registerPassword"
                v-model="registerForm.password"
                type="password"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请输入密码"
              />
            </div>

            <div>
              <label for="registerConfirmPassword" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                确认密码
              </label>
              <input
                id="registerConfirmPassword"
                v-model="registerForm.confirmPassword"
                type="password"
                required
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-dark-input text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="请再次输入密码"
              />
            </div>

            <div class="flex items-center">
              <input
                id="agreeTerms"
                v-model="registerForm.agreeTerms"
                type="checkbox"
                required
                class="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
              />
              <label for="agreeTerms" class="ml-2 text-sm text-gray-600 dark:text-gray-400">
                我已阅读并同意
                <a href="#" class="text-primary hover:text-primary/80 transition-colors">服务条款</a>
                和
                <a href="#" class="text-primary hover:text-primary/80 transition-colors">隐私政策</a>
              </label>
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              :class="[
                'w-full py-3 px-4 rounded-lg font-medium transition-colors',
                isLoading 
                  ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed' 
                  : 'bg-primary hover:bg-primary/90 text-white'
              ]"
            >
              <span v-if="!isLoading">注册</span>
              <span v-else class="flex items-center justify-center">
                <i class="fas fa-spinner fa-spin mr-2"></i>
                注册中...
              </span>
            </button>
          </form>


        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { authAPI } from '../services/api'

export default {
  name: 'LoginModal',
  props: {
    showLoginModal: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isLoginMode: true,
      isLoading: false,
      loginForm: {
        identifier: '',
        password: '',
        rememberMe: false
      },
      registerForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        agreeTerms: false
      }
    }
  },
  methods: {
    async handleLogin() {
      if (!this.loginForm.identifier || !this.loginForm.password) {
        this.$emit('show-error', '请输入用户名/邮箱和密码')
        return
      }

      this.isLoading = true
      try {
        // 使用API服务登录
        const response = await authAPI.login({
          identifier: this.loginForm.identifier,
          password: this.loginForm.password,
          remember_me: this.loginForm.rememberMe
        })
        
        if (response.success) {
          // 登录成功，传递正确的用户信息
          this.$emit('login-success', response.user)
          this.$emit('close-modal')
          this.resetForms()
        } else {
          this.$emit('show-error', response.message || '登录失败')
        }
      } catch (error) {
        console.error('登录请求失败:', error)
        this.$emit('show-error', '登录失败，请检查网络连接')
      } finally {
        this.isLoading = false
      }
    },
    
    async handleRegister() {
      if (!this.registerForm.username || !this.registerForm.email || !this.registerForm.password) {
        this.$emit('show-error', '请填写所有必填字段')
        return
      }

      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        this.$emit('show-error', '两次输入的密码不一致')
        return
      }

      if (!this.registerForm.agreeTerms) {
        this.$emit('show-error', '请同意服务条款和隐私政策')
        return
      }

      this.isLoading = true
      try {
        // 使用API服务注册
        const response = await authAPI.register({
          username: this.registerForm.username,
          email: this.registerForm.email,
          password: this.registerForm.password,
          confirm_password: this.registerForm.confirmPassword,
          agree_terms: this.registerForm.agreeTerms
        })
        
        if (response.success) {
          // 注册成功，切换到登录模式
          this.isLoginMode = true
          this.$emit('show-success', '注册成功，请登录')
          this.resetForms()
        } else {
          this.$emit('show-error', response.message || '注册失败')
        }
      } catch (error) {
        console.error('注册请求失败:', error)
        this.$emit('show-error', '注册失败，请检查网络连接')
      } finally {
        this.isLoading = false
      }
    },
    
    resetForms() {
      this.loginForm = {
        identifier: '',
        password: '',
        rememberMe: false
      }
      this.registerForm = {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        agreeTerms: false
      }
    }
  },
  watch: {
    showLoginModal(newVal) {
      if (!newVal) {
        this.resetForms()
        this.isLoading = false
      }
    }
  },
  emits: [
    'close-modal',
    'login-success',
    'show-success',
    'show-error'
  ]
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>