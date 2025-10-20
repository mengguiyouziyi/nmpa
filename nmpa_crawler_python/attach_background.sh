#!/bin/bash

# NMPA Python爬虫后台附加工具
# 使用screen或tmux会话来管理运行中的程序

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="$PROJECT_DIR/logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

# 检查screen或tmux是否可用
check_tools() {
    if command -v screen >/dev/null 2>&1; then
        echo "screen"
    elif command -v tmux >/dev/null 2>&1; then
        echo "tmux"
    else
        echo "none"
    fi
}

# 使用screen方法
screen_method() {
    local pid=$1
    local session_name="nmpa_crawler_$(date +%H%M%S)"

    info "使用screen创建后台会话..."
    info "会话名称: $session_name"

    # 检查进程是否存在
    if ! ps -p "$pid" > /dev/null 2>&1; then
        error "进程 $pid 不存在"
        return 1
    fi

    # 获取进程的命令行
    local cmdline=$(ps -p "$pid" -o args=)
    local cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null)

    info "当前进程信息："
    info "  PID: $pid"
    info "  工作目录: $cwd"
    info "  命令: $cmdline"

    echo ""
    warn "⚠️  此操作将会："
    warn "   1. 创建新的screen会话"
    warn "   2. 停止当前进程"
    warn "   3. 在screen会话中重新启动"
    warn "   4. 可以随时重新连接到会话"
    echo ""

    read -p "确认继续？(y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "操作已取消"
        return 0
    fi

    # 停止当前进程
    log "停止当前进程 $pid..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    # 创建screen会话并启动进程
    log "创建screen会话并启动爬虫..."
    cd "$PROJECT_DIR"

    # 使用screen -dmS 创建分离的会话，并在其中运行命令
    screen -dmS "$session_name" bash -c "
        cd '$PROJECT_DIR'
        $cmdline 2>&1 | tee '$LOG_DIR/crawler_screen_$(date +%Y%m%d_%H%M%S).log'
        echo '进程已退出，按任意键关闭会话...'
        read -n 1
    "

    # 等待一会儿让screen启动
    sleep 2

    # 检查screen会话是否创建成功
    if screen -list | grep -q "$session_name"; then
        log "✅ 成功创建screen会话！"
        echo ""
        info "会话管理命令："
        info "  查看所有会话: screen -ls"
        info "  重新连接会话: screen -r $session_name"
        info "  分离会话: 在会话中按 Ctrl+A 然后按 D"
        info "  终止会话: screen -X -S $session_name quit"
        echo ""
        info "查看会话日志："
        info "  ls -la $LOG_DIR/crawler_screen_*.log"
        info "  tail -f $LOG_DIR/crawler_screen_*.log"

        return 0
    else
        error "❌ 创建screen会话失败"
        return 1
    fi
}

