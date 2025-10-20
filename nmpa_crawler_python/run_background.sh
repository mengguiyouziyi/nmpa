#!/bin/bash

# NMPA Python爬虫后台运行脚本
# 支持日志管理、进程监控和自动重启

set -e

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PID_FILE="$PROJECT_DIR/crawler.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/crawler_$(date +%Y%m%d_%H%M%S).log"
PYTHON_CMD="python3"
CRAWLER_SCRIPT="crawler.py"
MAX_LOG_FILES=10
AUTO_RESTART=true
RESTART_DELAY=30
CHECK_INTERVAL=60

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 创建日志目录
create_log_dir() {
    mkdir -p "$LOG_DIR"
    log "日志目录创建成功: $LOG_DIR"
}

# 清理旧日志
cleanup_logs() {
    log "清理旧日志文件..."
    cd "$LOG_DIR"
    local log_count=$(ls crawler_*.log 2>/dev/null | wc -l)

    if [ "$log_count" -gt "$MAX_LOG_FILES" ]; then
        local files_to_remove=$((log_count - MAX_LOG_FILES))
        ls -t crawler_*.log | tail -n "$files_to_remove" | xargs rm -f
        log "已删除 $files_to_remove 个旧日志文件"
    fi
}

# 启动爬虫
start_crawler() {
    if check_running; then
        warn "爬虫已在运行中 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    log "启动Python NMPA爬虫..."
    create_log_dir
    cleanup_logs

    cd "$PROJECT_DIR"

    # 使用nohup在后台运行，同时输出到日志文件和控制台
    nohup "$PYTHON_CMD" "$CRAWLER_SCRIPT" \
        --log-level INFO \
        > >(tee -a "$LOG_FILE") 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    # 等待一小段时间检查进程是否正常启动
    sleep 3
    if ps -p "$pid" > /dev/null 2>&1; then
        log "爬虫启动成功! PID: $pid"
        log "日志文件: $LOG_FILE"
        log "使用 './manage_crawler.sh status' 查看状态"
        return 0
    else
        error "爬虫启动失败!"
        rm -f "$PID_FILE"
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
        log "爬虫已停止"
        rm -f "$PID_FILE"
        return 0
    fi
}

# 重启爬虫
restart_crawler() {
    log "重启爬虫..."
    stop_crawler
    sleep 2
    start_crawler
}

# 查看状态
show_status() {
    echo "=== NMPA Python爬虫状态 ==="

    if check_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "状态: ${GREEN}运行中${NC}"
        echo "PID: $pid"
        echo "启动时间: $(ps -p "$pid" -o lstart= 2>/dev/null || echo "未知")"
        echo "CPU使用率: $(ps -p "$pid" -o %cpu= 2>/dev/null || echo "未知")%"
        echo "内存使用: $(ps -p "$pid" -o %mem= 2>/dev/null || echo "未知")%"
        echo "运行时长: $(ps -p "$pid" -o etime= 2>/dev/null || echo "未知")"
    else
        echo -e "状态: ${RED}未运行${NC}"
    fi

    echo ""
    echo "=== 日志文件 ==="
    if [ -d "$LOG_DIR" ]; then
        local log_count=$(ls -1 "$LOG_DIR"/crawler_*.log 2>/dev/null | wc -l)
        echo "日志目录: $LOG_DIR"
        echo "日志文件数: $log_count"

        if [ "$log_count" -gt 0 ]; then
            echo "最新日志文件:"
            ls -lt "$LOG_DIR"/crawler_*.log | head -5 | awk '{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}'
        fi
    else
        echo "日志目录不存在"
    fi

    echo ""
    echo "=== 输出文件 ==="
    if [ -d "$PROJECT_DIR/outputs" ]; then
        local output_count=$(find "$PROJECT_DIR/outputs" -name "*.jsonl" 2>/dev/null | wc -l)
        echo "输出文件数: $output_count"
        if [ "$output_count" -gt 0 ]; then
            echo "总记录数: $(find "$PROJECT_DIR/outputs" -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")"
        fi
    fi
}

# 查看实时日志
tail_logs() {
    local log_file="$1"

    if [ -z "$log_file" ]; then
        # 使用最新的日志文件
        log_file=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)
    fi

    if [ -z "$log_file" ] || [ ! -f "$log_file" ]; then
        error "未找到日志文件"
        return 1
    fi

    log "正在查看日志: $log_file"
    tail -f "$log_file"
}

# 监控模式（自动重启）
monitor_crawler() {
    log "启动监控模式..."

    while true; do
        if ! check_running; then
            warn "检测到爬虫未运行，尝试自动重启..."
            if [ "$AUTO_RESTART" = true ]; then
                start_crawler
                if [ $? -eq 0 ]; then
                    log "自动重启成功，$CHECK_INTERVAL秒后继续监控..."
                else
                    error "自动重启失败，$RESTART_DELAY秒后重试..."
                    sleep "$RESTART_DELAY"
                    continue
                fi
            else
                warn "自动重启已禁用，退出监控"
                break
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|monitor|help}"
    echo ""
    echo "命令:"
    echo "  start    - 启动爬虫（后台运行）"
    echo "  stop     - 停止爬虫"
    echo "  restart  - 重启爬虫"
    echo "  status   - 查看运行状态"
    echo "  logs     - 查看实时日志"
    echo "  monitor  - 监控模式（自动重启）"
    echo "  help     - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动爬虫"
    echo "  $0 status          # 查看状态"
    echo "  $0 logs            # 查看最新日志"
    echo "  $0 logs /path/to/log  # 查看指定日志"
    echo "  $0 monitor         # 启动监控模式"
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
        "restart")
            restart_crawler
            ;;
        "status")
            show_status
            ;;
        "logs")
            tail_logs "$2"
            ;;
        "monitor")
            monitor_crawler
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

# 检查依赖
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
    error "未找到 $PYTHON_CMD 命令"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/$CRAWLER_SCRIPT" ]; then
    error "未找到爬虫脚本: $PROJECT_DIR/$CRAWLER_SCRIPT"
    exit 1
fi

# 执行主函数
main "$@"