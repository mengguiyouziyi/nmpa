#!/bin/bash

# NMPA 爬虫优化执行脚本 v2.0
# 支持青果隧道代理，可配置并发，已修复PAGE_SIZE错误
#
# 使用方法:
#   ./run_optimized_crawler.sh [并发数] [数据集] [页大小] [代理开关]
#
# 参数说明:
#   并发数: 1-10 (默认: 5)
#   数据集: domestic-h,domestic-s,imported (默认: 全部)
#   页大小: 20-200 (默认: 100)
#   代理开关: true/false (默认: true)
#
# 示例:
#   ./run_optimized_crawler.sh                           # 默认配置
#   ./run_optimized_crawler.sh 3 domestic-h 50 true    # 3并发，仅国内H，50条/页，使用代理
#   ./run_optimized_crawler.sh 1 domestic-h 20 false   # 单并发测试，本地IP

set -e

echo "🚀 NMPA 爬虫启动 - 优化配置版本 v2.0"
echo "====================================="

# 进入项目目录
cd "$(dirname "$0")"

# 参数解析
CONCURRENCY=${1:-5}           # 默认并发数: 5
DATASETS=${2:-"domestic-h,domestic-s,imported"}  # 默认数据集
NORMALIZED_DATASETS=$(printf "%s" "$DATASETS" | tr "A-Z" "a-z")
if [ "$NORMALIZED_DATASETS" = "all" ]; then
    DATASETS="domestic-h,domestic-s,imported"
fi
PAGE_SIZE=${3:-100}          # 默认每页条数: 100
USE_PROXY=${4:-"true"}        # 默认使用代理

echo "📋 启动参数:"
echo "   - 并发数: $CONCURRENCY"
echo "   - 数据集: $DATASETS"
echo "   - 每页条数: $PAGE_SIZE"
echo "   - 使用代理: $USE_PROXY"
echo ""

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖包..."
    npm install
fi

# 检查Playwright浏览器
if ! command -v npx &> /dev/null || ! npx playwright --version &> /dev/null; then
    echo "🌐 安装 Playwright 浏览器..."
    npx playwright install chromium
fi

echo "⚙️  配置环境和优化参数..."

# 代理配置 (根据参数决定是否启用)
if [ "$USE_PROXY" = "true" ]; then
    echo "🔌 启用青果隧道代理，并允许自动回退至本地 IP..."
    PRIMARY_PROXY="http://8C404999:EB0B62BEE671@tun-pmzmcw.qg.net:10009"
    export NMPA_PROXY_LIST="${PRIMARY_PROXY},direct"
else
    echo "🌐 使用本地IP抓取..."
    unset NMPA_PROXY_LIST
fi
export NMPA_PROXY_ALLOW_DIRECT=true
unset NMPA_PROXY HTTP_PROXY HTTPS_PROXY ALL_PROXY

# 核心配置参数 (修复后支持动态配置)
export NMPA_MAX_CONCURRENCY=$CONCURRENCY
export NMPA_PAGE_SIZE=$PAGE_SIZE
export NMPA_DOMESTIC_MAX_PAGES=200
export NMPA_DATASETS="$DATASETS"

export NMPA_MAX_ATTEMPTS=60
export NMPA_PROXY_MAX_ROTATIONS=60

# 延时配置 (支持外部环境变量预设)
if [ "$CONCURRENCY" -gt 3 ]; then
    # 高并发时增加延时避免封禁
    : "${NMPA_SEGMENT_DELAY_MIN:=2000}"
    : "${NMPA_SEGMENT_DELAY_MAX:=4000}"
    : "${NMPA_SEGMENT_PAUSE_MIN:=6000}"
    : "${NMPA_SEGMENT_PAUSE_MAX:=12000}"
    : "${NMPA_PAGE_DELAY_MIN:=800}"
    : "${NMPA_PAGE_DELAY_MAX=1600}"
    : "${NMPA_LIST_DELAY_MIN:=600}"
    : "${NMPA_LIST_DELAY_MAX=1200}"
    : "${NMPA_DETAIL_DELAY_MIN:=400}"
    : "${NMPA_DETAIL_DELAY_MAX=800}"
    : "${NMPA_RECORD_DELAY_MIN=100}"
    : "${NMPA_RECORD_DELAY_MAX=300}"
