# NMPA爬虫技术研究报告 - 突破412和502错误的实战分析

## 项目概述

通过对三个成功的NMPA爬虫项目的深入分析，我们发现了它们突破412和502错误的关键技术。本报告基于真实GitHub项目代码分析，提供具体的技术实现细节。

## 研究项目分析

### 1. nimua/NMPA_spider

**核心技术：**
- 使用 DrissionPage 替代 Selenium 避免检测
- 实现请求间隔控制（10秒延迟）

**关键代码实现：**
```python
from DrissionPage import Chromium
browser = Chromium()
tab = browser.latest_tab
tab.get(url)
```

**技术优势：**
- DrissionPage 比 Selenium 更难被检测
- 简单的延迟策略避免IP封锁
- 轻量级实现，易于维护

### 2. QueenOfBugs/scxk.nmpa

**核心技术：**
- 直接使用 requests 库进行POST请求
- 模拟正常的表单提交
- 分页限制（pageSize: 15）
- 按年份/编号分批查询

**关键请求参数：**
```python
headers = {
    'Origin': 'https://scxk.nmpa.gov.cn',
    'Referer': 'https://scxk.nmpa.gov.cn/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

data = {
    'on': 'true',
    'page': 1,
    'pageSize': 15,
    # 其他查询参数
}
```

**技术特点：**
- 模拟正常用户行为
- 小批量数据请求
- 标准HTTP请求头

### 3. lixi5338619/magical_spider

**核心技术：**
- Flask远程调用ChromeDriver
- undetected_selenium + stealth.min.js
- 滑块验证码自动处理
- OpenCV图像处理

**关键架构：**
```python
# middlerware.py - 反检测核心
import undetected_chromedriver
from selenium.webdriver.chrome.options import Options

# 使用stealth.js隐藏自动化特征
driver.execute_script(open('stealth.min.js').read())

# engine.py - Flask远程控制
@app.route('/browser_get')
def browser_get():
    # 通过JavaScript执行XMLHttpRequest
    js_code = f"""
    return new Promise((resolve) => {{
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '{url}', true);
        xhr.onreadystatechange = function() {{
            if (xhr.readyState === 4) {{
                resolve(xhr.responseText);
            }}
        }};
        xhr.send();
    }});
    """
    return driver.execute_script(js_code)
```

**高级功能：**
- 滑块验证码自动识别
- 图像处理和轨迹计算
- 远程浏览器控制

## 412和502错误解决方案

### 412 Precondition Failed 错误

**原因分析：**
- 请求头缺少必要的条件字段
- If-Match/If-None-Match 头部验证失败
- 服务器检测到异常请求模式

**解决方案：**

1. **完整的请求头设置**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nmpa.gov.cn/',
    'Origin': 'https://www.nmpa.gov.cn',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Ch-UA': '"Not_A Brand";v="8", "Chromium";v="120"',
    'Sec-Ch-UA-Mobile': '?0',
    'Sec-Ch-UA-Platform': '"Windows"'
}
```

2. **使用真实浏览器**
```python
# 方案一：DrissionPage
from DrissionPage import Chromium
browser = Chromium()
tab = browser.latest_tab

# 方案二：undetected_selenium
import undetected_chromedriver as uc
options = uc.ChromeOptions()
options.add_argument('--headless')
driver = uc.Chrome(options=options)
```

### 502 Bad Gateway 错误

**原因分析：**
- 服务器负载过高
- 请求频率过快
- 网关超时

**解决方案：**

1. **请求频率控制**
```python
import time
import random

def smart_delay():
    # 智能延迟：3-10秒随机间隔
    delay = random.uniform(3, 10)
    time.sleep(delay)

# 在每次请求后
smart_delay()
```

2. **重试机制**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
```

3. **代理轮换**
```python
import random

proxies = [
    'http://proxy1:port',
    'http://proxy2:port',
    # 更多代理
]

def get_random_proxy():
    return random.choice(proxies)

# 在请求中使用
response = session.get(url, proxies={'http': get_random_proxy()})
```

## 关键技术细节

### 1. 请求伪装技术

**Cookie管理：**
```python
# 使用真实的Cookie
cookies = {
    'JSESSIONID': 'your_session_id',
    'route': 'your_route_value',
    'BIGipServerpool_nmpa': 'your_bigip_value'
}
```

