# NMPA药品数据爬虫 - 使用指南

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Playwright
- 网络连接

### 安装依赖
```bash
npm install
```

### 运行爬虫

#### 1. 超级增强版（推荐）⭐
```bash
node super_main.js
```
**特点：** 功能最全，5层绕过策略，成功率最高

#### 2. 增强版
```bash
node enhanced_main.js
```
**特点：** 性能稳定，4层绕过策略

#### 3. 混合策略版
```bash
node hybrid_main.js
```
**特点：** 结合yiya-crawler经验，简化高效

#### 4. 数据专用版
```bash
node data_main.js
```
**特点：** 专门针对药品数据页面优化

## 📊 输出结果

### 文件位置
```
outputs/
├── drugs_super_YYYYMMDDTHHMMSS.jsonl  # 按版本分类
├── drugs_enhanced_YYYYMMDDTHHMMSS.jsonl
├── drugs_all.jsonl  # 汇总所有数据
└── ...

downloads/
├── page_analysis_YYYYMMDDTHHMMSS.json  # 页面分析报告
└── ...
```

### 数据格式
```json
{"code":"国药准字H12345678","zh":"阿莫西林胶囊","en":"","source":"strategy_1","url":"https://...","timestamp":"2025-10-14T08:30:00.000Z"}
{"code":"国药准字Z87654321","zh":"板蓝根颗粒","en":"","source":"strategy_2","url":"https://...","timestamp":"2025-10-14T08:30:01.000Z"}
```

## 🔧 配置选项

### 修改目标页面
编辑对应文件中的 `SITE_CONFIG`:
```javascript
const SITE_CONFIG = {
    nmpa: {
        pageList: [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
            // 添加更多页面...
        ]
    }
};
```

### 调整并发数
```javascript
maxConcurrency: 2,  // 同时处理的页面数
```

### 设置延迟时间
```javascript
function randomDelay(min = 2000, max = 5000) {
    return Math.random() * (max - min) + min;
}
```

## 🛠️ 故障排除

### 常见问题

#### 1. 412错误
**现象：** 所有策略都返回412状态码
**解决方案：**
- 等待一段时间后重试
- 尝试不同的时间段（非工作时间）
- 检查网络连接

#### 2. 连接超时
**现象：** `net::ERR_TIMED_OUT`
**解决方案：**
- 增加超时时间
- 检查网络稳定性
- 尝试使用代理

#### 3. 找不到模块
**现象：** `Cannot find module 'puppeteer'`
**解决方案：**
```bash
npm install puppeteer
# 或者使用本地Chromium
# 代码中已配置本地路径
```

### 日志分析

#### 成功访问
```
✅ 策略1成功
📊 响应状态: 200
📦 提取到 3 个药品信息
💾 保存 3 个药品到: drugs_super_20251014T083000.jsonl
```

#### 失败访问
```
❌ 所有策略都失败了
📊 响应状态: 412
⚠️ 策略1失败: page.goto: Timeout
```

## 📈 性能优化

### 提高成功率
1. **错峰运行** - 避开工作时间（9:00-18:00）
2. **增加延迟** - 适当延长访问间隔
3. **减少并发** - 降低同时访问的页面数

### 提高速度
1. **增加并发** - 适当提高 `maxConcurrency`
2. **减少延迟** - 缩短 `randomDelay` 时间范围
3. **选择性爬取** - 只爬取重要页面

## 🔍 监控和维护

### 实时监控
爬虫运行时会显示详细日志：
- 当前处理的页面URL
- 使用的绕过策略
- 响应状态码
- 提取的数据数量
- 保存的文件信息

### 定期维护
1. **清理输出文件** - 定期清理旧的输出文件
2. **更新策略** - 根据网站变化调整绕过策略
3. **监控性能** - 观察成功率变化趋势

## 📞 技术支持

### 日志文件
每次运行都会生成详细日志，可用于：
- 分析失败原因
- 优化访问策略
- 监控爬虫性能

### 自定义扩展
爬虫采用模块化设计，可以轻松：
- 添加新的绕过策略
- 扩展数据提取规则
- 增加新的数据源

---

**版本：** v1.0
**更新时间：** 2025年10月14日
**状态：** 生产就绪