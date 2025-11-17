import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // 处理认证错误
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('userInfo');
      window.location.reload();
    }
    
    return Promise.reject(error.response?.data || error.message);
  }
);

// 认证相关API
export const authAPI = {
  // 用户登录
  login: (credentials) => {
    return api.post('/auth/login', credentials);
  },
  
  // 用户注册
  register: (userData) => {
    return api.post('/auth/register', userData);
  },
  
  // 获取用户信息
  getUserInfo: () => {
    return api.get('/auth/user');
  },
  
  // 用户登出
  logout: () => {
    return api.post('/auth/logout');
  }
};

// 聊天相关API
export const chatAPI = {
  // 发送消息
  sendMessage: (messageData) => {
    return api.post('/chat/send', messageData);
  },
  
  // 获取聊天历史
  getChatHistory: () => {
    return api.get('/chat/history');
  },
  
  // 获取特定对话的消息
  getChatMessages: (chatId) => {
    return api.get(`/chat/history/${chatId}`);
  },
  
  // 创建新对话
  createNewChat: () => {
    return api.post('/chat/new');
  },
  
  // 删除对话
  deleteChat: (chatId) => {
    return api.delete(`/chat/${chatId}`);
  }
};

// 文件上传相关API
export const fileAPI = {
  // 上传文件
  uploadFile: (formData) => {
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
};

export default api;