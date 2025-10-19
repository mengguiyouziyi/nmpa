#!/bin/bash

# NMPA 爬虫停止脚本

set -e

echo "🛑 NMPA 爬虫停止脚本"
echo "===================="

cd "$(dirname "$0")"

PID_FILE="crawler.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到 PID 文件，可能没有运行的爬虫进程"
    exit 0
fi

CRAWLER_PID=$(cat "$PID_FILE")

if ! ps -p "$CRAWLER_PID" > /dev/null 2>&1; then
    echo "⚠️  进程 $CRAWLER_PID 不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 0
fi

echo "🔄 停止爬虫进程 (PID: $CRAWLER_PID)..."

# 发送TERM信号
kill "$CRAWLER_PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$CRAWLER_PID" > /dev/null 2>&1; then
        echo "✅ 爬虫已正常停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo "⏳ 等待进程结束... ($i/10)"
    sleep 1
done

# 强制结束
echo "⚠️  强制结束进程..."
kill -9 "$CRAWLER_PID" 2>/dev/null || true
rm -f "$PID_FILE"

echo "✅ 爬虫已强制停止"