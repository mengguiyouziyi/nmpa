# NMPA 爬虫延时参数配置指南

## 📊 延时参数说明

### ⏰ 延时参数详解

| 参数名称 | 作用时机 | 高并发默认值 | 低并发默认值 | 建议调整范围 | 说明 |
|----------|----------|--------------|--------------|--------------|------|
| **NMPA_SEGMENT_DELAY** | 检索段之间的随机等待 | 2000-4000ms | 1500-3000ms | 1000-10000ms | 每个大搜索段(如国药准字H0, H1...)之间的间隔 |
| **NMPA_SEGMENT_PAUSE** | 段落完成后的额外暂停 | 6000-12000ms | 4000-8000ms | 2000-20000ms | 一个完整段抓取完成后的休息时间 |
| **NMPA_PAGE_DELAY** | 同段内翻页之间的等待 | 800-1600ms | 600-1200ms | 500-5000ms | 在同一搜索段内，从第1页翻到第2页等的间隔 |
| **NMPA_LIST_DELAY** | 列表请求前的等待 | 600-1200ms | 500-1000ms | 300-3000ms | 发起列表API请求之前的准备时间 |
| **NMPA_DETAIL_DELAY** | 拉详情批次前的等待 | 400-800ms | 300-600ms | 200-2000ms | 批量获取详情页数据前的间隔 |
| **NMPA_RECORD_DELAY** | 每条记录写入后的等待 | 100-300ms | 80-200ms | 50-1000ms | 写入每条JSON记录后的微小间隔 |

## 🔧 使用方法

### 方法一：通过环境变量预设（推荐）

```bash
# 设置超大延时，确保稳定运行
export NMPA_SEGMENT_DELAY_MIN=3000
export NMPA_SEGMENT_DELAY_MAX=5000
export NMPA_SEGMENT_PAUSE_MIN=8000
export NMPA_SEGMENT_PAUSE_MAX=12000
export NMPA_PAGE_DELAY_MIN=1500
export NMPA_PAGE_DELAY_MAX=2500
export NMPA_LIST_DELAY_MIN=2000
export NMPA_LIST_DELAY_MAX=3500
export NMPA_DETAIL_DELAY_MIN=1500
export NMPA_DETAIL_DELAY_MAX=2500
export NMPA_RECORD_DELAY_MIN=200
export NMPA_RECORD_DELAY_MAX=400

# 启动爬虫
./run_optimized_crawler.sh 1 all 100 false
```

### 方法二：直接运行（绕过脚本）

```bash
NMPA_MAX_CONCURRENCY=1 \
NMPA_DATASETS=domestic-h,domestic-s,imported \
NMPA_SEGMENT_DELAY_MIN=3000 NMPA_SEGMENT_DELAY_MAX=5000 \
NMPA_SEGMENT_PAUSE_MIN=8000 NMPA_SEGMENT_PAUSE_MAX=12000 \
NMPA_PAGE_DELAY_MIN=1500 NMPA_PAGE_DELAY_MAX=2500 \
NMPA_LIST_DELAY_MIN=2000 NMPA_LIST_DELAY_MAX=3500 \
NMPA_DETAIL_DELAY_MIN=1500 NMPA_DETAIL_DELAY_MAX=2500 \
NMPA_RECORD_DELAY_MIN=200 NMPA_RECORD_DELAY_MAX=400 \
node super_main.js
```

## 🎯 延时策略建议

### 🐌 保守策略（单线程本地IP）
```bash
export NMPA_SEGMENT_DELAY_MIN=5000
export NMPA_SEGMENT_DELAY_MAX=8000
export NMPA_SEGMENT_PAUSE_MIN=10000
export NMPA_SEGMENT_PAUSE_MAX=15000
export NMPA_PAGE_DELAY_MIN=2000
export NMPA_PAGE_DELAY_MAX=3000
export NMPA_LIST_DELAY_MIN=3000
export NMPA_LIST_DELAY_MAX=5000
export NMPA_DETAIL_DELAY_MIN=2000
export NMPA_DETAIL_DELAY_MAX=3000
export NMPA_RECORD_DELAY_MIN=500
export NMPA_RECORD_DELAY_MAX=800
```

### 🚀 中等策略（2-3并发代理）
```bash
export NMPA_SEGMENT_DELAY_MIN=2000
export NMPA_SEGMENT_DELAY_MAX=4000
export NMPA_SEGMENT_PAUSE_MIN=6000
export NMPA_SEGMENT_PAUSE_MAX=10000
export NMPA_PAGE_DELAY_MIN=1000
export NMPA_PAGE_DELAY_MAX=2000
export NMPA_LIST_DELAY_MIN=1000
export NMPA_LIST_DELAY_MAX=2000
export NMPA_DETAIL_DELAY_MIN=800
export NMPA_DETAIL_DELAY_MAX=1500
export NMPA_RECORD_DELAY_MIN=200
export NMPA_RECORD_DELAY_MAX=400
```

### ⚡ 激进策略（5+并发代理）
```bash
export NMPA_SEGMENT_DELAY_MIN=1000
export NMPA_SEGMENT_DELAY_MAX=2000
export NMPA_SEGMENT_PAUSE_MIN=3000
export NMPA_SEGMENT_PAUSE_MAX=6000
export NMPA_PAGE_DELAY_MIN=500
export NMPA_PAGE_DELAY_MAX=1000
export NMPA_LIST_DELAY_MIN=500
export NMPA_LIST_DELAY_MAX=1000
export NMPA_DETAIL_DELAY_MIN=300
export NMPA_DETAIL_DELAY_MAX=600
export NMPA_RECORD_DELAY_MIN=100
export NMPA_RECORD_DELAY_MAX=200
```

## 🔍 调试建议

### 📈 增加延时的时机
- 出现频繁403/412错误时
- 代理连接不稳定时
- NMPA网站响应变慢时
- 多次重试仍然失败时

### 📉 减少延时的时机
- 连续运行30分钟无错误时
- 网络条件良好且响应稳定时
- 需要提高抓取效率时

### 🔧 监控要点
1. **观察日志中的延时信息**：检查实际延时是否符合预期
2. **监控错误率**：如果错误率低于1%，可以考虑减少延时
3. **关注网络稳定性**：代理断线或本地IP受限时增加延时
4. **记录成功率**：计算每分钟成功获取的记录数，优化平衡点

## 💡 最佳实践

1. **首次运行**：使用保守策略，确保能稳定获取数据
2. **逐步优化**：根据实际运行情况，逐步减少延时
3. **环境适配**：不同网络环境（本地IP、不同代理）需要不同延时设置
4. **数据完整性**：宁可慢一些，也要确保数据完整性和稳定性
5. **日志记录**：记录延时设置和运行结果，便于后续优化

## 📋 示例配置文件

创建 `.env.delay` 文件：
```bash
# 保守延时配置
NMPA_SEGMENT_DELAY_MIN=3000
NMPA_SEGMENT_DELAY_MAX=5000
NMPA_SEGMENT_PAUSE_MIN=8000
NMPA_SEGMENT_PAUSE_MAX=12000
NMPA_PAGE_DELAY_MIN=1500
NMPA_PAGE_DELAY_MAX=2500
NMPA_LIST_DELAY_MIN=2000
NMPA_LIST_DELAY_MAX=3500
NMPA_DETAIL_DELAY_MIN=1500
NMPA_DETAIL_DELAY_MAX=2500
NMPA_RECORD_DELAY_MIN=200
NMPA_RECORD_DELAY_MAX=400
```

使用时：
```bash
source .env.delay
./run_optimized_crawler.sh 1 all 100 false
```