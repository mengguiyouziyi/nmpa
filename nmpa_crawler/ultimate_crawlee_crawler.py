# -*- coding: utf-8 -*-
"""
终极 Crawlee 风格 NMPA 爬虫
集成 yiya-crawler 和我们已验证成功的所有技术亮点
"""

import asyncio
import json
import time
import random
import signal
import sys
import os
import re
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
    """配置管理器 - 参考 yiya-crawler 的环境变量管理"""
    def __init__(self, config_data):
        self.config_data = config_data if isinstance(config_data, dict) else {}

    def get(self, key, default=None):
        # 优先从环境变量读取，然后从配置文件读取
        env_value = os.getenv(key.upper())
        if env_value:
            return env_value
        return self.config_data.get(key, default)

class UltimateCrawleeNMPACrawler:
    """终极 Crawlee 风格 NMPA 爬虫 - 集成所有优秀技术"""

    def __init__(self, config: SimpleConfigManager):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.running = True
        self.shutdown_event = asyncio.Event()

        # Crawlee 风格配置 - 参考 yiya-crawler 环境变量
        self.navigation_timeout = int(config.get("navigation_timeout", 60000))
        self.request_handler_timeout = int(config.get("request_handler_timeout", 60000))
        self.max_request_retries = int(config.get("max_retries", 3))
        self.max_requests_per_crawl = int(config.get("max_pages", 20))
        self.max_concurrency = int(config.get("max_concurrency", 1))
        self.crawl_queue_size = int(config.get("crawl_queue_size", 4))
        self.headless = config.get("headless", True)

        # 请求队列 - Crawlee 核心特性
        self.request_queue = asyncio.Queue()
        self.processed_urls = set()
        self.failed_urls = set()
        self.page_data = {}  # 页面数据缓存

        # 统计信息 - 扩展版本
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "items_extracted": 0,
            "pdfs_generated": 0,
            "attachments_processed": 0,
            "start_time": None,
            "end_time": None,
            "pages_by_type": {},
            "errors_by_type": {}
        }

        # NMPA 配置
        self.nmpa_domain = "www.nmpa.gov.cn"
        self.nmpa_urls = [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",
        ]

        # 生成真实浏览器指纹 - 从已验证成功的爬虫复制
        self.browser_fingerprint = self.generate_browser_fingerprint()

        # 临时目录管理 - 参考 yiya-crawler
        self.temp_dir = "downloads"
        self.attachments_dir = os.path.join(self.temp_dir, "attachments")
        self.ensure_directories()

        # 设置信号处理
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """信号处理器"""
        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在优雅关闭...")
        self.running = False
        self.shutdown_event.set()

    def ensure_directories(self):
        """确保目录存在 - 参考 yiya-crawler"""
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.attachments_dir, exist_ok=True)

    def generate_browser_fingerprint(self) -> Dict:
        """生成真实浏览器指纹"""
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
            'geolocation': {'latitude': 39.9042, 'longitude': 116.4074},
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
            'reduced_motion': 'reduce'
        }

    def sanitize_filename(self, filename: str) -> str:
        """处理文件名中的特殊字符 - 参考 yiya-crawler"""
        return re.sub(r'[\\/:*?"<>|]', '_', filename)

    def generate_unique_name(self, url: str, ext: str = 'json') -> str:
        """生成唯一文件名 - 参考 yiya-crawler"""
        timestamp = int(time.time() * 1000)
        url_hash = abs(hash(url)) % 1000000
        return f"{timestamp}_{url_hash}.{ext}"

    async def start(self):
        """启动爬虫"""
        self.stats["start_time"] = datetime.now()
        rprint("[bold blue]🚀 启动终极 Crawlee 风格 NMPA 爬虫[/]")
        rprint("[dim]集成 yiya-crawler 和已验证成功的反检测技术[/]")

        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 浏览器配置 - 集成所有最佳实践
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

            # 创建上下文 - 完整的浏览器指纹伪装
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

            # 完整的反检测脚本
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

                // 伪造plugins
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

                // 伪造权限API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'granted' }) :
                        originalQuery(parameters)
                );

                // 伪造languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });

                console.log('终极反检测脚本加载完成');
            """)

            # 设置完整的HTTP头
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

            rprint("[green]✅ 终极爬虫启动成功 - 反检测技术已激活[/]")
            return True

        except Exception as e:
            rprint(f"[red]❌ 爬虫启动失败: {e}[/]")
            await self.stop()
            raise

    async def stop(self):
        """停止爬虫"""
        if self.stats["end_time"] is None:
            self.stats["end_time"] = datetime.now()
        rprint("[blue]🛑 正在停止爬虫...[/]")

        try:
            # 关闭上下文
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            # 生成最终报告
            await self.generate_final_report()

            # 打印统计信息
            self.print_stats()

            # 清理临时文件
            await self.cleanup_temp_files()

        except Exception as e:
            logger.error(f"停止爬虫时出错: {e}")

    async def cleanup_temp_files(self):
        """清理临时文件 - 参考 yiya-crawler"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                rprint(f"[dim]🧹 临时文件已清理: {self.temp_dir}[/]")
        except Exception as e:
            rprint(f"[yellow]⚠️ 清理临时文件失败: {e}[/]")

    async def generate_final_report(self):
        """生成最终报告 - 参考 yiya-crawler 的数据导出"""
        try:
            report = {
                "crawler_type": "ultimate_crawlee_nmpa",
                "crawl_session": {
                    "start_time": self.stats["start_time"].isoformat(),
                    "end_time": self.stats["end_time"].isoformat(),
                    "duration_seconds": (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
                },
                "statistics": self.stats,
                "pages_processed": list(self.page_data.keys()),
                "failed_urls": list(self.failed_urls),
                "browser_fingerprint": self.browser_fingerprint,
                "configuration": {
                    "max_pages": self.max_requests_per_crawl,
                    "max_retries": self.max_request_retries,
                    "max_concurrency": self.max_concurrency
                }
            }

            # 保存报告
            report_file = os.path.join(self.temp_dir, f"crawl_report_{int(time.time())}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            rprint(f"[green]📊 最终报告已保存: {report_file}[/]")

        except Exception as e:
            rprint(f"[yellow]⚠️ 生成报告失败: {e}[/]")

    def print_stats(self):
        """打印统计信息"""
        duration = self.stats["end_time"] - self.stats["start_time"] if self.stats["end_time"] and self.stats["start_time"] else "未知"

        rprint("[bold blue]🎯=== 终极 Crawlee 爬虫统计 ===[/]")
        rprint(f"📊 总请求数: {self.stats['total_requests']}")
        rprint(f"✅ 成功请求: {self.stats['successful_requests']}")
        rprint(f"❌ 失败请求: {self.stats['failed_requests']}")
        rprint(f"📦 提取条目: {self.stats['items_extracted']}")
        rprint(f"📄 生成页面数据: {len(self.page_data)}")
        rprint(f"⏱️ 运行时长: {duration}")
        success_rate = self.stats['successful_requests'] / max(1, self.stats['total_requests']) * 100
        rprint(f"🎯 成功率: {success_rate:.2f}%")

        # 按类型统计
        if self.stats["pages_by_type"]:
            rprint("[dim]📋 页面类型统计:[/]")
            for page_type, count in self.stats["pages_by_type"].items():
                rprint(f"   {page_type}: {count}")

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
        """绕过412保护 - 集成所有成功策略"""
        rprint(f"[bold cyan]🔓 绕过412保护: {url}[/]")

        strategies = [
            ("直接访问", lambda: page.goto(url, wait_until='domcontentloaded', timeout=30000)),
            ("延迟访问", lambda: asyncio.sleep(random.uniform(3, 6)) or page.goto(url, wait_until='domcontentloaded', timeout=30000)),
            ("JavaScript跳转", lambda: page.evaluate(f'window.location.href = "{url}"') and asyncio.sleep(3))
        ]

        for strategy_name, strategy_func in strategies:
            try:
                rprint(f"[blue]策略: {strategy_name}[/]")
                response = await strategy_func()

                if strategy_name == "JavaScript跳转":
                    await page.wait_for_load_state('domcontentloaded', timeout=30000)
                elif response:
                    if hasattr(response, 'status') and response.status == 200:
                        rprint(f"[green]✅ {strategy_name}成功[/]")
                        return True

                # 检查当前URL
                current_url = page.url
                if url in current_url:
                    rprint(f"[green]✅ {strategy_name}成功 - URL匹配[/]")
                    return True

            except Exception as e:
                rprint(f"[yellow]⚠️ {strategy_name}失败: {e}[/]")
                continue

        rprint(f"[red]❌ 所有策略都失败了[/]")
        return False

    async def add_requests(self, urls: List[str]):
        """添加请求到队列 - Crawlee 核心特性"""
        for url in urls:
            if url not in self.processed_urls:
                await self.request_queue.put(url)
                rprint(f"[dim]➕ 添加请求到队列: {url}[/]")

    async def request_handler(self, page: Page, url: str):
        """请求处理器 - 集成 yiya-crawler 的处理逻辑"""
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

            # 判断页面类型 - 参考 yiya-crawler
            if "index.html" in url:
                page_type = "list"
                items = await self.extract_list_items(page, url)
            else:
                page_type = "detail"
                items = await self.extract_detail_items(page, url)

            # 更新统计
            self.stats["pages_by_type"][page_type] = self.stats["pages_by_type"].get(page_type, 0) + 1
            self.stats["items_extracted"] += len(items)

            # 保存页面数据 - 参考 yiya-crawler 的数据结构
            page_data = {
                "url": url,
                "title": title,
                "type": page_type,
                "items": items,
                "crawl_time": datetime.now().isoformat(),
                "status": "success"
            }
            self.page_data[url] = page_data

            # 保存到文件
            await self.save_page_data(url, page_data)

            self.stats["successful_requests"] += 1
            self.processed_urls.add(url)

            rprint(f"[green]✅ 成功处理页面，提取了 {len(items)} 个项目[/]")

        except Exception as e:
            rprint(f"[red]❌ 处理请求失败 {url}: {e}[/]")
            self.stats["failed_requests"] += 1
            self.failed_urls.add(url)

            # 记录错误类型
            error_type = type(e).__name__
            self.stats["errors_by_type"][error_type] = self.stats["errors_by_type"].get(error_type, 0) + 1

    async def save_page_data(self, url: str, data: Dict):
        """保存页面数据 - 参考 yiya-crawler 的文件处理"""
        try:
            filename = self.generate_unique_name(url, 'json')
            filepath = os.path.join(self.temp_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            rprint(f"[dim]💾 页面数据已保存: {filepath}[/]")

        except Exception as e:
            rprint(f"[yellow]⚠️ 保存页面数据失败: {e}[/]")

    async def extract_list_items(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """提取列表页项目 - 参考 yiya-crawler 的选择器策略"""
        items = []

        try:
            # 等待页面元素
            await page.wait_for_selector('body', timeout=10000)

            # 尝试多种选择器策略
            selectors = [
                '.list li a', 'ul li a', 'a[href*=".html"]',
                '.news-list a', '.content-list a', '[class*="list"] a',
                '[class*="item"] a', '[class*="article"] a'
            ]

            found_elements = None
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        found_elements = elements
                        rprint(f"[green]✅ 使用选择器 {selector} 找到 {len(elements)} 个链接[/]")
                        break
                except:
                    continue

            if found_elements:
                # 限制处理数量，避免过多
                for i, element in enumerate(found_elements[:10]):
                    try:
                        href = await element.get_attribute('href')
                        text = await element.inner_text()

                        if href and text and text.strip():
                            # 处理相对链接
                            if href.startswith('/'):
                                href = f"https://{self.nmpa_domain}{href}"
                            elif not href.startswith('http'):
                                continue

                            # 只处理 NMPA 域名的链接
                            if self.nmpa_domain not in href:
                                continue

                            item = {
                                'title': text.strip(),
                                'href': href,
                                'source_url': url,
                                'crawl_time': datetime.now().isoformat(),
                                'type': 'link'
                            }

                            items.append(item)

                            # 添加到队列 - Crawlee 自动发现功能
                            if href not in self.processed_urls and "index.html" not in href:
                                await self.request_queue.put(href)

                    except Exception:
                        continue

        except Exception as e:
            rprint(f"[yellow]⚠️ 列表提取失败: {e}[/]")

        return items

    async def extract_detail_items(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """提取详情页项目"""
        items = []

        try:
            # 等待页面元素
            await page.wait_for_selector('body', timeout=10000)

            # 提取页面内容
            page_text = await page.evaluate('() => document.body.innerText')

            if page_text and len(page_text.strip()) > 50:
                # 提取标题
                title = await page.title()

                # 提取发布时间
                time_selectors = [
                    '.time', '.date', '.publish-time',
                    '[class*="time"]', '[class*="date"]',
                    'meta[name="date"]', 'meta[property="article:published_time"]'
                ]

                publish_time = ""
                for selector in time_selectors:
                    try:
                        if selector.startswith('meta'):
                            element = await page.query_selector(selector)
                            if element:
                                publish_time = await element.get_attribute('content')
                        else:
                            element = await page.query_selector(selector)
                            if element:
                                publish_time = await element.inner_text()

                        if publish_time:
                            break
                    except:
                        continue

                # 提取主要内容
                content_selectors = [
                    '.content', '.article-content', '.main-content',
                    'div[class*="content"]', '.text', 'article'
                ]

                content = ""
                for selector in content_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            content = await element.inner_text()
                            if content and len(content.strip()) > 100:
                                break
                    except:
                        continue

                item = {
                    'title': title,
                    'content': content[:500] + "..." if len(content) > 500 else content,
                    'url': url,
                    'publish_time': publish_time,
                    'crawl_time': datetime.now().isoformat(),
                    'type': 'content'
                }

                items.append(item)

        except Exception as e:
            rprint(f"[yellow]⚠️ 详情提取失败: {e}[/]")

        return items

    async def run(self) -> List[Dict[str, Any]]:
        """运行爬虫 - 终极版本"""
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

                        # 智能延迟
                        self.smart_delay(1, 3)

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

            # 返回统计信息
            stats_copy = self.stats.copy()
            stats_copy['start_time'] = stats_copy['start_time'].isoformat() if stats_copy['start_time'] else None
            stats_copy['end_time'] = stats_copy['end_time'].isoformat() if stats_copy['end_time'] else None

            return [{
                "stats": stats_copy,
                "processed_count": processed_count,
                "queue_size": self.request_queue.qsize(),
                "failed_urls": list(self.failed_urls)[:10],
                "pages_data_count": len(self.page_data),
                "temp_files_path": self.temp_dir
            }]

        finally:
            await self.stop()

async def create_ultimate_crawlee_crawler(config) -> UltimateCrawleeNMPACrawler:
    """创建终极 Crawlee 风格的爬虫实例"""
    return UltimateCrawleeNMPACrawler(config)

if __name__ == "__main__":
    import yaml

    async def main():
        with open("config_crawlee.yaml", "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = SimpleConfigManager(config_data)
        crawler = await create_ultimate_crawlee_crawler(config)

        results = await crawler.run()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(main())