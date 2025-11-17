#!/usr/bin/env python3
"""
DeepSeek Chat API 启动脚本
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 启动 DeepSeek Chat API 服务...")
    print("📡 服务地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("⏹️  按 Ctrl+C 停止服务\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )