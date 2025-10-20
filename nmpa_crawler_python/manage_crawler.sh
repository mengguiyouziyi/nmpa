#!/bin/bash

# NMPA Python爬虫综合管理脚本
# 集成进程管理、日志管理、监控和统计功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PID_FILE="$PROJECT_DIR/crawler.pid"
LOG_DIR="$PROJECT_DIR/logs"
OUTPUTS_DIR="$PROJECT_DIR/outputs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 状态图标
ICON_RUNNING="✅"
ICON_STOPPED="❌"
ICON_WARNING="⚠️"
ICON_INFO="ℹ️"
ICON_DATA="📊"
ICON_LOG="📄"

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

# 检查是否在运行
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

# 获取进程状态
get_process_status() {
    if check_running; then
        local pid=$(cat "$PID_FILE")
        local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | tr -d ' ' || echo "0")
        local mem=$(ps -p "$pid" -o %mem= 2>/dev/null | tr -d ' ' || echo "0")
        local runtime=$(ps -p "$pid" -o etime= 2>/dev/null | tr -d ' ' || echo "未知")

        echo "🟢 运行中"
        echo "   PID: $pid"
        echo "   CPU使用率: ${cpu}%"
        echo "   内存使用: ${mem}%"
        echo "   运行时长: $runtime"
    else
        echo "🔴 未运行"
        return 1
    fi
}

# 显示仪表板
show_dashboard() {
    clear
    echo "========================================"
    echo "    NMPA Python爬虫监控仪表板"
    echo "========================================"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 进程状态
    echo "🔄 进程状态"
    echo "-----------"
    if get_process_status; then
        echo ""
    else
        echo ""
    fi

    # 数据统计
    echo ""
    echo "$ICON_DATA 数据统计"
    echo "-----------"
    if [ -d "$OUTPUTS_DIR" ]; then
        local file_count=$(find "$OUTPUTS_DIR" -name "*.jsonl" 2>/dev/null | wc -l)
        local total_records=0

        if [ "$file_count" -gt 0 ]; then
            total_records=$(find "$OUTPUTS_DIR" -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
        fi

        echo "输出文件数: $file_count"
        echo "总记录数: $total_records"

        # 显示最新的几个文件
        if [ "$file_count" -gt 0 ]; then
            echo ""
            echo "最新输出文件:"
            find "$OUTPUTS_DIR" -name "*.jsonl" -type f -printf "%TY-%Tm-%Td %TH:%TM %p\n" 2>/dev/null | sort -r | head -3 | while read -r line; do
                local file=$(echo "$line" | awk '{for(i=3;i<=NF;i++) printf $i" "; print ""}')
                local records=$(wc -l < "$file" 2>/dev/null || echo "0")
                local size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "0")
                echo "  📄 $(basename "$file") ($records 记录, $size)"
            done
        fi
    else
        echo "输出目录不存在"
    fi

    # 日志状态
    echo ""
    echo "$ICON_LOG 日志状态"
    echo "-----------"
    if [ -d "$LOG_DIR" ]; then
        local log_count=$(ls -1 "$LOG_DIR"/crawler_*.log 2>/dev/null | wc -l)
        local log_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0")

        echo "活跃日志文件: $log_count"
        echo "日志总大小: $log_size"

        if [ "$log_count" -gt 0 ]; then
            local latest_log=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)
            if [ -f "$latest_log" ]; then
                local log_size=$(du -h "$latest_log" 2>/dev/null | cut -f1 || echo "0")
                local last_modified=$(stat -c %y "$latest_log" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
                echo ""
                echo "最新日志:"
                echo "  📄 $(basename "$latest_log")"
                echo "  📏 大小: $log_size"
                echo "  🕒 更新: $last_modified"
            fi
        fi
    else
        echo "日志目录不存在"
    fi

    # 系统资源
    echo ""
    echo "💻 系统资源"
    echo "-----------"
    echo "系统负载: $(uptime | awk -F'load average:' '{print $2}' | tr -d ' ')"
    echo "内存使用: $(free -h | awk '/^Mem:/ {printf "%s/%s (%.0f%%)", $3,$2,$3*100/$2}')"
    echo "磁盘使用: $(df -h "$PROJECT_DIR" | awk 'NR==2 {printf "%s/%s (%s)", $3,$2,$5}')"

    echo ""
    echo "========================================"
    echo "按 Ctrl+C 退出，按 r 刷新，输入命令执行操作"
    echo "可用命令: start, stop, restart, status, logs, clean, help"
}

# 交互式监控
interactive_monitor() {
    show_dashboard

    while true; do
        echo ""
        read -p "命令> " -t 10 cmd || continue

        case "$cmd" in
            "r"|"refresh")
                show_dashboard
                ;;
            "start")
                start_crawler
                sleep 2
                show_dashboard
                ;;
            "stop")
                stop_crawler
                sleep 2
                show_dashboard
                ;;
            "restart")
                restart_crawler
                sleep 2
                show_dashboard
                ;;
            "status")
                if check_running; then
                    echo "🟢 爬虫正在运行"
                else
                    echo "🔴 爬虫未运行"
                fi
                ;;
            "logs")
                echo "打开日志查看器..."
                ./log_manager.sh follow
                ;;
            "clean")
                echo "清理工具..."
                ./log_manager.sh cleanup
                ;;
            "help")
                echo "可用命令:"
                echo "  start   - 启动爬虫"
                echo "  stop    - 停止爬虫"
                echo "  restart - 重启爬虫"
                echo "  status  - 查看状态"
                echo "  logs    - 查看日志"
                echo "  clean   - 清理日志"
                echo "  r       - 刷新仪表板"
                echo "  help    - 显示帮助"
                ;;
            "")
                # 超时后自动刷新
                show_dashboard
                ;;
            *)
                echo "未知命令: $cmd (输入 help 查看帮助)"
                ;;
        esac
    done
}

