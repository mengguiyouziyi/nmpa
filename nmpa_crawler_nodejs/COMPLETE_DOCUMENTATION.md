# NMPA药品数据爬虫 - 完整技术文档

## 📋 项目概述

### 项目信息
- **项目名称**: NMPA药品数据爬虫 (超级增强版)
- **版本**: v2.0 Super Enhanced
- **开发语言**: Node.js + JavaScript (ES6)
- **核心框架**: Playwright
- **目标网站**: 国家药品监督管理局 (nmpa.gov.cn)
- **主要功能**: 突破412防护，提取国药准字药品信息

### 技术特色
- ✅ **5层绕过策略** - 成功突破NMPA网站412防护机制
- ✅ **智能反检测技术** - User-Agent轮换、请求头伪装、JavaScript反检测
- ✅ **高效数据提取** - 专门针对国药准字格式优化的多策略提取算法
- ✅ **自动化链接发现** - 智能识别相关链接并自动跟进
- ✅ **完整监控体系** - 实时日志、状态监控、错误处理

---

## 🏗️ 系统架构

### 核心模块结构
```
super_main.js
├── 配置模块 (第5-84行)
│   ├── 站点配置 (SITE_CONFIG)
│   ├── 输出目录配置
│   ├── 用户代理池 (USER_AGENTS)
│   └── 请求头组合 (REQUEST_HEADERS)
├── 绕过策略模块 (第86-293行)
│   ├── 策略1: 超级基础访问
│   ├── 策略2: 模拟真实用户浏览
│   ├── 策略3: iframe绕过检测
│   ├── 策略4: fetch API模拟
│   └── 策略5: 镜像域名尝试
├── 数据提取模块 (第295-389行)
│   ├── 页面信息分析
│   ├── 多策略药品数据提取
│   └── 数据清理和去重
├── 智能发现模块 (第391-456行)
│   ├── 链接相关性分析
│   ├── NMPA路径模式匹配
│   └── 链接优先级排序
├── 数据存储模块 (第458-479行)
│   ├── JSONL格式输出
│   ├── 时间戳文件管理
│   └── 汇总文件维护
└── 主控制模块 (第481-707行)
    ├── 浏览器配置和启动
    ├── 反检测脚本注入
    ├── 页面处理流程控制
    └── 结果统计和报告
```

### 技术栈详情
```javascript
// 核心依赖
import { chromium } from 'playwright';  // 浏览器自动化
import fs from 'fs-extra';              // 文件系统操作
import path from 'path';                // 路径处理

// 运行环境要求
Node.js: >= 18.0.0
Playwright: chromium-1187
操作系统: Linux (推荐Ubuntu 20.04+)
```

---

## 🛡️ 412防护突破技术详解

### 问题分析
NMPA网站实施的412 Precondition Failed防护机制：
- **User-Agent检测** - 识别并阻止爬虫用户代理
- **请求头验证** - 检查缺失或异常的HTTP头
- **行为模式分析** - 检测非人类浏览行为
- **JavaScript挑战** - 需要执行特定JS代码验证

### 5层绕过策略详解

#### 策略1: 超级基础访问 + 增强延迟
```javascript
// 核心代码位置: super_main.js:103-125
console.log('🔄 策略1: 超级基础访问');
await page.waitForTimeout(randomDelay(3000, 6000));

const response = await page.goto(url, {
    waitUntil: 'domcontentloaded',
    timeout: 60000
});

const status = response.status();
console.log(`📊 响应状态: ${status}`);

if (status === 200) {
    const content = await page.content();
    if (content.length > 2000) {
        console.log('✅ 策略1成功');
        return true;
    }
}
```

**技术要点:**
- 随机User-Agent和请求头组合
- 3-6秒随机延迟模拟人类犹豫
- 内容长度验证确保页面完整性
- 超时时间延长至60秒