else
    # 低并发时使用较快延时
    : "${NMPA_SEGMENT_DELAY_MIN:=1500}"
    : "${NMPA_SEGMENT_DELAY_MAX=3000}"
    : "${NMPA_SEGMENT_PAUSE_MIN:=4000}"
    : "${NMPA_SEGMENT_PAUSE_MAX=8000}"
    : "${NMPA_PAGE_DELAY_MIN=600}"
    : "${NMPA_PAGE_DELAY_MAX=1200}"
    : "${NMPA_LIST_DELAY_MIN=500}"
    : "${NMPA_LIST_DELAY_MAX=1000}"
    : "${NMPA_DETAIL_DELAY_MIN=300}"
    : "${NMPA_DETAIL_DELAY_MAX=600}"
    : "${NMPA_RECORD_DELAY_MIN=80}"
    : "${NMPA_RECORD_DELAY_MAX=200}"
fi

echo "✅ 配置完成，准备启动爬虫..."
echo "📊 最终配置:"
echo "   - 并发数: $NMPA_MAX_CONCURRENCY"
echo "   - 每页条数: $NMPA_PAGE_SIZE"
echo "   - 最大页数: $NMPA_DOMESTIC_MAX_PAGES"
echo "   - 数据集: $NMPA_DATASETS"
echo "   - 代理: ${USE_PROXY:-true}"
echo "   - 延时策略: $([ "$CONCURRENCY" -gt 3 ] && echo "高并发模式" || echo "标准模式")"
echo ""

# 生成唯一的日志文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="crawler_${TIMESTAMP}.log"
PID_FILE="crawler.pid"

# 停止之前的进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  发现运行中的爬虫进程 (PID: $OLD_PID)，正在停止..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 3
        # 强制停止如果还在运行
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "⚠️  强制停止进程..."
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
    fi
    rm -f "$PID_FILE"
fi

# 清理旧的本地测试文件
rm -f local_test.pid local_test_*.log

echo "📝 日志文件: $LOG_FILE"
echo "🔄 启动爬虫 (后台运行)..."
echo ""

# 启动爬虫 (后台运行)
nohup node super_main.js > "$LOG_FILE" 2>&1 &
CRAWLER_PID=$!

# 保存PID
echo "$CRAWLER_PID" > "$PID_FILE"

echo "✅ 爬虫已启动!"
echo "📋 进程信息:"
echo "   - PID: $CRAWLER_PID"
echo "   - 日志: $LOG_FILE"
echo "   - PID文件: $PID_FILE"
echo ""

# 显示配置摘要
echo "🎯 运行配置摘要:"
echo "   - 输出目录根路径: outputs/runs/"
echo "   - 目标数据集: $NMPA_DATASETS"
echo "   - 并发浏览器数: $NMPA_MAX_CONCURRENCY"
echo "   - 每页数据量: $NMPA_PAGE_SIZE 条"
echo "   - 预计性能: $((NMPA_MAX_CONCURRENCY * NMPA_PAGE_SIZE)) 条/批次"
echo ""

echo "📊 监控和管理命令:"
echo "   📈 实时日志:     tail -f $LOG_FILE"
echo "   🔍 进程状态:     ps -p $CRAWLER_PID"
echo "   🛑 停止爬虫:     kill $CRAWLER_PID"
echo "   📂 输出目录:     outputs/datasets/"
echo "   📋 检查文件:     ls -la outputs/datasets/*.jsonl"
echo "   🔄 重启脚本:     ./run_optimized_crawler.sh"
echo ""

# 等待几秒检查启动状态
echo "⏳ 检查启动状态..."
sleep 8

