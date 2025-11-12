# -*- coding: utf-8 -*-
"""
Crawlee 风格的 Python NMPA 爬虫
基于 Node.js Crawlee 框架的设计理念，结合我们的反检测技术栈
"""

import asyncio
import json
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
# from pyquery import PyQuery as pq  # 不使用，改用原生 Playwright 选择器
import logging

# from config_manager import ConfigManager  # 改用简单的配置管理

class SimpleConfigManager:
    """简单的配置管理器"""
    def __init__(self, config_data):
        self.config_data = config_data if isinstance(config_data, dict) else {}

    def get(self, key, default=None):
        return self.config_data.get(key, default)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrawleeStyleNMPACrawler:
    """基于 Crawlee 设计理念的 Python NMPA 爬虫"""

    def __init__(self, config: SimpleConfigManager):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None

        # Crawlee 风格的配置
        self.navigation_timeout = config.get("navigation_timeout", 60000)  # 60秒
        self.request_handler_timeout = config.get("request_handler_timeout", 60000)  # 60秒
        self.max_request_retries = config.get("max_request_retries", 3)
        self.max_requests_per_crawl = config.get("max_pages", 50)
        self.max_concurrency = config.get("max_concurrency", 2)
        self.headless = config.get("headless", True)

        # 请求队列
        self.request_queue = asyncio.Queue()
        self.processed_urls = set()
        self.failed_urls = set()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "items_extracted": 0,
            "start_time": None,
            "end_time": None
        }

        # NMPA 特定配置
        self.nmpa_domain = "www.nmpa.gov.cn"
        self.nmpa_urls = [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",  # 监管工作
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",  # 公告通知
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",  # 法规文件
            "https://www.nmpa.gov.cn/yaopin/ypzhcjd/index.html",  # 政策解读
            "https://www.nmpa.gov.cn/zwfw/zwfwgggs/index.html",  # 政务服务公告
        ]

    async def start(self):
        """启动爬虫"""
        self.stats["start_time"] = datetime.now()
        logger.info("启动 Crawlee 风格的 NMPA 爬虫")

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 浏览器配置 - 类似 Crawlee 的 launchContext
            browser_options = {
                "headless": self.headless,
                "args": [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            }

            self.browser = await self.playwright.chromium.launch(**browser_options)

            # 创建上下文 - 反检测配置
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "permissions": ["geolocation", "notifications"],
                "ignore_https_errors": True,
            }

            self.context = await self.browser.new_context(**context_options)

            # 反检测脚本
            await self.context.add_init_script("""
                // 移除 webdriver 标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 伪造 Chrome 对象
                window.chrome = {
                    runtime: {}
                };

                // 伪造 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Cypress.resolveStatus('granted') }) :
                        originalQuery(parameters)
                );

                // 伪造 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        }
                    ]
                });

                // 伪造 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)

            logger.info("✅ Crawlee 风格爬虫启动成功")

        except Exception as e:
            logger.error(f"❌ 爬虫启动失败: {e}")
            await self.stop()
            raise

    async def stop(self):
        """停止爬虫"""
        self.stats["end_time"] = datetime.now()
        logger.info("正在停止爬虫...")

        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            # 打印统计信息
            self.print_stats()

        except Exception as e:
            logger.error(f"停止爬虫时出错: {e}")

    def print_stats(self):
        """打印统计信息"""
        duration = self.stats["end_time"] - self.stats["start_time"] if self.stats["end_time"] and self.stats["start_time"] else "未知"

        logger.info("=== Crawlee 风格爬虫统计 ===")
        logger.info(f"总请求数: {self.stats['total_requests']}")
        logger.info(f"成功请求: {self.stats['successful_requests']}")
        logger.info(f"失败请求: {self.stats['failed_requests']}")
        logger.info(f"提取条目: {self.stats['items_extracted']}")
        logger.info(f"运行时长: {duration}")
        logger.info(f"成功率: {self.stats['successful_requests'] / max(1, self.stats['total_requests']) * 100:.2f}%")

    async def add_requests(self, urls: List[str]):
        """添加请求到队列 - 类似 Crawlee 的 addRequests"""
        for url in urls:
            if url not in self.processed_urls:
                await self.request_queue.put(url)
                logger.info(f"添加请求到队列: {url}")

    async def request_handler(self, page: Page, url: str):
        """请求处理器 - 类似 Crawlee 的 requestHandler"""
        try:
            logger.info(f"处理请求: {url}")
            self.stats["total_requests"] += 1

            # 设置超时
            page.set_default_timeout(self.navigation_timeout)

            # 访问页面
            await page.goto(url, wait_until="domcontentloaded", timeout=self.navigation_timeout)

            # 等待关键元素
            try:
                await page.wait_for_selector('.list li', timeout=10000)
            except:
                logger.warning(f"未找到 .list li 选择器，尝试其他选择器")
                # 尝试其他可能的选择器
                selectors = ['.list-item', '.news-list', 'ul li', '[class*="list"]']
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        break
                    except:
                        continue

            # 判断页面类型
            if "index.html" in url:
                # 列表页面
                items = await self.extract_list_items(page, url)
                self.stats["items_extracted"] += len(items)

                # 添加详情页到队列
                for item in items:
                    if item.get('href') and item['href'] not in self.processed_urls:
                        await self.request_queue.put(item['href'])

            else:
                # 详情页面
                item = await self.extract_detail_item(page, url)
                if item:
                    self.stats["items_extracted"] += 1
                    logger.info(f"提取详情: {item.get('title', '未知标题')}")

            self.stats["successful_requests"] += 1
            self.processed_urls.add(url)

        except Exception as e:
            logger.error(f"处理请求失败 {url}: {e}")
            self.stats["failed_requests"] += 1
            self.failed_urls.add(url)

            # 重试逻辑
            if url not in self.failed_urls:
                logger.info(f"准备重试: {url}")
                await asyncio.sleep(random.uniform(2, 5))
                await self.request_queue.put(url)

    async def extract_list_items(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """提取列表页面的项目"""
        try:
            # 尝试多种选择器策略
            selectors = [
                '.list li',
                '.news-list li',
                '.content-list li',
                'ul li',
                '[class*="list-item"]'
            ]

            items = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"使用选择器 {selector} 找到 {len(elements)} 个元素")

                        for element in elements:
                            try:
                                # 提取标题和链接
                                title_element = await element.query_selector('a')
                                if title_element:
                                    title = await title_element.inner_text()
                                    href = await title_element.get_attribute('href')

                                    # 提取日期
                                    date_element = await element.query_selector('span, .date, .time')
                                    date = await date_element.inner_text() if date_element else ""

                                    # 处理相对链接
                                    if href and not href.startswith('http'):
                                        href = f"https://{self.nmpa_domain}{href}"

                                    items.append({
                                        'title': title.strip() if title else "",
                                        'href': href,
                                        'date': date.strip() if date else "",
                                        'source_url': url,
                                        'crawl_time': datetime.now().isoformat()
                                    })
                            except Exception as e:
                                logger.warning(f"提取单个项目时出错: {e}")
                                continue

                        if items:
                            break

                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue

            logger.info(f"从列表页 {url} 提取了 {len(items)} 个项目")
            return items

        except Exception as e:
            logger.error(f"提取列表项目失败 {url}: {e}")
            return []

    async def extract_detail_item(self, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """提取详情页面的内容"""
        try:
            # 等待页面加载
            await page.wait_for_selector('h1, h2, .title, .content', timeout=10000)

            # 提取标题
            title_selectors = ['h1', 'h2.title', '.title', '.article-title']
            title = ""
            for selector in title_selectors:
                try:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title = await title_element.inner_text()
                        title = title.strip()
                        if title:
                            break
                except:
                    continue

            # 提取内容
            content_selectors = ['.content', '.article-content', '.main-content', 'div[class*="content"]']
            content = ""
            for selector in content_selectors:
                try:
                    content_element = await page.query_selector(selector)
                    if content_element:
                        content = await content_element.inner_text()
                        content = content.strip()
                        if content:
                            break
                except:
                    continue

            # 提取发布时间
            time_selectors = ['.time', '.date', '.publish-time', '[class*="time"]', '[class*="date"]']
            publish_time = ""
            for selector in time_selectors:
                try:
                    time_element = await page.query_selector(selector)
                    if time_element:
                        publish_time = await time_element.inner_text()
                        publish_time = publish_time.strip()
                        if publish_time:
                            break
                except:
                    continue

            item = {
                'title': title,
                'content': content[:500] + "..." if len(content) > 500 else content,  # 限制内容长度
                'url': url,
                'publish_time': publish_time,
                'crawl_time': datetime.now().isoformat(),
                'type': 'detail'
            }

            return item

        except Exception as e:
            logger.error(f"提取详情内容失败 {url}: {e}")
            return None

    async def run(self, initial_urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """运行爬虫 - 类似 Crawlee 的 run"""
        if not initial_urls:
            initial_urls = self.nmpa_urls

        await self.start()

        try:
            # 添加初始请求
            await self.add_requests(initial_urls)

            # 处理请求队列
            processed_count = 0
            while not self.request_queue.empty() and processed_count < self.max_requests_per_crawl:
                # 创建新页面
                page = await self.context.new_page()

                try:
                    url = await self.request_queue.get()

                    # 处理请求
                    await self.request_handler(page, url)

                    processed_count += 1

                    # 添加延迟以避免被封
                    await asyncio.sleep(random.uniform(1, 3))

                finally:
                    await page.close()

                # 防止无限循环
                if self.request_queue.qsize() > 1000:  # 队列过大时停止
                    logger.warning("请求队列过大，停止处理")
                    break

            logger.info(f"爬虫运行完成，处理了 {processed_count} 个请求")

            # 返回统计信息
            return [{
                "stats": self.stats,
                "processed_count": processed_count,
                "queue_size": self.request_queue.qsize(),
                "failed_urls": list(self.failed_urls)[:10]  # 只返回前10个失败的URL
            }]

        finally:
            await self.stop()

async def create_crawlee_style_crawler(config) -> CrawleeStyleNMPACrawler:
    """创建 Crawlee 风格的爬虫实例"""
    return CrawleeStyleNMPACrawler(config)

if __name__ == "__main__":
    import yaml

    async def main():
        with open("config_crawlee.yaml", "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = SimpleConfigManager(config_data)
        crawler = await create_crawlee_style_crawler(config)

        results = await crawler.run()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(main())