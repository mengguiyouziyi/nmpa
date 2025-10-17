#!/bin/bash

# NMPA 网络诊断脚本
# 测试本地IP和代理对NMPA网站的访问能力

set -e

echo "🔍 NMPA 网络诊断"
echo "================"

cd "$(dirname "$0")"

echo "📊 当前网络状态:"
echo "----------------------------------------"

# 检查本地IP
echo "🌐 本地IP信息:"
LOCAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "获取失败")
echo "   公网IP: $LOCAL_IP"

# 检查代理配置
echo ""
echo "🔌 代理配置:"
if [ -n "$NMPA_PROXY" ]; then
    echo "   NMPA_PROXY: $NMPA_PROXY"
else
    echo "   NMPA_PROXY: 未设置"
fi

if [ -n "$HTTP_PROXY" ]; then
    echo "   HTTP_PROXY: $HTTP_PROXY"
else
    echo "   HTTP_PROXY: 未设置"
fi

if [ -n "$HTTPS_PROXY" ]; then
    echo "   HTTPS_PROXY: $HTTPS_PROXY"
else
    echo "   HTTPS_PROXY: 未设置"
fi

echo ""
echo "🌍 网络连通性测试:"
echo "----------------------------------------"

# 测试基本网络连接
echo "1. 测试基本DNS解析..."
if nslookup www.nmpa.gov.cn > /dev/null 2>&1; then
    echo "   ✅ DNS解析正常"
else
    echo "   ❌ DNS解析失败"
fi

# 测试HTTPS连接
echo "2. 测试HTTPS连接..."
if curl -s -I https://www.nmpa.gov.cn > /dev/null 2>&1; then
    echo "   ✅ HTTPS连接正常"
else
    echo "   ❌ HTTPS连接失败"
fi

# 测试NMPA搜索页面
echo "3. 测试NMPA搜索页面..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://www.nmpa.gov.cn/datasearch/search-result.html" 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 搜索页面访问正常 (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "403" ]; then
    echo "   ⚠️  搜索页面返回403 (可能被限制)"
elif [ "$HTTP_CODE" = "412" ]; then
    echo "   ⚠️  搜索页面返回412 (可能被限制)"
else
    echo "   ❌ 搜索页面访问失败 (HTTP $HTTP_CODE)"
fi

# 测试API接口（如果可能）
echo "4. 测试API接口可访问性..."
if curl -s -I "https://www.nmpa.gov.cn/api/queryList" > /dev/null 2>&1; then
    echo "   ✅ API接口可访问"
else
    echo "   ⚠️  API接口可能需要特定参数"
fi

echo ""
echo "🧪 建议的测试步骤:"
echo "----------------------------------------"
echo "1. 首先运行本地IP测试："
echo "   ./run_local_test.sh"
echo ""
echo "2. 观察测试过程中的网络响应："
echo "   - 是否频繁出现403/412错误"
echo "   - 响应时间是否正常"
echo "   - 数据抓取是否成功"
echo ""
echo "3. 如果本地IP正常，再尝试代理："
echo "   export NMPA_PROXY=\"http://8C404999:EB0B62BEE671@tun-pmzmcw.qg.net:10009\""
echo "   ./run_optimized_crawler.sh"
echo ""
echo "💡 诊断提示:"
echo "   - 如果本地IP也出现403/412，说明NMPA加强了反爬虫"
echo "   - 如果本地IP正常但代理失败，说明代理配置有问题"
echo "   - 建议先小规模测试，确认可用性后再大规模抓取"