if ps -p "$CRAWLER_PID" > /dev/null 2>&1; then
    echo "✅ 爬虫启动成功!"
    echo ""

    # 显示启动日志片段
    if [ -f "$LOG_FILE" ]; then
        echo "📋 启动日志 (最近15行):"
        echo "----------------------------------------"
        tail -15 "$LOG_FILE" | grep -E "(启动|✅|❌|配置|NMPA|并发|数据集)" || tail -15 "$LOG_FILE"
        echo "----------------------------------------"
        echo ""
    fi

    # 预估运行时间 (简单估算)
    TOTAL_RECORDS=0
    case "$DATASETS" in
        *"domestic-h"*) TOTAL_RECORDS=$((TOTAL_RECORDS + 15000)) ;;
    esac
    case "$DATASETS" in
        *"domestic-s"*) TOTAL_RECORDS=$((TOTAL_RECORDS + 8000)) ;;
    esac
    case "$DATASETS" in
        *"imported"*) TOTAL_RECORDS=$((TOTAL_RECORDS + 2000)) ;;
    esac

    if [ "$TOTAL_RECORDS" -gt 0 ]; then
        BATCH_SIZE=$((NMPA_MAX_CONCURRENCY * NMPA_PAGE_SIZE * 2))
        if [ "$BATCH_SIZE" -gt 0 ]; then
            ESTIMATED_MINUTES=$((TOTAL_RECORDS / BATCH_SIZE))
            if [ "$ESTIMATED_MINUTES" -lt 1 ]; then
                ESTIMATED_MINUTES=1
            fi
            echo "⏱️  预估运行时间: 约 ${ESTIMATED_MINUTES} 分钟 (基于 $TOTAL_RECORDS 条总记录)"
        fi
    fi

    echo ""
    echo "💡 提示:"
    echo "   - 使用 'tail -f $LOG_FILE' 实时查看抓取进度"
    echo "   - 数据写入 outputs/runs/<run_id>/datasets/，run_id 可在 outputs/state/current_run.json 查看"
    echo "   - 如需调整参数，可使用: ./run_optimized_crawler.sh <并发数> <数据集> <页大小> <代理开关>"
    echo ""
    echo "🚀 开始数据抓取任务..."

else
    echo "❌ 爬虫启动失败，请检查错误日志:"
    if [ -f "$LOG_FILE" ]; then
        echo "----------------------------------------"
        echo "错误信息:"
        tail -20 "$LOG_FILE"
        echo "----------------------------------------"
        echo ""
        echo "🔍 可能的解决方案:"
        echo "   1. 检查代理配置是否正确"
        echo "   2. 确认网络连接正常"
        echo "   3. 降低并发数重新尝试"
        echo "   4. 使用本地IP测试: ./run_optimized_crawler.sh 1 domestic-h 50 false"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

# 创建快速监控脚本
cat > "monitor_${TIMESTAMP}.sh" << EOF
#!/bin/bash
echo "📊 NMPA 爬虫监控 - $TIMESTAMP"
echo "==============================="
echo "进程状态:"
ps -p $CRAWLER_PID -o pid,etime,pcpu,pmem,cmd 2>/dev/null || echo "进程已结束"
echo ""
RUNS_BASE="outputs/runs"
LATEST_RUN=$(ls -1dt "${RUNS_BASE}"/* 2>/dev/null | head -n 1)
if [ -z "$LATEST_RUN" ]; then
    echo "输出目录: 暂无运行记录"
else
    echo "最新输出目录: $LATEST_RUN"
    echo ""
    echo "输出文件大小:"
    ls -lh "$LATEST_RUN"/datasets/*.jsonl 2>/dev/null | awk '{print \$9 "\: " \$5}' || echo "暂无数据文件"
fi
echo ""
echo "最近日志:"
tail -5 "$LOG_FILE" 2>/dev/null || echo "日志文件不存在"
echo ""
echo "实时监控命令: tail -f $LOG_FILE"
EOF
chmod +x "monitor_${TIMESTAMP}.sh"
echo ""
echo "🔧 已生成监控脚本: ./monitor_${TIMESTAMP}.sh"