# 使用tmux方法
tmux_method() {
    local pid=$1
    local session_name="nmpa_crawler_$(date +%H%M%S)"

    info "使用tmux创建后台会话..."
    info "会话名称: $session_name"

    # 检查进程是否存在
    if ! ps -p "$pid" > /dev/null 2>&1; then
        error "进程 $pid 不存在"
        return 1
    fi

    # 获取进程的命令行
    local cmdline=$(ps -p "$pid" -o args=)

    info "当前进程信息："
    info "  PID: $pid"
    info "  命令: $cmdline"

    echo ""
    warn "⚠️  此操作将会："
    warn "   1. 创建新的tmux会话"
    warn "   2. 停止当前进程"
    warn "   3. 在tmux会话中重新启动"
    warn "   4. 可以随时重新连接到会话"
    echo ""

    read -p "确认继续？(y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "操作已取消"
        return 0
    fi

    # 停止当前进程
    log "停止当前进程 $pid..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    # 创建tmux会话并启动进程
    log "创建tmux会话并启动爬虫..."
    cd "$PROJECT_DIR"

    # 使用tmux new-session -d 创建分离的会话
    tmux new-session -d -s "$session_name" "
        cd '$PROJECT_DIR'
        $cmdline 2>&1 | tee '$LOG_DIR/crawler_tmux_$(date +%Y%m%d_%H%M%S).log'
        echo '进程已退出，按任意键关闭会话...'
        read -n 1
    "

    # 等待一会儿让tmux启动
    sleep 2

    # 检查tmux会话是否创建成功
    if tmux list-sessions | grep -q "$session_name"; then
        log "✅ 成功创建tmux会话！"
        echo ""
        info "会话管理命令："
        info "  查看所有会话: tmux list-sessions"
        info "  重新连接会话: tmux attach -t $session_name"
        info "  分离会话: 在会话中按 Ctrl+B 然后按 D"
        info "  终止会话: tmux kill-session -t $session_name"
        echo ""
        info "查看会话日志："
        info "  ls -la $LOG_DIR/crawler_tmux_*.log"
        info "  tail -f $LOG_DIR/crawler_tmux_*.log"

        return 0
    else
        error "❌ 创建tmux会话失败"
        return 1
    fi
}

# 使用nohup重定向方法（简单方法）
nohup_redirect_method() {
    local pid=$1

    info "使用nohup重定向方法..."

    # 检查进程是否存在
    if ! ps -p "$pid" > /dev/null 2>&1; then
        error "进程 $pid 不存在"
        return 1
    fi

    # 获取进程信息
    local cmdline=$(ps -p "$pid" -o args=)
    local log_file="$LOG_DIR/crawler_nohup_$(date +%Y%m%d_%H%M%S).log"

    info "当前进程信息："
    info "  PID: $pid"
    info "  命令: $cmdline"
    info "  日志文件: $log_file"

    echo ""
    warn "⚠️  此方法将会："
    warn "   1. 停止当前进程"
    warn "   2. 使用nohup在后台重新启动"
    warn "   3. 将输出重定向到日志文件"
    warn "   4. 原进程的所有输出将被保存到日志"
    echo ""

    read -p "确认继续？(y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "操作已取消"
        return 0
    fi

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 停止当前进程
    log "停止当前进程 $pid..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    # 在后台重新启动
    log "使用nohup在后台重新启动..."
    cd "$PROJECT_DIR"
    nohup $cmdline > "$log_file" 2>&1 &
    local new_pid=$!

    # 等待新进程启动
    sleep 3

    # 验证新进程运行正常
    if ps -p "$new_pid" > /dev/null 2>&1; then
        echo "$new_pid" > "$PROJECT_DIR/crawler.pid"
        log "✅ 成功转移进程到后台！"
        log "新进程PID: $new_pid"
        log "日志文件: $log_file"
        echo ""
        info "管理命令："
        info "  查看状态: ./manage_crawler.sh status"
        info "  查看日志: tail -f $log_file"
        info "  停止进程: ./manage_crawler.sh stop"

        return 0
    else
        error "❌ 后台进程启动失败"

        # 显示错误信息
        if [ -f "$log_file" ]; then
            echo ""
            error "启动错误信息："
            tail -10 "$log_file"
        fi

        return 1
    fi
}

