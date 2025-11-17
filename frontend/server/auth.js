// 用户认证相关测试数据
const testUsers = [
  {
    id: 1,
    username: "冷丶布丁",
    email: "498128186@qq.com",
    password: "shuishui",
    avatar: "https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png",
    plan: "个人版",
    createdAt: "2023-11-01"
  }
];

// 模拟登录验证函数
function loginUser(identifier, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 查找用户（通过邮箱或用户名）
      const user = testUsers.find(u => 
        u.email === identifier || u.username === identifier
      );
      
      if (!user) {
        reject({ success: false, message: '用户不存在' });
        return;
      }
      
      if (user.password !== password) {
        reject({ success: false, message: '密码错误' });
        return;
      }
      
      // 登录成功，返回用户信息（不包含密码）
      const { password: _, ...userInfo } = user;
      resolve({ success: true, user: userInfo });
    }, 500); // 模拟网络延迟
  });
}

// 模拟注册函数（暂不实现注册功能）
function registerUser(userData) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 检查邮箱是否已存在
      const emailExists = testUsers.some(u => u.email === userData.email);
      if (emailExists) {
        reject({ success: false, message: '邮箱已被注册' });
        return;
      }
      
      // 检查用户名是否已存在
      const usernameExists = testUsers.some(u => u.username === userData.username);
      if (usernameExists) {
        reject({ success: false, message: '用户名已被使用' });
        return;
      }
      
      // 创建新用户
      const newUser = {
        id: testUsers.length + 1,
        ...userData,
        plan: "个人版",
        createdAt: new Date().toISOString().split('T')[0]
      };
      
      testUsers.push(newUser);
      
      // 返回用户信息（不包含密码）
      const { password: _, ...userInfo } = newUser;
      resolve({ success: true, user: userInfo });
    }, 1000);
  });
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { loginUser, registerUser, testUsers };
} else {
  // 浏览器环境
  window.authAPI = { loginUser, registerUser, testUsers };
}