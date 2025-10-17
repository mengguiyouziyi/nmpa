#!/bin/bash

# NMPA 爬虫本地IP测试脚本
# 恢复初始配置，使用本地IP进行测试

set -e

echo "🔍 NMPA 爬虫本地IP测试"
echo "===================="

# 进入项目目录
cd "$(dirname "$0")"

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

echo "⚙️  配置本地IP和初始参数..."

# 清理所有代理环境变量（确保使用本地IP）
unset NMPA_PROXY
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY

# 恢复初始配置参数（更保守的设置）
export NMPA_PAGE_SIZE=20
export NMPA_DOMESTIC_MAX_PAGES=500
export NMPA_SEGMENT_DELAY_MIN=1200
export NMPA_SEGMENT_DELAY_MAX=2800
export NMPA_PAGE_DELAY_MIN=450
export NMPA_PAGE_DELAY_MAX=900
export NMPA_LIST_DELAY_MIN=900
export NMPA_LIST_DELAY_MAX=2000
export NMPA_RECORD_DELAY_MIN=80
export NMPA_RECORD_DELAY_MAX=180

# 测试模式：只抓取国内H数据（小规模测试）
export NMPA_DATASETS="domestic-h"

echo "✅ 配置完成，启动本地测试..."
echo "📊 测试配置:"
echo "   - 并发数: 1"
echo "   - 每页条数: 20"
echo "   - 最大页数: 500"
echo "   - 数据集: $NMPA_DATASETS (仅国内H，测试用)"
echo "   - 代理: 本地IP (无代理)"
echo "   - IP地址: $(curl -s ifconfig.me 2>/dev/null || echo '未知')"
echo ""

# 检查是否有日志文件
LOG_FILE="local_test_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="local_test.pid"

# 停止之前的测试进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  发现运行中的测试进程 (PID: $OLD_PID)，正在停止..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 3
    fi
    rm -f "$PID_FILE"
fi

echo "📝 测试日志: $LOG_FILE"
echo "🔄 启动测试爬虫 (前台运行，便于观察)..."
echo ""

# 前台运行测试，便于实时观察
echo "按 Ctrl+C 可随时停止测试"
echo "----------------------------------------"

# 启动爬虫 (前台运行)
node super_main.js 2>&1 | tee "$LOG_FILE" &
TEST_PID=$!

# 保存PID
echo "$TEST_PID" > "$PID_FILE"

echo ""
echo "✅ 测试已启动!"
echo "📋 测试信息:"
echo "   - PID: $TEST_PID"
echo "   - 日志: $LOG_FILE"
echo "   - 模式: 前台运行 (可实时查看)"
echo ""
echo "🔍 观察要点:"
echo "   - 是否能正常访问 NMPA 网站"
echo "   - 是否出现 403/412 错误"
echo "   - 数据抓取是否正常"
echo "   - 网络连接是否稳定"
echo ""
echo "💡 提示: "
echo "   - 测试运行5-10分钟后即可判断基本可用性"
echo "   - 如需停止，按 Ctrl+C 或运行 ./stop_local_test.sh"

# 等待几秒检查启动状态
sleep 3

if ps -p "$TEST_PID" > /dev/null 2>&1; then
    echo "✅ 测试运行正常!"
    echo ""
    echo "📋 实时日志:"
    echo "----------------------------------------"

    # 等待进程结束或用户中断
    wait "$TEST_PID"

    echo "----------------------------------------"
    echo "🏁 测试结束"
else
    echo "❌ 测试启动失败，请检查日志:"
    if [ -f "$LOG_FILE" ]; then
        echo "----------------------------------------"
        cat "$LOG_FILE"
        echo "----------------------------------------"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

# 清理PID文件
rm -f "$PID_FILE"