#!/bin/bash

# 简单的proxy_off + 爬虫后台运行脚本
# 用法: ./simple_proxy_off_runner.sh

set -e

# 配置
LOG_FILE="logs/crawler_debug_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="crawler_proxy_off_simple.pid"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
}

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        warn "爬虫已在运行 (PID: $pid)"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 创建日志目录
mkdir -p logs

log "准备启动爬虫..."
log "日志文件: $LOG_FILE"

# 在后台执行完整命令
{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 开始运行 =========="

    # 执行proxy_off（如果函数存在）
    if type proxy_off >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行proxy_off..."
        proxy_off
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] proxy_off函数不存在，跳过代理关闭"
    fi

    # 等待代理完全关闭
    sleep 2

    # 启动爬虫
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动DEBUG模式爬虫..."
    python3 crawler.py --log-level DEBUG

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 进程结束 =========="
} > "$LOG_FILE" 2>&1 &

# 保存PID
pid=$!
echo "$pid" > "$PID_FILE"

log "✅ 已在后台启动! PID: $pid"
log "查看日志: tail -f $LOG_FILE"
log "停止进程: kill $pid"

# 等待启动确认
sleep 3
if ps -p "$pid" > /dev/null 2>&1; then
    log "进程运行正常"
else
    error "进程启动失败，查看日志:"
    tail -5 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi