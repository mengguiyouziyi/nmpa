# -*- coding: utf-8 -*-
"""
Crawlee 风格爬虫调试版本 - 分析 NMPA 页面结构
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NMPADebugAnalyzer:
    """NMPA 页面结构调试分析器"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # 使用 headless 模式
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 反检测脚本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

    async def stop(self):
        """停止浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"停止浏览器时出错: {e}")

    async def analyze_page(self, url: str):
        """分析单个页面的结构"""
        logger.info(f"正在分析页面: {url}")

        page = await self.context.new_page()

        try:
            # 访问页面
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            logger.info(f"页面标题: {await page.title()}")

            # 等待页面加载
            await asyncio.sleep(3)

            # 分析页面结构
            page_content = await page.content()
            analysis = {
                "url": url,
                "title": await page.title(),
                "selectors_found": {},
                "potential_lists": [],
                "page_content_sample": page_content[:2000] + "..."
            }

            # 测试各种选择器
            selectors_to_test = [
                '.list li', '.news-list li', '.content-list li',
                'ul li', '[class*="list-item"]', '.list-item',
                '[class*="item"]', '.item', '[class*="article"]',
                '.article', '[class*="news"]', '.news',
                'a[href*=".html"]', 'a', 'li a'
            ]

            for selector in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        analysis["selectors_found"][selector] = len(elements)
                        logger.info(f"✅ 找到 {len(elements)} 个元素匹配 '{selector}'")

                        # 如果是列表项，分析结构
                        if 'li' in selector and len(elements) > 0:
                            sample_element = elements[0]
                            text_content = await sample_element.inner_text()
                            html_content = await sample_element.inner_html()

                            analysis["potential_lists"].append({
                                "selector": selector,
                                "count": len(elements),
                                "sample_text": text_content[:100] + "..." if len(text_content) > 100 else text_content,
                                "sample_html": html_content[:200] + "..." if len(html_content) > 200 else html_content
                            })
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 失败: {e}")

            # 查找所有链接
            links = await page.query_selector_all('a[href]')
            analysis["total_links"] = len(links)

            # 分析链接模式
            link_patterns = {}
            for link in links[:20]:  # 只分析前20个链接
                href = await link.get_attribute('href')
                if href:
                    if '.html' in href:
                        link_patterns['html_links'] = link_patterns.get('html_links', 0) + 1
                    if 'nmpa.gov.cn' in href:
                        link_patterns['internal_links'] = link_patterns.get('internal_links', 0) + 1

            analysis["link_patterns"] = link_patterns

            # 查找可能的列表容器
            list_containers = await page.query_selector_all('[class*="list"], [class*="content"]')
            analysis["list_containers"] = len(list_containers)

            return analysis

        except Exception as e:
            logger.error(f"分析页面失败 {url}: {e}")
            return {"url": url, "error": str(e)}

        finally:
            await page.close()

    async def analyze_urls(self, urls: list):
        """分析多个URL"""
        results = []

        for url in urls:
            try:
                analysis = await self.analyze_page(url)
                results.append(analysis)
                await asyncio.sleep(2)  # 避免请求过快
            except Exception as e:
                logger.error(f"分析URL失败 {url}: {e}")
                results.append({"url": url, "error": str(e)})

        return results

async def main():
    analyzer = NMPADebugAnalyzer()

    try:
        await analyzer.start()

        urls = [
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",
        ]

        logger.info("开始分析 NMPA 页面结构...")
        results = await analyzer.analyze_urls(urls)

        # 输出分析结果
        print("\n" + "="*80)
        print("NMPA 页面结构分析结果")
        print("="*80)

        for result in results:
            print(f"\n📄 URL: {result['url']}")
            print(f"📋 标题: {result.get('title', 'N/A')}")
            print(f"🔗 总链接数: {result.get('total_links', 0)}")
            print(f"📦 列表容器数: {result.get('list_containers', 0)}")

            if 'error' in result:
                print(f"❌ 错误: {result['error']}")
                continue

            print("\n✅ 找到的选择器:")
            selectors = result.get('selectors_found', {})
            for selector, count in selectors.items():
                print(f"  - {selector}: {count} 个元素")

            print("\n📊 链接模式:")
            patterns = result.get('link_patterns', {})
            for pattern, count in patterns.items():
                print(f"  - {pattern}: {count} 个链接")

            potential_lists = result.get('potential_lists', [])
            if potential_lists:
                print("\n🎯 潜在列表结构:")
                for lst in potential_lists[:3]:  # 只显示前3个
                    print(f"  - 选择器: {lst['selector']} ({lst['count']} 个)")
                    print(f"    示例文本: {lst['sample_text']}")

        # 保存详细分析结果
        with open("nmpa_page_analysis.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n📁 详细分析结果已保存到: nmpa_page_analysis.json")

    finally:
        await analyzer.stop()

if __name__ == "__main__":
    asyncio.run(main())