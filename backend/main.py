from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv
import bcrypt
import logging
import httpx
import json
from datetime import datetime
import dashscope
from dashscope import Application

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL和API密钥必须在.env文件中配置")

app = FastAPI(
    title="DeepSeek Chat API",
    description="DeepSeek聊天应用后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "https://deepseek.lbuding.com", "http://deepseek.lbuding.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型定义
class User(BaseModel):
    id: str
    username: str
    email: str
    avatar: Optional[str] = None
    plan: str = "个人版"
    created_at: str

class UserLogin(BaseModel):
    identifier: str  # 用户名或邮箱
    password: str
    remember_me: bool = False

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str
    agree_terms: bool

class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[User] = None

class Message(BaseModel):
    id: str
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: int

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    response: Optional[Message] = None
    chat_id: Optional[str] = None

class Chat(BaseModel):
    id: str
    user_id: str
    title: str
    color: str
    icon_color: str
    created_at: str
    updated_at: str

# 数据库服务类 - 使用HTTP请求直接连接Supabase
class DatabaseService:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    async def get_user_by_identifier(self, identifier: str):
        """通过用户名或邮箱获取用户"""
        async with httpx.AsyncClient() as client:
            try:
                # 先尝试通过用户名查找
                response = await client.get(
                    f"{self.base_url}/users",
                    headers=self.headers,
                    params={"username": f"eq.{identifier}"}
                )
                if response.status_code == 200 and response.json():
                    return response.json()[0]
                
                # 再尝试通过邮箱查找
                response = await client.get(
                    f"{self.base_url}/users",
                    headers=self.headers,
                    params={"email": f"eq.{identifier}"}
                )
                if response.status_code == 200 and response.json():
                    return response.json()[0]
                
                return None
            except Exception as e:
                logger.error(f"查询用户失败: {e}")
                return None
    
    async def create_user(self, username: str, email: str, password_hash: str):
        """创建新用户"""
        async with httpx.AsyncClient() as client:
            try:
                user_id = str(uuid.uuid4())
                user_data = {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'password_hash': password_hash,
                    'avatar_url': 'https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png',
                    'plan': '个人版'
                }
                
                response = await client.post(
                    f"{self.base_url}/users",
                    headers=self.headers,
                    json=user_data
                )
                
                if response.status_code == 201:
                    return response.json()[0]
                else:
                    logger.error(f"创建用户失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"创建用户失败: {e}")
                return None
    
    async def create_chat(self, user_id: str, title: str = "新对话"):
        """创建新对话"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"准备创建对话: user_id={user_id}, title={title}")
                
                chat_id = str(uuid.uuid4())
                chat_data = {
                    'id': chat_id,
                    'user_id': user_id,
                    'title': title,
                    'color': 'bg-blue-100',
                    'icon_color': 'text-blue-500'
                }
                
                logger.info(f"发送对话数据到Supabase: {chat_data}")
                
                response = await client.post(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    json=chat_data
                )
                
                logger.info(f"Supabase对话创建响应状态码: {response.status_code}")
                logger.info(f"Supabase对话创建响应内容: {response.text}")
                
                if response.status_code == 201:
                    result = response.json()[0]
                    logger.info(f"对话创建成功: {result}")
                    return result
                else:
                    logger.error(f"创建对话失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"创建对话失败: {e}", exc_info=True)
                return None
    
    async def get_user_chats(self, user_id: str):
        """获取用户的所有对话"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "order": "created_at.desc"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
            except Exception as e:
                logger.error(f"获取用户对话失败: {e}")
                return []

    async def get_user_chats_paginated(self, user_id: str, page: int = 1, page_size: int = 10):
        """获取用户的分页对话列表"""
        async with httpx.AsyncClient() as client:
            try:
                offset = (page - 1) * page_size
                response = await client.get(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "order": "created_at.desc",
                        "limit": page_size,
                        "offset": offset
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
            except Exception as e:
                logger.error(f"获取用户分页对话失败: {e}")
                return []

    async def get_user_chats_count(self, user_id: str):
        """获取用户对话总数"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    params={
                        "user_id": f"eq.{user_id}",
                        "select": "count"
                    }
                )
                
                if response.status_code == 200:
                    # Supabase返回的count格式
                    count_data = response.json()
                    if isinstance(count_data, list) and len(count_data) > 0:
                        return count_data[0].get('count', 0)
                    return 0
                return 0
            except Exception as e:
                logger.error(f"获取用户对话总数失败: {e}")
                return 0

    async def save_message(self, chat_id: str, role: str, content: str, timestamp: int):
        """创建消息"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"准备保存消息: chat_id={chat_id}, role={role}, content长度={len(content)}, timestamp={timestamp}")
                
                message_id = str(uuid.uuid4())
                message_data = {
                    'id': message_id,
                    'chat_id': chat_id,
                    'role': role,
                    'content': content,
                    'timestamp': timestamp
                }
                
                logger.info(f"发送消息数据到Supabase: {message_data}")
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=message_data
                )
                
                logger.info(f"Supabase响应状态码: {response.status_code}")
                logger.info(f"Supabase响应内容: {response.text}")
                
                if response.status_code == 201:
                    result = response.json()[0]
                    logger.info(f"消息保存成功: {result}")
                    return result
                else:
                    logger.error(f"创建消息失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"创建消息失败: {e}", exc_info=True)
                return None
    
    async def check_chat_exists(self, chat_id: str):
        """检查对话是否存在"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"检查对话是否存在: chat_id={chat_id}")
                
                response = await client.get(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    params={
                        "id": f"eq.{chat_id}",
                        "select": "id"
                    }
                )
                
                logger.info(f"检查对话存在性响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    exists = len(result) > 0
                    logger.info(f"对话存在性检查结果: {exists}")
                    return exists
                else:
                    logger.error(f"检查对话存在性失败，状态码: {response.status_code}, 响应: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"检查对话存在性失败: {e}", exc_info=True)
                return False
    
    async def create_chat_with_id(self, user_id: str, chat_id: str, title: str = "新对话"):
        """使用指定ID创建新对话"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"准备使用指定ID创建对话: user_id={user_id}, chat_id={chat_id}, title={title}")
                
                chat_data = {
                    'id': chat_id,
                    'user_id': user_id,
                    'title': title,
                    'color': 'bg-blue-100',
                    'icon_color': 'text-blue-500'
                }
                
                logger.info(f"发送对话数据到Supabase: {chat_data}")
                
                response = await client.post(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    json=chat_data
                )
                
                logger.info(f"Supabase对话创建响应状态码: {response.status_code}")
                logger.info(f"Supabase对话创建响应内容: {response.text}")
                
                if response.status_code == 201:
                    result = response.json()[0]
                    logger.info(f"使用指定ID创建对话成功: {result}")
                    return result
                else:
                    logger.error(f"使用指定ID创建对话失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"使用指定ID创建对话失败: {e}", exc_info=True)
                return None
    
    async def update_chat_title(self, chat_id: str, title: str):
        """更新对话标题"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"准备更新对话标题: chat_id={chat_id}, title={title}")
                
                update_data = {
                    'title': title
                }
                
                response = await client.patch(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    json=update_data,
                    params={"id": f"eq.{chat_id}"}
                )
                
                logger.info(f"Supabase对话标题更新响应状态码: {response.status_code}")
                logger.info(f"Supabase对话标题更新响应内容: {response.text}")
                
                if response.status_code == 200 or response.status_code == 204:
                    logger.info(f"更新对话标题成功: {chat_id}, title: {title}")
                    return True
                else:
                    logger.error(f"更新对话标题失败，状态码: {response.status_code}, 响应: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"更新对话标题失败: {e}", exc_info=True)
                return False
    
    async def get_chat_messages(self, chat_id: str):
        """获取对话的所有消息"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    params={
                        "chat_id": f"eq.{chat_id}",
                        "order": "timestamp.asc"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
            except Exception as e:
                logger.error(f"获取对话消息失败: {e}")
                return []
    
    async def delete_chat(self, chat_id: str):
        """删除对话及其所有消息"""
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"准备删除对话: {chat_id}")
                
                # 直接删除对话，由于有ON DELETE CASCADE约束，消息会自动删除
                chat_response = await client.delete(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    params={"id": f"eq.{chat_id}"}
                )
                
                logger.info(f"删除对话响应状态码: {chat_response.status_code}")
                logger.info(f"删除对话响应内容: {chat_response.text}")
                
                if chat_response.status_code in [200, 204]:
                    logger.info(f"成功删除对话: {chat_id}")
                    return True
                else:
                    logger.error(f"删除对话失败，状态码: {chat_response.status_code}, 响应: {chat_response.text}")
                    return False
            except Exception as e:
                logger.error(f"删除对话失败: {e}", exc_info=True)
                return False

# 全局数据库服务实例
db_service = DatabaseService()

# 阿里云百炼智能体服务类
class DashScopeService:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.app_id = os.getenv("DASHSCOPE_APP_ID")
        
        if not self.api_key:
            logger.error("DASHSCOPE_API_KEY环境变量未设置")
            raise ValueError("DASHSCOPE_API_KEY环境变量未设置")
        
        if not self.app_id:
            logger.error("DASHSCOPE_APP_ID环境变量未设置")
            raise ValueError("DASHSCOPE_APP_ID环境变量未设置")
        
        # 设置API密钥
        dashscope.api_key = self.api_key
        logger.info(f"DashScope服务初始化成功，APP_ID: {self.app_id}")
    
    async def call_agent(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        调用阿里云百炼智能体
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选，用于保持上下文）
            
        Returns:
            dict: 包含回复内容和状态信息
        """
        try:
            logger.info(f"调用阿里云百炼智能体，消息: {message[:50]}...")
            
            # 准备请求参数
            request_params = {
                'app_id': self.app_id,
                'prompt': message,
                'stream': False,  # 不使用流式响应
                'incremental_output': False
            }
            
            # 如果有会话ID，添加到请求中
            if session_id:
                request_params['session_id'] = session_id
            
            # 调用智能体
            response = Application.call(**request_params)
            
            if response.status_code == 200:
                result = response.output
                logger.info(f"智能体调用成功，回复: {result.get('text', '')[:100]}...")
                
                return {
                    'success': True,
                    'response': result.get('text', ''),
                    'session_id': result.get('session_id', session_id),
                    'usage': result.get('usage', {})
                }
            else:
                logger.error(f"智能体调用失败，状态码: {response.status_code}, 错误: {response.message}")
                return {
                    'success': False,
                    'error': f"智能体调用失败: {response.message}",
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"调用阿里云百炼智能体异常: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"调用智能体异常: {str(e)}"
            }
    
    def get_fallback_response(self, message: str) -> str:
        """
        获取备用回复（当智能体不可用时使用）
        
        Args:
            message: 用户消息
            
        Returns:
            str: 备用回复
        """
        logger.info("使用备用回复方案")
        
        # 简单的备用回复逻辑
        if "你好" in message or "hi" in message.lower():
            return "您好！我是AI助手，很高兴为您服务。虽然我现在连接智能体遇到了一些问题，但我仍然会尽力帮助您。"
        elif "帮助" in message or "help" in message.lower():
            return "我可以帮您解答问题、创作内容、分析文档等。目前智能体服务暂时不可用，请稍后再试。"
        else:
            return f"我已收到您的消息：'{message}'。目前智能体服务暂时不可用，请稍后再试。我会尽快恢复服务。"

# 全局智能体服务实例
try:
    agent_service = DashScopeService()
    logger.info("阿里云百炼智能体服务初始化成功")
except Exception as e:
    logger.error(f"阿里云百炼智能体服务初始化失败: {e}")
    agent_service = None

# API路由
@app.get("/")
async def root():
    return {"message": "DeepSeek Chat API 服务运行中", "version": "1.0.0"}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(user_data: UserLogin):
    """用户登录"""
    try:
        user = await db_service.get_user_by_identifier(user_data.identifier)
        
        if not user:
            return LoginResponse(success=False, message="用户不存在")
        
        # 验证密码
        if not db_service.check_password(user_data.password, user['password_hash']):
            return LoginResponse(success=False, message="密码错误")
        
        # 登录成功，返回用户信息（不包含密码）
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'avatar': user.get('avatar_url', 'https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png'),
            'plan': user.get('plan', '个人版'),
            'created_at': user.get('created_at', datetime.now().isoformat())
        }
        
        return LoginResponse(success=True, user=User(**user_info))
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return LoginResponse(success=False, message="登录失败，请稍后重试")

@app.post("/api/auth/register", response_model=LoginResponse)
async def register(user_data: UserRegister):
    """用户注册"""
    try:
        # 检查密码确认
        if user_data.password != user_data.confirm_password:
            return LoginResponse(success=False, message="密码确认不匹配")
        
        # 检查是否同意条款
        if not user_data.agree_terms:
            return LoginResponse(success=False, message="请同意服务条款")
        
        # 检查用户名是否已存在
        existing_user = await db_service.get_user_by_identifier(user_data.username)
        if existing_user:
            return LoginResponse(success=False, message="用户名已被使用")
        
        # 检查邮箱是否已存在
        existing_email = await db_service.get_user_by_identifier(user_data.email)
        if existing_email:
            return LoginResponse(success=False, message="邮箱已被注册")
        
        # 创建新用户
        hashed_password = db_service.hash_password(user_data.password)
        user = await db_service.create_user(user_data.username, user_data.email, hashed_password)
        
        if not user:
            return LoginResponse(success=False, message="用户创建失败")
        
        # 创建默认对话
        default_chat = await db_service.create_chat(user['id'], "欢迎使用DeepSeek")
        if default_chat:
            # 添加欢迎消息
            welcome_message_timestamp = int(datetime.now().timestamp() * 1000)
            await db_service.save_message(default_chat['id'], 'assistant', '欢迎使用DeepSeek！我是您的AI助手，可以帮您解答问题、创作内容、分析文档等。有什么我可以帮助您的吗？', welcome_message_timestamp)
        
        # 返回用户信息
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'avatar': 'https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png',
            'plan': '个人版',
            'created_at': datetime.now().isoformat()
        }
        
        return LoginResponse(success=True, user=User(**user_info))
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return LoginResponse(success=False, message="注册失败，请稍后重试")

@app.get("/api/auth/chats/{user_id}")
async def get_user_chats(user_id: str):
    """获取用户的所有对话"""
    try:
        chats = await db_service.get_user_chats(user_id)
        return {"success": True, "chats": chats}
    except Exception as e:
        logger.error(f"获取用户对话失败: {e}")
        return {"success": False, "message": "获取对话失败", "chats": []}

from pydantic import BaseModel

class CreateChatRequest(BaseModel):
    user_id: str = None

class GetUserChatsRequest(BaseModel):
    user_id: str
    page: int = 1
    page_size: int = 10

@app.post("/api/chat/new")
async def create_new_chat(request_data: CreateChatRequest = None):
    """创建新对话"""
    try:
        # 从前端传递的数据中获取用户ID
        user_id = None
        if request_data and request_data.user_id:
            user_id = request_data.user_id
        
        # 如果前端没有传递用户ID，使用测试用户ID
        if not user_id:
            user_id = "a2431f9f-f48e-4225-b59e-c1a16cb590f2"  # 测试用户ID
        
        chat = await db_service.create_chat(user_id, "新对话")
        
        if chat:
            return {
                "success": True, 
                "chat": {
                    "id": chat['id'],
                    "title": chat['title'],
                    "color": chat['color'],
                    "icon_color": chat['icon_color'],
                    "created_at": chat['created_at']
                }
            }
        else:
            return {"success": False, "message": "创建对话失败"}
    except Exception as e:
        logger.error(f"创建新对话失败: {e}")
        return {"success": False, "message": "创建对话失败"}

@app.post("/api/auth/chats")
async def get_user_chats_paginated(request: GetUserChatsRequest):
    """获取用户的分页对话列表"""
    try:
        chats = await db_service.get_user_chats_paginated(request.user_id, request.page, request.page_size)
        total_count = await db_service.get_user_chats_count(request.user_id)
        
        return {
            "success": True, 
            "chats": chats,
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total_count": total_count,
                "total_pages": (total_count + request.page_size - 1) // request.page_size
            }
        }
    except Exception as e:
        logger.error(f"获取用户对话失败: {e}")
        return {"success": False, "message": "获取对话失败", "chats": []}

# 保持原有的API兼容性
@app.get("/api/auth/chats/{user_id}")
async def get_user_chats(user_id: str):
    """获取用户的所有对话（兼容旧版本）"""
    try:
        chats = await db_service.get_user_chats(user_id)
        return {"success": True, "chats": chats}
    except Exception as e:
        logger.error(f"获取用户对话失败: {e}")
        return {"success": False, "message": "获取对话失败", "chats": []}

@app.post("/api/chat/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest):
    """发送聊天消息"""
    try:
        logger.info(f"收到消息发送请求: message='{chat_request.message}', chat_id={chat_request.chat_id}")
        
        if not chat_request.message.strip():
            logger.warning("消息内容为空")
            return ChatResponse(success=False, message="消息内容不能为空")
        
        # 生成聊天ID（如果未提供）
        chat_id = chat_request.chat_id
        
        # 如果没有提供chat_id，需要先创建对话
        if not chat_id:
            logger.info("未提供chat_id，需要创建新对话")
            # 从前端传递的数据中获取用户ID
            user_id = None
            if hasattr(chat_request, 'user_id') and chat_request.user_id:
                user_id = chat_request.user_id
            
            # 如果前端没有传递用户ID，使用测试用户ID
            if not user_id:
                user_id = "a2431f9f-f48e-4225-b59e-c1a16cb590f2"  # 测试用户ID
                logger.info(f"使用测试用户ID: {user_id}")
            
            # 使用用户第一条消息作为对话标题（截取前20个字符）
            title = chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message
            logger.info(f"使用用户消息作为对话标题: {title}")
            
            new_chat = await db_service.create_chat(user_id, title)
            
            if not new_chat:
                logger.error("创建对话失败")
                return ChatResponse(success=False, message="创建对话失败")
            
            chat_id = new_chat['id']
            logger.info(f"成功创建新对话，chat_id: {chat_id}, title: {title}")
        else:
            # 如果提供了chat_id，检查对话是否存在
            logger.info(f"检查chat_id是否存在: {chat_id}")
            chat_exists = await db_service.check_chat_exists(chat_id)
            if not chat_exists:
                logger.info(f"chat_id不存在，需要创建新对话: {chat_id}")
                # 从前端传递的数据中获取用户ID
                user_id = None
                if hasattr(chat_request, 'user_id') and chat_request.user_id:
                    user_id = chat_request.user_id
                
                # 如果前端没有传递用户ID，使用测试用户ID
                if not user_id:
                    user_id = "a2431f9f-f48e-4225-b59e-c1a16cb590f2"  # 测试用户ID
                    logger.info(f"使用测试用户ID: {user_id}")
                
                # 使用用户第一条消息作为对话标题（截取前20个字符）
                title = chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message
                logger.info(f"使用用户消息作为对话标题: {title}")
                
                # 使用前端提供的chat_id创建对话
                new_chat = await db_service.create_chat_with_id(user_id, chat_id, title)
                
                if not new_chat:
                    logger.error(f"使用指定ID创建对话失败: {chat_id}")
                    return ChatResponse(success=False, message="创建对话失败")
                
                logger.info(f"成功使用指定ID创建新对话: {chat_id}, title: {title}")
            else:
                logger.info(f"chat_id存在，直接使用: {chat_id}")
                
                # 检查这是否是该对话的第一条消息，如果是则更新标题
                messages = await db_service.get_chat_messages(chat_id)
                if not messages:  # 如果没有消息，说明这是第一条消息
                    logger.info(f"检测到这是对话的第一条消息，更新标题")
                    title = chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message
                    logger.info(f"使用用户消息作为对话标题: {title}")
                    
                    # 更新对话标题
                    update_success = await db_service.update_chat_title(chat_id, title)
                    if update_success:
                        logger.info(f"成功更新对话标题: {chat_id}, title: {title}")
                    else:
                        logger.warning(f"更新对话标题失败，但继续处理消息: {chat_id}")
        
        # 保存用户消息
        logger.info(f"开始保存用户消息到chat_id: {chat_id}")
        user_message_timestamp = int(datetime.now().timestamp() * 1000)
        user_message = await db_service.save_message(chat_id, 'user', chat_request.message, user_message_timestamp)
        
        if not user_message:
            logger.error(f"保存用户消息失败，chat_id: {chat_id}")
            return ChatResponse(success=False, message="消息保存失败")
        
        logger.info(f"成功保存用户消息，message_id: {user_message['id']}")
        
        # 调用阿里云百炼智能体生成回复
        ai_response = None
        session_id = chat_id  # 使用chat_id作为session_id以保持上下文
        
        if agent_service:
            logger.info("开始调用阿里云百炼智能体")
            agent_result = await agent_service.call_agent(chat_request.message, session_id)
            
            if agent_result['success']:
                ai_response = agent_result['response']
                logger.info(f"智能体调用成功，生成回复长度: {len(ai_response)}")
            else:
                logger.warning(f"智能体调用失败: {agent_result.get('error', '未知错误')}")
                # 使用备用回复
                ai_response = agent_service.get_fallback_response(chat_request.message)
                logger.info("使用备用回复方案")
        else:
            logger.warning("智能体服务未初始化，使用备用回复")
            # 智能体服务未初始化，使用备用回复
            ai_response = f"我已收到您的消息：'{chat_request.message}'。智能体服务暂时不可用，请稍后再试。"
        
        # 确保AI回复不为空
        if not ai_response or not ai_response.strip():
            logger.warning("AI回复为空，使用默认回复")
            ai_response = f"我已收到您的消息：'{chat_request.message}'，正在处理中..."
        
        logger.info(f"最终AI回复: {ai_response[:100]}...")
        
        # 保存AI回复
        logger.info(f"开始保存AI回复到chat_id: {chat_id}")
        ai_message_timestamp = int(datetime.now().timestamp() * 1000)
        ai_message = await db_service.save_message(chat_id, 'assistant', ai_response, ai_message_timestamp)
        
        if not ai_message:
            logger.error(f"保存AI回复失败，chat_id: {chat_id}")
            return ChatResponse(success=False, message="AI回复保存失败")
        
        logger.info(f"成功保存AI回复，message_id: {ai_message['id']}")
        
        response_message = Message(
            id=ai_message['id'],
            role="assistant",
            content=ai_response,
            timestamp=ai_message_timestamp
        )
        
        logger.info(f"消息发送成功，返回response，chat_id: {chat_id}")
        
        # 手动构建响应，确保timestamp格式正确
        response_data = {
            "success": True,
            "response": {
                "id": response_message.id,
                "role": response_message.role,
                "content": response_message.content,
                "timestamp": response_message.timestamp
            },
            "message": "消息发送成功",
            "chat_id": chat_id
        }
        
        return response_data
    except Exception as e:
        logger.error(f"发送消息失败: {e}", exc_info=True)
        return ChatResponse(success=False, message="消息发送失败，请稍后重试")

@app.get("/api/chat/history/{chat_id}")
async def get_chat_history(chat_id: str):
    """获取聊天历史"""
    try:
        messages = await db_service.get_chat_messages(chat_id)
        
        # 格式化消息数据
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg['id'],
                "role": msg['role'],
                "content": msg['content'],
                "timestamp": msg['timestamp']
            })
        
        return {"success": True, "messages": formatted_messages}
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        return {"success": False, "message": "获取聊天历史失败", "messages": []}

@app.delete("/api/chat/{chat_id}")
async def delete_chat(chat_id: str):
    """删除对话及其所有消息"""
    try:
        logger.info(f"收到删除对话请求: {chat_id}")
        
        # 检查对话是否存在
        chat_exists = await db_service.check_chat_exists(chat_id)
        if not chat_exists:
            logger.warning(f"要删除的对话不存在: {chat_id}")
            return {"success": False, "message": "对话不存在"}
        
        # 删除对话
        success = await db_service.delete_chat(chat_id)
        
        if success:
            logger.info(f"成功删除对话: {chat_id}")
            return {"success": True, "message": "对话删除成功"}
        else:
            logger.error(f"删除对话失败: {chat_id}")
            return {"success": False, "message": "删除对话失败"}
    except Exception as e:
        logger.error(f"删除对话失败: {e}", exc_info=True)
        return {"success": False, "message": "删除对话失败，请稍后重试"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)