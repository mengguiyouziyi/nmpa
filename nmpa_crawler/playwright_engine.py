#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright引擎 - 2024年最新反检测技术
基于GitHub成功项目的Playwright实现
"""

import asyncio
import json
import time
import random
import hashlib
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from urllib.parse import urljoin, urlencode, parse_qs


class PlaywrightNMPACrawler:
    """Playwright NMPA爬虫 - 2024年最新反检测技术"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.base_url = "https://www.nmpa.gov.cn"
        self.captured_signatures = {}

    async def start(self):
        """启动Playwright浏览器"""
        print("🚀 启动Playwright引擎（2024年最新反检测技术）...")

        self.playwright = await async_playwright().start()

        # 启动Chromium浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=self.cfg.get("headless", True),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list"
            ]
        )

        # 创建上下文（反检测配置）
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            permissions=["geolocation", "notifications"],
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "application/json, text/plain, */*",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
        )

        # 创建页面
        self.page = await self.context.new_page()

        # 注入反检测脚本
        await self._inject_stealth_scripts()

        # 设置请求拦截器
        await self.page.route("**/*", self._handle_request)

    async def _inject_stealth_scripts(self):
        """注入反检测脚本"""
        stealth_scripts = [
            # 移除webdriver标识
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            """,

            # 伪装Chrome对象
            """
            window.chrome = {
                runtime: {},
                loadTimes: {},
                csi: function() {},
                app: {}
            };
            """,

            # 伪装插件
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }
                ],
            });
            """,

            # 伪装语言
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            """,

            # 移除自动化标识
            """
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """,

            # 伪装权限
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """
        ]

        for script in stealth_scripts:
            await self.page.add_script_tag(content=script)

    async def _handle_request(self, route, request):
        """处理请求拦截"""
        if 'datasearch/data/nmpadata/search' in request.url:
            # 捕获搜索请求的签名
            url = request.url
            parsed = parse_qs(url.split('?')[1])

            search_key = f"{parsed.get('searchValue', [''])[0]}_{parsed.get('pageNum', ['1'])[0]}"

            if 'sign' in parsed:
                self.captured_signatures[search_key] = {
                    'sign': parsed['sign'][0],
                    'timestamp': parsed.get('timestamp', [''])[0],
                    'params': {k: v[0] for k, v in parsed.items()}
                }
                print(f"🔐 Playwright捕获签名: {search_key} -> {parsed['sign'][0][:16]}...")

        # 继续请求
        await route.continue_()

    async def navigate_to_search_page(self):
        """导航到搜索页面"""
        try:
            await self.page.goto(f"{self.base_url}/datasearch/home-index.html")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            print("✅ 已导航到NMPA搜索页面")
            return True
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False

    async def find_and_use_search_elements(self, search_value: str) -> bool:
        """查找并使用搜索元素"""
        search_selectors = [
            'input[placeholder*="搜索"]',
            'input[placeholder*="输入"]',
            'input[type="text"]',
            '.search-input',
            '#searchInput',
            'input[name*="search"]',
            'input[name*="keyword"]',
            '[data-testid*="search"]'
        ]

        # 尝试查找搜索框
        search_input = None
        for selector in search_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        search_input = element
                        print(f"✅ 找到搜索框: {selector}")
                        break
                if search_input:
                    break
            except:
                continue

        if not search_input:
            print("⚠️ 未找到搜索框，尝试JavaScript搜索")
            return await self._try_javascript_search(search_value)

        # 输入搜索内容
        try:
            await search_input.fill("")
            await search_input.type(search_value)
            await asyncio.sleep(1)

            # 查找搜索按钮
            button_selectors = [
                'button[type="submit"]',
                '.search-btn',
                '.btn-search',
                'button[aria-label*="搜索"]',
                'input[type="submit"]',
                '.search-button',
                '[data-testid*="submit"]'
            ]

            search_button = None
            for selector in button_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            search_button = element
                            print(f"✅ 找到搜索按钮: {selector}")
                            break
                    if search_button:
                        break
                except:
                    continue

            if search_button:
                await search_button.click()
                print("✅ 点击搜索按钮")
            else:
                await search_input.press("Enter")
                print("✅ 按Enter键搜索")

            # 等待搜索结果
            await asyncio.sleep(5)
            return True

        except Exception as e:
            print(f"❌ 搜索操作失败: {e}")
            return False

    async def _try_javascript_search(self, search_value: str) -> bool:
        """尝试JavaScript搜索"""
        js_search_scripts = [
            # 方式1: 使用fetch API
            f"""
            fetch('/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue={search_value}&pageNum=1&pageSize=10&timestamp=' + Date.now(), {{
                headers: {{
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json',
                    'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
                    'X-Requested-With': 'XMLHttpRequest'
                }}
            }}).then(response => response.json())
            .then(data => {{
                console.log('Fetch搜索结果:', data);
                window.playwrightSearchResult = data;
                return data;
            }}).catch(error => {{
                console.error('Fetch搜索失败:', error);
                return {{error: error.message}};
            }});
            """,

            # 方式2: 使用XMLHttpRequest
            """
            const xhr = new XMLHttpRequest();
            xhr.open('GET', '/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue={search_value}&pageNum=1&pageSize=10&timestamp=' + Date.now());
            xhr.setRequestHeader('Accept', 'application/json, text/plain, */*');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('Referer', 'https://www.nmpa.gov.cn/datasearch/search-result.html');
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    const data = JSON.parse(xhr.responseText);
                    console.log('XHR搜索结果:', data);
                    return data;
                }} else {{
                    console.error('XHR搜索失败');
                    return {{error: '请求失败'}};
                }}
            }};
            xhr.onerror = function() {{
                console.error('XHR网络错误');
                return {{error: '网络错误'}};
            }};
            xhr.send();
            """,

            # 方式3: 模拟表单提交
            """
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = '/datasearch/data/nmpadata/search';

            const params = {{
                'itemId': 'ff80808183cad75001840881f848179f',
                'isSenior': 'N',
                'searchValue': '{search_value}',
                'pageNum': '1',
                'pageSize': '10',
                'timestamp': Date.now()
            }};

            const queryString = Object.keys(params).map(key => key + '=' + encodeURIComponent(params[key])).join('&');
            form.action = form.action + '?' + queryString;

            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);

            return new Promise(resolve => {{
                setTimeout(() => resolve({{success: true}}), 3000);
            }});
            """
        ]

        for i, script in enumerate(js_search_scripts):
            try:
                print(f"🔧 尝试Playwright JavaScript搜索方式 {i+1}")
                result = await self.page.evaluate(script)

                if result and not result.get('error'):
                    if result.get('code') == 200:
                        print(f"✅ Playwright JavaScript搜索成功: 方式{i+1}")
                        return result
                    elif result.get('success'):
                        print(f"✅ Playwright表单提交成功: 方式{i+1}")
                        await asyncio.sleep(3)
                        # 检查页面是否更新
                        return await self._check_search_results()

                await asyncio.sleep(2)

            except Exception as e:
                print(f"Playwright JavaScript方式 {i+1} 失败: {e}")
                continue

        return None

    async def _check_search_results(self) -> Optional[Dict[str, Any]]:
        """检查搜索结果"""
        try:
            # 查找结果相关的元素
            result_selectors = [
                'table tbody tr',
                '.result-item',
                '.search-result-item',
                '.data-row',
                '[data-row]',
                '.list-item'
            ]

            for selector in result_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    print(f"✅ 找到搜索结果: {len(elements)} 条")
                    # 尝试提取数据
                    return await self._extract_results_from_page(elements)

            # 检查是否有JSON数据
            json_data = await self.page.evaluate("window.playwrightSearchResult || null")
            if json_data and json_data.get('code') == 200:
                return json_data

        except Exception as e:
            print(f"检查搜索结果失败: {e}")

        return None

    async def _extract_results_from_page(self, elements) -> Dict[str, Any]:
        """从页面元素提取结果"""
        try:
            results = []
            for element in elements[:10]:  # 限制提取数量
                try:
                    # 提取文本内容
                    text = await element.inner_text()
                    if text.strip():
                        # 尝试解析为表格行
                        cells = await element.query_selector_all('td, div, span')
                        if cells:
                            row_data = {}
                            for j, cell in enumerate(cells):
                                cell_text = await cell.inner_text()
                                if cell_text.strip():
                                    row_data[f'col_{j}'] = cell_text.strip()
                            results.append(row_data)
                        else:
                            results.append({'text': text.strip()})
                except:
                    continue

            return {
                'code': 200,
                'data': {
                    'list': results,
                    'total': len(results)
                },
                'message': 'success'
            }

        except Exception as e:
            print(f"提取结果失败: {e}")
            return None

    async def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """执行搜索"""
        print(f"🔍 Playwright搜索: {search_value}, 第{page_num}页")

        # 检查缓存签名
        cache_key = f"{search_value}_{page_num}"
        if cache_key in self.captured_signatures:
            print(f"✅ 使用缓存的Playwright签名")
            return await self._use_cached_signature(cache_key, search_value, page_num)

        # 执行搜索
        if page_num == 1:
            # 首页搜索，需要触发搜索行为
            success = await self.find_and_use_search_elements(search_value)
            if success:
                await asyncio.sleep(3)
                return await self._check_search_results()

        # 尝试构造直接请求
        return await self._try_direct_request(item_id, search_value, page_num, page_size)

    async def _use_cached_signature(self, cache_key: str, search_value: str, page_num: int) -> Optional[Dict[str, Any]]:
        """使用缓存的签名"""
        cached = self.captured_signatures[cache_key]

        try:
            params = cached['params'].copy()
            if 'pageNum' in params:
                params['pageNum'] = str(page_num)

            query_string = urlencode(params)
            url = f"{self.base_url}/datasearch/data/nmpadata/search?{query_string}"

            response = await self.page.goto(url)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # 检查响应
            content = await self.page.content()
            if content:
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = json.loads(content.decode('utf-8'))
                if data.get('code') == 200:
                    return data

        except Exception as e:
            print(f"使用缓存签名失败: {e}")

        return None

    async def _try_direct_request(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """尝试直接请求"""
        timestamp = int(time.time() * 1000)

        # 尝试不同的请求方式
        request_attempts = [
            # 无签名请求
            {
                'params': {
                    'itemId': item_id,
                    'isSenior': 'N',
                    'searchValue': search_value,
                    'pageNum': page_num,
                    'pageSize': page_size,
                    'timestamp': timestamp
                }
            },
            # 简单签名请求
            {
                'params': {
                    'itemId': item_id,
                    'isSenior': 'N',
                    'searchValue': search_value,
                    'pageNum': page_num,
                    'pageSize': page_size,
                    'timestamp': timestamp,
                    'sign': hashlib.md5(f"{item_id}{search_value}{page_num}{timestamp}playwright".encode()).hexdigest()
                }
            }
        ]

        for i, attempt in enumerate(request_attempts):
            try:
                query_string = urlencode(attempt['params'])
                url = f"{self.base_url}/datasearch/data/nmpadata/search?{query_string}"

                response = await self.page.goto(url)
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                content = await self.page.content()
                if content:
                    data = json.loads(content.decode('utf-8'))
                    if data.get('code') == 200:
                        print(f"✅ Playwright直接请求成功: 方式{i+1}")
                        return data

            except Exception as e:
                print(f"Playwright直接请求方式{i+1}失败: {e}")
                continue

        return None

    async def get_item_ids(self) -> Dict[str, str]:
        """获取数据库ID"""
        return {
            "domestic": "ff80808183cad75001840881f848179f",
            "imported": "ff80808183cad75001840881f84817a0"
        }

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict[str, Any]]:
        """完整爬取任务"""
        print(f"🚀 开始Playwright爬取: {dataset} - {code_prefix}")

        # 导航到搜索页面
        if not await self.navigate_to_search_page():
            return []

        item_ids = await self.get_item_ids()
        item_id = item_ids.get(dataset)

        if not item_id:
            print(f"❌ 未找到数据集ID: {dataset}")
            return []

        all_records = []
        max_pages = self.cfg.get("max_pages", 2)

        for page in range(1, max_pages + 1):
            print(f"📄 Playwright爬取第 {page} 页...")

            result = await self.search_once(item_id, code_prefix, page, 10)

            if not result:
                print(f"第 {page} 页无数据，停止")
                break

            data_list = result.get('data', {}).get('list', [])

            if not data_list:
                print(f"第 {page} 页为空，停止")
                break

            # 处理数据
            for record in data_list:
                full_record = {
                    'raw_data': record,
                    'crawl_time': time.time(),
                    'dataset': dataset,
                    'code_prefix': code_prefix,
                    'page': page,
                    'engine': 'playwright'
                }
                all_records.append(full_record)

            print(f"第 {page} 页完成: {len(data_list)} 条记录")
            await asyncio.sleep(2)

        print(f"🎉 Playwright爬取完成: {dataset} - {code_prefix}, 共 {len(all_records)} 条")
        return all_records

    async def stop(self):
        """停止Playwright"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


def create_playwright_crawler(cfg: Dict[str, Any]) -> PlaywrightNMPACrawler:
    """创建Playwright爬虫实例"""
    return PlaywrightNMPACrawler(cfg)


if __name__ == "__main__":
    import asyncio
    import hashlib

    async def test_playwright():
        """测试Playwright引擎"""
        config = {
            "headless": True,
            "max_pages": 2,
            "page_size": 10
        }

        crawler = create_playwright_crawler(config)

        try:
            print("🧪 测试Playwright引擎...")
            await crawler.start()

            result = await crawler.search_once(
                "ff80808183cad75001840881f848179f",
                "国药准字H",
                1,
                10
            )

            if result:
                print(f"✅ Playwright测试成功: {result}")
            else:
                print("❌ Playwright测试失败")

        finally:
            await crawler.stop()
            print("🏁 Playwright测试完成")

    # 运行测试
    asyncio.run(test_playwright())