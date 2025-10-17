#!/bin/bash

# NMPA 爬虫监控脚本

set -e

echo "📊 NMPA 爬虫监控"
echo "==============="

cd "$(dirname "$0")"

PID_FILE="crawler.pid"

# 检查进程状态
if [ -f "$PID_FILE" ]; then
    CRAWLER_PID=$(cat "$PID_FILE")
    if ps -p "$CRAWLER_PID" > /dev/null 2>&1; then
        echo "✅ 爬虫正在运行 (PID: $CRAWLER_PID)"

        # 显示进程信息
        echo ""
        echo "📋 进程信息:"
        ps -p "$CRAWLER_PID" -o pid,ppid,cmd,etime,pcpu,pmem --no-headers

        # 显示资源使用
        echo ""
        echo "💾 内存使用:"
        if command -v free &> /dev/null; then
            free -h
        fi

    else
        echo "❌ 爬虫未运行 (PID 文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
else
    echo "❌ 爬虫未运行 (无 PID 文件)"
fi

# 检查日志文件
echo ""
echo "📝 日志文件:"
ls -lh crawler_*.log 2>/dev/null | head -5 || echo "无日志文件"

# 检查输出文件
echo ""
echo "📂 输出文件:"
if [ -d "outputs/datasets" ]; then
    echo "数据集文件:"
    ls -lh outputs/datasets/*.jsonl 2>/dev/null | while read -r line; do
        filename=$(echo "$line" | awk '{print $9}')
        size=$(echo "$line" | awk '{print $5}')
        lines=$(wc -l < "$filename" 2>/dev/null || echo "0")
        echo "  $(basename "$filename"): $size ($lines 条记录)"
    done
else
    echo "输出目录不存在"
fi

# 显示最新日志
echo ""
echo "📋 最新日志 (最近20行):"
echo "----------------------------------------"
LATEST_LOG=$(ls -t crawler_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "日志文件: $LATEST_LOG"
    tail -20 "$LATEST_LOG"
else
    echo "无日志文件"
fi
echo "----------------------------------------"

# 提供常用命令
echo ""
echo "🔧 常用命令:"
echo "  启动爬虫: ./run_optimized_crawler.sh"
echo "  停止爬虫: ./stop_crawler.sh"
echo "  实时日志: tail -f crawler_*.log"
echo "  检查输出: ls -la outputs/datasets/"