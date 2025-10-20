#!/bin/bash

# NMPA Python爬虫带代理关闭功能的后台运行脚本
# 专门用于运行: proxy_off & python3 crawler.py --log-level DEBUG

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PID_FILE="$PROJECT_DIR/crawler_proxy_off.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/crawler_debug_$(date +%Y%m%d_%H%M%S).log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# 检查是否已有进程在运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # 进程正在运行
        else
            rm -f "$PID_FILE"  # 清理无效PID文件
            return 1  # 进程不存在
        fi
    fi
    return 1  # 没有PID文件
}

# 获取proxy_off函数的定义
get_proxy_off_function() {
    # 从当前shell中获取proxy_off函数定义
    type proxy_off 2>/dev/null | tail -n +2
}

# 创建运行脚本
create_run_script() {
    local run_script="$LOG_DIR/run_proxy_off_$$.sh"

    cat > "$run_script" << 'EOF'
#!/bin/bash

# 设置工作目录
cd "/home/langchao6/projects/taya/nmpa/nmpa_crawler_python"

# 加载proxy_off函数（如果需要）
# 这里假设proxy_off函数在当前shell中已定义
# 如果没有定义，我们提供一个基本的实现

if ! type proxy_off >/dev/null 2>&1; then
    # 如果proxy_off未定义，提供一个基本实现
    proxy_off() {
        echo "🛑 关闭代理..."
        if pgrep -f v2ray > /dev/null; then
            pkill -f v2ray
            echo "✅ V2Ray已停止"
        else
            echo "ℹ️ V2Ray未运行"
        fi
        unset all_proxy
        unset http_proxy
        unset https_proxy
        echo "✅ 代理环境变量已清除"
        echo "🌐 代理状态: 已关闭"
    }
fi

# 执行proxy_off
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行proxy_off..."
proxy_off

# 等待一下确保代理完全关闭
sleep 2

# 运行爬虫
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动爬虫..."
exec python3 crawler.py --log-level DEBUG
EOF

    chmod +x "$run_script"
    echo "$run_script"
}

# 启动爬虫
start_crawler() {
    if check_running; then
        warn "爬虫已在运行中 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    log "启动带代理关闭功能的Python NMPA爬虫..."

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 创建运行脚本
    local run_script=$(create_run_script)

    log "日志文件: $LOG_FILE"
    log "运行脚本: $run_script"

    cd "$PROJECT_DIR"

    # 使用nohup在后台运行整个流程
    nohup "$run_script" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # 等待一小段时间检查进程是否正常启动
    sleep 3
    if ps -p "$pid" > /dev/null 2>&1; then
        log "✅ 爬虫启动成功! PID: $pid"
        log "代理已关闭，爬虫以DEBUG模式运行"
        log "日志文件: $LOG_FILE"
        log "使用 './manage_proxy_off.sh status' 查看状态"
        log "使用 'tail -f $LOG_FILE' 查看实时日志"
        return 0
    else
        error "❌ 爬虫启动失败!"
        rm -f "$PID_FILE"

        # 显示错误信息
        if [ -f "$LOG_FILE" ]; then
            echo "错误信息:"
            tail -10 "$LOG_FILE"
        fi

        return 1
    fi
}

# 停止爬虫
stop_crawler() {
    if ! check_running; then
        warn "爬虫未在运行"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    log "停止爬虫 (PID: $pid)..."

    # 发送SIGTERM信号优雅停止
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果进程仍在运行，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        warn "进程未响应TERM信号，强制停止..."
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

# 查看状态
show_status() {
    echo "=== NMPA爬虫(代理关闭版)状态 ==="

    if check_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "状态: ${GREEN}运行中${NC}"
        echo "PID: $pid"
        echo "启动时间: $(ps -p "$pid" -o lstart= 2>/dev/null || echo "未知")"
        echo "CPU使用率: $(ps -p "$pid" -o %cpu= 2>/dev/null || echo "未知")%"
        echo "内存使用: $(ps -p "$pid" -o %mem= 2>/dev/null || echo "未知")%"
        echo "运行时长: $(ps -p "$pid" -o etime= 2>/dev/null || echo "未知")"
        echo "日志级别: DEBUG"
        echo "代理状态: 已关闭"
    else
        echo -e "状态: ${RED}未运行${NC}"
    fi

    echo ""
    echo "=== 日志文件 ==="
    if [ -d "$LOG_DIR" ]; then
        local log_count=$(ls -1 "$LOG_DIR"/crawler_debug_*.log 2>/dev/null | wc -l)
        echo "日志目录: $LOG_DIR"
        echo "DEBUG日志文件数: $log_count"

        if [ "$log_count" -gt 0 ]; then
            echo "最新日志文件:"
            ls -lt "$LOG_DIR"/crawler_debug_*.log | head -3 | awk '{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}'
        fi
    else
        echo "日志目录不存在"
    fi

    echo ""
    echo "=== 代理状态 ==="
    if [ -n "$http_proxy" ] || [ -n "$https_proxy" ] || [ -n "$all_proxy" ]; then
        echo -e "代理状态: ${YELLOW}部分开启${NC}"
        [ -n "$http_proxy" ] && echo "  http_proxy: $http_proxy"
        [ -n "$https_proxy" ] && echo "  https_proxy: $https_proxy"
        [ -n "$all_proxy" ] && echo "  all_proxy: $all_proxy"
    else
        echo -e "代理状态: ${GREEN}已关闭${NC}"
    fi
}

# 查看实时日志
tail_logs() {
    local latest_log=$(ls -t "$LOG_DIR"/crawler_debug_*.log 2>/dev/null | head -1)

    if [ -z "$latest_log" ]; then
        error "未找到DEBUG日志文件"
        return 1
    fi

    log "正在查看DEBUG日志: $(basename "$latest_log")"
    log "按 Ctrl+C 停止跟踪"
    echo "----------------------------------------"

    tail -f "$latest_log"
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫代理关闭版管理脚本"
    echo ""
    echo "用法: $0 {start|stop|status|logs|help}"
    echo ""
    echo "命令:"
    echo "  start   - 启动爬虫（关闭代理后以DEBUG模式运行）"
    echo "  stop    - 停止爬虫"
    echo "  status  - 查看运行状态"
    echo "  logs    - 查看实时DEBUG日志"
    echo "  help    - 显示此帮助信息"
    echo ""
    echo "说明:"
    echo "  此脚本会先执行proxy_off关闭代理，然后启动DEBUG模式的爬虫"
    echo "  所有输出（包括代理关闭过程）都会被记录到日志文件"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动爬虫"
    echo "  $0 status         # 查看状态"
    echo "  $0 logs           # 查看实时日志"
}

# 主函数
main() {
    case "${1:-}" in
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
            tail_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "错误: 未知命令 '${1:-}'"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"