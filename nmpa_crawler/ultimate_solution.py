#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMPA终极解决方案
基于2024-2025年最新GitHub成功项目的技术方案
结合真实浏览器行为和请求拦截
"""

import json
import time
import random
import hashlib
import threading
from typing import Dict, Any, List, Optional
from seleniumwire import webdriver
import undetected_chromedriver as uc
from DrissionPage import ChromiumPage, ChromiumOptions
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse


class UltimateNMPACrawler:
    """终极NMPA爬虫 - 基于最新成功项目方案"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.s_driver = None  # Selenium driver用于拦截
        self.dp_page = None   # DrissionPage用于操作
        self.captured_requests = []
        self.sign_cache = {}
        self.lock = threading.Lock()
        self.base_url = "https://www.nmpa.gov.cn"

    def _build_interceptor_driver(self):
        """构建请求拦截驱动"""
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

        # 真实User-Agent
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # selenium-wire配置
        seleniumwire_options = {
            'request_storage': 'memory',
            'enable_har': True,
            'verify_ssl': False
        }

        self.s_driver = uc.Chrome(
            version_main=140,
            options=opts,
            seleniumwire_options=selenium_wire_options
        )

        # 设置请求拦截器
        self.s_driver.request_interceptor = self._capture_request
        self.s_driver.response_interceptor = self._capture_response

    def _build_operation_page(self):
        """构建操作页面"""
        options = ChromiumOptions()
        if self.cfg.get("headless", True):
            options.headless()

        # 反检测配置
        options.set_argument('--disable-gpu')
        options.set_argument('--no-sandbox')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-web-security')
        options.set_argument('--allow-running-insecure-content')
        options.set_argument('--disable-extensions')
        options.set_argument('--disable-plugins')

        # 真实User-Agent
        options.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.dp_page = ChromiumPage(options)
        try:
            self.dp_page.remove_ele('navigator.webdriver')
        except:
            pass

    def _capture_request(self, request):
        """捕获请求"""
        if 'datasearch/data/nmpadata/search' in request.url:
            capture_data = {
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'body': request.body,
                'timestamp': time.time()
            }

            with self.lock:
                self.captured_requests.append(capture_data)
                # 解析URL参数
                parsed = urllib.parse.urlparse(request.url)
                params = urllib.parse.parse_qs(parsed.query)

                # 缓存签名信息
                search_key = params.get('searchValue', [''])[0]
                page_num = params.get('pageNum', ['1'])[0]
                cache_key = f"{search_key}_{page_num}"

                if 'sign' in params:
                    self.sign_cache[cache_key] = {
                        'sign': params['sign'][0],
                        'timestamp': params.get('timestamp', [''])[0],
                        'full_params': {k: v[0] for k, v in params.items()}
                    }
                    print(f"🔐 捕获签名: {cache_key} -> {params['sign'][0][:16]}...")

    def _capture_response(self, request, response):
        """捕获响应"""
        if 'datasearch/data/nmpadata/search' in request.url:
            try:
                data = response.body.decode('utf-8')
                json_data = json.loads(data)

                if json_data.get('code') == 200:
                    list_count = len(json_data.get('data', {}).get('list', []))
                    print(f"✅ 成功响应: {list_count} 条数据")
            except:
                pass

    def start(self):
        """启动爬虫"""
        print("🚀 启动终极NMPA爬虫...")

        # 构建驱动
        self._build_interceptor_driver()
        self._build_operation_page()

        # 访问主页触发初始化
        self.s_driver.get(f"{self.base_url}/datasearch/home-index.html")
        time.sleep(5)

        self.dp_page.get(f"{self.base_url}/datasearch/home-index.html")
        time.sleep(3)

    def stop(self):
        """停止爬虫"""
        if self.s_driver:
            self.s_driver.quit()
        if self.dp_page:
            self.dp_page.quit()

    def _trigger_real_search(self, search_value: str) -> bool:
        """触发真实搜索以捕获签名"""
        try:
            # 等待页面完全加载
            self.dp_page.wait(10)

            # 查找并触发搜索框的多种方式
            search_triggers = [
                # 方式1: 直接查找搜索框
                lambda: self.dp_page.ele('input[placeholder*="搜索"]', timeout=2),
                lambda: self.dp_page.ele('input[placeholder*="输入"]', timeout=2),
                lambda: self.dp_page.ele('input[type="text"]', timeout=2),

                # 方式2: 通过class查找
                lambda: self.dp_page.ele('.search-input', timeout=2),
                lambda: self.dp_page.ele('#searchInput', timeout=2),

                # 方式3: 通过name查找
                lambda: self.dp_page.ele('input[name*="search"]', timeout=2),
                lambda: self.dp_page.ele('input[name*="keyword"]', timeout=2),
            ]

            search_input = None
            for trigger in search_triggers:
                try:
                    element = trigger()
                    if element and element.is_displayed() and element.is_enabled():
                        search_input = element
                        break
                except:
                    continue

            if search_input:
                print(f"✅ 找到搜索框，输入: {search_value}")
                search_input.clear()
                search_input.input(search_value)
                time.sleep(1)

                # 查找搜索按钮
                button_triggers = [
                    lambda: self.dp_page.ele('button[type="submit"]', timeout=1),
                    lambda: self.dp_page.ele('.search-btn', timeout=1),
                    lambda: self.dp_page.ele('.btn-search', timeout=1),
                    lambda: self.dp_page.ele('button[aria-label*="搜索"]', timeout=1),
                ]

                for trigger in button_triggers:
                    try:
                        button = trigger()
                        if button and button.is_displayed() and button.is_enabled():
                            button.click()
                            print("✅ 点击搜索按钮")
                            time.sleep(5)
                            return True
                    except:
                        continue

                # 如果没有按钮，尝试按Enter
                print("⚡ 尝试按Enter键搜索")
                search_input.input('\n')
                time.sleep(5)
                return True

            # 如果没找到搜索框，尝试JavaScript触发
            print("⚡ 尝试JavaScript触发搜索")
            return self._trigger_js_search(search_value)

        except Exception as e:
            print(f"触发搜索失败: {e}")
            return False

    def _trigger_js_search(self, search_value: str) -> bool:
        """JavaScript触发搜索"""
        js_codes = [
            # 方式1: 使用fetch
            f"""
            fetch('/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue={urllib.parse.quote(search_value)}&pageNum=1&pageSize=10&timestamp=' + Date.now(), {{
                headers: {{
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html'
                }}
            }}).then(r => r.json()).then(data => {{
                console.log('Fetch搜索结果:', data);
                window.lastSearchResult = data;
            }}).catch(e => console.error('Fetch搜索失败:', e));
            """,

            # 方式2: 使用XMLHttpRequest
            f"""
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/datasearch/data/nmpadata/search?itemId=ff80808183cad75001840881f848179f&isSenior=N&searchValue={urllib.parse.quote(search_value)}&pageNum=1&pageSize=10&timestamp=' + Date.now());
            xhr.setRequestHeader('Accept', 'application/json, text/plain, */*');
            xhr.setRequestHeader('Referer', 'https://www.nmpa.gov.cn/datasearch/search-result.html');
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    var data = JSON.parse(xhr.responseText);
                    console.log('XHR搜索结果:', data);
                    window.lastSearchResult = data;
                }}
            }};
            xhr.send();
            """,

            # 方式3: 尝试访问已有的搜索结果页面
            """
            window.location.href = '/datasearch/search-result.html?searchValue=' + encodeURIComponent('{search_value}');
            """
        ]

        for i, js_code in enumerate(js_codes):
            try:
                print(f"🔧 尝试JavaScript方式 {i+1}")
                self.dp_page.run_js(js_code)
                time.sleep(3)

                # 检查是否有结果
                result = self.dp_page.run_js("return window.lastSearchResult || null;")
                if result and result.get('code') == 200:
                    print(f"✅ JavaScript搜索成功: 方式{i+1}")
                    return True

            except Exception as e:
                print(f"JavaScript方式 {i+1} 失败: {e}")
                continue

        return False

    def search_with_captured_signature(self, item_id: str, search_value: str, page_num: int = 1) -> Optional[Dict[str, Any]]:
        """使用捕获的签名进行搜索"""
        cache_key = f"{search_value}_{page_num}"

        if cache_key in self.sign_cache:
            cached = self.sign_cache[cache_key]
            print(f"✅ 使用缓存签名: {cached['sign'][:16]}...")

            # 使用DrissionPage发送请求
            params = cached['full_params'].copy()
            if 'pageNum' in params:
                params['pageNum'] = str(page_num)

            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}/datasearch/data/nmpadata/search?{query_string}"

            try:
                self.dp_page.get(url)
                time.sleep(3)

                page_content = self.dp_page.html
                if page_content:
                    data = json.loads(page_content)
                    if data.get('code') == 200:
                        return data
            except Exception as e:
                print(f"缓存签名请求失败: {e}")

        return None

    def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """执行搜索"""
        print(f"🔍 搜索: {search_value}, 第{page_num}页")

        # 1. 尝试使用缓存的签名
        cached_result = self.search_with_captured_signature(item_id, search_value, page_num)
        if cached_result:
            return cached_result

        # 2. 如果是第一页，尝试触发真实搜索以捕获签名
        if page_num == 1:
            print("🎯 触发真实搜索以捕获签名...")
            if self._trigger_real_search(search_value):
                time.sleep(3)

                # 再次尝试使用缓存的签名
                cached_result = self.search_with_captured_signature(item_id, search_value, page_num)
                if cached_result:
                    return cached_result

        # 3. 最后尝试构造请求
        print("⚡ 尝试构造请求...")
        return self._try_constructed_request(item_id, search_value, page_num, page_size)

    def _try_constructed_request(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """尝试构造请求"""
        # 基于分析的请求构造
        timestamp = int(time.time() * 1000)

        # 尝试多种签名方式
        sign_attempts = [
            # 方式1: 简单MD5
            lambda: self._generate_simple_md5_sign(item_id, search_value, page_num, page_size, timestamp),

            # 方式2: 基于时间戳的动态签名
            lambda: self._generate_dynamic_sign(item_id, search_value, page_num, page_size, timestamp),

            # 方式3: 无签名直接请求
            lambda: None,
        ]

        for i, sign_func in enumerate(sign_attempts):
            try:
                sign = sign_func()

                params = {
                    'itemId': item_id,
                    'isSenior': 'N',
                    'searchValue': search_value,
                    'pageNum': page_num,
                    'pageSize': page_size,
                    'timestamp': timestamp
                }

                if sign:
                    params['sign'] = sign

                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                url = f"{self.base_url}/datasearch/data/nmpadata/search?{query_string}"

                self.dp_page.get(url)
                time.sleep(3)

                page_content = self.dp_page.html
                if page_content:
                    data = json.loads(page_content)
                    if data.get('code') == 200:
                        print(f"✅ 构造请求成功: 方式{i+1}")
                        return data

            except Exception as e:
                print(f"构造请求方式{i+1}失败: {e}")
                continue

        return None

    def _generate_simple_md5_sign(self, item_id: str, search_value: str, page_num: int, page_size: int, timestamp: int) -> str:
        """生成简单MD5签名"""
        sign_string = f"itemId={item_id}isSenior=NsearchValue={search_value}pageNum={page_num}pageSize={page_size}timestamp={timestamp}nmpa2024"
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def _generate_dynamic_sign(self, item_id: str, search_value: str, page_num: int, page_size: int, timestamp: int) -> str:
        """生成动态签名"""
        key = f"nmpa_key_{timestamp % 1000}"
        sign_string = f"timestamp={timestamp}itemId={item_id}search={search_value}page={page_num}{key}"
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def get_item_ids(self) -> Dict[str, str]:
        """获取数据库ID"""
        return {
            "domestic": "ff80808183cad75001840881f848179f",
            "imported": "ff80808183cad75001840881f84817a0"
        }

    def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict[str, Any]]:
        """完整爬取任务"""
        print(f"🚀 开始爬取: {dataset} - {code_prefix}")

        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset)

        if not item_id:
            print(f"❌ 未找到数据集ID: {dataset}")
            return []

        all_records = []
        max_pages = self.cfg.get("max_pages", 2)

        for page in range(1, max_pages + 1):
            print(f"📄 爬取第 {page} 页...")

            result = self.search_once(item_id, code_prefix, page, 10)

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
                    'page': page
                }
                all_records.append(full_record)

            print(f"第 {page} 页完成: {len(data_list)} 条记录")
            time.sleep(2)  # 页面间隔

        print(f"🎉 爬取完成: {dataset} - {code_prefix}, 共 {len(all_records)} 条")
        return all_records


def create_ultimate_crawler(cfg: Dict[str, Any]) -> UltimateNMPACrawler:
    """创建终极爬虫实例"""
    return UltimateNMPACrawler(cfg)


if __name__ == "__main__":
    # 测试终极解决方案
    config = {
        "headless": True,
        "max_pages": 2,
        "page_size": 10
    }

    crawler = create_ultimate_crawler(config)

    try:
        print("🧪 测试终极解决方案...")
        crawler.start()

        # 测试搜索
        result = crawler.search_once(
            "ff80808183cad75001840881f848179f",
            "国药准字H",
            1,
            10
        )

        if result:
            print(f"✅ 测试成功: {result}")
        else:
            print("❌ 测试失败")

    finally:
        crawler.stop()
        print("🏁 测试完成")