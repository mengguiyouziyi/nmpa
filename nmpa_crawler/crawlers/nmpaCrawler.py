# -*- coding: utf-8 -*-
"""
NMPA 爬虫 - 完全仿照 yiya-crawler 的 nmpaCrawler.js
使用 PuppeteerCrawler 模式
"""

import asyncio
import json
import time
import random
import os
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from rich import print as rprint

from config.constants import SITE_CONFIG, SPIDER_SITE_TYPE
from utils.fileHandler import handleWeb2Pdf, createNewPage
from utils.logger import logger


class PuppeteerCrawler:
    """PuppeteerCrawler - 完全仿照 yiya-crawler 的实现"""

    def __init__(self, options: Dict[str, Any] = None):
        self.options = options or {}

        # 从 yiya-crawler 复制的配置
        self.navigationTimeoutSecs = self.options.get("navigationTimeoutSecs", 60)
        self.requestHandlerTimeoutSecs = self.options.get("requestHandlerTimeoutSecs", 60)
        self.maxRequestRetries = self.options.get("maxRequestRetries", 3)
        self.maxRequestsPerCrawl = self.options.get("maxRequestsPerCrawl", 50)
        self.maxConcurrency = self.options.get("maxConcurrency", 2)
        self.headless = self.options.get("headless", True)

        # 浏览器配置 - 从 yiya-crawler 复制
        self.launchContext = self.options.get("launchContext", {
            "launchOptions": {
                "headless": self.headless,
                "args": ['--no-sandbox', '--disable-setuid-sandbox']
            }
        })

        # 内部状态
        self.playwright = None
        self.browser = None
        self.context = None

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "items_extracted": 0,
            "start_time": None,
            "end_time": None
        }

    async def start(self):
        """启动爬虫"""
        self.stats["start_time"] = time.time()
        rprint("[bold blue]启动 PuppeteerCrawler (仿照 yiya-crawler)[/]")

        try:
            self.playwright = await async_playwright().start()

            # 启动浏览器 - 使用 yiya-crawler 的配置
            self.browser = await self.playwright.chromium.launch(**self.launchContext["launchOptions"])

            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 添加反检测脚本 - 我们的412绕过技术
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                console.log('反检测脚本加载完成');
            """)

            rprint("[green]✅ PuppeteerCrawler 启动成功[/]")

        except Exception as e:
            rprint(f"[red]❌ 爬虫启动失败: {e}[/]")
            await self.stop()
            raise

    async def stop(self):
        """停止爬虫"""
        self.stats["end_time"] = time.time()
        rprint("[blue]正在停止爬虫...[/]")

        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            # 打印统计
            self.print_stats()

        except Exception as e:
            rprint(f"[yellow]停止爬虫时出错: {e}[/]")

    def print_stats(self):
        """打印统计信息"""
        duration = self.stats["end_time"] - self.stats["start_time"] if self.stats["end_time"] and self.stats["start_time"] else 0

        rprint("[bold blue]=== PuppeteerCrawler 统计 ===[/]")
        rprint(f"📊 总请求数: {self.stats['total_requests']}")
        rprint(f"✅ 成功请求: {self.stats['successful_requests']}")
        rprint(f"❌ 失败请求: {self.stats['failed_requests']}")
        rprint(f"📦 提取条目: {self.stats['items_extracted']}")
        rprint(f"⏱️ 运行时长: {duration:.2f}秒")
        success_rate = self.stats['successful_requests'] / max(1, self.stats['total_requests']) * 100
        rprint(f"🎯 成功率: {success_rate:.2f}%")

    async def bypass_412_protection(self, page: Page, url: str) -> bool:
        """绕过412保护 - 我们的突破性技术"""
        try:
            # 策略1: 直接访问
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response and response.status == 200:
                return True

            # 策略2: JavaScript跳转
            await page.evaluate(f'window.location.href = "{url}"')
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
            return True

        except Exception as e:
            logger.error(f"绕过412保护失败: {e}")
            return False

    async def request_handler(self, request_info: Dict[str, Any]):
        """请求处理器 - 完全仿照 yiya-crawler 的逻辑"""
        request = request_info.get("request")
        page = request_info.get("page")
        enqueue_links = request_info.get("enqueue_links")

        url = request.url
        site_config = request_info.get("site_config")
        site_code = site_config["code"]
        site_name = site_config["name"]
        site_domain = site_config["domain"]

        try:
            if site_domain not in url:
                logger.info(f"不是 NMPA 站点请求: {url}")
                return

            logger.info(f"-----------(nmpa) request url: {url}")
            self.stats["total_requests"] += 1

            # 绕过412保护
            if not await self.bypass_412_protection(page, url):
                raise Exception("无法绕过412保护")

            # 判断页面类型 - 完全仿照 yiya-crawler
            if "index.html" in url:  # 常规列表页面
                # 等待列表元素加载
                try:
                    await page.wait_for_selector('.list li', timeout=10000)
                except:
                    # 尝试其他选择器
                    await asyncio.sleep(3)

                # 提取法规文件列表 - 完全仿照 yiya-crawler 的逻辑
                items = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('.list li');
                        return Array.from(elements).map((el) => {
                            const titleElement = el.querySelector('a');
                            const title = titleElement ? titleElement.innerText.trim() : '';
                            const href = titleElement ? titleElement.href : '';
                            const dateElement = el.querySelector('span');
                            const date = dateElement ? dateElement.innerText.trim() : '';
                            const parentUrl = window.location.href;
                            return { title, href, date, parentUrl };
                        });
                    }
                """)

                # 处理URL堆栈 - 完全仿照 yiya-crawler
                for item in items:
                    if item.get("date"):
                        # 这里可以添加时间检查逻辑，暂时跳过
                        item["date"] = item["date"].strip().strip('()')
                        await createNewPage(site_domain, site_name, site_code, item["href"], item)

                        # 添加到队列
                        if enqueue_links and item.get("href"):
                            await enqueue_links({
                                "urls": [item["href"]],
                                "transformRequestFunction": lambda req: req,
                                "limit": 4  # 从环境变量读取 CRAWL_QUEUE_SIZE
                            })
                    else:
                        logger.warning(f"{site_code}: 未找到时间, href={item.get('href')}")

            else:
                # 详情页面处理 - 完全仿照 yiya-crawler
                try:
                    await page.wait_for_selector('h2.title', timeout=10000)
                except:
                    await asyncio.sleep(2)

                logger.info(f">>>>{site_code}: 正在访问页面! title={await page.title()}, url={url}")
                await handleWeb2Pdf(request, page, site_code, site_name)

            self.stats["successful_requests"] += 1
            self.stats["items_extracted"] += len(items) if 'items' in locals() else 1

        except Exception as e:
            logger.error(f"处理请求失败 {url}: {e}")
            self.stats["failed_requests"] += 1

    async def run(self, page_list: List[str]) -> List[Dict[str, Any]]:
        """运行爬虫 - 完全仿照 yiya-crawler 的主要逻辑"""
        await self.start()

        try:
            site_config = SITE_CONFIG["nmpa"]
            site_code = site_config["code"]
            site_name = site_config["name"]
            site_domain = site_config["domain"]

            # 处理每个页面
            for url in page_list:
                logger.info(f"开始处理页面: {url}")

                page = await self.context.new_page()

                try:
                    # 创建请求信息
                    request_info = {
                        "request": type('Request', (), {"url": url})(),
                        "page": page,
                        "enqueue_links": None,  # 简化版本
                        "site_config": site_config
                    }

                    # 处理请求
                    await self.request_handler(request_info)

                    # 添加延迟
                    await asyncio.sleep(random.uniform(2, 4))

                finally:
                    await page.close()

                # 检查是否达到最大请求数
                if self.stats["total_requests"] >= self.maxRequestsPerCrawl:
                    logger.info(f"达到最大请求数 {self.maxRequestsPerCrawl}，停止爬取")
                    break

            rprint(f"爬虫运行完成")

            # 返回统计信息
            return [{
                "stats": self.stats,
                "processed_count": self.stats["successful_requests"],
                "site_code": site_code,
                "site_name": site_name
            }]

        finally:
            await self.stop()


# 创建实例 - 完全仿照 yiya-crawler 的导出方式
nmpa_crawler = PuppeteerCrawler({
    "navigationTimeoutSecs": 60,
    "requestHandlerTimeoutSecs": 60,
    "maxRequestRetries": 3,
    "maxRequestsPerCrawl": 50,
    "maxConcurrency": 2,
    "headless": True,
    "launchContext": {
        "launchOptions": {
            "headless": True,
            "args": ['--no-sandbox', '--disable-setuid-sandbox']
        }
    }
})