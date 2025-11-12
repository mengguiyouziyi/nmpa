# -*- coding: utf-8 -*-
"""
简单调试工具 - 快速分析 NMPA 页面
"""

import asyncio
from playwright.async_api import async_playwright

async def analyze_nmpa_pages():
    """分析 NMPA 页面结构"""

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    )

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 反检测
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    urls = [
        "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html",
        "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html",
        "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",
    ]

    for url in urls:
        print(f"\n🔍 分析页面: {url}")

        page = await context.new_page()

        try:
            # 访问页面
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response.status != 200:
                print(f"❌ HTTP状态码: {response.status}")
                continue

            title = await page.title()
            print(f"📋 标题: {title}")

            # 等待页面加载
            await asyncio.sleep(2)

            # 测试基础选择器
            selectors = [
                '.list li', 'ul li', 'li',
                'a', 'a[href*=".html"]',
                '[class*="list"]', '[class*="item"]',
                '[class*="news"]', '[class*="article"]'
            ]

            found_selectors = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        count = len(elements)
                        found_selectors.append(f"{selector}({count})")

                        # 如果找到链接，显示一些示例
                        if selector == 'a' and count > 0:
                            sample_links = []
                            for i, link in enumerate(elements[:5]):
                                href = await link.get_attribute('href')
                                text = await link.inner_text()
                                if href and text.strip():
                                    sample_links.append(f"{text.strip()[:30]} -> {href[:50]}")

                            if sample_links:
                                print(f"🔗 示例链接:")
                                for link in sample_links:
                                    print(f"   {link}")

                        # 如果找到列表项，显示结构
                        if 'li' in selector and count > 0 and count < 50:  # 避免太多元素
                            sample_item = elements[0]
                            text = await sample_item.inner_text()
                            html = await sample_item.inner_html()
                            print(f"📦 列表项示例: {text[:50]}...")
                            print(f"   HTML片段: {html[:100]}...")

                except Exception as e:
                    pass

            if found_selectors:
                print(f"✅ 找到的选择器: {', '.join(found_selectors)}")
            else:
                print("❌ 未找到任何有用的选择器")

            # 获取页面内容片段用于分析
            body_text = await page.evaluate('() => document.body.innerText')
            if body_text:
                print(f"📄 页面内容片段: {body_text[:200]}...")

        except Exception as e:
            print(f"❌ 错误: {e}")

        finally:
            await page.close()
            await asyncio.sleep(1)

    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(analyze_nmpa_pages())
