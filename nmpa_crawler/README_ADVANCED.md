# NMPA 爬虫高级功能说明

## 概述

本项目在原有基础上增加了多项高级功能，大幅提升了爬虫的效率、稳定性和反检测能力。

## 🆕 新增功能

### 1. DrissionPage 引擎支持

**优势：**
- 比Selenium更好的反检测能力
- 更快的页面操作速度
- 更稳定的元素定位
- 自动处理反爬虫机制

**使用方法：**
```yaml
mode: drission
```

### 2. 高级JS签名算法破解

**支持的签名算法：**
- **V1**: 基础MD5签名
- **V2**: HMAC-SHA256签名
- **V3**: AES加密签名
- **V4**: 复合签名算法
- **自动检测**: 根据URL特征自动选择算法

**配置方法：**
```yaml
sign_engine:
  secret_key: "your_custom_secret_key"
  algorithm: "auto"  # auto | v1 | v2 | v3 | v4
```

### 3. 并发处理能力

**多线程并发模式：**
```yaml
concurrent:
  enabled: true
  max_workers: 3
  engine_type: "auto"
```

**异步IO模式：**
```yaml
async:
  enabled: true
  max_async_tasks: 10
```

### 4. 智能代理轮换

**功能特性：**
- 代理池管理
- 健康检查
- 故障转移
- 自动轮换

**配置示例：**
```yaml
proxy:
  enabled: true
  check_interval: 300
  max_failure_rate: 0.3
  proxies:
    - host: "proxy1.example.com"
      port: 8080
      username: "user1"
      password: "pass1"
      type: "http"
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install DrissionPage  # 新增依赖
pip install pycryptodome  # 签名算法依赖
```

### 2. 基础使用

**使用DrissionPage引擎（推荐）：**
```yaml
mode: drission
```

**启用并发模式：**
```yaml
concurrent:
  enabled: true
  max_workers: 3
```

**使用代理：**
```yaml
proxy:
  http: "http://user:pass@proxy.example.com:8080"
```

### 3. 运行爬虫

```bash
# 使用默认配置
python main.py

# 使用高级配置
python main.py -c config_advanced.yaml
```

## 📊 性能对比

| 引擎类型 | 反检测能力 | 速度 | 稳定性 | 推荐场景 |
|---------|-----------|------|--------|----------|
| Selenium | 中 | 中 | 高 | 通用场景 |
| DrissionPage | 高 | 高 | 高 | 生产环境 |
| HTTP | 最高 | 最高 | 中 | 大规模爬取 |

## 🔧 技术实现细节

### DrissionPage引擎实现

```python
from drission_engine import NMPADrissionCrawler

crawler = NMPADrissionCrawler(cfg)
crawler.start()
records = crawler.crawl_job("domestic", "国药准字H", "outputs")
```

### 签名算法破解

```python
from sign_cracker import NMPASignCracker

cracker = NMPASignCracker(cfg)
headers, sign_data = cracker.generate_headers(url, params)
```

### 并发处理

```python
from concurrent_crawler import create_concurrent_crawler

manager = create_concurrent_crawler(cfg)
manager.add_task("domestic", "国药准字H")
results = manager.run_concurrent()
```

### 代理管理

```python
from proxy_manager import create_proxy_pool, create_proxy_rotator

pool = create_proxy_pool(cfg)
rotator = create_proxy_rotator(pool, "best")
proxy = rotator.get_proxy()
```

## 🛠️ 配置详解

### 引擎选择

```yaml
# 三种引擎模式
mode: browser    # Selenium WebDriver
mode: drission   # DrissionPage (推荐)
mode: http       # HTTP + 签名算法
```

### 并发配置

```yaml
# 多线程并发
concurrent:
  enabled: true
  max_workers: 3
  engine_type: "auto"  # 自动选择最佳引擎

# 异步IO并发
async:
  enabled: true
  max_async_tasks: 10
```

### 代理配置

```yaml
proxy:
  # 基础代理
  http: "http://user:pass@host:port"

  # 代理池
  enabled: true
  proxies:
    - host: "proxy1.com"
      port: 8080
      type: "http"
```

## 📈 性能优化建议

### 1. 引擎选择优化
- **生产环境**: 使用DrissionPage引擎
- **测试环境**: 使用Selenium引擎
- **大规模爬取**: 使用HTTP引擎 + 代理池

### 2. 并发优化
- **CPU密集型**: 设置max_workers为CPU核心数
- **IO密集型**: 可以设置更高的并发数
- **混合任务**: 使用异步IO模式

### 3. 代理优化
- **高质量代理**: 使用商业代理服务
- **代理池**: 配置多个代理备选
- **健康检查**: 启用自动健康检查

### 4. 延迟优化
```yaml
delay_min_ms: 800    # 避免请求过于频繁
delay_max_ms: 2000   # 随机延迟
```

## 🔍 故障排除

### 常见问题

**1. DrissionPage无法启动**
```bash
pip install --upgrade DrissionPage
```

**2. 签名算法失败**
- 检查密钥配置
- 启用调试模式查看签名过程

**3. 代理连接失败**
- 检查代理配置
- 启用代理健康检查

**4. 并发任务失败**
- 减少并发数量
- 检查系统资源

### 调试模式

```yaml
logging:
  level: "DEBUG"
  file: "debug.log"
```

## 📝 使用示例

### 示例1：基础DrissionPage爬取
```yaml
mode: drission
max_pages: 10
jobs:
  - dataset: domestic
    code_prefix: "国药准字H"
```

### 示例2：并发+代理配置
```yaml
mode: drission
concurrent:
  enabled: true
  max_workers: 3
proxy:
  enabled: true
  proxies:
    - host: "proxy1.com"
      port: 8080
jobs:
  - dataset: domestic
    code_prefix: "国药准字H"
  - dataset: imported
    code_prefix: "国药准字H"
```

### 示例3：HTTP引擎+签名算法
```yaml
mode: http
sign_engine:
  algorithm: "v2"
  secret_key: "your_key"
jobs:
  - dataset: domestic
    code_prefix: "国药准字H"
```

## 🎯 最佳实践

1. **引擎选择**: 优先使用DrissionPage
2. **并发控制**: 根据目标网站调整并发数
3. **代理使用**: 在高并发场景下使用代理池
4. **错误处理**: 启用重试机制和错误日志
5. **性能监控**: 使用详细日志记录性能指标

## 📞 技术支持

如遇到问题，请检查：
1. 配置文件格式是否正确
2. 依赖包是否完整安装
3. 网络连接是否正常
4. 代理配置是否有效

更多技术细节请参考各模块源代码注释。