-- DeepSeek Chat 数据库初始化脚本
-- 请先在Supabase中执行此脚本重新创建数据库结构

-- 1. 删除现有表（如果存在）
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS chats;
DROP TABLE IF EXISTS users;

-- 2. 创建用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    plan VARCHAR(20) DEFAULT '个人版',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 创建对话表
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    color VARCHAR(50) DEFAULT 'bg-blue-100',
    icon_color VARCHAR(50) DEFAULT 'text-blue-500',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 添加索引以提高查询性能
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 为对话表添加索引
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_created_at ON chats(created_at DESC);
CREATE INDEX idx_chats_updated_at ON chats(updated_at DESC);

-- 4. 创建消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 添加索引以提高查询性能
    CONSTRAINT fk_chat FOREIGN KEY (chat_id) REFERENCES chats(id)
);

-- 为消息表添加索引
CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp ASC);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- 5. 创建触发器自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表添加触发器
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为对话表添加触发器
CREATE TRIGGER update_chats_updated_at 
    BEFORE UPDATE ON chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 6. 插入测试数据（可选）
INSERT INTO users (id, username, email, password_hash, plan) VALUES 
    ('9ddf16ae-00e4-4c0a-9f8e-725d96c976a2', 'testuser', 'test@example.com', '$2b$12$hashedpassword', '个人版');

INSERT INTO chats (id, user_id, title, color, icon_color) VALUES 
    ('759bab63-a614-434b-bf39-d5ae6c659e18', '9ddf16ae-00e4-4c0a-9f8e-725d96c976a2', '欢迎使用DeepSeek', 'bg-blue-100', 'text-blue-500');

INSERT INTO messages (id, chat_id, role, content, timestamp) VALUES 
    (gen_random_uuid(), '759bab63-a614-434b-bf39-d5ae6c659e18', 'assistant', '欢迎使用DeepSeek！我是您的AI助手，可以帮您解答问题、创作内容、分析文档等。有什么我可以帮助您的吗？', extract(epoch from NOW()) * 1000);

-- 7. 创建视图方便查询（可选）
CREATE VIEW user_chats_with_latest_message AS
SELECT 
    c.*,
    u.username,
    u.email,
    (SELECT content FROM messages m WHERE m.chat_id = c.id ORDER BY m.timestamp DESC LIMIT 1) as latest_message,
    (SELECT timestamp FROM messages m WHERE m.chat_id = c.id ORDER BY m.timestamp DESC LIMIT 1) as latest_message_time
FROM chats c
JOIN users u ON c.user_id = u.id
ORDER BY c.updated_at DESC;

-- 8. 权限设置（确保API可以访问）
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 为用户表创建策略
CREATE POLICY "用户可以看到自己的数据" ON users FOR ALL USING (auth.uid() = id);
CREATE POLICY "用户可以查看所有用户（公开信息）" ON users FOR SELECT USING (true);

-- 为对话表创建策略
CREATE POLICY "用户可以管理自己的对话" ON chats FOR ALL USING (auth.uid() = user_id);

-- 为消息表创建策略
CREATE POLICY "用户可以查看自己对话的消息" ON messages FOR ALL USING (
    EXISTS (SELECT 1 FROM chats WHERE chats.id = messages.chat_id AND chats.user_id = auth.uid())
);

-- 完成提示
SELECT '数据库初始化完成！' as status;