#### 策略2: 模拟真实用户完整浏览流程
```javascript
// 核心代码位置: super_main.js:127-177
// 1. 访问首页建立信任
await page.goto('https://www.nmpa.gov.cn/', {
    waitUntil: 'domcontentloaded',
    timeout: 30000
});

// 2. 模拟鼠标移动和滚动
await page.mouse.move(150, 150);
await page.waitForTimeout(800);
await page.mouse.move(300, 300);
await page.evaluate(() => {
    window.scrollBy(0, 200);
});

// 3. 访问药品频道
await page.goto('https://www.nmpa.gov.cn/yaopin/');
await page.waitForTimeout(randomDelay(3000, 6000));

// 4. 最终访问目标页面
const response = await page.goto(url, {
    waitUntil: 'domcontentloaded',
    timeout: 45000
});
```

**技术要点:**
- 完整用户浏览路径模拟
- 鼠标移动和页面滚动交互
- 多步骤渐进式访问
- 信任度逐步建立

#### 策略3: iframe绕过检测
```javascript
// 核心代码位置: super_main.js:179-216
await page.goto('about:blank');

// 通过iframe加载目标页面
await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head><title>Loading...</title></head>
    <body>
        <iframe id="target" src="${url}" width="100%" height="100%"></iframe>
        <script>
            document.getElementById('target').onload = function() {
                setTimeout(() => {
                    const iframeDoc = document.getElementById('target').contentDocument;
                    if (iframeDoc && iframeDoc.body) {
                        document.body.innerHTML = iframeDoc.body.innerHTML;
                    }
                }, 2000);
            };
        </script>
    </body>
    </html>
`);
```

**技术要点:**
- 避免直接访问目标URL
- 通过iframe间接加载内容
- JavaScript动态内容提取
- 规避直接请求检测

#### 策略4: fetch API模拟AJAX请求
```javascript
// 核心代码位置: super_main.js:218-257
const result = await page.evaluate(async (targetUrl) => {
    try {
        const response = await fetch(targetUrl, {
            method: 'GET',
            headers: {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'max-age=0',
                'User-Agent': navigator.userAgent
            },
            credentials: 'omit'
        });

        if (response.ok) {
            const text = await response.text();
            return { success: true, content: text };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}, url);
```

**技术要点:**
- 使用浏览器原生fetch API
- 模拟AJAX请求特征
- 绕过页面导航检测
- 内容动态设置

#### 策略5: 镜像域名尝试
```javascript
// 核心代码位置: super_main.js:259-292
const mirrorUrls = [
    'http://nmpa.gov.cn/yaopin/ypggtg/index.html',
    'https://nmpa.gov.cn/yaopin/ypggtg/index.html'
];

for (const mirrorUrl of mirrorUrls) {
    try {
        console.log(`🔗 尝试镜像: ${mirrorUrl}`);
        const response = await page.goto(mirrorUrl, {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        if (response.status() === 200) {
            const content = await page.content();
            if (content.length > 2000) {
                console.log('✅ 策略5成功');
                return true;
            }
        }
    } catch (mirrorError) {
        console.log(`镜像失败: ${mirrorUrl} - ${mirrorError.message}`);
    }
}
```

**技术要点:**
- 尝试不同协议和域名
- HTTP/HTTPS双重尝试
- 备用访问路径
- 错误隔离处理

---

## 🔍 智能数据提取技术

### 国药准字格式识别
国药准字的标准格式：`国药准字 + 1个字母 + 8位数字`
例如：`国药准字Z20230001`

### 多策略提取算法
```javascript
// 核心代码位置: super_main.js:323-334
const strategies = [
    // 策略1: 标准国药准字格式
    /国药准字([A-Z]\d{8})[\s\S]{0,50}?([^\n\r]{2,50}?)(?:[\n\r]|$)/g,

    // 策略2: 宽松格式
    /国药准字([A-Z]\d{8})[：:\s]*([^\n\r]{2,50}?)/g,

    // 策略3: 包含各种字符的格式
    /国药准字([A-Z]\d{8})[^\n\r]*?([^\n\r]{2,50}?)/g,

    // 策略4: 表格格式 (扩展上下文200字符)
    /国药准字([A-Z]\d{8})[\s\S]{1,200}?([^\n\r]{2,100}?)(?:[\n\r]|$)/g,

    // 策略5: 括号格式
    /国药准字([A-Z]\d{8})\s*[（\(][^）\)]*[）\)][\s\S]*?([^\n\r]{2,50}?)/g
];
```

### 数据清理和标准化
```javascript
// 药品名称清理
name = name.replace(/[，。、；：""''（）【】\[\]《》]/g, '').trim();

// 数据结构标准化
results.push({
    code: code,                    // 国药准字编号
    zh: name,                     // 中文名称
    en: '',                       // 英文名称 (预留)
    source: `strategy_${i + 1}`,  // 数据来源策略
    rawMatch: match[0]           // 原始匹配文本
});
```

### 数据去重机制
```javascript
// 基于国药准字编号去重
const uniqueResults = [];
const seen = new Set();

results.forEach(item => {
    const key = item.code;
    if (!seen.has(key)) {
        seen.add(key);
        uniqueResults.push(item);
    }
});
```

---

## 🔗 智能链接发现系统

### 相关性分析算法
```javascript
// 核心代码位置: super_main.js:400-420
// 药品相关关键词
const drugKeywords = [
    '药品', '批准', '查询', '目录', '数据库', '准字', '说明书', '注册', '备案',
    'drug', 'approval', 'database', 'catalog', 'license', 'registration',
    '通告', '公示', '公告', '名单', '清单'
];

// NMPA特定路径模式
const nmpaPatterns = [
    /\/yaopin\//,           // 药品频道
    /\/yp[a-z]+\//,         // 药品缩写路径
    /\/WS\d+\//,           // 药品标准文档
    /\/CL\d+\//,           // 药品临床文档
    /\/药品\//,            // 中文药品路径
    /\/query\//,           // 查询接口
    /\/search\//,          // 搜索页面
    /\/list\//,            // 列表页面
    /\/data\//,            // 数据页面
    /\/tg\//,              // 通告
    /\/gg\//,              // 公告
    /\/gs\//               // 公示
];
```

### 链接评分机制
```javascript
// 链接相关性评分
links.forEach(link => {
    const href = link.getAttribute('href');
    const text = link.innerText.trim();

    // 关键词匹配得分
    const keywordScore = drugKeywords.reduce((score, keyword) => {
        return score + (text.toLowerCase().includes(keyword.toLowerCase()) ? 1 : 0);
    }, 0);

    // 路径模式匹配得分
    const patternScore = nmpaPatterns.reduce((score, pattern) => {
        return score + (pattern.test(href) ? 2 : 0);
    }, 0);

    // 域名相关性得分
    const domainScore = (href.includes('nmpa.gov.cn') || href.includes(currentDomain)) ? 3 : 0;

    // 综合评分
    const totalScore = keywordScore + patternScore + domainScore;
    if (totalScore > 0) {
        results.push({ url: fullUrl, score: totalScore });
    }
});

// 按评分排序并返回前15个
return uniqueLinks.slice(0, 15);
```

---

## 🛡️ 反检测技术详解

### 浏览器指纹伪装
```javascript
// 核心代码位置: super_main.js:527-594
// 1. 隐藏webdriver属性
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 2. 模拟浏览器插件
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' }
    ]
});