# 列出可用的会话
list_sessions() {
    echo "=== 查看现有的后台会话 ==="

    # 检查screen会话
    if command -v screen >/dev/null 2>&1; then
        echo ""
        info "🖥️  Screen会话："
        if screen -list 2>/dev/null | grep -q "No Sockets"; then
            echo "   (无screen会话)"
        else
            screen -list 2>/dev/null | grep -E "[0-9]+\." | while read -r line; do
                echo "   $line"
            done
        fi
    fi

    # 检查tmux会话
    if command -v tmux >/dev/null 2>&1; then
        echo ""
        info "🖥️  Tmux会话："
        local tmux_sessions=$(tmux list-sessions 2>/dev/null)
        if [ -z "$tmux_sessions" ]; then
            echo "   (无tmux会话)"
        else
            echo "$tmux_sessions" | while read -r line; do
                echo "   $line"
            done
        fi
    fi

    # 检查nohup进程
    echo ""
    info "🖥️  Nohup进程："
    local nohup_processes=$(ps aux | grep -E "nohup.*python.*crawler" | grep -v grep)
    if [ -z "$nohup_processes" ]; then
        echo "   (无nohup爬虫进程)"
    else
        echo "$nohup_processes" | while read -r line; do
            local pid=$(echo "$line" | awk '{print $2}')
            local cmd=$(echo "$line" | cut -d' ' -f11-)
            echo "   PID: $pid - $cmd"
        done
    fi

    echo ""
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫后台附加工具"
    echo ""
    echo "用法: $0 [选项] [PID]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示此帮助信息"
    echo "  -l, --list      列出现有的后台会话"
    echo "  -s, --screen    强制使用screen方法"
    echo "  -t, --tmux      强制使用tmux方法"
    echo "  -n, --nohup     强制使用nohup方法"
    echo "  -y, --yes       跳过确认提示"
    echo ""
    echo "示例:"
    echo "  $0                    # 自动选择最佳方法"
    echo "  $0 12345              # 转移指定PID的进程"
    echo "  $0 --list             # 列出现有会话"
    echo "  $0 --screen 12345     # 强制使用screen方法"
    echo ""
    echo "说明："
    echo "• screen方法: 创建可重新连接的终端会话，推荐使用"
    echo "• tmux方法: 类似screen，功能更强大"
    echo "• nohup方法: 简单的后台运行，输出重定向到文件"
}

# 主函数
main() {
    local list_only=false
    local force_method="auto"
    local auto_confirm=false
    local target_pid=""

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                list_only=true
                shift
                ;;
            -s|--screen)
                force_method="screen"
                shift
                ;;
            -t|--tmux)
                force_method="tmux"
                shift
                ;;
            -n|--nohup)
                force_method="nohup"
                shift
                ;;
            -y|--yes)
                auto_confirm=true
                shift
                ;;
            -*)
                error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ "$1" =~ ^[0-9]+$ ]]; then
                    target_pid="$1"
                else
                    error "无效的PID: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # 如果只是列出会话
    if [ "$list_only" = true ]; then
        list_sessions
        exit 0
    fi

    # 确定目标PID
    if [ -z "$target_pid" ]; then
        error "请指定要转移的进程PID"
        echo "使用 '$0 --list' 查看运行中的进程"
        exit 1
    fi

    # 验证目标进程
    if ! ps -p "$target_pid" > /dev/null 2>&1; then
        error "进程 $target_pid 不存在"
        exit 1
    fi

    # 确定使用的方法
    if [ "$force_method" = "auto" ]; then
        local available_tool=$(check_tools)
        case "$available_tool" in
            "screen")
                force_method="screen"
                ;;
            "tmux")
                force_method="tmux"
                ;;
            *)
                force_method="nohup"
                warn "screen和tmux都不可用，使用nohup方法"
                ;;
        esac
    fi

    info "使用方法: $force_method"

    # 执行相应的方法
    case "$force_method" in
        "screen")
            if ! command -v screen >/dev/null 2>&1; then
                error "screen未安装，请先安装: sudo apt-get install screen"
                exit 1
            fi
            if ! screen_method "$target_pid"; then
                exit 1
            fi
            ;;
        "tmux")
            if ! command -v tmux >/dev/null 2>&1; then
                error "tmux未安装，请先安装: sudo apt-get install tmux"
                exit 1
            fi
            if ! tmux_method "$target_pid"; then
                exit 1
            fi
            ;;
        "nohup")
            if ! nohup_redirect_method "$target_pid"; then
                exit 1
            fi
            ;;
    esac

    log "操作完成！"
}

# 执行主函数
main "$@"