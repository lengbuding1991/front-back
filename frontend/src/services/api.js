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
    console.log('API sendMessage 发送请求:', messageData);
    return api.post('/chat/send', messageData)
      .then(response => {
        console.log('API sendMessage 收到响应:', response);
        return response;
      })
      .catch(error => {
        console.error('API sendMessage 错误:', error);
        if (error.response) {
          console.error('错误响应数据:', error.response.data);
          console.error('错误状态码:', error.response.status);
        }
        throw error;
      });
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
    // 从localStorage获取用户信息
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    return api.post('/chat/new', { user_id: userInfo.id });
  },
  
  // 获取用户的所有对话
  getUserChats: (userId) => {
    return api.get(`/auth/chats/${userId}`);
  },
  
  // 获取用户的分页对话列表
  getUserChatsPaginated: (userId, page = 1, pageSize = 10) => {
    return api.post('/auth/chats', { 
      user_id: userId, 
      page: page, 
      page_size: pageSize 
    });
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