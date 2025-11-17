from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

# 创建FastAPI应用
app = FastAPI(
    title="DeepSeek Chat API",
    description="DeepSeek聊天应用后端API",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],  # 支持Vite开发服务器和前端实际运行端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型定义
class User(BaseModel):
    id: int
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

class ChatResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    response: Optional[Message] = None

# 模拟数据存储
class DataStore:
    def __init__(self):
        self.users = [
            {
                "id": 1,
                "username": "冷丶布丁",
                "email": "498128186@qq.com",
                "password": "shuishui",
                "avatar": "https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png",
                "plan": "个人版",
                "created_at": "2023-11-01"
            }
        ]
        self.chats = {}
    
    def get_user_by_identifier(self, identifier: str):
        """通过用户名或邮箱查找用户"""
        for user in self.users:
            if user["username"] == identifier or user["email"] == identifier:
                return user
        return None
    
    def add_user(self, user_data: dict):
        """添加新用户"""
        new_id = max([u["id"] for u in self.users]) + 1 if self.users else 1
        user_data["id"] = new_id
        user_data["created_at"] = datetime.now().strftime("%Y-%m-%d")
        self.users.append(user_data)
        return user_data

# 全局数据存储实例
data_store = DataStore()

# API路由
@app.get("/")
async def root():
    return {"message": "DeepSeek Chat API 服务运行中", "version": "1.0.0"}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(user_data: UserLogin):
    """用户登录"""
    user = data_store.get_user_by_identifier(user_data.identifier)
    
    if not user:
        return LoginResponse(success=False, message="用户不存在")
    
    if user["password"] != user_data.password:
        return LoginResponse(success=False, message="密码错误")
    
    # 登录成功，返回用户信息（不包含密码）
    user_info = {k: v for k, v in user.items() if k != "password"}
    return LoginResponse(success=True, user=User(**user_info))

@app.post("/api/auth/register", response_model=LoginResponse)
async def register(user_data: UserRegister):
    """用户注册"""
    # 检查邮箱是否已存在
    if data_store.get_user_by_identifier(user_data.email):
        return LoginResponse(success=False, message="邮箱已被注册")
    
    # 检查用户名是否已存在
    if data_store.get_user_by_identifier(user_data.username):
        return LoginResponse(success=False, message="用户名已被使用")
    
    # 检查密码确认
    if user_data.password != user_data.confirm_password:
        return LoginResponse(success=False, message="密码确认不匹配")
    
    # 检查是否同意条款
    if not user_data.agree_terms:
        return LoginResponse(success=False, message="请同意服务条款")
    
    # 创建新用户
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "password": user_data.password,
        "avatar": "https://design.gemcoder.com/staticResource/echoAiSystemImages/3af53b10252ba2331a996da3c32fd378.png",
        "plan": "个人版"
    }
    
    user = data_store.add_user(new_user)
    user_info = {k: v for k, v in user.items() if k != "password"}
    return LoginResponse(success=True, user=User(**user_info))

@app.post("/api/chat/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest):
    """发送聊天消息"""
    if not chat_request.message.strip():
        return ChatResponse(success=False, message="消息内容不能为空")
    
    # 生成聊天ID（如果未提供）
    chat_id = chat_request.chat_id or str(uuid.uuid4())
    
    # 模拟AI回复
    ai_response = f"我已经收到您的消息：'{chat_request.message}'。这是一个模拟回复，实际应用中会调用AI接口生成回复内容。"
    
    response_message = Message(
        id=str(uuid.uuid4()),
        role="assistant",
        content=ai_response,
        timestamp=int(datetime.now().timestamp() * 1000)
    )
    
    return ChatResponse(
        success=True,
        response=response_message,
        message="消息发送成功"
    )

@app.get("/api/chat/history/{chat_id}")
async def get_chat_history(chat_id: str):
    """获取聊天历史（模拟数据）"""
    # 模拟聊天历史
    if chat_id == "1":
        return {
            "success": True,
            "messages": [
                {
                    "id": "1",
                    "role": "assistant",
                    "content": "欢迎使用DeepSeek！我是您的AI助手，可以帮您解答问题、创作内容、分析文档等。有什么我可以帮助您的吗？",
                    "timestamp": int(datetime.now().timestamp() * 1000) - 60000
                }
            ]
        }
    else:
        return {"success": True, "messages": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)