// 3. 模拟语言设置
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// 4. 模拟操作系统平台
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});
```

### Chrome对象模拟
```javascript
// 模拟Chrome运行时对象
window.chrome = {
    runtime: {
        onConnect: undefined,
        onMessage: undefined
    },
    loadTimes: function() {
        return {
            requestTime: Date.now() / 1000 - Math.random(),
            startLoadTime: Date.now() / 1000 - Math.random(),
            commitLoadTime: Date.now() / 1000 - Math.random(),
            finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
            finishLoadTime: Date.now() / 1000 - Math.random(),
            firstPaintTime: Date.now() / 1000 - Math.random(),
            firstPaintAfterLoadTime: 0,
            navigationType: 'Other'
        };
    },
    csi: function() {
        return {
            startE: Date.now(),
            onloadT: Date.now(),
            pageT: Date.now(),
            tran: 15
        };
    }
};
```

### 自动化检测清除
```javascript
// 移除常见的自动化检测标记
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
```

### 浏览器启动参数优化
```javascript
// 核心代码位置: super_main.js:486-513
const browser = await chromium.launch({
    headless: true,
    executablePath: '/home/langchao6/.cache/ms-playwright/chromium-1187/chrome-linux/chrome',
    args: [
        '--no-sandbox',                              // 禁用沙箱
        '--disable-setuid-sandbox',                   // 禁用UID沙箱
        '--disable-blink-features=AutomationControlled',  // 禁用自动化控制
        '--disable-web-security',                     // 禁用Web安全
        '--disable-features=VizDisplayCompositor',    // 禁用可视化组件
        '--disable-background-networking',            // 禁用后台网络
        '--disable-default-apps',                     // 禁用默认应用
        '--disable-extensions',                       // 禁用扩展
        '--disable-sync',                            // 禁用同步
        '--disable-translate',                       // 禁用翻译
        '--hide-scrollbars',                        // 隐藏滚动条
        '--metrics-recording-only',                 // 仅记录指标
        '--mute-audio',                             // 静音
        '--no-first-run',                           // 跳过首次运行
        '--safebrowsing-disable-auto-update',       // 禁用安全浏览自动更新
        '--ignore-certificate-errors',              // 忽略证书错误
        '--ignore-ssl-errors',                      // 忽略SSL错误
        '--ignore-certificate-errors-spki-list',    // 忽略证书错误SPKI列表
        '--disable-dev-shm-usage',                  // 禁用共享内存
        '--disable-gpu',                            // 禁用GPU
        '--no-zygote',                              // 禁用Zygote进程
        '--single-process'                          // 单进程模式
    ]
});
```

---

## 📊 数据输出和管理

### JSONL格式输出
```javascript
// 核心代码位置: super_main.js:458-479
const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
const filename = `drugs_${timestamp}.jsonl`;
const filepath = path.join(OUTPUT_DIR, filename);

