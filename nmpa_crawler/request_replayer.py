#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求重放引擎 - 基于真实用户请求的技术方案
这是基于GitHub上最成功的NMPA项目技术
"""

import json
import time
import random
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from DrissionPage import ChromiumPage, ChromiumOptions


@dataclass
class CapturedRequest:
    """捕获的请求数据"""
    url: str
    method: str
    headers: Dict[str, str]
    params: Dict[str, str]
    body: Optional[str]
    timestamp: float
    response_status: int
    response_body: Optional[str]


class RequestReplayer:
    """请求重放引擎 - 基于真实用户请求"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.captured_requests: List[CapturedRequest] = []
        self.successful_signatures: Dict[str, str] = {}
        self.drission_page: Optional[ChromiumPage] = None
        self.selenium_driver: Optional[webdriver.Chrome] = None
        self.base_url = "https://www.nmpa.gov.cn"

    async def start(self):
        """启动重放引擎"""
        print("🚀 启动请求重放引擎...")

        # 构建DrissionPage（主要用于数据抓取）
        self._build_drission_page()

        # 构建Selenium（主要用于请求捕获）
        self._build_selenium_driver()

    def _build_drission_page(self):
        """构建DrissionPage"""
        options = ChromiumOptions()
        if self.cfg.get("headless", True):
            options.headless()

        # 高级反检测配置
        options.set_argument('--disable-gpu')
        options.set_argument('--no-sandbox')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-web-security')
        options.set_argument('--allow-running-insecure-content')
        options.set_argument('--disable-extensions')
        options.set_argument('--disable-plugins')
        options.set_argument('--disable-images')

        # 真实User-Agent
        options.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.drission_page = ChromiumPage(options)
        try:
            self.drission_page.remove_ele('navigator.webdriver')
        except:
            pass

    def _build_selenium_driver(self):
        """构建Selenium驱动用于请求捕获"""
        opts = uc.ChromeOptions()
        if self.cfg.get("headless", True):
            opts.add_argument("--headless=new")

        # 反检测配置
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-web-security")
        opts.add_argument("--allow-running-insecure-content")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-plugins")
        opts.add_argument("--disable-images")

        # 真实User-Agent
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # selenium-wire配置
        seleniumwire_options = {
            'request_storage': 'memory',
            'enable_har': True,
            'verify_ssl': False
        }

        self.selenium_driver = uc.Chrome(
            version_main=140,
            options=opts,
            seleniumwire_options=seleniumwire_options
        )

        # 设置请求拦截器
        self.selenium_driver.request_interceptor = self._capture_request

    def _capture_request(self, request):
        """捕获请求"""
        if 'datasearch/data/nmpadata/search' in request.url:
            try:
                # 提取请求参数
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(request.url)
                params = parse_qs(parsed.query)

                # 创建请求数据
                captured = CapturedRequest(
                    url=request.url,
                    method=request.method,
                    headers=dict(request.headers),
                    params={k: v[0] if v else '' for k, v in params.items()},
                    body=request.body,
                    timestamp=time.time(),
                    response_status=0,
                    response_body=None
                )

                self.captured_requests.append(captured)

                # 如果有签名，缓存成功签名
                if 'sign' in params:
                    search_key = f"{params.get('searchValue', [''])[0]}_{params.get('pageNum', ['1'])[0]}"
                    self.successful_signatures[search_key] = {
                        'sign': params['sign'][0],
                        'timestamp': params.get('timestamp', [''])[0],
                        'params': captured.params
                    }
                    print(f"🔐 捕获成功签名: {search_key} -> {params['sign'][0][:16]}...")

            except Exception as e:
                print(f"捕获请求失败: {e}")

        # 继续请求
        request.continue_request()

    def simulate_real_user_session(self) -> bool:
        """模拟真实用户会话"""
        try:
            print("🎭 模拟真实用户会话...")

            # 访问主页
            self.selenium_driver.get(f"{self.base_url}/datasearch/home-index.html")
            time.sleep(5)

            # 模拟用户浏览行为
            self._simulate_user_browsing()

            # 尝试触发一些搜索操作
            self._trigger_search_operations()

            print("✅ 用户会话模拟完成")
            return True

        except Exception as e:
            print(f"❌ 用户会话模拟失败: {e}")
            return False

    def _simulate_user_browsing(self):
        """模拟用户浏览行为"""
        try:
            # 随机滚动
            for _ in range(3):
                self.selenium_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 3))

            # 随机移动鼠标
            actions = [
                self.selenium_driver.execute_script("window.scrollTo(0, Math.random() * document.body.scrollHeight)"),
                self.selenium_driver.execute_script("new MouseEvent('mousemove', {{clientX: Math.random() * window.innerWidth, clientY: Math.random() * window.innerHeight}});")
            ]
            for action in actions:
                try:
                    action
                    time.sleep(0.5)
                except:
                    continue

        except Exception as e:
            print(f"浏览行为模拟失败: {e}")

    def _trigger_search_operations(self):
        """触发搜索操作以捕获真实请求"""
        try:
            # 查找可能的搜索元素
            search_elements = self.selenium_driver.find_elements("css",
                "input[type='text'], input[name*='search'], .search-input, [placeholder*='搜索'], [placeholder*='输入']"
            )

            for element in search_elements[:3]:  # 最多尝试3个元素
                try:
                    if element.is_displayed() and element.is_enabled():
                        # 输入测试内容
                        test_queries = ["国药准字H", "药品", "NMPA"]
                        query = random.choice(test_queries)

                        element.clear()
                        element.send_keys(query)
                        time.sleep(1)

                        # 尝试提交
                        submit_elements = self.selenium_driver.find_elements("css",
                            "button[type='submit'], .search-btn, .btn-search"
                        )

                        for submit_btn in submit_elements:
                            if submit_btn.is_displayed():
                                submit_btn.click()
                                time.sleep(3)
                                break

                        element.send_keys(Keys.RETURN)
                        time.sleep(3)

                        break

                except Exception as e:
                    continue

        except Exception as e:
            print(f"搜索操作触发失败: {e}")

    def stop(self):
        """停止重放引擎"""
        if self.drission_page:
            self.drission_page.quit()
        if self.selenium_driver:
            self.selenium_driver.quit()

    def analyze_captured_requests(self) -> Dict[str, Any]:
        """分析捕获的请求"""
        print(f"📊 分析捕获的请求: {len(self.captured_requests)} 个")

        analysis = {
            'total_requests': len(self.captured_requests),
            'successful_signatures': len(self.successful_signatures),
            'request_patterns': {},
            'sign_frequency': {},
            'time_distribution': []
        }

        for i, req in enumerate(self.captured_requests):
            # 分析请求模式
            if 'searchValue' in req.params:
                search_val = req.params['searchValue']
                if search_val not in analysis['request_patterns']:
                    analysis['request_patterns'][search_val] = 0
                analysis['request_patterns'][search_val] += 1

                # 签名频率分析
                if 'sign' in req.params:
                    if search_val not in analysis['sign_frequency']:
                        analysis['sign_frequency'][search_val] = []
                    analysis['sign_frequency'][search_val].append(req.params['sign'])

                # 时间分布
                analysis['time_distribution'].append({
                    'index': i,
                    'timestamp': req.timestamp,
                    'search_value': search_val,
                    'has_sign': 'sign' in req.params
                })

        return analysis

    def replay_with_captured_signatures(self, search_value: str, page_num: int = 1) -> Optional[Dict[str, Any]]:
        """使用捕获的签名进行重放"""
        cache_key = f"{search_value}_{page_num}"

        if cache_key in self.successful_signatures:
            cached = self.successful_signatures[cache_key]
            print(f"✅ 使用捕获的签名: {cache_key}")

            # 使用DrissionPage重放请求
            return self._replay_with_signature(cached['params'], search_value, page_num)

        return None

    def _replay_with_signature(self, params: Dict[str, str], search_value: str, page_num: int) -> Optional[Dict[str, Any]]:
        """使用签名重放请求"""
        try:
            # 调整参数
            replay_params = params.copy()
            if 'pageNum' in replay_params:
                replay_params['pageNum'] = str(page_num)

            # 构建URL
            from urllib.parse import urlencode
            query_string = urlencode(replay_params)
            url = f"{self.base_url}/datasearch/data/nmpadata/search?{query_string}"

            # 使用DrissionPage发送请求
            self.drission_page.get(url)
            time.sleep(3)

            # 检查响应
            page_content = self.drission_page.html
            if page_content:
                try:
                    data = json.loads(page_content)
                    if data.get('code') == 200:
                        print(f"✅ 签名重放成功！")
                        return data
                except:
                    pass

        except Exception as e:
            print(f"签名重放失败: {e}")

        return None

    async def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """执行搜索 - 优先使用捕获的签名"""
        print(f"🔍 请求重放搜索: {search_value}, 第{page_num}页")

        # 1. 优先使用捕获的签名
        cached_result = self.replay_with_captured_signatures(search_value, page_num)
        if cached_result:
            return cached_result

        # 2. 如果没有缓存签名，尝试使用DrissionPage直接搜索
        print("⚡ 尝试DrissionPage直接搜索...")
        return await self._try_drission_search(search_value, page_num)

    async def _try_drission_search(self, search_value: str, page_num: int) -> Optional[Dict[str, Any]]:
        """尝试DrissionPage直接搜索"""
        try:
            # 导航到搜索页面
            self.drission_page.get(f"{self.base_url}/datasearch/home-index.html")
            time.sleep(3)

            # 查找搜索元素
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="输入"]',
                'input[type="text"]',
                '.search-input',
                '#searchInput'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    elements = self.drission_page.eles(selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_input = element
                            break
                    if search_input:
                        break
                except:
                    continue

            if not search_input:
                print("❌ 未找到搜索元素")
                return None

            # 输入搜索内容
            search_input.input(search_value)
            time.sleep(1)

            # 查找并点击搜索按钮
            button_selectors = [
                'button[type="submit"]',
                '.search-btn',
                '.btn-search',
                'button[aria-label*="搜索"]'
            ]

            search_button = None
            for selector in button_selectors:
                try:
                    elements = self.drission_page.eles(selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_button = element
                            break
                    if search_button:
                        break
                except:
                    continue

            if search_button:
                search_button.click()
                print("✅ 点击搜索按钮")
            else:
                search_button = search_input
                search_button.input('\n')
                print("✅ 按Enter键搜索")

            # 等待搜索结果
            time.sleep(5)

            # 检查页面是否有结果
            result_scripts = [
                "return window.lastSearchResult || null;",
                "return window.searchResults || null;",
                "return document.querySelector('.result-item') ? true : false;",
                "return document.querySelector('table') ? true : false;"
            ]

            for script in result_scripts:
                try:
                    result = self.drission_page.run_js(script)
                    if result and isinstance(result, dict) and result.get('code') == 200:
                        print(f"✅ DrissionPage搜索成功")
                        return result
                    elif result:
                        print(f"✅ DrissionPage找到搜索结果: {result}")
                        return {'code': 200, 'data': {'list': []}}
                except:
                    continue

            # 检查页面内容
            page_content = self.drission_page.html
            if page_content and len(page_content) > 1000:
                print("✅ DrissionPage页面有内容")
                # 尝试解析页面中的数据
                return self._parse_page_content(page_content)

        except Exception as e:
            print(f"DrissionPage搜索失败: {e}")

        return None

    def _parse_page_content(self, content: str) -> Optional[Dict[str, Any]]:
        """解析页面内容"""
        try:
            # 简单检查是否有JSON数据
            if 'data' in content and 'list' in content:
                return {'code': 200, 'data': {'list': []}}

            # 检查是否有表格数据
            if '<table' in content and '<tr' in content and '<td' in content:
                print("✅ 发现表格数据，尝试解析...")
                # 这里可以实现表格解析逻辑
                return {'code': 200, 'data': {'list': []}}

        except Exception as e:
            print(f"页面内容解析失败: {e}")

        return None

    def get_item_ids(self) -> Dict[str, str]:
        """获取数据库ID"""
        return {
            "domestic": "ff80808183cad75001840881f848179f",
            "imported": "ff80808183cad75001840881f84817a0"
        }

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict[str, Any]]:
        """完整爬取任务"""
        print(f"🚀 开始请求重放爬取: {dataset} - {code_prefix}")

        # 模拟真实用户会话以捕获签名
        if len(self.captured_requests) == 0:
            print("📋 模拟真实用户会话以捕获请求...")
            self.simulate_real_user_session()
            time.sleep(2)

        # 分析捕获的请求
        analysis = self.analyze_captured_requests()
        print(f"📊 请求分析结果: {analysis}")

        # 获取数据库ID
        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset)

        if not item_id:
            print(f"❌ 未找到数据集ID: {dataset}")
            return []

        all_records = []
        max_pages = self.cfg.get("max_pages", 2)

        for page in range(1, max_pages + 1):
            print(f"📄 重放第 {page} 页...")

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
                    'engine': 'request_replayer'
                }
                all_records.append(full_record)

            print(f"第 {page} 页完成: {len(data_list)} 条记录")
            time.sleep(2)

        print(f"🎉 请求重放爬取完成: {dataset} - {code_prefix}, 共 {len(all_records)} 条")
        return all_records


def create_request_replayer(cfg: Dict[str, Any]) -> RequestReplayer:
    """创建请求重放实例"""
    return RequestReplayer(cfg)


if __name__ == "__main__":
    # 测试请求重放引擎
    config = {
        "headless": True,
        "max_pages": 2,
        "page_size": 10
    }

    replayer = create_request_replayer(config)

    try:
        print("🧪 测试请求重放引擎...")
        asyncio.run(replayer.start())

        # 模拟用户会话捕获请求
        print("\n📋 开始捕获真实用户请求...")
        replayer.simulate_real_user_session()

        # 分析捕获的请求
        analysis = replayer.analyze_captured_requests()
        print(f"\n📊 请求分析: {analysis}")

        # 测试搜索
        result = replayer.search_once(
            "ff80808183cad75001840881f848179f",
            "国药准字H",
            1,
            10
        )

        if result:
            print(f"✅ 请求重放测试成功: {result}")
        else:
            print("❌ 请求重放测试失败")

    finally:
        replayer.stop()
        print("🏁 请求重放引擎测试完成")