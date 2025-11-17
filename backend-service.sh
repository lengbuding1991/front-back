#!/bin/bash

# DeepSeek 后端服务管理脚本
# 使用方法：./backend-service.sh [start|stop|restart|status]

SERVICE_NAME="deepseek-backend"
WORKING_DIR="/www/server/deepseek-backend"
LOG_FILE="$WORKING_DIR/backend.log"
PID_FILE="$WORKING_DIR/backend.pid"

# 检查服务是否正在运行
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ $SERVICE_NAME 服务正在运行 (PID: $PID)"
            return 0
        else
            echo "❌ $SERVICE_NAME 服务PID文件存在但进程不存在"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "❌ $SERVICE_NAME 服务未运行"
        return 1
    fi
}

# 启动服务
start_service() {
    echo "🚀 启动 $SERVICE_NAME 服务..."
    
    if check_status; then
        echo "⚠️  $SERVICE_NAME 服务已经在运行"
        return 0
    fi
    
    cd "$WORKING_DIR"
    
    # 激活虚拟环境并启动服务
    nohup source venv/bin/activate && ENVIRONMENT=production python3 run.py > "$LOG_FILE" 2>&1 &
    
    # 获取进程ID
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if check_status; then
        echo "✅ $SERVICE_NAME 服务启动成功 (PID: $PID)"
        echo "📋 日志文件: $LOG_FILE"
    else
        echo "❌ $SERVICE_NAME 服务启动失败"
        echo "🔍 查看日志: tail -f $LOG_FILE"
    fi
}

# 停止服务
stop_service() {
    echo "🛑 停止 $SERVICE_NAME 服务..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
                echo "⚠️  强制终止 $SERVICE_NAME 服务 (PID: $PID)"
            else
                echo "✅ $SERVICE_NAME 服务已停止 (PID: $PID)"
            fi
            rm -f "$PID_FILE"
        else
            echo "⚠️  PID文件存在但进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  $SERVICE_NAME 服务未运行或PID文件不存在"
        # 尝试通过进程名停止
        pkill -f "python3 run.py" && echo "✅ 通过进程名停止服务" || echo "❌ 无法找到相关进程"
    fi
}

# 重启服务
restart_service() {
    echo "🔄 重启 $SERVICE_NAME 服务..."
    stop_service
    sleep 3
    start_service
}

# 查看服务状态和日志
status_service() {
    echo "📊 $SERVICE_NAME 服务状态:"
    check_status
    
    echo ""
    echo "📋 最近日志 (最后20行):"
    if [ -f "$LOG_FILE" ]; then
        tail -20 "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
    
    echo ""
    echo "🌐 检查端口监听:"
    netstat -tlnp | grep 8000 || echo "端口8000未监听"
    
    echo ""
    echo "🔍 检查进程:"
    ps aux | grep "python3 run.py" | grep -v grep
}

# 主程序
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status}"
        echo ""
        echo "示例:"
        echo "  $0 start     # 启动服务"
        echo "  $0 stop      # 停止服务"
        echo "  $0 restart   # 重启服务"
        echo "  $0 status    # 查看服务状态"
        exit 1
        ;;
esac