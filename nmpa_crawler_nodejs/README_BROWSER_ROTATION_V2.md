# 🚀 NMPA 爬虫增强版 v2.0 - 浏览器轮换与智能容错

> **版本号**: v2.0.0
> **提交哈希**: 215561e
> **发布日期**: 2025-10-19
> **状态**: 生产就绪 ✅

---

## 📋 目录

- [🎯 核心功能](#-核心功能)
- [🔧 技术架构](#-技术架构)
- [⚙️ 配置参数](#️-配置参数)
- [📊 性能优化](#-性能优化)
- [🛡️ 容错机制](#️-容错机制)
- [🚀 快速开始](#-快速开始)
- [📈 监控与调试](#-监控与调试)
- [❓ 常见问题](#-常见问题)
- [🔄 版本更新](#-版本更新)

---

## 🎯 核心功能

### 🔄 多浏览器轮换机制

**支持的浏览器类型**:
- ✅ **Chromium** (主力浏览器)
- ✅ **Firefox** (备选浏览器)
- ✅ **WebKit** (实验性支持)

**轮换触发条件**:
1. **段间切换**: 每个检索段开始前
2. **批量切换**: 每处理N页后 (可配置)
3. **错误切换**: 检测到异常时自动切换
4. **手动切换**: 支持强制轮换

**智能路径检测**:
```javascript
// 自动检测浏览器安装路径
const firefoxPaths = [
    path.join(os.homedir(), '.cache/ms-playwright/firefox-1490/firefox/firefox'),
    path.join(os.homedir(), '.cache/ms-playwright/firefox-1495/firefox/firefox'),
];
```

### 📊 智能容错系统

**详情成功率监控**:
- 📈 **实时监控**: 按页计算详情抓取成功率
- 🎯 **动态阈值**: 默认20%成功率阈值
- 🔄 **自动恢复**: 低于阈值时自动切换浏览器

**浏览器健康度检测**:
```javascript
markCurrentBrowserUnhealthy(reason) {
    this.logger.warning(`${type} 浏览器已标记为不可用：${reason}`);
    this.disabledTypes.add(type);
    return true;
}
```

### 📂 分段存储结构

**智能拆分算法**:
- 📏 **严格限制**: 每段≤50页 (≤1000条记录)
- 🔄 **递归拆分**: 按0-9A-Z前缀自动细分
- 📁 **独立存储**: 每段专属目录

**目录结构**:
```
outputs/datasets/
├── 国药准字H10/
│   ├── 国药准字H10_001.jsonl  (前20条)
│   ├── 国药准字H10_002.jsonl  (21-40条)
│   └── 国药准字H10_003.jsonl  (41-60条)
├── 国药准字H108/
│   └── 国药准字H108_001.jsonl  (细分段数据)
└── 国药准字H109/
    └── 国药准字H109_001.jsonl
```

---

## 🔧 技术架构

### 🏗️ 核心组件

#### 1. BrowserController (浏览器控制器)
```javascript
class BrowserController {
    constructor({ initialPage, logger, proxy, browserArgs, swapDelayMs, sequence });
    async launchNextBrowser();     // 启动下一个浏览器
    async rotateBrowser(reason);   // 轮换浏览器
    markCurrentBrowserUnhealthy(); // 标记不健康
}
```

#### 2. 智能错误检测
```javascript
function shouldRotateForListError(error) {
    const message = typeof error.message === 'string' ? error.message.toLowerCase() : '';
    return /status code 4\d\d|403|412|timeout|target page|context or browser has been closed/.test(message);
}
```

#### 3. WAF冷却机制
```javascript
if (looksBlocked && BLOCK_COOLDOWN_MS > 0 && recoveryAttempts < BLOCK_MAX_COOLDOWN_ATTEMPTS) {
    crawlerLog.warning(`列表请求连续失败，等待 ${BLOCK_COOLDOWN_MS}ms 后重试`);
    await sleep(BLOCK_COOLDOWN_MS);
}
```

### 🔄 数据流程

```
1. 启动爬虫 → 2. 检测浏览器 → 3. 段分析
                                    ↓
8. 数据写入 ← 7. 详情抓取 ← 6. 浏览器轮换
                                    ↓
               9. 错误处理 → 10. 自动恢复
```

---

## ⚙️ 配置参数

### 🌐 浏览器配置

| 参数名 | 默认值 | 说明 | 推荐值 |
|--------|--------|------|--------|
| `NMPA_BROWSER_SEQUENCE` | `chromium` | 浏览器轮换顺序 | `chromium,firefox` |
| `NMPA_BROWSER_SWAP_DELAY_MS` | `300000` | 浏览器切换延迟 | `300000` (5分钟) |
| `NMPA_BROWSER_PAGE_BATCH` | `0` | 批量页数阈值 | `0` (仅段间切换) |

### 📊 性能配置

| 参数名 | 默认值 | 说明 | 推荐值 |
|--------|--------|------|--------|
| `NMPA_PAGE_SIZE` | `20` | 每页条数 | `20` |
| `NMPA_DOMESTIC_MAX_PAGES` | `50` | 每段最大页数 | `50` |
| `NMPA_SEGMENT_DELAY_MIN` | `1200` | 段间延迟最小值 | `1200` |
| `NMPA_SEGMENT_DELAY_MAX` | `2800` | 段间延迟最大值 | `2800` |

### 🛡️ 容错配置

| 参数名 | 默认值 | 说明 | 推荐值 |
|--------|--------|------|--------|
| `NMPA_DETAIL_SUCCESS_MIN_RATIO` | `0.2` | 详情成功率阈值 | `0.2` |
| `NMPA_BLOCK_COOLDOWN_MS` | `300000` | WAF冷却时间 | `600000` (10分钟) |
| `NMPA_BLOCK_MAX_COOLDOWN_ATTEMPTS` | `3` | 最大冷却次数 | `3` |
| `NMPA_LIST_RETRY_LIMIT` | `3` | 列表重试次数 | `3` |

---

## 📈 性能优化

### ⚡ 速度优化

**Chrome 优先策略**:
- 🎯 **主浏览器**: Chrome保证数据质量
- 🔄 **自动降级**: Firefox失败时自动回退
- 📊 **成功率监控**: 实时检测抓取效率

**分段并行**:
```javascript
// 智能分段避免单次请求过大
if ((total <= DOMESTIC_SEGMENT_LIMIT) && (totalPages <= DOMESTIC_MAX_PAGES)) {
    // 直接抓取
} else {
    // 递归细分
    for (const digit of SEGMENT_DIGITS) {
        await split(`${searchValue}${digit}`, depth + 1);
    }
}
```

### 🧠 智能延迟

**动态延迟机制**:
- 📊 **成功率驱动**: 成功率低时增加延迟
- 🔄 **自适应调整**: 根据响应时间动态调整
- ⏰ **冷却机制**: WAF触发时自动冷却

---

## 🛡️ 容错机制

### 🔄 自动恢复

**多级容错**:
1. **浏览器级**: 失效浏览器自动禁用
2. **页面级**: 单页失败自动重试
3. **段级**: 整段失败重新分析
4. **系统级**: WAF触发冷却恢复

**错误分类处理**:
```javascript
// 网络错误 - 切换浏览器
if (shouldRotateForListError(error)) {
    await controller.rotateBrowser(`${segment.searchValue}: 列表请求异常`);
}

// WAF错误 - 冷却等待
if (looksBlocked && BLOCK_COOLDOWN_MS > 0) {
    await sleep(BLOCK_COOLDOWN_MS);
}
```

### 📊 数据完整性

**防重复机制**:
```javascript
const seenCodes = new Set();
if (seenCodes.has(record.code)) continue;
seenCodes.add(record.code);
```

**原子写入**:
```javascript
// 批量写入确保数据完整性
await writeJsonLine(stream, record);
totalWritten += 1;
```

---

## 🚀 快速开始

### 📦 环境准备

**1. 安装依赖**:
```bash
npm install
```

**2. 安装浏览器**:
```bash
# Python方法 (推荐)
sudo python3 -m playwright install chromium firefox webkit --with-deps

# 或者npm方法
npx playwright install chromium firefox webkit
```

**3. 权限配置**:
```bash
# 确保浏览器可执行权限
sudo chown -R $USER:$USER ~/.cache/ms-playwright/
```

### 🎯 运行配置

#### 稳定配置 (推荐)
```bash
export NMPA_BROWSER_SEQUENCE=chromium
export NMPA_BLOCK_COOLDOWN_MS=300000
./run_optimized_crawler.sh 1 domestic-h 20 false
```

#### 轮换配置
```bash
export NMPA_BROWSER_SEQUENCE=chromium,firefox
export NMPA_BROWSER_SWAP_DELAY_MS=300000
export NMPA_DETAIL_SUCCESS_MIN_RATIO=0.2
./run_optimized_crawler.sh 1 domestic-h 20 false
```

#### 高频配置
```bash
export NMPA_BROWSER_SEQUENCE=chromium
export NMPA_BLOCK_COOLDOWN_MS=600000
export NMPA_SEGMENT_DELAY_MAX=5000
export NMPA_PAGE_DELAY_MAX=1500
./run_optimized_crawler.sh 1 domestic-h 20 false
```

### 📊 监控命令

**实时日志**:
```bash
tail -f crawler_*.log
```

**进程状态**:
```bash
ps -p $(cat crawler.pid)
```

**停止爬虫**:
```bash
./stop_crawler.sh
# 或
kill $(cat crawler.pid)
```

---

## 📈 监控与调试

### 📊 日志分析

**关键日志标识**:
- ✅ `"已切换至 ${browserTypeName} 浏览器实例"` - 浏览器切换成功
- ⚠️ `"${browserTypeName} 浏览器已标记为不可用"` - 浏览器被禁用
- ⏸️ `"等待 ${BLOCK_COOLDOWN_MS}ms 后重试"` - WAF冷却
- 📈 `"详情成功率 ${(successRatio * 100).toFixed(1)}%"` - 成功率统计

**性能指标**:
```bash
# 统计成功抓取记录数
find outputs/datasets -name "*.jsonl" -exec wc -l {} \; | awk '{sum+=$1} END {print "总记录数:", sum}'

# 检查错误日志
grep -E "(失败|错误|error|failed)" crawler_*.log | wc -l
```

### 🔍 调试工具

**浏览器兼容性测试**:
```bash
node test_browser_isolated.js
```

**连接测试**:
```bash
node test_connection.js
```

**API调试**:
```bash
node debug_list.js
```

---

## ❓ 常见问题

### Q1: Firefox 频繁失败怎么办？

**问题现象**: 日志显示大量 `"无法获取记录 ... 已跳过"`

**解决方案**:
```bash
# 1. 检查Firefox是否正确安装
ls -la ~/.cache/ms-playwright/firefox-*/

# 2. 使用Chrome单浏览器模式
export NMPA_BROWSER_SEQUENCE=chromium

# 3. 如果必须使用Firefox，增加成功率阈值
export NMPA_DETAIL_SUCCESS_MIN_RATIO=0.1
```

### Q2: 遇到 412/403 错误怎么处理？

**问题现象**: WAF拦截，返回状态码 412 或 403

**解决方案**:
```bash
# 1. 增加冷却时间
export NMPA_BLOCK_COOLDOWN_MS=600000  # 10分钟

# 2. 增加请求延迟
export NMPA_PAGE_DELAY_MAX=2000       # 2秒
export NMPA_SEGMENT_DELAY_MAX=5000    # 5秒

# 3. 减少页大小
export NMPA_PAGE_SIZE=10
```

### Q3: 数据重复怎么解决？

**问题现象**: 同一记录在多个文件中出现

**解决方案**:
- ✅ **自动去重**: v2.0版本已内置 `seenCodes` 去重机制
- 🧹 **清理数据**: 使用脚本清理历史重复数据
- 📊 **监控日志**: 检查是否有段重抓的日志

### Q4: 爬虫运行缓慢怎么优化？

**性能优化建议**:
```bash
# 1. 关闭浏览器轮换延迟
export NMPA_BROWSER_SWAP_DELAY_MS=0

# 2. 减少冷却时间
export NMPA_BLOCK_COOLDOWN_MS=120000  # 2分钟

# 3. 优化并发参数
export NMPA_DETAIL_CONCURRENCY=6      # 增加详情并发
export NMPA_RECORD_DELAY_MIN=50       # 减少记录延迟
```

### Q5: 断点续传怎么实现？

**当前状态**: v2.0版本支持段级恢复

**恢复步骤**:
```bash
# 1. 检查已完成段
ls -la outputs/datasets/

# 2. 分析日志进度
grep "使用当前检索段" crawler_*.log

# 3. 重新启动 (会跳过已完成的段)
./run_optimized_crawler.sh 1 domestic-h 20 false
```

---

## 🔄 版本更新

### 📅 v2.0.0 (2025-10-19)

#### ✨ 新功能
- 🔄 **多浏览器轮换**: Chromium + Firefox + WebKit 支持
- 🧠 **智能容错**: 自动检测和禁用失效浏览器
- 📊 **成功率监控**: 实时监控详情抓取成功率
- ❄️ **WAF冷却机制**: 自动冷却恢复
- 📂 **分段存储**: 按段独立存储数据

#### 🔧 技术改进
- **BrowserController**: 统一浏览器管理
- **错误检测**: 智能错误分类和处理
- **去重机制**: 防止重复数据写入
- **路径检测**: 自动检测浏览器安装路径

#### 🐛 修复问题
- 修复Firefox token获取失败问题
- 修复浏览器切换时的资源泄漏
- 修复分段拆分的深度控制
- 修复详情失败时的无限重试

#### ⚡ 性能提升
- Chrome主浏览器保证数据质量
- Firefox自动降级机制
- 智能延迟算法
- 批量处理优化

### 📅 v1.x.x 历史版本

#### v1.5.0
- 基础浏览器轮换功能
- 简单错误重试机制

#### v1.0.0
- 初始版本发布
- 基础爬虫功能

---

## 📞 技术支持

### 📋 调试信息收集

**遇到问题时请提供**:
1. 📊 **运行日志**: `crawler_*.log`
2. 🔧 **环境配置**: `env | grep NMPA_`
3. 📁 **输出目录**: `outputs/datasets/` 结构
4. 🌐 **浏览器版本**: `ls -la ~/.cache/ms-playwright/`

### 🎯 最佳实践建议

1. **生产环境**: 使用Chrome单浏览器模式
2. **测试环境**: 可启用Firefox轮换测试
3. **监控频率**: 建议每30分钟检查一次日志
4. **数据备份**: 定期备份 `outputs/datasets/` 目录
5. **性能调优**: 根据网络状况调整延迟参数

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

**🎉 感谢使用 NMPA 爬虫增强版 v2.0！**

如有问题或建议，欢迎提交 Issue 或 Pull Request。