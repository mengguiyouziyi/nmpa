#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合爬虫引擎
结合浏览器拦截和智能签名的最新解决方案
基于2024-2025年GitHub项目分析
"""

import json
import time
import random
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from seleniumwire import webdriver
import undetected_chromedriver as uc
from DrissionPage import ChromiumPage, ChromiumOptions

from enhanced_sign_engine import enhanced_sign_engine
from utils import sleep_jitter, deep_find_item_id, extract_required_fields


class HybridNMPACrawler:
    """混合NMPA爬虫引擎 - 结合浏览器拦截和智能签名"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.driver = None
        self.drission_page = None
        self.captured_signatures = {}
        self.signature_cache = {}
        self.request_interceptor_enabled = True
        self.lock = threading.Lock()

    def _build_selenium_driver(self):
        """构建Selenium驱动用于请求拦截"""
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

        # selenium-wire选项
        seleniumwire_options = {
            'request_storage': 'memory',
            'enable_har': True
        }

        # 代理配置
        proxy_cfg = self.cfg.get("proxy")
        if proxy_cfg and proxy_cfg.get("https"):
            seleniumwire_options["proxy"] = {
                "https": proxy_cfg["https"],
                "http": proxy_cfg.get("http", proxy_cfg["https"])
            }

        self.driver = uc.Chrome(
            version_main=140,
            options=opts,
            seleniumwire_options=seleniumwire_options
        )

        # 请求拦截器
        self.driver.request_interceptor = self._intercept_request
        self.driver.response_interceptor = self._intercept_response

    def _build_drission_page(self):
        """构建DrissionPage实例用于数据抓取"""
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
        options.set_argument('--disable-images')

        # 真实User-Agent
        options.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 代理配置
        proxy_cfg = self.cfg.get("proxy")
        if proxy_cfg and proxy_cfg.get("https"):
            proxy = proxy_cfg.get("https") or proxy_cfg.get("http")
            options.set_proxy(proxy)

        self.drission_page = ChromiumPage(options)
        # 移除webdriver标识
        try:
            self.drission_page.remove_ele('navigator.webdriver')
        except:
            pass

    def _intercept_request(self, request):
        """拦截请求，捕获签名参数"""
        if 'datasearch/data/nmpadata/search' in request.url:
            # 记录请求参数
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(request.url)
            params = parse_qs(parsed.query)

            # 提取签名相关信息
            signature_info = {
                'url': request.url,
                'params': {k: v[0] if v else '' for k, v in params.items()},
                'headers': dict(request.headers),
                'timestamp': time.time()
            }

            # 缓存签名信息
            search_key = f"{params.get('searchValue', [''])[0]}_{params.get('pageNum', ['1'])[0]}"
            with self.lock:
                self.signature_cache[search_key] = signature_info
                self.captured_signatures[search_key] = signature_info['params'].get('sign', [''])[0]

            print(f"🔍 捕获到请求签名: {search_key} -> {signature_info['params'].get('sign', [''])[0][:16]}...")

    def _intercept_response(self, request, response):
        """拦截响应，分析数据结构"""
        if 'datasearch/data/nmpadata/search' in request.url:
            try:
                data = response.body.decode('utf-8')
                json_data = json.loads(data)

                # 记录成功的响应结构
                if json_data.get('code') == 200:
                    print(f"✅ 捕获到成功响应，数据量: {len(json_data.get('data', {}).get('list', []))}")
            except:
                pass

    def start(self):
        """启动混合引擎"""
        print("🚀 启动混合NMPA爬虫引擎...")

        # 启动浏览器用于请求拦截
        if self.request_interceptor_enabled:
            print("📡 启动请求拦截器...")
            self._build_selenium_driver()

        # 启动DrissionPage用于数据抓取
        print("🌐 启动DrissionPage引擎...")
        self._build_drission_page()

        # 访问NMPA主页，触发签名生成
        base_url = "https://www.nmpa.gov.cn"
        if self.driver:
            self.driver.get(f"{base_url}/datasearch/home-index.html")
            time.sleep(5)

        if self.drission_page:
            self.drission_page.get(f"{base_url}/datasearch/home-index.html")
            time.sleep(3)

    def stop(self):
        """停止引擎"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass

    def get_item_ids(self) -> Dict[str, str]:
        """获取数据库ID"""
        # 使用预配置的正确ID
        return {
            "domestic": "ff80808183cad75001840881f848179f",
            "imported": "ff80808183cad75001840881f84817a0"
        }

    def _get_cached_signature(self, search_value: str, page_num: int) -> Optional[str]:
        """获取缓存的签名"""
        cache_key = f"{search_value}_{page_num}"
        return self.captured_signatures.get(cache_key)

    def _try_browser_search(self, item_id: str, search_value: str, page_num: int = 1) -> Optional[Dict[str, Any]]:
        """尝试通过浏览器搜索获取数据"""
        if not self.drission_page:
            return None

        try:
            # 等待并查找搜索相关元素
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
                print("⚠️ 未找到搜索输入框，尝试JavaScript搜索")
                return self._try_javascript_search(item_id, search_value, page_num)

            # 输入搜索内容
            search_input.clear()
            time.sleep(0.5)
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
            else:
                search_input.input('\n')  # 按Enter键

            # 等待搜索结果
            time.sleep(5)

            # 尝试解析搜索结果
            return self._parse_search_results()

        except Exception as e:
            print(f"浏览器搜索失败: {e}")
            return None

    def _try_javascript_search(self, item_id: str, search_value: str, page_num: int) -> Optional[Dict[str, Any]]:
        """尝试JavaScript搜索"""
        try:
            # 直接调用axios进行搜索
            js_code = f"""
            return axios.get('/datasearch/data/nmpadata/search', {{
                params: {{
                    itemId: '{item_id}',
                    isSenior: 'N',
                    searchValue: '{search_value}',
                    pageNum: {page_num},
                    pageSize: 10,
                    timestamp: Date.now()
                }}
            }}).then(response => {{
                return response.data;
            }}).catch(error => {{
                return {{ error: error.message, status: error.response?.status }};
            }});
            """

            result = self.drission_page.run_js(js_code)
            if result and not result.get('error'):
                return result
            else:
                print(f"JavaScript搜索失败: {result}")
                return None

        except Exception as e:
            print(f"JavaScript搜索异常: {e}")
            return None

    def _parse_search_results(self) -> Optional[Dict[str, Any]]:
        """解析搜索结果页面"""
        try:
            # 查找结果表格或列表
            result_selectors = [
                'table tr',
                '.result-item',
                '.search-result',
                '.data-list tr',
                '[data-id]'
            ]

            results = []
            for selector in result_selectors:
                try:
                    elements = self.drission_page.eles(selector)
                    if elements:
                        for element in elements:
                            try:
                                # 提取数据
                                row_data = {}
                                cells = element.eles('td, div, span')
                                for i, cell in enumerate(cells):
                                    if cell.text.strip():
                                        row_data[f'col_{i}'] = cell.text.strip()

                                if row_data:
                                    results.append(row_data)
                            except:
                                continue

                        if results:
                            break
                except:
                    continue

            if results:
                return {
                    'code': 200,
                    'data': {
                        'list': results,
                        'total': len(results)
                    },
                    'message': 'success'
                }

        except Exception as e:
            print(f"解析搜索结果失败: {e}")

        return None

    def search_once(self, item_id: str, search_value: str, page_num: int, page_size: int) -> Optional[Dict[str, Any]]:
        """执行一次搜索 - 混合方案"""
        print(f"🔍 搜索: {search_value}, 第{page_num}页")

        # 1. 尝试使用缓存的签名
        cached_sign = self._get_cached_signature(search_value, page_num)
        if cached_sign:
            print(f"✅ 使用缓存签名: {cached_sign[:16]}...")
            # 这里可以构建HTTP请求使用缓存签名

        # 2. 尝试浏览器搜索
        browser_result = self._try_browser_search(item_id, search_value, page_num)
        if browser_result and browser_result.get('code') == 200:
            print(f"🎉 浏览器搜索成功，获取 {len(browser_result.get('data', {}).get('list', []))} 条数据")
            return browser_result

        # 3. 尝试JavaScript搜索
        js_result = self._try_javascript_search(item_id, search_value, page_num)
        if js_result and js_result.get('code') == 200:
            print(f"🎉 JavaScript搜索成功，获取 {len(js_result.get('data', {}).get('list', []))} 条数据")
            return js_result

        # 4. 最后尝试智能签名生成
        print("⚡ 尝试智能签名生成...")
        try:
            params = {
                "itemId": item_id,
                "isSenior": "N",
                "searchValue": search_value,
                "pageNum": page_num,
                "pageSize": page_size
            }

            signed_params = enhanced_sign_engine.build_request_params(params)

            # 使用DrissionPage发送带签名的请求
            url = f"https://www.nmpa.gov.cn/datasearch/data/nmpadata/search"
            query_string = '&'.join([f"{k}={v}" for k, v in signed_params.items()])
            full_url = f"{url}?{query_string}"

            self.drission_page.get(full_url)
            time.sleep(3)
            page_content = self.drission_page.html
            if page_content:
                try:
                    data = json.loads(page_content)
                    if data.get('code') == 200:
                        print(f"🎉 智能签名成功，获取 {len(data.get('data', {}).get('list', []))} 条数据")
                        return data
                except:
                    pass

        except Exception as e:
            print(f"智能签名尝试失败: {e}")

        print("❌ 所有搜索方法都失败了")
        return None

    def fetch_detail(self, item_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取详情数据"""
        try:
            # 尝试多种详情获取方式
            detail_methods = [
                self._fetch_detail_by_ajax,
                self._fetch_detail_by_navigation,
                self._fetch_detail_by_javascript
            ]

            for method in detail_methods:
                try:
                    result = method(item_id, doc_id)
                    if result:
                        return result
                except:
                    continue

        except Exception as e:
            print(f"获取详情失败: {e}")

        return None

    def _fetch_detail_by_ajax(self, item_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """通过AJAX获取详情"""
        js_code = f"""
        return axios.get('/datasearch/data/nmpadata/queryDetail', {{
            params: {{
                itemId: '{item_id}',
                id: '{doc_id}',
                timestamp: Date.now()
            }}
        }}).then(response => {{
            return response.data;
        }}).catch(error => {{
            return {{ error: error.message }};
        }});
        """

        result = self.drission_page.run_js(js_code)
        return result if result and not result.get('error') else None

    def _fetch_detail_by_navigation(self, item_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """通过页面导航获取详情"""
        # 这里可以实现点击详情链接的导航逻辑
        return None

    def _fetch_detail_by_javascript(self, item_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """通过JavaScript直接获取详情"""
        return None

    def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict[str, Any]]:
        """完整的爬取任务"""
        print(f"🚀 开始爬取任务: {dataset} - {code_prefix}")

        # 获取数据库ID
        item_ids = self.get_item_ids()
        item_id = item_ids.get(dataset)

        if not item_id:
            print(f"❌ 未找到数据集ID: {dataset}")
            return []

        all_records = []
        max_pages = self.cfg.get("max_pages", 2)
        page_size = self.cfg.get("page_size", 10)

        for page in range(1, max_pages + 1):
            print(f"📄 爬取第 {page} 页...")

            # 搜索数据
            search_result = self.search_once(item_id, code_prefix, page, page_size)

            if not search_result:
                print(f"第 {page} 页无数据，停止爬取")
                break

            data_list = search_result.get('data', {}).get('list', [])

            if not data_list:
                print(f"第 {page} 页列表为空，停止爬取")
                break

            # 处理每条记录
            for record in data_list:
                try:
                    # 提取文档ID
                    doc_id = record.get('id') or record.get('docId') or record.get('dataId')

                    if doc_id:
                        # 获取详情数据
                        detail_data = self.fetch_detail(item_id, doc_id)

                        # 合并数据
                        full_record = {
                            'list_data': record,
                            'detail_data': detail_data,
                            'crawl_time': time.time(),
                            'dataset': dataset,
                            'code_prefix': code_prefix,
                            'page': page
                        }

                        all_records.append(full_record)
                    else:
                        # 如果没有详情ID，保留列表数据
                        all_records.append({
                            'list_data': record,
                            'detail_data': None,
                            'crawl_time': time.time(),
                            'dataset': dataset,
                            'code_prefix': code_prefix,
                            'page': page
                        })

                except Exception as e:
                    print(f"处理记录时出错: {e}")
                    continue

                # 添加延迟
                sleep_jitter(1000, 2000)

            print(f"第 {page} 页完成，获取 {len(data_list)} 条记录")

            # 检查是否还有更多数据
            if len(data_list) < page_size:
                break

        print(f"🎉 爬取任务完成: {dataset} - {code_prefix}，共 {len(all_records)} 条记录")
        return all_records


def create_hybrid_crawler(cfg: Dict[str, Any]) -> HybridNMPACrawler:
    """创建混合爬虫实例"""
    return HybridNMPACrawler(cfg)


if __name__ == "__main__":
    # 测试混合爬虫引擎
    config = {
        "headless": True,
        "max_retries": 3,
        "request_delay": 2
    }

    crawler = create_hybrid_crawler(config)

    try:
        print("🧪 测试混合爬虫引擎...")
        crawler.start()

        # 测试搜索
        result = crawler.search_once(
            "ff80808183cad75001840881f848179f",
            "国药准字H",
            1,
            10
        )

        if result:
            print(f"✅ 搜索测试成功: {result}")
        else:
            print("❌ 搜索测试失败")

    finally:
        crawler.stop()
        print("🏁 测试完成")