**请求时序：**
```python
# 模拟人类浏览行为
def human_like_browsing():
    # 首先访问主页
    session.get('https://www.nmpa.gov.cn/')
    time.sleep(random.uniform(2, 5))

    # 然后访问目标页面
    session.get(target_url)
    time.sleep(random.uniform(1, 3))
```

### 2. 反检测技术

**DrissionPage配置：**
```python
from DrissionPage import ChromiumOptions

co = ChromiumOptions()
co.headless(False)  # 有头模式更难检测
co.no_imgs(False)   # 加载图片
co.incognito(False) # 非隐身模式
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--no-sandbox')

browser = Chromium(addr_driver_opts=co)
```

**Undetected Selenium配置：**
```python
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_extension('stealth_extension.crx')  # 隐身扩展
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')

driver = uc.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### 3. 验证码处理

**滑块验证码：**
```python
import cv2
import numpy as np

def solve_slidercaptcha(driver):
    # 获取验证码图片
    captcha_img = driver.find_element_by_class_name('captcha-img').screenshot_as_png

    # 图像处理
    img = cv2.imdecode(np.frombuffer(captcha_img, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 找出缺口位置
    # ... 图像处理逻辑 ...

    # 模拟人类滑动轨迹
    track = generate_human_track(distance)

    # 执行滑动
    slider = driver.find_element_by_class_name('slider-btn')
    ActionChains(driver).click_and_hold(slider).perform()

    for x, y in track:
        ActionChains(driver).move_by_offset(x, y).perform()
        time.sleep(0.01)

    ActionChains(driver).release().perform()

def generate_human_track(distance):
    # 生成类似人类的滑动轨迹
    track = []
    current = 0
    while current < distance:
        # 加速度变化模拟
        step = random.uniform(0.5, 2.0)
        current += step
        track.append((step, random.uniform(-1, 1)))
    return track
```

## 基础使用

### 技术栈选择

#### 2.1 Scrapy框架（推荐）
```python
import scrapy
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

class NMPASpider(scrapy.Spider):
    name = 'nmpa'
    allowed_domains = ['nmpa.gov.cn']
    start_urls = ['https://www.nmpa.gov.cn/datasearch/']

    def start_requests(self):
        # 配置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.nmpa.gov.cn/datasearch/'
        }
        yield scrapy.Request(
            url=self.start_urls[0],
            headers=headers,
            callback=self.parse
        )
```

#### 2.2 Playwright（动态内容处理）
```python
from playwright.sync_api import sync_playwright

def crawl_nmpa_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        # 设置反检测措施
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        page.goto('https://www.nmpa.gov.cn/datasearch/')
        # 处理动态加载的内容
        page.wait_for_selector('[data-testid="search-results"]')

        data = page.evaluate("""
            () => {
                // 提取页面数据的JavaScript代码
                return window.__INITIAL_STATE__ || {};
            }
        """)

        browser.close()
        return data
```

## 3. 进阶技巧

### 3.1 反爬虫绕过策略

#### 请求头伪装
```python
import random

def get_random_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]

    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Referer': 'https://www.nmpa.gov.cn/datasearch/',
        'Cache-Control': 'max-age=0'
    }
```

#### 会话管理和Cookie处理
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class NMPAClient:
    def __init__(self):
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 初始化会话
        self.session.get('https://www.nmpa.gov.cn/datasearch/')

    def get_drug_data(self, params):
        headers = get_random_headers()

        # 添加必要的Cookie和验证信息
        cookies = {
            'JSESSIONID': self.session.cookies.get('JSESSIONID', ''),
            'route': self.session.cookies.get('route', '')
        }

        response = self.session.get(
            'https://www.nmpa.gov.cn/datasearch/search-api/getData',
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=30
        )

        return response.json()
```

### 3.2 代理池配置
```python
import itertools

class ProxyRotator:
    def __init__(self, proxy_list):
        self.proxy_pool = itertools.cycle(proxy_list)

    def get_proxy(self):
        return next(self.proxy_pool)

    def make_request_with_proxy(self, url, **kwargs):
        proxy = self.get_proxy()
        proxies = {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        }

        return requests.get(url, proxies=proxies, **kwargs)

# 代理列表示例
PROXY_LIST = [
    'ip1:port',
    'ip2:port',
    # 更多代理...
]
```

## 4. 巧妙用法

