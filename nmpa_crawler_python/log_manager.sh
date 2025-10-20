#!/bin/bash

# NMPA Python爬虫日志管理工具
# 提供日志查看、搜索、分析和清理功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
ARCHIVE_DIR="$LOG_DIR/archive"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# 确保目录存在
ensure_dirs() {
    mkdir -p "$LOG_DIR" "$ARCHIVE_DIR"
}

# 列出所有日志文件
list_logs() {
    echo "=== NMPA爬虫日志文件列表 ==="

    ensure_dirs

    echo ""
    echo "📂 活跃日志文件:"
    if [ -d "$LOG_DIR" ] && [ "$(ls -A "$LOG_DIR" 2>/dev/null)" ]; then
        ls -lh "$LOG_DIR"/crawler_*.log 2>/dev/null | while read -r line; do
            echo "  $line"
        done
    else
        echo "  (无活跃日志文件)"
    fi

    echo ""
    echo "📦 归档日志文件:"
    if [ -d "$ARCHIVE_DIR" ] && [ "$(ls -A "$ARCHIVE_DIR" 2>/dev/null)" ]; then
        ls -lh "$ARCHIVE_DIR"/*.gz 2>/dev/null | tail -10 | while read -r line; do
            echo "  $line"
        done
        local total_archived=$(ls -1 "$ARCHIVE_DIR"/*.gz 2>/dev/null | wc -l)
        echo "  ... (总计 $total_archived 个归档文件)"
    else
        echo "  (无归档日志文件)"
    fi

    echo ""
    echo "📊 日志统计:"
    local active_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "0")
    local archive_size=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1 || echo "0")
    echo "  活跃日志大小: $active_size"
    echo "  归档日志大小: $archive_size"
}

# 查看最新日志
show_latest() {
    local lines="${1:-50}"

    ensure_dirs

    local latest_log=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)

    if [ -z "$latest_log" ]; then
        error "未找到日志文件"
        return 1
    fi

    info "显示最新日志文件: $(basename "$latest_log")"
    echo "显示最后 $lines 行:"
    echo "----------------------------------------"

    tail -n "$lines" "$latest_log" | while IFS= read -r line; do
        # 根据日志级别添加颜色
        if [[ "$line" =~ ERROR|error|Error ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ "$line" =~ WARNING|warning|Warning ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ "$line" =~ SUCCESS|success|Success|完成|成功 ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ "$line" =~ INFO|info|Info ]]; then
            echo -e "${BLUE}$line${NC}"
        else
            echo "$line"
        fi
    done
}

# 实时跟踪日志
follow_log() {
    local log_file="$1"

    ensure_dirs

    if [ -z "$log_file" ]; then
        log_file=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)
    fi

    if [ -z "$log_file" ] || [ ! -f "$log_file" ]; then
        error "未找到日志文件: $log_file"
        return 1
    fi

    info "实时跟踪日志: $(basename "$log_file")"
    info "按 Ctrl+C 停止跟踪"
    echo "----------------------------------------"

    tail -f "$log_file" | while IFS= read -r line; do
        # 根据日志级别添加颜色
        if [[ "$line" =~ ERROR|error|Error|失败|异常 ]]; then
            echo -e "${RED}$(date '+%H:%M:%S') $line${NC}"
        elif [[ "$line" =~ WARNING|warning|Warning|警告|注意 ]]; then
            echo -e "${YELLOW}$(date '+%H:%M:%S') $line${NC}"
        elif [[ "$line" =~ SUCCESS|success|Success|完成|成功|✅ ]]; then
            echo -e "${GREEN}$(date '+%H:%M:%S') $line${NC}"
        elif [[ "$line" =~ INFO|info|Info|信息|📊|📄|🔍|🔄 ]]; then
            echo -e "${BLUE}$(date '+%H:%M:%S') $line${NC}"
        else
            echo "$(date '+%H:%M:%S') $line"
        fi
    done
}

# 搜索日志
search_logs() {
    local pattern="$1"
    local log_file="$2"

    if [ -z "$pattern" ]; then
        error "请提供搜索模式"
        echo "用法: $0 search <pattern> [log_file]"
        return 1
    fi

    ensure_dirs

    if [ -z "$log_file" ]; then
        # 搜索所有日志文件
        info "搜索模式: $pattern (在所有日志文件中)"
        echo "----------------------------------------"
        grep -n --color=always -r "$pattern" "$LOG_DIR"/crawler_*.log 2>/dev/null || echo "未找到匹配项"
    else
        if [ ! -f "$log_file" ]; then
            error "日志文件不存在: $log_file"
            return 1
        fi
        info "搜索模式: $pattern (在 $(basename "$log_file") 中)"
        echo "----------------------------------------"
        grep -n --color=always "$pattern" "$log_file" || echo "未找到匹配项"
    fi
}

# 分析日志统计
analyze_logs() {
    local hours="${1:-24}"  # 默认分析最近24小时

    ensure_dirs

    local latest_log=$(ls -t "$LOG_DIR"/crawler_*.log 2>/dev/null | head -1)

    if [ -z "$latest_log" ]; then
        error "未找到日志文件"
        return 1
    fi

    info "分析日志文件: $(basename "$latest_log")"
    info "时间范围: 最近 $hours 小时"
    echo "========================================"

    # 时间戳过滤（最近N小时）
    local since_time=$(date -d "$hours hours ago" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -v-"$hours"H '+%Y-%m-%d %H:%M:%S')

    echo "📊 统计摘要:"
    echo "  总日志行数: $(grep -c '' "$latest_log" 2>/dev/null || echo "0")"
    echo "  错误数量: $(grep -ci "error\|错误\|失败\|异常" "$latest_log" 2>/dev/null || echo "0")"
    echo "  警告数量: $(grep -ci "warning\|警告\|注意" "$latest_log" 2>/dev/null || echo "0")"
    echo "  成功数量: $(grep -ci "success\|成功\|完成\|✅" "$latest_log" 2>/dev/null || echo "0")"

    echo ""
    echo "📈 爬取统计:"
    echo "  段处理总数: $(grep -c "使用当前检索段" "$latest_log" 2>/dev/null || echo "0")"
    echo "  数据写入次数: $(grep -c "成功写入" "$latest_log" 2>/dev/null || echo "0")"
    echo "  重试次数: $(grep -c "重试" "$latest_log" 2>/dev/null || echo "0")"

    echo ""
    echo "🔄 最近活动 (最后10条):"
    tail -10 "$latest_log" | while IFS= read -r line; do
        echo "  $line"
    done

    echo ""
    echo "⚠️  错误摘要 (最后5个错误):"
    grep -i "error\|错误\|失败\|异常" "$latest_log" | tail -5 | while IFS= read -r line; do
        echo "  $line"
    done
}

# 清理日志
cleanup_logs() {
    local days="${1:-7}"  # 默认保留7天
    local force="${2:-false}"  # 是否强制删除

    ensure_dirs

    info "清理超过 $days 天的日志文件"

    if [ "$force" != "true" ]; then
        echo "将要删除以下文件:"
        find "$LOG_DIR" -name "crawler_*.log" -mtime +$days -ls 2>/dev/null
        find "$ARCHIVE_DIR" -name "*.gz" -mtime +$days -ls 2>/dev/null

        echo ""
        read -p "确认删除? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "取消删除操作"
            return 0
        fi
    fi

    local deleted_files=0

    # 删除旧的活跃日志
    while IFS= read -r -d '' file; do
        echo "删除: $(basename "$file")"
        rm -f "$file"
        ((deleted_files++))
    done < <(find "$LOG_DIR" -name "crawler_*.log" -mtime +$days -print0 2>/dev/null)

    # 删除旧的归档日志
    while IFS= read -r -d '' file; do
        echo "删除: $(basename "$file")"
        rm -f "$file"
        ((deleted_files++))
    done < <(find "$ARCHIVE_DIR" -name "*.gz" -mtime +$days -print0 2>/dev/null)

    echo "已删除 $deleted_files 个文件"
}

# 导出日志
export_logs() {
    local output_file="$1"
    local days="${2:-7}"  # 默认导出最近7天

    if [ -z "$output_file" ]; then
        output_file="nmpa_crawler_logs_$(date +%Y%m%d_%H%M%S).tar.gz"
    fi

    ensure_dirs

    info "导出最近 $days 天的日志到: $output_file"

    # 创建临时目录
    local temp_dir=$(mktemp -d)

    # 复制最近的日志文件
    find "$LOG_DIR" -name "crawler_*.log" -mtime -$days -exec cp {} "$temp_dir/" \;
    find "$ARCHIVE_DIR" -name "*.gz" -mtime -$days -exec cp {} "$temp_dir/" \;

    # 创建日志摘要
    {
        echo "NMPA Python爬虫日志导出"
        echo "导出时间: $(date)"
        echo "时间范围: 最近 $days 天"
        echo "==================="
        echo ""
        echo "包含的文件:"
        ls -la "$temp_dir/"
        echo ""
        echo "基本统计:"
        for file in "$temp_dir"/*.log "$temp_dir"/*.gz; do
            if [ -f "$file" ]; then
                local filename=$(basename "$file")
                local line_count
                if [[ "$file" == *.gz ]]; then
                    line_count=$(zcat "$file" | wc -l)
                else
                    line_count=$(wc -l < "$file")
                fi
                echo "  $filename: $line_count 行"
            fi
        done
    } > "$temp_dir/README.txt"

    # 压缩导出
    tar -czf "$output_file" -C "$temp_dir" .

    # 清理临时目录
    rm -rf "$temp_dir"

    echo "导出完成: $output_file"
}

# 显示帮助
show_help() {
    echo "NMPA Python爬虫日志管理工具"
    echo ""
    echo "用法: $0 <command> [arguments]"
    echo ""
    echo "命令:"
    echo "  list                    - 列出所有日志文件"
    echo "  latest [lines]          - 显示最新日志 (默认50行)"
    echo "  follow [log_file]       - 实时跟踪日志"
    echo "  search <pattern> [file] - 搜索日志内容"
    echo "  analyze [hours]         - 分析日志统计 (默认24小时)"
    echo "  cleanup [days]          - 清理旧日志 (默认7天)"
    echo "  cleanup-force [days]    - 强制清理旧日志"
    echo "  export [output] [days]  - 导出日志 (默认7天)"
    echo "  help                    - 显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 list                 # 列出所有日志文件"
    echo "  $0 latest 100           # 显示最新100行日志"
    echo "  $0 follow               # 实时跟踪最新日志"
    echo "  $0 search 'error'       # 搜索包含error的日志"
    echo "  $0 analyze 48           # 分析最近48小时的日志"
    echo "  $0 cleanup 30           # 清理30天前的日志"
    echo "  $0 export logs.tar.gz   # 导出最近7天的日志"
}

# 主函数
main() {
    case "${1:-}" in
        "list")
            list_logs
            ;;
        "latest")
            show_latest "${2:-50}"
            ;;
        "follow")
            follow_log "$2"
            ;;
        "search")
            search_logs "$2" "$3"
            ;;
        "analyze")
            analyze_logs "${2:-24}"
            ;;
        "cleanup")
            cleanup_logs "${2:-7}" false
            ;;
        "cleanup-force")
            cleanup_logs "${2:-7}" true
            ;;
        "export")
            export_logs "$2" "${3:-7}"
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