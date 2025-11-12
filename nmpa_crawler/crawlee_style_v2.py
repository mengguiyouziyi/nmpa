# -*- coding: utf-8 -*-
"""
Crawlee 风格的 NMPA 爬虫 V2 - 改进版本
优化了选择器策略和中断处理
"""

import asyncio
import json
import time
import random
import signal
import sys
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleConfigManager:
    """简单的配置管理器"""
    def __init__(self, config_data):
        self.config_data = config_data if isinstance(config_data, dict) else {}

    def get(self, key, default=None):
        return self.config_data.get(key, default)

class CrawleeStyleNMPACrawlerV2:
    """改进版的 Crawlee 风格 NMPA 爬虫"""

    def __init__(self, config: SimpleConfigManager):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.running = True
        self.shutdown_event = asyncio.Event()

        # Crawlee 风格的配置
        self.navigation_timeout = config.get("navigation_timeout", 60000)
        self.request_handler_timeout = config.get("request_handler_timeout", 60000)
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

        # NMPA 配置
        self.nmpa_domain = "www.nmpa.gov.cn"
        self.nmpa_urls = [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",  # 监管工作
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",  # 公告通知
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",  # 法规文件
        ]

        # 设置信号处理
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在优雅关闭...")
        self.running = False
        self.shutdown_event.set()

    async def start(self):
        """启动爬虫"""
        self.stats["start_time"] = datetime.now()
        logger.info("启动 Crawlee 风格的 NMPA 爬虫 V2")

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 浏览器配置
            browser_options = {
                "headless": self.headless,
                "args": [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                ]
            }

            self.browser = await self.playwright.chromium.launch(**browser_options)

            # 创建上下文
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "ignore_https_errors": True,
            }

            self.context = await self.browser.new_context(**context_options)

            # 反检测脚本
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)

            logger.info("✅ Crawlee 风格爬虫 V2 启动成功")

        except Exception as e:
            logger.error(f"❌ 爬虫启动失败: {e}")
            await self.stop()
            raise

    async def stop(self):
        """停止爬虫"""
        if self.stats["end_time"] is None:
            self.stats["end_time"] = datetime.now()
        logger.info("正在停止爬虫...")

        try:
            # 关闭上下文
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

        logger.info("=== Crawlee 风格爬虫 V2 统计 ===")
        logger.info(f"总请求数: {self.stats['total_requests']}")
        logger.info(f"成功请求: {self.stats['successful_requests']}")
        logger.info(f"失败请求: {self.stats['failed_requests']}")
        logger.info(f"提取条目: {self.stats['items_extracted']}")
        logger.info(f"运行时长: {duration}")
        logger.info(f"成功率: {self.stats['successful_requests'] / max(1, self.stats['total_requests']) * 100:.2f}%")

    async def add_requests(self, urls: List[str]):
        """添加请求到队列"""
        for url in urls:
            if url not in self.processed_urls:
                await self.request_queue.put(url)
                logger.info(f"添加请求到队列: {url}")

    async def request_handler(self, page: Page, url: str):
        """请求处理器"""
        try:
            logger.info(f"处理请求: {url}")
            self.stats["total_requests"] += 1

            # 设置超时
            page.set_default_timeout(self.navigation_timeout)

            # 访问页面
            response = await page.goto(url, wait_until="domcontentloaded", timeout=self.navigation_timeout)

            if not response or response.status != 200:
                raise Exception(f"HTTP状态码: {response.status if response else '无响应'}")

            title = await page.title()
            logger.info(f"页面标题: {title}")

            # 等待页面加载
            await asyncio.sleep(2)

            # 智能选择器策略
            items = await self.extract_content_smart(page, url)
            self.stats["items_extracted"] += len(items)

            self.stats["successful_requests"] += 1
            self.processed_urls.add(url)

            logger.info(f"✅ 成功处理页面，提取了 {len(items)} 个项目")

        except Exception as e:
            logger.error(f"处理请求失败 {url}: {e}")
            self.stats["failed_requests"] += 1
            self.failed_urls.add(url)

    async def extract_content_smart(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """智能内容提取"""
        items = []

        try:
            # 策略1: 寻找所有链接
            links = await page.query_selector_all('a[href]')
            logger.info(f"找到 {len(links)} 个链接")

            if links:
                # 处理链接
                for i, link in enumerate(links[:20]):  # 最多处理20个链接
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()

                        if href and text and text.strip():
                            # 处理相对链接
                            if href.startswith('/'):
                                href = f"https://{self.nmpa_domain}{href}"
                            elif not href.startswith('http'):
                                continue

                            # 只处理 NMPA 域名的链接
                            if self.nmpa_domain not in href:
                                continue

                            items.append({
                                'title': text.strip(),
                                'href': href,
                                'source_url': url,
                                'crawl_time': datetime.now().isoformat(),
                                'type': 'link'
                            })

                            # 添加到队列
                            if href not in self.processed_urls and "index.html" not in href:
                                await self.request_queue.put(href)

                    except Exception as e:
                        continue

            # 策略2: 如果没有找到链接，尝试提取页面文本内容
            if not items:
                try:
                    body_text = await page.evaluate('() => document.body.innerText')
                    if body_text and len(body_text.strip()) > 50:
                        items.append({
                            'title': await page.title(),
                            'content': body_text[:500] + "...",
                            'url': url,
                            'crawl_time': datetime.now().isoformat(),
                            'type': 'content'
                        })
                except:
                    pass

        except Exception as e:
            logger.error(f"内容提取失败: {e}")

        return items

    async def run(self) -> List[Dict[str, Any]]:
        """运行爬虫"""
        await self.start()

        try:
            # 添加初始请求
            await self.add_requests(self.nmpa_urls)

            # 处理请求队列
            processed_count = 0

            while not self.request_queue.empty() and self.running and processed_count < self.max_requests_per_crawl:
                try:
                    # 等待任务或关闭信号
                    try:
                        url = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # 检查是否需要关闭
                        if self.shutdown_event.is_set():
                            break
                        continue

                    # 创建新页面
                    page = await self.context.new_page()

                    try:
                        # 处理请求
                        await self.request_handler(page, url)
                        processed_count += 1

                        # 添加延迟
                        await asyncio.sleep(random.uniform(1, 2))

                    finally:
                        await page.close()

                    # 检查关闭信号
                    if self.shutdown_event.is_set():
                        logger.info("收到关闭信号，停止处理")
                        break

                except Exception as e:
                    logger.error(f"处理队列时出错: {e}")
                    continue

            logger.info(f"爬虫运行完成，处理了 {processed_count} 个请求")

            # 返回统计信息
            return [{
                "stats": self.stats,
                "processed_count": processed_count,
                "queue_size": self.request_queue.qsize(),
                "failed_urls": list(self.failed_urls)[:10]
            }]

        finally:
            await self.stop()

async def create_crawlee_style_crawler_v2(config) -> CrawleeStyleNMPACrawlerV2:
    """创建改进版 Crawlee 风格的爬虫实例"""
    return CrawleeStyleNMPACrawlerV2(config)

if __name__ == "__main__":
    import yaml

    async def main():
        with open("config_crawlee.yaml", "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = SimpleConfigManager(config_data)
        crawler = await create_crawlee_style_crawler_v2(config)

        results = await crawler.run()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(main())