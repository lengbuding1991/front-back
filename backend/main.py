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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
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
                chat_id = str(uuid.uuid4())
                chat_data = {
                    'id': chat_id,
                    'user_id': user_id,
                    'title': title,
                    'color': 'bg-blue-100',
                    'icon_color': 'text-blue-500'
                }
                
                response = await client.post(
                    f"{self.base_url}/chats",
                    headers=self.headers,
                    json=chat_data
                )
                
                if response.status_code == 201:
                    return response.json()[0]
                else:
                    logger.error(f"创建对话失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"创建对话失败: {e}")
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
                message_id = str(uuid.uuid4())
                message_data = {
                    'id': message_id,
                    'chat_id': chat_id,
                    'role': role,
                    'content': content,
                    'timestamp': timestamp
                }
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=message_data
                )
                
                if response.status_code == 201:
                    return response.json()[0]
                else:
                    logger.error(f"创建消息失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"创建消息失败: {e}")
                return None
    
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

# 全局数据库服务实例
db_service = DatabaseService()

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
        if not chat_request.message.strip():
            return ChatResponse(success=False, message="消息内容不能为空")
        
        # 生成聊天ID（如果未提供）
        chat_id = chat_request.chat_id
        
        # 如果没有提供chat_id，需要先创建对话
        if not chat_id:
            # 从前端传递的数据中获取用户ID
            user_id = None
            if hasattr(chat_request, 'user_id') and chat_request.user_id:
                user_id = chat_request.user_id
            
            # 如果前端没有传递用户ID，使用测试用户ID
            if not user_id:
                user_id = "a2431f9f-f48e-4225-b59e-c1a16cb590f2"  # 测试用户ID
            
            new_chat = await db_service.create_chat(user_id, "新对话")
            
            if not new_chat:
                return ChatResponse(success=False, message="创建对话失败")
            
            chat_id = new_chat['id']
        
        # 保存用户消息
        user_message_timestamp = int(datetime.now().timestamp() * 1000)
        user_message = await db_service.save_message(chat_id, 'user', chat_request.message, user_message_timestamp)
        
        if not user_message:
            return ChatResponse(success=False, message="消息保存失败")
        
        # 模拟AI回复
        ai_response = f"我已经收到您的消息：'{chat_request.message}'。这是一个模拟回复，实际应用中会调用AI接口生成回复内容。"
        
        # 保存AI回复
        ai_message_timestamp = int(datetime.now().timestamp() * 1000)
        ai_message = await db_service.save_message(chat_id, 'assistant', ai_response, ai_message_timestamp)
        
        if not ai_message:
            return ChatResponse(success=False, message="AI回复保存失败")
        
        response_message = Message(
            id=ai_message['id'],
            role="assistant",
            content=ai_response,
            timestamp=ai_message_timestamp
        )
        
        return ChatResponse(
            success=True,
            response=response_message,
            message="消息发送成功",
            chat_id=chat_id  # 返回对话ID，前端可能需要使用
        )
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)