# 启动爬虫（调用后台脚本）
start_crawler() {
    ./run_background.sh start
}

# 停止爬虫（调用后台脚本）
stop_crawler() {
    ./run_background.sh stop
}

# 重启爬虫（调用后台脚本）
restart_crawler() {
    ./run_background.sh restart
}

# 快速状态
show_status() {
    echo "=== NMPA爬虫快速状态 ==="
    if get_process_status; then
        echo ""
    else
        echo ""
    fi

    # 快速数据统计
    if [ -d "$OUTPUTS_DIR" ]; then
        local file_count=$(find "$OUTPUTS_DIR" -name "*.jsonl" 2>/dev/null | wc -l)
        local total_records=0
        if [ "$file_count" -gt 0 ]; then
            total_records=$(find "$OUTPUTS_DIR" -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
        fi
        echo "📊 数据: $file_count 文件, $total_records 记录"
    fi

    # 快速日志状态
    if [ -d "$LOG_DIR" ]; then
        local latest_log=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)
        if [ -f "$latest_log" ]; then
            local last_line=$(tail -1 "$latest_log" 2>/dev/null)
            echo "📄 最新日志: $last_line"
        fi
    fi
}

# 健康检查
health_check() {
    echo "=== NMPA爬虫健康检查 ==="

    local issues=0

    # 检查进程
    echo "🔍 检查进程状态..."
    if check_running; then
        echo "✅ 进程运行正常"
    else
        echo "❌ 进程未运行"
        ((issues++))
    fi

    # 检查日志
    echo "🔍 检查日志系统..."
    if [ -d "$LOG_DIR" ] && [ "$(ls -A "$LOG_DIR" 2>/dev/null)" ]; then
        echo "✅ 日志系统正常"

        # 检查最近是否有错误
        local latest_log=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)
        if [ -f "$latest_log" ]; then
            local error_count=$(grep -ci "error\|错误\|失败\|异常" "$latest_log" 2>/dev/null || echo "0")
            if [ "$error_count" -gt 10 ]; then
                echo "⚠️ 最近日志中发现较多错误 ($error_count 个)"
                ((issues++))
            fi
        fi
    else
        echo "❌ 日志系统异常"
        ((issues++))
    fi

    # 检查输出
    echo "🔍 检查数据输出..."
    if [ -d "$OUTPUTS_DIR" ]; then
        local recent_files=$(find "$OUTPUTS_DIR" -name "*.jsonl" -mtime -1 2>/dev/null | wc -l)
        if [ "$recent_files" -gt 0 ]; then
            echo "✅ 数据输出正常"
        else
            echo "⚠️ 最近24小时无新数据输出"
            ((issues++))
        fi
    else
        echo "❌ 输出目录不存在"
        ((issues++))
    fi

    # 检查磁盘空间
    echo "🔍 检查磁盘空间..."
    local disk_usage=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$disk_usage" -lt 90 ]; then
        echo "✅ 磁盘空间充足"
    else
        echo "⚠️ 磁盘空间不足 (${disk_usage}%)"
        ((issues++))
    fi

    # 总结
    echo ""
    if [ "$issues" -eq 0 ]; then
        echo "🎉 系统健康状态良好"
        return 0
    else
        echo "⚠️ 发现 $issues 个问题需要关注"
        return 1
    fi
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫综合管理工具"
    echo ""
    echo "用法: $0 <command> [arguments]"
    echo ""
    echo "主要命令:"
    echo "  dashboard   - 显示监控仪表板"
    echo "  start       - 启动爬虫"
    echo "  stop        - 停止爬虫"
    echo "  restart     - 重启爬虫"
    echo "  status      - 快速状态查看"
    echo "  health      - 健康检查"
    echo ""
    echo "日志管理:"
    echo "  logs        - 查看实时日志"
    echo "  log-list    - 列出所有日志"
    echo "  log-search  - 搜索日志"
    echo "  log-clean   - 清理旧日志"
    echo ""
    echo "其他:"
    echo "  help        - 显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 dashboard     # 启动交互式监控"
    echo "  $0 status        # 快速查看状态"
    echo "  $0 health        # 系统健康检查"
    echo "  $0 logs          # 查看实时日志"
}

# 主函数
main() {
    case "${1:-}" in
        "dashboard"|"dash")
            interactive_monitor
            ;;
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
        "health")
            health_check
            ;;
        "logs")
            ./log_manager.sh follow
            ;;
        "log-list")
            ./log_manager.sh list
            ;;
        "log-search")
            ./log_manager.sh search "$2"
            ;;
        "log-clean")
            ./log_manager.sh cleanup "${2:-7}"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                show_help
            else
                echo "错误: 未知命令 '$1'"
                echo "使用 '$0 help' 查看帮助"
                exit 1
            fi
            ;;
    esac
}

# 检查依赖文件
for dep_file in "run_background.sh" "log_manager.sh"; do
    if [ ! -f "$PROJECT_DIR/$dep_file" ]; then
        error "缺少依赖文件: $dep_file"
        exit 1
    fi
done

# 执行主函数
main "$@"