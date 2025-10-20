#!/bin/bash

# 最简单的方法：直接在后台运行proxy_off和爬虫
# 用法: ./quick_start.sh

LOG_FILE="logs/crawler_debug_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 启动NMPA爬虫 (DEBUG模式 + 代理关闭)"
echo "📄 日志文件: $LOG_FILE"
echo ""

# 创建日志目录
mkdir -p logs

# 使用nohup在后台运行，先执行proxy_off，再启动爬虫
nohup bash -c "
    echo '[\$(date)] ========== 开始运行 =========='

    # 执行proxy_off函数
    if type proxy_off >/dev/null 2>&1; then
        echo '[\$(date)] 执行proxy_off...'
        proxy_off
    else
        echo '[\$(date)] proxy_off函数不存在，跳过代理关闭'
    fi

    sleep 2
    echo '[\$(date)] 启动DEBUG模式爬虫...'
    python3 crawler.py --log-level DEBUG
    echo '[\$(date)] ========== 进程结束 =========='
" > "$LOG_FILE" 2>&1 &

PID=$!
echo "✅ 已在后台启动! PID: $PID"
echo ""
echo "🔍 管理命令:"
echo "  查看日志: tail -f $LOG_FILE"
echo "  停止进程: kill $PID"
echo "  查看进程: ps -p $PID"
echo ""
echo "💡 提示: 按 Ctrl+C 不会影响后台进程"