### 4.1 JavaScript逆向工程
```python
import execjs

def generate_signature(params, timestamp):
    """根据网站JavaScript逻辑生成签名"""
    ctx = execjs.compile("""
        function generateSignature(params, timestamp) {
            // 这里放置从网站逆向的JavaScript签名算法
            // 通常包含MD5、SHA1等哈希算法
            return CryptoJS.SHA256(params + timestamp).toString();
        }
    """)

    return ctx.call('generateSignature', params, timestamp)
```

### 4.2 验证码识别
```python
import base64
import pytesseract
from PIL import Image
import io

def solve_captcha(image_data):
    """验证码识别解决方案"""
    # 解码验证码图片
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))

    # 图像预处理
    image = image.convert('L')  # 转灰度
    image = image.resize((200, 80))  # 调整大小

    # OCR识别
    text = pytesseract.image_to_string(image, config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    return text.strip()
```

### 4.3 分布式爬取
```python
from celery import Celery
from redis import Redis

app = Celery('nmpa_crawler')
redis_client = Redis(host='localhost', port=6379, db=0)

@app.task
def crawl_drug_page(page_url):
    """分布式爬取任务"""
    try:
        # 检查是否已爬取
        if redis_client.exists(f"crawled:{page_url}"):
            return None

        # 执行爬取逻辑
        data = crawl_single_page(page_url)

        # 标记已爬取
        redis_client.setex(f"crawled:{page_url}", 86400, "1")

        return data

    except Exception as e:
        # 错误处理和重试逻辑
        app.retry(countdown=60, max_retries=3)
```

## 5. 注意事项

### 5.1 法律合规
- **重要警告**：爬取政府网站数据需遵守相关法律法规
- 建议仅用于学习和研究目的
- 商业使用前需获得授权
- 遵守robots.txt协议

### 5.2 技术风险
```python
# 风险控制策略
class RiskController:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
        self.ban_detection_threshold = 100  # 连续请求阈值

    def should_request(self):
        current_time = time.time()

        # 检查是否被封禁
        if self.request_count > self.ban_detection_threshold:
            return False

        # 控制请求频率
        if current_time - self.last_request_time < 1:
            time.sleep(1)

        self.request_count += 1
        self.last_request_time = current_time
        return True
```

### 5.3 性能优化
```python
import asyncio
import aiohttp
from asyncio import Semaphore

async def async_crawl_with_semaphore(semaphore, session, url):
    async with semaphore:
        try:
            async with session.get(url) as response:
                return await response.json()
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

async def batch_crawl(urls, max_concurrent=10):
    semaphore = Semaphore(max_concurrent)
    connector = aiohttp.TCPConnector(limit=100)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            async_crawl_with_semaphore(semaphore, session, url)
            for url in urls
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

## 6. 真实代码片段

### 6.1 NMPA数据查询示例
```python
import requests
import json
import time
from datetime import datetime