// JSONL格式: 每行一个JSON对象
const jsonlData = drugs.map(drug => JSON.stringify(drug)).join('\n');
await fs.writeFile(filepath, jsonlData, 'utf8');

// 追加到汇总文件
const mainFile = path.join(OUTPUT_DIR, 'drugs_all.jsonl');
await fs.appendFile(mainFile, jsonlData + '\n', 'utf8');
```

### 数据结构标准
```json
{
  "code": "国药准字Z20230001",
  "zh": "药品中文名称",
  "en": "",
  "source": "strategy_1",
  "rawMatch": "国药准字Z20230001 药品中文名称"
}
```

### 文件命名规范
- **时间戳文件**: `drugs_20251014T083000.jsonl`
- **汇总文件**: `drugs_all.jsonl`
- **输出目录**: `outputs/`

---

## 🚀 部署和运行指南

### 环境要求
```bash
# 系统要求
Ubuntu 20.04+ / CentOS 8+ / Debian 11+
Node.js >= 18.0.0
内存 >= 2GB
磁盘空间 >= 1GB

# 网络要求
稳定的互联网连接
支持HTTPS
无需代理（如需代理请配置）
```

### 安装步骤
```bash
# 1. 克隆项目
git clone <repository-url>
cd nmpa_crawler_nodejs

# 2. 安装依赖
npm install playwright fs-extra

# 3. 安装Playwright浏览器
npx playwright install chromium

# 4. 验证安装
node -v  # 应该显示 v18.x.x 或更高
npx playwright --version  # 验证Playwright安装
```

### 运行命令
```bash
# 运行超级增强版（推荐）
node super_main.js

# 运行其他版本
node enhanced_main.js    # 增强版
node hybrid_main.js      # 混合策略版
node data_main.js        # 数据专用版
node simple_main.js      # 简单版
```

### 监控和日志
```bash
# 实时监控输出
node super_main.js 2>&1 | tee crawler.log

# 后台运行
nohup node super_main.js > crawler.log 2>&1 &

# 查看进程
ps aux | grep node

# 停止进程
pkill -f "node super_main.js"
```

---

## 🔧 配置和自定义

### 站点配置修改
```javascript
// 修改 super_main.js 第6-16行
const SITE_CONFIG = {
    nmpa: {
        code: "LG0001",
        domain: "www.nmpa.gov.cn",
        name: "国家药品监督管理局",
        pageList: [
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",    // 药品公告通知
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html"     // 药品监管动态
            // 添加更多页面...
        ]
    },
    // 添加其他站点...
};
```

### 用户代理池自定义
```javascript
// 修改 super_main.js 第26-35行
const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    // 添加更多User-Agent...
];
```

### 输出目录配置
```javascript
// 修改 super_main.js 第18-24行
const OUTPUT_DIR = 'outputs';    // 输出目录
const TEMP_DIR = 'downloads';    // 临时下载目录

// 确保目录存在
fs.ensureDirSync(OUTPUT_DIR);
fs.ensureDirSync(TEMP_DIR);
```

---

## 📈 性能优化和监控

### 性能指标监控
```javascript
// 监控关键指标
const performanceMetrics = {
    startTime: Date.now(),
    pageCount: 0,
    successCount: 0,
    failureCount: 0,
    dataCount: 0,

    record(page, success, dataCount = 0) {
        this.pageCount++;
        if (success) this.successCount++;
        else this.failureCount++;
        this.dataCount += dataCount;
    },

    getReport() {
        const duration = Date.now() - this.startTime;
        return {
            duration: `${Math.round(duration / 1000)}s`,
            successRate: `${Math.round(this.successCount / this.pageCount * 100)}%`,
            dataEfficiency: `${Math.round(this.dataCount / this.pageCount)}`
        };
    }
};
```

### 内存管理优化
```javascript
// 页面资源及时释放
try {
    const page = await context.newPage();
    // 执行页面操作...
} finally {
    await page.close();  // 确保页面关闭
}

// 浏览器上下文管理
const context = await browser.newContext();
try {
    // 执行爬取任务...
} finally {
    await context.close();
}
```

### 错误恢复机制
```javascript
// 重试机制
async function retryOperation(operation, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await operation();
        } catch (error) {
            console.log(`操作失败，重试 ${i + 1}/${maxRetries}: ${error.message}`);
            if (i === maxRetries - 1) throw error;
            await page.waitForTimeout(2000 * (i + 1));  // 递增延迟
        }
    }
}
```

---

## 🚨 故障排除指南

### 常见问题和解决方案

#### 1. 412错误频繁出现
**症状**: 所有策略都返回412状态码
**解决方案**:
```javascript
// 增加延迟时间
await page.waitForTimeout(randomDelay(8000, 15000));

// 使用更真实的请求头
const headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
};
```

#### 2. 超时错误
**症状**: page.goto超时
**解决方案**:
```javascript
// 增加超时时间
const response = await page.goto(url, {
    waitUntil: 'domcontentloaded',
    timeout: 120000  // 2分钟
});

// 或者使用更宽松的等待条件
const response = await page.goto(url, {
    waitUntil: 'commit',  // 只要请求提交即可
    timeout: 60000
});
```

#### 3. 内存不足
**症状**: Node.js进程内存溢出
**解决方案**:
```bash
# 增加Node.js内存限制
node --max-old-space-size=4096 super_main.js

# 或者在代码中优化
// 及时释放不需要的对象
await page.close();
await context.clearCookies();
```

#### 4. 数据提取失败
**症状**: 页面访问成功但提取不到药品数据
**解决方案**:
```javascript
// 调试页面内容
const content = await page.content();
console.log('页面内容长度:', content.length);
console.log('页面内容预览:', content.substring(0, 1000));

// 检查页面是否完全加载
await page.waitForLoadState('networkidle');
await page.waitForTimeout(5000);
```

### 调试模式启用
```javascript
// 启用调试模式
const browser = await chromium.launch({
    headless: false,  // 显示浏览器窗口
    slowMo: 1000,     // 慢速执行
    devtools: true    // 开启开发者工具
});
```

### 日志级别配置
```javascript
// 配置详细日志
console.log('🚀 启动超级增强版NMPA药品数据爬虫');
console.log('📁 输出目录:', OUTPUT_DIR);
console.log(`🎯 站点: ${siteConfig.name} (${siteConfig.code})`);
console.log(`📋 页面数量: ${pageList.length}`);

// 错误日志
console.error('处理页面失败:', url, error.message);

// 成功日志
console.log(`✅ 策略${strategy}成功`);
console.log(`📦 提取到 ${drugs.length} 个药品信息`);
```

---

## 📊 结果分析和报告

### 数据质量评估
```javascript
// 数据质量指标
const qualityMetrics = {
    totalRecords: drugs.length,
    validCodes: drugs.filter(d => /^国药准字[A-Z]\d{8}$/.test(d.code)).length,
    validNames: drugs.filter(d => d.zh && d.zh.length >= 2).length,
    uniqueCodes: [...new Set(drugs.map(d => d.code))].length,

    getQualityScore() {
        return Math.round(
            (this.validCodes / this.totalRecords * 40) +
            (this.validNames / this.totalRecords * 30) +
            (this.uniqueCodes / this.totalRecords * 30)
        );
    }
};
```

### 统计报告生成
```javascript
// 生成运行报告
const report = {
    timestamp: new Date().toISOString(),
    duration: `${Math.round((Date.now() - startTime) / 1000)}s`,
    pagesProcessed: pageList.length,
    successfulPages: successCount,
    totalDrugsExtracted: totalDrugs,
    averageDrugsPerPage: Math.round(totalDrugs / successCount),
    strategiesUsed: successfulStrategies,
    outputFiles: generatedFiles,

    performance: {
        successRate: `${Math.round(successCount / pageList.length * 100)}%`,
        extractionRate: `${Math.round(totalDrugs / successCount)} drugs/page`,
        averageResponseTime: `${Math.round(avgResponseTime)}ms`
    }
};
```

---

## 🔮 未来扩展计划

### 短期优化 (1-2周)
- [ ] 添加更多NMPA页面支持
- [ ] 优化数据提取算法准确率
- [ ] 增加更多反检测技术
- [ ] 实现分布式爬取支持

### 中期发展 (1-2月)
- [ ] 支持其他药品监管机构
- [ ] 添加药品说明书PDF解析
- [ ] 实现数据增量更新
- [ ] 添加API接口服务

### 长期规划 (3-6月)
- [ ] 机器学习数据质量评估
- [ ] 实时监控和报警系统
- [ ] 数据可视化界面
- [ ] 云端部署和弹性扩展

---

## 📞 技术支持和维护

### 联系方式
- **技术文档**: 查看本文档和相关README文件
- **问题反馈**: 通过项目Issues提交
- **更新日志**: 关注项目commits和releases

### 维护建议
1. **定期更新**: 每月更新依赖和浏览器版本
2. **监控运行**: 建立日志监控和报警机制
3. **数据备份**: 定期备份爬取的数据
4. **性能优化**: 根据运行情况调整参数

### 版本记录
- **v2.0 Super Enhanced** - 2025年10月14日
  - 实现5层412绕过策略
  - 添加智能反检测技术
  - 优化数据提取算法
  - 完善监控和日志系统

- **v1.0 Basic** - 2025年10月14日
  - 基础爬虫功能
  - 简单数据提取
  - 基本错误处理

---

## 📄 许可证和使用条款

### 使用许可
本项目仅供学习和研究使用，请遵守以下条款：
1. 遵守目标网站的robots.txt和服务条款
2. 合理控制爬取频率，避免对服务器造成压力
3. 不得用于商业用途或数据贩卖
4. 使用者需自行承担使用风险

### 免责声明
本项目仅提供技术实现，不保证：
1. 100%的爬取成功率
2. 数据的绝对准确性
3. 服务的持续可用性
4. 符合所有法律法规

使用者应确保：
1. 符合当地法律法规要求
2. 获得必要的使用授权
3. 合理使用获取的数据
4. 承担相应的法律责任

---

*文档最后更新: 2025年10月14日*
*版本: v2.0 Super Enhanced*