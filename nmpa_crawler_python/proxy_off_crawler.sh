#!/bin/bash

# 简单可靠的proxy_off + 爬虫后台运行脚本
# 直接替代: proxy_off & python3 crawler.py --log-level DEBUG

set -e

LOG_FILE="logs/crawler_debug_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="crawler_proxy_off.pid"

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

log "🚀 启动NMPA爬虫 (DEBUG模式 + 代理关闭)"
log "📄 日志文件: $LOG_FILE"

# 创建执行脚本
cat > /tmp/crawler_runner_$$.sh << 'EOF'
#!/bin/bash
cd "/home/langchao6/projects/taya/nmpa/nmpa_crawler_python"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 开始运行 =========="

# 显示代理状态
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 当前代理状态:"
echo "  http_proxy: '${http_proxy:-未设置}'"
echo "  https_proxy: '${https_proxy:-未设置}'"
echo "  all_proxy: '${all_proxy:-未设置}'"

# 执行proxy_off
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行proxy_off..."
if type proxy_off >/dev/null 2>&1; then
    proxy_off
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] proxy_off函数不存在，使用内置代理关闭..."
    # 内置代理关闭逻辑
    if pgrep -f v2ray > /dev/null; then
        pkill -f v2ray
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] V2Ray已停止"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] V2Ray未运行"
    fi
    unset all_proxy http_proxy https_proxy
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 代理环境变量已清除"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待代理关闭完成..."
sleep 3

# 显示关闭后状态
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 代理关闭后状态:"
echo "  http_proxy: '${http_proxy:-未设置}'"
echo "  https_proxy: '${https_proxy:-未设置}'"
echo "  all_proxy: '${all_proxy:-未设置}'"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动DEBUG模式爬虫..."
python3 crawler.py --log-level DEBUG

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 进程结束 =========="
EOF

chmod +x /tmp/crawler_runner_$$.sh

# 在后台运行执行脚本
nohup /tmp/crawler_runner_$$.sh > "$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"

# 清理临时脚本
sleep 2
rm -f /tmp/crawler_runner_$$.sh

log "✅ 已在后台启动! PID: $pid"
log ""
log "🔍 管理命令:"
log "  查看状态: ps -p $pid"
log "  查看日志: tail -f $LOG_FILE"
log "  停止进程: kill $pid"
log "  删除PID: rm -f $PID_FILE"

# 等待启动确认
sleep 3
if ps -p "$pid" > /dev/null 2>&1; then
    log "🎉 进程运行正常"
else
    error "❌ 进程启动失败，查看日志:"
    tail -10 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi