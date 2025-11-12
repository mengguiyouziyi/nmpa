# NMPA（国家药监局）爬虫技术调研报告

## 调研概述

本报告基于对GitHub、技术社区和爬虫相关资源的深入调研，重点关注2024-2025年NMPA爬虫的技术发展和实际应用情况。

## 调研结果

### 1. 公开项目现状

**调研发现：**
- GitHub上公开的专门针对NMPA的爬虫项目相对较少
- 大多数相关项目采用私有化方式，不在公开平台分享
- 找到1个相关项目：`guidelines-crawler`（针对医疗器械指南，2025年1月更新）

**原因分析：**
- NMPA网站具有较强的反爬虫机制
- 药品数据敏感性较高，开发者倾向于私有化部署
- 反爬虫技术更新频繁，公开项目容易失效

### 2. NMPA网站技术特点

**网站架构：**
- 域名：`nmpa.gov.cn`
- 采用前后端分离架构
- 前端使用现代JavaScript框架
- 数据通过API接口动态获取

**反爬虫机制：**
- 动态签名算法验证
- 请求频率限制
- User-Agent检测
- IP地址追踪
- 可能包含验证码机制

### 3. 技术方案分析

#### 3.1 主流技术栈

**前端自动化方案：**
- **Selenium WebDriver**：成熟的浏览器自动化工具
- **Playwright**：微软开发的现代化浏览器自动化框架
- **Puppeteer**：Chrome无头浏览器控制

**数据处理方案：**
- **BeautifulSoup4**：HTML解析
- **Scrapy**：完整的爬虫框架
- **requests + aiohttp**：HTTP客户端

#### 3.2 反爬虫绕过技术

**签名算法破解：**
```javascript
// 示例：动态签名生成逻辑
function generateSignature(timestamp, nonce) {
    // 通常需要逆向分析网站JS代码
    const params = {
        timestamp: timestamp,
        nonce: nonce,
        // 其他参数...
    };

    // MD5/SHA256等加密算法
    return crypto.createHash('md5')
        .update(JSON.stringify(params))
        .digest('hex');
}
```

**请求头伪装：**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nmpa.gov.cn/',
    'X-Requested-With': 'XMLHttpRequest'
}
```

### 4. 技术实现方案

#### 4.1 基础实现架构

```python
# NMPA爬虫基础架构示例
import requests
import json
import time
import hashlib
import random
from urllib.parse import urlencode

class NMPACrawler:
    def __init__(self):
        self.base_url = "https://www.nmpa.gov.cn"
        self.api_url = "https://api.nmpa.gov.cn"  # 需要逆向分析获取
        self.session = requests.Session()
        self.session.headers.update(self.get_headers())

    def get_headers(self):
        """获取伪装请求头"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def generate_signature(self, params):
        """生成请求签名（需要逆向分析）"""
        # 这里需要根据实际网站算法实现
        timestamp = str(int(time.time() * 1000))
        nonce = ''.join(random.choices('0123456789abcdef', k=16))

        signature_data = {
            'timestamp': timestamp,
            'nonce': nonce,
            **params
        }

        # 示例签名算法（需要根据实际情况调整）
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted(signature_data.items())])
        signature = hashlib.md5(sign_str.encode()).hexdigest()

        return {
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce
        }

    def request_api(self, endpoint, params=None):
        """API请求封装"""
        if params is None:
            params = {}

        # 生成签名
        auth_params = self.generate_signature(params)
        params.update(auth_params)

        # 添加延时避免频率限制
        time.sleep(random.uniform(1, 3))

        try:
            response = self.session.get(
                f"{self.api_url}/{endpoint}",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
```

#### 4.2 数据获取示例

```python
class NMPADrugCrawler(NMPACrawler):
    def __init__(self):
        super().__init__()
        self.drug_api_endpoints = {
            'drug_list': '/datasearch/data/face/base/queryDrug',
            'drug_detail': '/datasearch/data/face/base/queryDrugDetail',
        }

    def search_drugs(self, keyword, page=1, page_size=20):
        """搜索药品信息"""
        params = {
            'keyword': keyword,
            'pageNo': page,
            'pageSize': page_size,
            'sort': '',
            'sortOrder': ''
        }

        return self.request_api(self.drug_api_endpoints['drug_list'], params)

    def get_drug_detail(self, drug_id):
        """获取药品详细信息"""
        params = {
            'id': drug_id
        }

        return self.request_api(self.drug_api_endpoints['drug_detail'], params)

    def batch_download_drugs(self, keywords, output_file='nmpa_drugs.json'):
        """批量下载药品数据"""
        all_drugs = []

        for keyword in keywords:
            print(f"正在搜索关键词: {keyword}")

            page = 1
            while True:
                result = self.search_drugs(keyword, page)

                if not result or not result.get('data'):
                    break

                drugs = result['data'].get('list', [])
                if not drugs:
                    break

                all_drugs.extend(drugs)
                print(f"  第{page}页: 获取{len(drugs)}条数据")

                # 保存进度
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_drugs, f, ensure_ascii=False, indent=2)

                page += 1

                # 随机延时
                time.sleep(random.uniform(2, 5))

        return all_drugs
```

#### 4.3 Playwright现代化方案

```python
# 使用Playwright的现代化爬虫实现
from playwright.async_api import async_playwright
import asyncio
import json

class AsyncNMPACrawler:
    def __init__(self):
        self.base_url = "https://www.nmpa.gov.cn"

    async def setup_browser(self):
        """设置浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # 设为False可以看到浏览器操作
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )

        self.page = await self.context.new_page()

        # 反检测脚本
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def search_drugs_with_browser(self, keyword):
        """使用浏览器搜索药品"""
        # 访问搜索页面
        await self.page.goto(f"{self.base_url}/datasearch/home")

        # 等待页面加载
        await self.page.wait_for_selector('input[placeholder*="药品"]')

        # 输入搜索关键词
        await self.page.fill('input[placeholder*="药品"]', keyword)

        # 点击搜索按钮
        await self.page.click('button[type="submit"]')

        # 等待结果加载
        await self.page.wait_for_selector('.drug-list')

        # 提取数据
        drugs = await self.page.evaluate("""
            () => {
                const items = Array.from(document.querySelectorAll('.drug-item'));
                return items.map(item => ({
                    name: item.querySelector('.drug-name')?.textContent,
                    approval: item.querySelector('.approval-number')?.textContent,
                    company: item.querySelector('.company')?.textContent,
                    spec: item.querySelector('.specification')?.textContent
                }));
            }
        """)

        return drugs

    async def close(self):
        """关闭浏览器"""
        await self.browser.close()
        await self.playwright.stop()

# 使用示例
async def main():
    crawler = AsyncNMPACrawler()
    await crawler.setup_browser()

    try:
        drugs = await crawler.search_drugs_with_browser("阿司匹林")
        print(f"找到 {len(drugs)} 个药品")
        for drug in drugs:
            print(f"- {drug['name']}: {drug['approval']}")
    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 高级技巧和最佳实践

#### 5.1 代理池管理

```python
import random
import requests
from concurrent.futures import ThreadPoolExecutor

class ProxyPool:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.bad_proxies = set()

    def load_proxies(self, proxy_list):
        """加载代理列表"""
        self.proxies = proxy_list

    def get_proxy(self):
        """获取可用代理"""
        available_proxies = [p for p in self.proxies if p not in self.bad_proxies]
        if not available_proxies:
            raise Exception("没有可用代理")

        return random.choice(available_proxies)

    def mark_bad(self, proxy):
        """标记坏代理"""
        self.bad_proxies.add(proxy)

    def test_proxy(self, proxy, timeout=10):
        """测试代理可用性"""
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy, 'https': proxy},
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False
```

#### 5.2 数据清洗和验证

```python
import re
import pandas as pd

class DataCleaner:
    @staticmethod
    def clean_drug_name(name):
        """清洗药品名称"""
        if not name:
            return None
        # 移除多余空格
        name = re.sub(r'\s+', ' ', name.strip())
        # 标准化药品名称格式
        return name

    @staticmethod
    def validate_approval_number(approval):
        """验证批准文号格式"""
        if not approval:
            return False
        # 国药准字格式验证
        pattern = r'^国药准字[A-Z][A-Z]\d{8}$'
        return bool(re.match(pattern, approval))

    @staticmethod
    def standardize_company(company):
        """标准化生产单位名称"""
        if not company:
            return None
        # 移除"有限公司"等后缀的变体
        company = re.sub(r'(有限公司|有限责任公司|股份有限公司)', '有限公司', company)
        return company.strip()

    def clean_drug_data(self, drug_list):
        """清洗药品数据"""
        cleaned_data = []

        for drug in drug_list:
            cleaned_drug = {
                'name': self.clean_drug_name(drug.get('name')),
                'approval_number': drug.get('approval_number'),
                'company': self.standardize_company(drug.get('company')),
                'specification': drug.get('specification'),
                'is_valid': self.validate_approval_number(drug.get('approval_number'))
            }
            cleaned_data.append(cleaned_drug)

        return cleaned_data
```

#### 5.3 增量更新机制

```python
import sqlite3
import hashlib
from datetime import datetime

class NMPADataUpdater:
    def __init__(self, db_path='nmpa_data.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drugs (
                id TEXT PRIMARY KEY,
                name TEXT,
                approval_number TEXT,
                company TEXT,
                specification TEXT,
                data_hash TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def calculate_hash(self, data):
        """计算数据哈希值"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def is_duplicate(self, drug_id, data_hash):
        """检查是否重复数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT data_hash FROM drugs WHERE id = ?
        ''', (drug_id,))

        result = cursor.fetchone()
        conn.close()

        return result and result[0] == data_hash

    def upsert_drug(self, drug_data):
        """插入或更新药品数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        drug_id = drug_data.get('id')
        data_hash = self.calculate_hash(drug_data)

        if self.is_duplicate(drug_id, data_hash):
            print(f"药品 {drug_id} 数据未变化，跳过")
            return False

        cursor.execute('''
            INSERT OR REPLACE INTO drugs
            (id, name, approval_number, company, specification, data_hash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            drug_id,
            drug_data.get('name'),
            drug_data.get('approval_number'),
            drug_data.get('company'),
            drug_data.get('specification'),
            data_hash,
            datetime.now()
        ))

        conn.commit()
        conn.close()

        print(f"更新药品数据: {drug_id}")
        return True
```

### 6. 法律合规和注意事项

#### 6.1 合规性要求

**重要提醒：**
- 爬虫行为必须遵守《网络安全法》等相关法律法规
- 不得对网站服务器造成过大负担
- 获取的数据不得用于商业用途
- 需要遵守网站的robots.txt规则
- 建议设置合理的访问频率（每秒不超过1次）

#### 6.2 技术风险

**常见问题：**
- IP被封禁
- 账号被限制
- 数据结构变化
- 反爬虫策略升级

**应对措施：**
- 使用代理池轮换IP
- 模拟真实用户行为
- 定期更新爬虫代码
- 设置错误重试机制

### 7. 监控和维护

#### 7.1 日志记录

```python
import logging
from datetime import datetime

class NMPACrawlerLogger:
    def __init__(self, log_file='nmpa_crawler.log'):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NMPACrawler')

    def log_request(self, url, status_code, response_time):
        """记录请求日志"""
        self.logger.info(f"请求: {url} | 状态: {status_code} | 耗时: {response_time}ms")

    def log_error(self, error, context=""):
        """记录错误日志"""
        self.logger.error(f"错误: {error} | 上下文: {context}")

    def log_data_count(self, count, data_type):
        """记录数据统计"""
        self.logger.info(f"获取{data_type}数据: {count}条")
```

#### 7.2 性能监控

```python
import time
import psutil
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        try:
            result = func(*args, **kwargs)
            status = "成功"
        except Exception as e:
            result = None
            status = f"失败: {str(e)}"
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            print(f"函数 {func.__name__}:")
            print(f"  状态: {status}")
            print(f"  耗时: {end_time - start_time:.2f}秒")
            print(f"  内存变化: {end_memory - start_memory:.2f}MB")

        return result
    return wrapper
```

### 8. 结论和建议

#### 8.1 技术选型建议

**推荐方案：**
1. **首选Playwright**：现代化、稳定、反检测能力强
2. **备选Selenium**：成熟稳定，社区支持好
3. **结合使用**：Playwright处理动态页面，requests处理API调用

#### 8.2 实施策略

**分阶段实施：**
1. **第一阶段**：网站分析，了解API结构和反爬虫机制
2. **第二阶段**：开发基础爬虫，实现数据获取
3. **第三阶段**：优化反爬虫绕过，提高稳定性
4. **第四阶段**：建立监控体系，确保长期稳定运行

#### 8.3 风险控制

**重要提醒：**
- 严格遵守相关法律法规
- 控制访问频率，避免对目标网站造成影响
- 定期备份重要数据
- 建立错误监控和报警机制

---

**免责声明：** 本报告仅用于技术研究和学习目的，使用者需要自行承担相关法律责任。建议在使用前咨询法律专业人士，确保合规性。