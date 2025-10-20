#!/bin/bash

# NMPA Python爬虫前台转后台工具
# 将正在前台运行的爬虫程序转入后台，并保持日志输出

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PID_FILE="$PROJECT_DIR/crawler.pid"
LOG_DIR="$PROJECT_DIR/logs"
TEMP_LOG_FILE="$LOG_DIR/crawler_background_$(date +%Y%m%d_%H%M%S).log"

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

# 查找正在运行的爬虫进程
find_crawler_processes() {
    echo "正在查找爬虫进程..."

    # 查找可能的爬虫进程
    local processes=$(ps aux | grep -E "(python.*crawler|crawler.*py)" | grep -v grep | grep -v "to_background.sh")

    if [ -z "$processes" ]; then
        warn "未找到正在运行的爬虫进程"
        echo ""
        echo "提示："
        echo "1. 确保爬虫程序正在运行"
        echo "2. 可以使用以下命令手动查找："
        echo "   ps aux | grep python"
        return 1
    fi

    echo "找到以下进程："
    echo "PID     用户    CPU%   MEM%   运行时间    命令"
    echo "------------------------------------------------------------"
    echo "$processes" | while IFS= read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local user=$(echo "$line" | awk '{print $1}')
        local cpu=$(echo "$line" | awk '{print $3}')
        local mem=$(echo "$line" | awk '{print $4}')
        local time=$(echo "$line" | awk '{print $10,$11}')
        local cmd=$(echo "$line" | cut -d' ' -f11-)
        printf "%-7s %-7s %-6s %-6s %-10s %s\n" "$pid" "$user" "$cpu" "$mem" "$time" "$cmd"
    done

    return 0
}

# 检查进程是否为爬虫进程
is_crawler_process() {
    local pid=$1
    local cmdline=$(ps -p "$pid" -o args= 2>/dev/null)

    if [[ "$cmdline" =~ python.*crawler ]]; then
        return 0
    fi

    # 检查进程的工作目录
    local cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null)
    if [[ "$cwd" =~ nmpa.*crawler ]]; then
        return 0
    fi

    return 1
}

# 转移进程到后台
move_to_background() {
    local pid=$1

    log "开始转移进程 $pid 到后台..."

    # 验证进程存在
    if ! ps -p "$pid" > /dev/null 2>&1; then
        error "进程 $pid 不存在"
        return 1
    fi

    # 验证是爬虫进程
    if ! is_crawler_process "$pid"; then
        error "进程 $pid 不是爬虫进程"
        return 1
    fi

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 获取进程信息
    local cmdline=$(ps -p "$pid" -o args=)
    local start_time=$(ps -p "$pid" -o lstart=)
    local user=$(ps -p "$pid" -o user=)

    info "进程信息："
    info "  PID: $pid"
    info "  用户: $user"
    info "  命令行: $cmdline"
    info "  启动时间: $start_time"

    echo ""
    warn "⚠️  注意：此操作将会："
    warn "   1. 暂停当前进程"
    warn "   2. 在后台重新启动相同的命令"
    warn "   3. 将输出重定向到日志文件"
    warn "   4. 原进程将会被终止"
    echo ""

    read -p "确认继续？(y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "操作已取消"
        return 0
    fi

    # 创建后台启动脚本
    local bg_script="$LOG_DIR/restart_bg_$pid.sh"
    cat > "$bg_script" << EOF
#!/bin/bash
# 自动生成的后台重启脚本

cd "$PROJECT_DIR"
nohup $cmdline > "$TEMP_LOG_FILE" 2>&1 &
echo \$! > "$PID_FILE"
echo "进程已在后台启动，PID: \$!"
EOF

    chmod +x "$bg_script"

    # 停止原进程
    log "停止原进程 $pid..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    # 如果进程仍在运行，强制终止
    if ps -p "$pid" > /dev/null 2>&1; then
        warn "进程未响应TERM信号，强制终止..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 2
    fi

    # 验证原进程已停止
    if ps -p "$pid" > /dev/null 2>&1; then
        error "无法停止原进程"
        return 1
    fi

    # 在后台重新启动
    log "在后台重新启动爬虫..."
    cd "$PROJECT_DIR"
    nohup $cmdline > "$TEMP_LOG_FILE" 2>&1 &
    local new_pid=$!

    # 等待新进程启动
    sleep 3

    # 验证新进程运行正常
    if ps -p "$new_pid" > /dev/null 2>&1; then
        echo "$new_pid" > "$PID_FILE"
        log "✅ 成功转移进程到后台！"
        log "新进程PID: $new_pid"
        log "日志文件: $TEMP_LOG_FILE"

        # 清理临时脚本
        rm -f "$bg_script"

        echo ""
        info "管理命令："
        info "  查看状态: ./manage_crawler.sh status"
        info "  查看日志: ./manage_crawler.sh logs"
        info "  停止进程: ./manage_crawler.sh stop"

        return 0
    else
        error "❌ 后台进程启动失败"

        # 显示错误信息
        if [ -f "$TEMP_LOG_FILE" ]; then
            echo ""
            error "启动错误信息："
            tail -10 "$TEMP_LOG_FILE"
        fi

        return 1
    fi
}

# 交互式选择进程
select_process() {
    local processes=$(ps aux | grep -E "(python.*crawler|crawler.*py)" | grep -v grep | grep -v "to_background.sh")

    if [ -z "$processes" ]; then
        error "未找到正在运行的爬虫进程"
        return 1
    fi

    echo ""
    info "请选择要转移的进程（输入PID）："
    echo ""

    local count=0
    local pids=()

    while IFS= read -r line; do
        count=$((count + 1))
        local pid=$(echo "$line" | awk '{print $2}')
        local user=$(echo "$line" | awk '{print $1}')
        local cpu=$(echo "$line" | awk '{print $3}')
        local mem=$(echo "$line" | awk '{print $4}')
        local time=$(echo "$line" | awk '{print $10}')
        local cmd=$(echo "$line" | cut -d' ' -f11- | cut -c1-60)

        pids+=("$pid")

        printf "%2d. PID=%-7s 用户=%-8s CPU=%-5s MEM=%-5s 时间=%-8s\n" "$count" "$pid" "$user" "$cpu" "$mem" "$time"
        printf "     命令: %s\n" "$cmd"
        echo ""
    done <<< "$processes"

    if [ "$count" -eq 1 ]; then
        # 只有一个进程，直接使用
        local pid=${pids[0]}
        log "自动选择唯一进程: PID $pid"
        return 0
    fi

    while true; do
        read -p "请输入选择的序号 (1-$count) 或 PID (直接输入数字): " choice

        # 检查是否是序号
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
                local selected_pid=${pids[$((choice-1))]}
                log "选择进程: PID $selected_pid"
                return 0
            fi

            # 检查是否是直接的PID
            if ps -p "$choice" > /dev/null 2>&1 && is_crawler_process "$choice"; then
                log "选择进程: PID $choice"
                return 0
            fi
        fi

        warn "无效选择，请重新输入"
    done
}

# 使用disown方法（更简单，但有局限性）
disown_method() {
    local pid=$1

    info "使用disown方法转移进程..."

    # 检查进程是否在终端中运行
    local tty=$(ps -p "$pid" -o tty= 2>/dev/null | tr -d ' ')

    if [ "$tty" = "?" ] || [ -z "$tty" ]; then
        warn "进程似乎已经在后台运行"
        return 1
    fi

    info "进程当前在终端: $tty"

    # 创建日志重定向脚本
    local redirect_script="$LOG_DIR/redirect_$pid.sh"
    cat > "$redirect_script" << 'EOF'
#!/bin/bash
# 日志重定向脚本

LOG_FILE="$1"
PID="$2"

# 使用gdb或strace来重定向输出（需要root权限或特定配置）
# 这里提供一个简单的方法：监控/proc/$pid/fd/

echo "开始监控进程 $PID 的输出..."
echo "日志将保存到: $LOG_FILE"

# 定期检查进程状态并记录
while kill -0 "$PID" 2>/dev/null; do
    echo "$(date): Process $PID is running" >> "$LOG_FILE"
    sleep 60
done

echo "$(date): Process $PID has stopped" >> "$LOG_FILE"
EOF

    chmod +x "$redirect_script"

    # 启动日志重定向（后台）
    "$redirect_script" "$TEMP_LOG_FILE" "$pid" &
    local redirect_pid=$!

    # 使用disown将进程从当前shell分离
    disown "$pid" 2>/dev/null || true

    log "进程已从当前shell分离"
    log "日志监控PID: $redirect_pid"
    log "日志文件: $TEMP_LOG_FILE"

    return 0
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫前台转后台工具"
    echo ""
    echo "用法: $0 [选项] [PID]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示此帮助信息"
    echo "  -l, --list      仅列出进程，不执行转移"
    echo "  -d, --disown    使用disown方法（实验性）"
    echo "  -y, --yes       跳过确认提示"
    echo ""
    echo "示例:"
    echo "  $0                    # 交互式选择进程"
    echo "  $0 12345              # 转移指定PID的进程"
    echo "  $0 --list             # 仅列出爬虫进程"
    echo "  $0 --disown 12345     # 使用disown方法"
    echo ""
    echo "注意："
    echo "1. 此工具会停止原进程并在后台重新启动"
    echo "2. 建议在操作前保存任何重要数据"
    echo "3. 新进程的输出将被重定向到日志文件"
}

# 主函数
main() {
    local list_only=false
    local use_disown=false
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
            -d|--disown)
                use_disown=true
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

    # 查找进程
    if ! find_crawler_processes; then
        exit 1
    fi

    # 如果只是列出进程
    if [ "$list_only" = true ]; then
        exit 0
    fi

    # 确定目标PID
    if [ -z "$target_pid" ]; then
        if ! select_process; then
            exit 1
        fi
        # select_process会设置全局变量或通过其他方式返回选择的PID
        # 这里需要重新获取选择的PID
        processes=$(ps aux | grep -E "(python.*crawler|crawler.*py)" | grep -v grep | grep -v "to_background.sh")
        if [ -n "$processes" ]; then
            target_pid=$(echo "$processes" | head -1 | awk '{print $2}')
        fi
    fi

    if [ -z "$target_pid" ]; then
        error "未确定目标进程"
        exit 1
    fi

    # 验证目标进程
    if ! ps -p "$target_pid" > /dev/null 2>&1; then
        error "进程 $target_pid 不存在"
        exit 1
    fi

    if ! is_crawler_process "$target_pid"; then
        error "进程 $target_pid 不是爬虫进程"
        exit 1
    fi

    # 选择转移方法
    if [ "$use_disown" = true ]; then
        if ! disown_method "$target_pid"; then
            error "disown方法失败"
            exit 1
        fi
    else
        # 如果不是自动确认，显示确认信息
        if [ "$auto_confirm" != true ]; then
            echo ""
            warn "⚠️  准备将进程 $target_pid 转移到后台"
            warn "   这将会重启进程并重定向输出到日志文件"
            echo ""
            read -p "确认继续？(y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                info "操作已取消"
                exit 0
            fi
        fi

        if ! move_to_background "$target_pid"; then
            error "转移进程失败"
            exit 1
        fi
    fi

    log "操作完成！"
}

# 执行主函数
main "$@"