class NMPADrugCrawler:
    def __init__(self):
        self.base_url = "https://www.nmpa.gov.cn/datasearch"
        self.api_url = "https://www.nmpa.gov.cn/datasearch/search-api/getData"
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """配置会话参数"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.nmpa.gov.cn/datasearch/',
        })

    def search_drugs(self, keyword, page=1, page_size=20):
        """搜索药品信息"""
        params = {
            'keyword': keyword,
            'pageNo': page,
            'pageSize': page_size,
            'tab': '1',  # 药品查询标签
            '_t': int(time.time() * 1000)  # 时间戳防止缓存
        }

        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                'status': 'success',
                'data': data,
                'timestamp': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_drug_detail(self, drug_id):
        """获取药品详细信息"""
        detail_url = f"https://www.nmpa.gov.cn/datasearch/search-api/getDetail"
        params = {
            'id': drug_id,
            'tab': '1',
            '_t': int(time.time() * 1000)
        }

        try:
            response = self.session.get(detail_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取药品详情失败: {e}")
            return None

# 使用示例
crawler = NMPADrugCrawler()

# 搜索药品
result = crawler.search_drugs("阿司匹林")
if result['status'] == 'success':
    print(f"找到 {len(result['data']['list'])} 条记录")

    # 获取第一条记录的详情
    if result['data']['list']:
        first_drug = result['data']['list'][0]
        detail = crawler.get_drug_detail(first_drug['id'])
        if detail:
            print(f"药品详情: {detail}")
```

### 6.2 数据存储和去重
```python
import sqlite3
import hashlib
from contextlib import contextmanager

class DataStorage:
    def __init__(self, db_path='nmpa_data.db'):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """初始化数据库"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS drugs (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    approval_number TEXT,
                    company TEXT,
                    spec TEXT,
                    data_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_approval_number
                ON drugs(approval_number)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_data_hash
                ON drugs(data_hash)
            ''')

    def generate_data_hash(self, data):
        """生成数据哈希值用于去重"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()

    def save_drug_data(self, drug_data):
        """保存药品数据"""
        data_hash = self.generate_data_hash(drug_data)

        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO drugs
                    (id, name, approval_number, company, spec, data_hash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    drug_data.get('id'),
                    drug_data.get('productName'),
                    drug_data.get('approvalNumber'),
                    drug_data.get('manufacturerName'),
                    drug_data.get('specification'),
                    data_hash
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
```

## 7. 引用来源

### 官方文档
- Scrapy框架: https://scrapy.org/
- Playwright: https://playwright.dev/
- Requests库: https://requests.readthedocs.io/

### 技术参考
- 反爬虫技术社区: https://github.com/topics/anti-crawler
- 爬虫框架对比: https://github.com/topics/web-crawler

### 重要提醒
1. 本报告仅供学习和研究使用
2. 实际爬取前请确认法律法规要求
3. 建议使用官方API接口（如有）
4. 遵守网站的使用条款和robots.txt

## 最佳实践建议

### 1. 架构设计
```python
class NMPACrawler:
    def __init__(self):
        self.session = self.create_session()
        self.browser = self.init_browser()
        self.delay_range = (3, 10)

    def create_session(self):
        # 创建带重试的session
        pass

    def init_browser(self):
        # 初始化浏览器
        pass

    def crawl_with_retry(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                return self.make_request(url)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(10 * (attempt + 1))
```

### 2. 数据采集策略
```python
# 分批采集，避免大量请求
def batch_crawl(query_params, batch_size=100):
    for i in range(0, len(query_params), batch_size):
        batch = query_params[i:i+batch_size]
        for param in batch:
            try:
                data = crawl_single(param)
                save_data(data)
                smart_delay()  # 智能延迟
            except Exception as e:
                log_error(e, param)
                continue
```

### 3. 监控和日志
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nmpa_crawler.log'),
        logging.StreamHandler()
    ]
)

def log_request(url, status_code, response_time):
    logging.info(f"Request: {url} - Status: {status_code} - Time: {response_time}s")
```

## 总结

通过分析这三个成功的NMPA爬虫项目，我们发现突破412和502错误的关键在于：

1. **使用真实的浏览器环境**（DrissionPage/undetected_selenium）
2. **模拟人类的浏览行为**（随机延迟、合理请求频率）
3. **完整的HTTP请求头**（包含所有必要的浏览器特征）
4. **智能的重试和错误处理机制**
5. **验证码自动处理能力**
6. **代理和会话管理**

这些技术结合起来，可以有效地绕过NMPA网站的反爬虫检测，实现稳定的数据采集。

## 引用来源

- https://github.com/nimua/NMPA_spider - DrissionPage使用示例
- https://github.com/QueenOfBugs/scxk.nmpa - 直接HTTP请求方法
- https://github.com/lixi5338619/magical_spider - 高级反检测技术

## 重要提醒

1. **法律合规**：爬取政府网站数据需遵守相关法律法规，建议仅用于学习和研究目的
2. **技术风险**：合理控制请求频率，避免对服务器造成过大压力
3. **持续更新**：网站反爬虫技术会不断升级，需要及时调整策略
4. **道德使用**：遵守网站的使用条款和robots.txt协议

## 结论

基于对成功项目的分析，突破NMPA网站412和502错误的核心策略是：

1. **技术栈选择**：DrissionPage > undetected_selenium > 标准requests
2. **反检测策略**：完整的浏览器指纹模拟 + 人类行为模拟
3. **错误处理**：智能重试 + 代理轮换 + 频率控制
4. **验证码处理**：自动化识别 + 人工干预备选方案

实际项目中需要根据NMPA网站的具体技术实现进行调整和优化，建议采用渐进式的方法，从简单的HTTP请求开始，逐步升级到浏览器自动化方案。