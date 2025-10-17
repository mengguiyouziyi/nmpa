#!/bin/bash

# NMPA 本地测试停止脚本

set -e

echo "🛑 停止本地测试"
echo "=============="

cd "$(dirname "$0")"

PID_FILE="local_test.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到本地测试 PID 文件"
    exit 0
fi

TEST_PID=$(cat "$PID_FILE")

if ! ps -p "$TEST_PID" > /dev/null 2>&1; then
    echo "⚠️  测试进程 $TEST_PID 不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 0
fi

echo "🔄 停止本地测试进程 (PID: $TEST_PID)..."

# 发送TERM信号
kill "$TEST_PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$TEST_PID" > /dev/null 2>&1; then
        echo "✅ 本地测试已正常停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo "⏳ 等待进程结束... ($i/10)"
    sleep 1
done

# 强制结束
echo "⚠️  强制结束进程..."
kill -9 "$TEST_PID" 2>/dev/null || true
rm -f "$PID_FILE"

echo "✅ 本地测试已强制停止"