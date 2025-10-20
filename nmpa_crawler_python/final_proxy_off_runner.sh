#!/bin/bash

# 最终版本：完整的proxy_off + 爬虫后台运行脚本
# 用法: ./final_proxy_off_runner.sh

set -e

# 配置
LOG_FILE="logs/crawler_debug_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="crawler_final.pid"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO:${NC} $1"
}

# 检查是否已在运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 代理关闭函数（内嵌版本）
proxy_off_embedded() {
    echo "🛑 关闭代理..."

    # 停止V2Ray
    if pgrep -f v2ray > /dev/null; then
        pkill -f v2ray
        echo "✅ V2Ray已停止"
    else
        echo "ℹ️ V2Ray未运行"
    fi

    # 清除环境变量
    unset all_proxy
    unset http_proxy
    unset https_proxy

    echo "✅ 代理环境变量已清除"
    echo "🌐 代理状态: 已关闭"
}

# 启动函数
start_crawler() {
    if check_running; then
        warn "爬虫已在运行中 (PID: $(cat "$PID_FILE"))"
        exit 1
    fi

    log "🚀 启动NMPA爬虫 (DEBUG模式 + 代理关闭)"
    log "📄 日志文件: $LOG_FILE"

    # 创建日志目录
    mkdir -p logs

    # 在后台执行完整命令
    nohup bash -c '
        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] ========== 开始运行 =========="

        # 显示当前代理状态
        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 当前代理状态:"
        echo "  http_proxy: '${http_proxy:-未设置}'"
        echo "  https_proxy: '${https_proxy:-未设置}'"
        echo "  all_proxy: '${all_proxy:-未设置}'"

        # 尝试调用系统proxy_off函数
        if type proxy_off >/dev/null 2>&1; then
            echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 使用系统proxy_off函数..."
            proxy_off
        else
            echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 使用内嵌proxy_off函数..."
            '"$(declare -f proxy_off_embedded)"'
            proxy_off_embedded
        fi

        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 等待代理完全关闭..."
        sleep 3

        # 再次显示代理状态
        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 代理关闭后状态:"
        echo "  http_proxy: '${http_proxy:-未设置}'"
        echo "  https_proxy: '${https_proxy:-未设置}'"
        echo "  all_proxy: '${all_proxy:-未设置}'"

        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] 启动DEBUG模式爬虫..."
        python3 crawler.py --log-level DEBUG

        echo "['$(date '+%Y-%m-%d %H:%M:%S')'] ========== 进程结束 =========="
    ' > "$LOG_FILE" 2>&1 &

    # 保存PID
    local pid=$!
    echo "$pid" > "$PID_FILE"

    log "✅ 已在后台启动! PID: $pid"
    log "🔍 管理命令:"
    log "  查看状态: $0 status"
    log "  查看日志: $0 logs"
    log "  停止进程: $0 stop"
    log "  实时日志: tail -f $LOG_FILE"

    # 等待启动确认
    sleep 5
    if ps -p "$pid" > /dev/null 2>&1; then
        log "🎉 进程运行正常"
        return 0
    else
        error "❌ 进程启动失败，查看日志:"
        tail -10 "$LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止函数
stop_crawler() {
    if ! check_running; then
        warn "爬虫未在运行"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    log "🛑 停止爬虫 (PID: $pid)..."

    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 15 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    if ps -p "$pid" > /dev/null 2>&1; then
        warn "强制停止进程..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 2
    fi

    if ps -p "$pid" > /dev/null 2>&1; then
        error "无法停止进程 PID: $pid"
        return 1
    else
        log "✅ 爬虫已停止"
        rm -f "$PID_FILE"
        return 0
    fi
}

# 状态函数
show_status() {
    echo "========================================"
    echo "    NMPA爬虫状态 (代理关闭版)"
    echo "========================================"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    if check_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "状态: ${GREEN}🟢 运行中${NC}"
        echo "PID: $pid"
        echo "启动时间: $(ps -p "$pid" -o lstart= 2>/dev/null || echo "未知")"
        echo "CPU使用率: $(ps -p "$pid" -o %cpu= 2>/dev/null || echo "未知")%"
        echo "内存使用: $(ps -p "$pid" -o %mem= 2>/dev/null || echo "未知")%"
        echo "运行时长: $(ps -p "$pid" -o etime= 2>/dev/null || echo "未知")"
        echo "日志级别: DEBUG"
        echo "代理状态: 已关闭"
    else
        echo -e "状态: ${RED}🔴 未运行${NC}"
    fi

    echo ""
    echo "📄 日志信息:"
    if [ -f "$LOG_FILE" ]; then
        echo "当前日志: $LOG_FILE"
        echo "日志大小: $(du -h "$LOG_FILE" 2>/dev/null | cut -f1 || echo "未知")"
        echo "最后修改: $(stat -c %y "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)"
    else
        echo "当前日志: 无"
    fi

    echo ""
    echo "🌐 代理状态:"
    if [ -n "$http_proxy" ] || [ -n "$https_proxy" ] || [ -n "$all_proxy" ]; then
        echo -e "状态: ${YELLOW}部分开启${NC}"
        [ -n "$http_proxy" ] && echo "  http_proxy: $http_proxy"
        [ -n "$https_proxy" ] && echo "  https_proxy: $https_proxy"
        [ -n "$all_proxy" ] && echo "  all_proxy: $all_proxy"
    else
        echo -e "状态: ${GREEN}已关闭${NC}"
    fi

    echo "========================================"
}

# 日志函数
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        error "日志文件不存在: $LOG_FILE"
        return 1
    fi

    log "📄 查看DEBUG日志: $(basename "$LOG_FILE")"
    log "按 Ctrl+C 停止跟踪"
    echo "----------------------------------------"
    tail -f "$LOG_FILE"
}

# 主函数
case "${1:-start}" in
    "start")
        start_crawler
        ;;
    "stop")
        stop_crawler
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "help"|"-h"|"--help")
        echo "NMPA爬虫代理关闭版管理脚本"
        echo ""
        echo "用法: $0 {start|stop|status|logs|help}"
        echo ""
        echo "命令:"
        echo "  start   - 启动爬虫（默认）"
        echo "  stop    - 停止爬虫"
        echo "  status  - 查看状态"
        echo "  logs    - 查看实时日志"
        echo "  help    - 显示帮助"
        echo ""
        echo "功能:"
        echo "  ✅ 自动关闭代理（V2Ray + 环境变量）"
        echo "  ✅ DEBUG模式运行爬虫"
        echo "  ✅ 完整日志记录"
        echo "  ✅ 后台进程管理"
        ;;
    *)
        error "未知命令: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac