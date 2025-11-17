import { ref } from 'vue'

// 创建全局提示管理器
export function useToast() {
  const toastRef = ref(null)

  const showToast = (options) => {
    if (toastRef.value) {
      toastRef.value.show(options)
    }
  }

  const hideToast = () => {
    if (toastRef.value) {
      toastRef.value.hide()
    }
  }

  // 快捷方法
  const success = (message, title = '成功') => {
    showToast({ title, message, type: 'success' })
  }

  const error = (message, title = '错误') => {
    showToast({ title, message, type: 'error' })
  }

  const warning = (message, title = '提示') => {
    showToast({ title, message, type: 'warning' })
  }

  const info = (message, title = '信息') => {
    showToast({ title, message, type: 'info' })
  }

  const setRef = (ref) => {
    toastRef.value = ref
  }

  return {
    show: showToast,
    hide: hideToast,
    success,
    error,
    warning,
    info,
    setRef
  }
}