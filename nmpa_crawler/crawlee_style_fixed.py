# -*- coding: utf-8 -*-
"""
Crawlee 风格的 NMPA 爬虫 - 412错误修复版
集成已验证成功的反检测技术和JavaScript跳转策略
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
from rich import print as rprint

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

class CrawleeStyleNMPACrawlerFixed:
    """Crawlee 风格 NMPA 爬虫 - 412错误修复版"""

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
        self.max_requests_per_crawl = config.get("max_pages", 10)
        self.max_concurrency = config.get("max_concurrency", 1)
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

        # NMPA 配置 - 从已验证成功的爬虫复制
        self.nmpa_domain = "www.nmpa.gov.cn"
        self.nmpa_urls = [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",
        ]

        # 生成真实的浏览器指纹
        self.browser_fingerprint = self.generate_browser_fingerprint()

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

    def generate_browser_fingerprint(self) -> Dict:
        """生成真实浏览器指纹 - 从fixed_breakthrough_crawler复制"""
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept_language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'accept_encoding': 'gzip, deflate, br, zstd',
            'platform': 'Win32',
            'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec_ch_ua_mobile': '?0',
            'sec_ch_ua_platform': '"Windows"',
            'viewport': {'width': 1366, 'height': 768},
            'timezone': 'Asia/Shanghai',
            'geolocation': {'latitude': 39.9042, 'longitude': 116.4074},  # 北京
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
            'reduced_motion': 'reduce'
        }

    async def start(self):
        """启动爬虫"""
        self.stats["start_time"] = datetime.now()
        rprint("[bold blue]启动 Crawlee 风格的 NMPA 爬虫（412错误修复版）[/]")

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 浏览器配置 - 使用已验证成功的参数
            browser_options = {
                "headless": self.headless,
                "args": [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-background-networking',
                    '--disable-default-browser-check',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-client-side-phishing-detection',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--disable-background-logging',
                    '--disable-gpu',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--enable-automation=false',
                    '--excludeSwitches=enable-automation',
                    '--disable-infobars'
                ]
            }

            self.browser = await self.playwright.chromium.launch(**browser_options)

            # 创建上下文 - 使用真实浏览器指纹
            context_options = {
                "viewport": self.browser_fingerprint['viewport'],
                "user_agent": self.browser_fingerprint['user_agent'],
                "locale": "zh-CN",
                "timezone_id": self.browser_fingerprint['timezone'],
                "permissions": self.browser_fingerprint['permissions'],
                "geolocation": self.browser_fingerprint['geolocation'],
                "color_scheme": self.browser_fingerprint['color_scheme'],
                "reduced_motion": self.browser_fingerprint['reduced_motion'],
                "extra_http_headers": {
                    'Accept-Language': self.browser_fingerprint['accept_language'],
                    'Accept-Encoding': self.browser_fingerprint['accept_encoding'],
                    'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                    'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                    'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                }
            }

            self.context = await self.browser.new_context(**context_options)

            # 反检测脚本 - 使用已验证成功的脚本
            await self.context.add_init_script("""
                // 移除webdriver标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 移除自动化标识
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

                // 伪造Chrome对象
                window.chrome = {
                    runtime: {
                        onConnect: undefined,
                        onMessage: undefined,
                    },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: {}
                };

                // 伪造权限API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'granted' }) :
                        originalQuery(parameters)
                );

                console.log('反检测脚本加载完成');
            """)

            # 设置额外的HTTP头
            await self.context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': self.browser_fingerprint['accept_language'],
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive'
            })

            rprint("[green]✅ Crawlee 风格爬虫（412修复版）启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]❌ 爬虫启动失败: {e}[/]")
            await self.stop()
            raise

    async def stop(self):
        """停止爬虫"""
        if self.stats["end_time"] is None:
            self.stats["end_time"] = datetime.now()
        rprint("[blue]正在停止爬虫...[/]")

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

        rprint("[bold blue]=== Crawlee 风格爬虫（412修复版）统计 ===[/]")
        rprint(f"📊 总请求数: {self.stats['total_requests']}")
        rprint(f"✅ 成功请求: {self.stats['successful_requests']}")
        rprint(f"❌ 失败请求: {self.stats['failed_requests']}")
        rprint(f"📦 提取条目: {self.stats['items_extracted']}")
        rprint(f"⏱️ 运行时长: {duration}")
        success_rate = self.stats['successful_requests'] / max(1, self.stats['total_requests']) * 100
        rprint(f"🎯 成功率: {success_rate:.2f}%")

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[dim]⏳ 智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def simulate_human_behavior(self, page: Page):
        """模拟人类行为"""
        rprint("[blue]👤 模拟人类浏览行为...[/]")

        # 随机移动鼠标
        await page.mouse.move(
            random.randint(100, 1266),
            random.randint(100, 668)
        )
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # 随机滚动
        await page.evaluate(f'window.scrollBy(0, {random.randint(100, 300)})')
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # 再滚动回来
        await page.evaluate(f'window.scrollBy(0, -{random.randint(50, 150)})')
        await asyncio.sleep(random.uniform(0.3, 1.0))

    async def bypass_412_protection(self, page: Page, url: str) -> bool:
        """绕过412保护 - 使用已验证成功的方法"""
        rprint(f"[bold cyan]🔓 绕过412保护: {url}[/]")

        try:
            # 方法1: 直接访问
            rprint("[blue]方法1: 直接访问[/]")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response and response.status == 200:
                rprint("[green]✅ 方法1成功 - 直接访问成功[/]")
                return True

            # 方法2: 添加随机延迟访问
            rprint("[blue]方法2: 延迟访问[/]")
            self.smart_delay(3, 6)
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response and response.status == 200:
                rprint("[green]✅ 方法2成功 - 延迟访问成功[/]")
                return True

            # 方法3: 通过JavaScript跳转
            rprint("[blue]方法3: JavaScript跳转[/]")
            await page.evaluate(f'window.location.href = "{url}"')
            await page.wait_for_load_state('domcontentloaded', timeout=30000)

            current_url = page.url
            if url in current_url:
                rprint("[green]✅ 方法3成功 - JavaScript跳转成功[/]")
                return True

        except Exception as e:
            rprint(f"[yellow]⚠️ 绕过412保护失败: {e}[/]")
            return False

    async def add_requests(self, urls: List[str]):
        """添加请求到队列"""
        for url in urls:
            if url not in self.processed_urls:
                await self.request_queue.put(url)
                rprint(f"[dim]➕ 添加请求到队列: {url}[/]")

    async def request_handler(self, page: Page, url: str):
        """请求处理器"""
        try:
            rprint(f"[blue]🔄 处理请求: {url}[/]")
            self.stats["total_requests"] += 1

            # 绕过412保护
            if not await self.bypass_412_protection(page, url):
                raise Exception("无法绕过412保护")

            title = await page.title()
            rprint(f"[cyan]📋 页面标题: {title}[/]")

            # 等待页面加载
            await asyncio.sleep(3)

            # 模拟人类行为
            await self.simulate_human_behavior(page)

            # 智能内容提取
            items = await self.extract_content_smart(page, url)
            self.stats["items_extracted"] += len(items)

            self.stats["successful_requests"] += 1
            self.processed_urls.add(url)

            rprint(f"[green]✅ 成功处理页面，提取了 {len(items)} 个项目[/]")

        except Exception as e:
            rprint(f"[red]❌ 处理请求失败 {url}: {e}[/]")
            self.stats["failed_requests"] += 1
            self.failed_urls.add(url)

    async def extract_content_smart(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """智能内容提取"""
        items = []

        try:
            # 检查页面是否为空白
            page_text = await page.evaluate('() => document.body.innerText')
            if not page_text or len(page_text.strip()) < 50:
                rprint("[yellow]⚠️ 页面内容为空或过少[/]")
                return items

            # 策略1: 寻找所有链接
            links = await page.query_selector_all('a[href]')
            rprint(f"[blue]🔗 找到 {len(links)} 个链接[/]")

            if links:
                # 处理链接
                for i, link in enumerate(links[:10]):  # 限制处理数量
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

                    except Exception:
                        continue

            # 策略2: 提取页面主要内容
            if page_text:
                items.append({
                    'title': await page.title(),
                    'content': page_text[:300] + "..." if len(page_text) > 300 else page_text,
                    'url': url,
                    'crawl_time': datetime.now().isoformat(),
                    'type': 'content'
                })

        except Exception as e:
            rprint(f"[yellow]⚠️ 内容提取失败: {e}[/]")

        return items

    async def run(self) -> List[Dict[str, Any]]:
        """运行爬虫"""
        success = await self.start()
        if not success:
            return []

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
                        self.smart_delay(2, 4)

                    finally:
                        await page.close()

                    # 检查关闭信号
                    if self.shutdown_event.is_set():
                        rprint("[yellow]收到关闭信号，停止处理[/]")
                        break

                except Exception as e:
                    rprint(f"[red]处理队列时出错: {e}[/]")
                    continue

            rprint(f"[green]爬虫运行完成，处理了 {processed_count} 个请求[/]")

            # 返回统计信息 - 修复datetime序列化问题
            stats_copy = self.stats.copy()
            stats_copy['start_time'] = stats_copy['start_time'].isoformat() if stats_copy['start_time'] else None
            stats_copy['end_time'] = stats_copy['end_time'].isoformat() if stats_copy['end_time'] else None

            return [{
                "stats": stats_copy,
                "processed_count": processed_count,
                "queue_size": self.request_queue.qsize(),
                "failed_urls": list(self.failed_urls)[:10]
            }]

        finally:
            await self.stop()

async def create_crawlee_style_crawler_fixed(config) -> CrawleeStyleNMPACrawlerFixed:
    """创建412修复版 Crawlee 风格的爬虫实例"""
    return CrawleeStyleNMPACrawlerFixed(config)

if __name__ == "__main__":
    import yaml

    async def main():
        with open("config_crawlee.yaml", "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = SimpleConfigManager(config_data)
        crawler = await create_crawlee_style_crawler_fixed(config)

        results = await crawler.run()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(main())