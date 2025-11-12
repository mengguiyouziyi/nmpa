#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级NMPA爬虫引擎 - 基于最新调研成果的优化版本
整合2024-2025年最新的反爬虫绕过技术和最佳实践
"""

import asyncio
import json
import time
import random
import logging
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import pandas as pd


@dataclass
class DrugRecord:
    """药品记录数据结构"""
    id: str
    name: str
    approval_number: str
    company: str
    specification: str
    dosage_form: str = ""
    category: str = ""
    crawl_time: float = 0.0
    raw_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'approval_number': self.approval_number,
            'company': self.company,
            'specification': self.specification,
            'dosage_form': self.dosage_form,
            'category': self.category,
            'crawl_time': self.crawl_time,
            'raw_data': self.raw_data
        }


class DataCleaner:
    """数据清洗和验证工具"""

    @staticmethod
    def clean_drug_name(name: str) -> Optional[str]:
        """清洗药品名称"""
        if not name:
            return None
        name = re.sub(r'\s+', ' ', str(name).strip())
        return name if name else None

    @staticmethod
    def validate_approval_number(approval: str) -> bool:
        """验证批准文号格式"""
        if not approval:
            return False
        # 国药准字格式验证
        patterns = [
            r'^国药准字[A-Z]\d{8}$',
            r'^国药准字[A-Z]{2}\d{8}$',
            r'^国药准字[A-Z]{1,2}\d{8}$'
        ]
        return any(re.match(pattern, str(approval)) for pattern in patterns)

    @staticmethod
    def standardize_company(company: str) -> Optional[str]:
        """标准化生产单位名称"""
        if not company:
            return None
        company = re.sub(r'(有限公司|有限责任公司|股份有限公司)', '有限公司', str(company))
        return re.sub(r'\s+', ' ', company.strip())


class PerformanceMonitor:
    """性能监控工具"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    def log_request(self, success: bool = True):
        """记录请求"""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        elapsed = time.time() - self.start_time
        return {
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_count / max(self.request_count, 1) * 100,
            'elapsed_time': elapsed,
            'requests_per_minute': self.request_count / max(elapsed / 60, 1)
        }


class AdvancedNMPACrawler:
    """高级NMPA爬虫引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://www.nmpa.gov.cn"
        self.search_url = "https://www.nmpa.gov.cn/datasearch/home-index.html"

        # 初始化组件
        self.data_cleaner = DataCleaner()
        self.monitor = PerformanceMonitor()

        # 设置日志
        self._setup_logging()

        # Playwright相关
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 反检测配置
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]

        self.logger.info("高级NMPA爬虫引擎初始化完成")

    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nmpa_crawler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AdvancedNMPACrawler')

    async def start(self):
        """启动爬虫引擎"""
        self.logger.info("🚀 启动高级NMPA爬虫引擎...")

        try:
            self.playwright = await async_playwright().start()

            # 启动浏览器
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',  # 禁用JS以防检测
                '--disable-default-apps',
                '--disable-sync',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-background-networking'
            ]

            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=browser_args
            )

            # 创建上下文
            user_agent = random.choice(self.user_agents)
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 添加反检测脚本
            await self._add_anti_detection_scripts()

            # 设置请求拦截
            await self._setup_request_interception()

            self.logger.info("✅ 爬虫引擎启动成功")

        except Exception as e:
            self.logger.error(f"❌ 爬虫引擎启动失败: {e}")
            raise

    async def _add_anti_detection_scripts(self):
        """添加反检测脚本"""
        stealth_scripts = """
        // 移除webdriver标识
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // 伪造Chrome对象
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // 伪造权限API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // 伪造插件
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

        // 伪造语言
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en'],
        });

        // 伪造连接
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 100,
                downlink: 10,
            }),
        });
        """

        await self.page.add_init_script(stealth_scripts)
        self.logger.debug("✅ 反检测脚本注入完成")

    async def _setup_request_interception(self):
        """设置请求拦截"""
        async def handle_request(route, request):
            # 添加随机延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # 修改请求头
            headers = request.headers
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })

            await route.continue_(headers=headers)

        await self.page.route('**/*', handle_request)
        self.logger.debug("✅ 请求拦截设置完成")

    async def navigate_to_search_page(self) -> bool:
        """导航到搜索页面"""
        try:
            self.logger.info(f"📄 正在访问NMPA搜索页面: {self.search_url}")

            await self.page.goto(self.search_url,
                wait_until='domcontentloaded',
                timeout=30000
            )

            # 等待页面加载
            await asyncio.sleep(random.uniform(2, 4))

            # 检查是否成功加载
            title = await self.page.title()
            self.logger.info(f"✅ 页面加载成功: {title}")

            return True

        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            return False

    async def search_drugs(self, keyword: str, max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:
        """搜索药品信息"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔍 搜索药品: {keyword} (第{attempt + 1}次尝试)")

                # 导航到搜索页面
                if not await self.navigate_to_search_page():
                    continue

                # 多种搜索选择器
                search_selectors = [
                    'input[placeholder*="输入"]',
                    'input[placeholder*="搜索"]',
                    'input[type="text"]',
                    '.search-input',
                    '#searchInput',
                    'input[name*="search"]',
                    'input[placeholder*="药品"]'
                ]

                search_input = None
                for selector in search_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        for element in elements:
                            if await element.is_visible() and await element.is_enabled():
                                search_input = element
                                self.logger.info(f"✅ 找到搜索框: {selector}")
                                break
                        if search_input:
                            break
                    except:
                        continue

                if not search_input:
                    self.logger.warning("❌ 未找到搜索输入框")
                    continue

                # 清空并输入搜索关键词
                await search_input.clear()
                await asyncio.sleep(random.uniform(0.5, 1.0))

                # 模拟人类输入
                for char in keyword:
                    await search_input.type(char, delay=random.uniform(50, 150))
                    await asyncio.sleep(random.uniform(0.05, 0.15))

                await asyncio.sleep(random.uniform(1, 2))

                # 查找搜索按钮
                button_selectors = [
                    'button[type="submit"]',
                    '.search-btn',
                    '.btn-search',
                    'button[aria-label*="搜索"]',
                    'button:has-text("搜索")',
                    'button:has-text("查询")',
                    '.search-button'
                ]

                search_button = None
                for selector in button_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        for element in elements:
                            if await element.is_visible() and await element.is_enabled():
                                search_button = element
                                self.logger.info(f"✅ 找到搜索按钮: {selector}")
                                break
                        if search_button:
                            break
                    except:
                        continue

                if search_button:
                    await search_button.click()
                    self.logger.info("✅ 点击搜索按钮")
                else:
                    # 尝试按Enter键
                    await search_input.press('Enter')
                    self.logger.info("✅ 按Enter键搜索")

                # 等待搜索结果
                await asyncio.sleep(random.uniform(3, 5))

                # 尝试多种方式获取数据
                results = await self._extract_search_results()

                if results:
                    self.logger.info(f"✅ 搜索成功，找到 {len(results)} 条结果")
                    self.monitor.log_request(True)
                    return results
                else:
                    self.logger.warning("⚠️ 搜索完成但未找到数据")

            except Exception as e:
                self.logger.error(f"❌ 搜索失败 (第{attempt + 1}次): {e}")
                self.monitor.log_request(False)

                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))

        return None

    async def _extract_search_results(self) -> Optional[List[Dict[str, Any]]]:
        """提取搜索结果"""
        try:
            # 方法1: 尝试从页面内容提取表格数据
            table_results = await self._extract_table_data()
            if table_results:
                return table_results

            # 方法2: 尝试从JavaScript变量提取
            js_results = await self._extract_from_javascript()
            if js_results:
                return js_results

            # 方法3: 尝试从API响应提取
            api_results = await self._extract_from_api_responses()
            if api_results:
                return api_results

            # 方法4: 尝试从页面文本提取
            text_results = await self._extract_from_page_text()
            if text_results:
                return text_results

            return None

        except Exception as e:
            self.logger.error(f"❌ 数据提取失败: {e}")
            return None

    async def _extract_table_data(self) -> Optional[List[Dict[str, Any]]]:
        """从表格中提取数据"""
        try:
            # 查找表格
            table_selectors = [
                'table',
                '.table',
                '.data-table',
                '.result-table',
                '[class*="table"]'
            ]

            for selector in table_selectors:
                tables = await self.page.query_selector_all(selector)
                for table in tables:
                    if await table.is_visible():
                        rows = await table.query_selector_all('tr')
                        if len(rows) > 1:  # 至少有标题行和一行数据
                            data = []
                            for row in rows[1:]:  # 跳过标题行
                                cells = await row.query_selector_all('td')
                                if len(cells) >= 3:
                                    row_data = [await cell.text_content() for cell in cells]
                                    if any(row_data):  # 确保不是空行
                                        data.append({
                                            'raw_data': row_data,
                                            'source': 'table'
                                        })

                            if data:
                                self.logger.info(f"✅ 从表格提取到 {len(data)} 条数据")
                                return data

            return None

        except Exception as e:
            self.logger.debug(f"表格数据提取失败: {e}")
            return None

    async def _extract_from_javascript(self) -> Optional[List[Dict[str, Any]]]:
        """从JavaScript变量提取数据"""
        try:
            # 尝试多种常见的JavaScript变量
            js_scripts = [
                "return window.searchResults || null;",
                "return window.resultData || null;",
                "return window.dataList || null;",
                "return window.nmpaData || null;",
                "return window.searchData || null;",
                "return document.querySelector('[data-results]')?.dataset?.results || null;"
            ]

            for script in js_scripts:
                try:
                    result = await self.page.evaluate(script)
                    if result and isinstance(result, (list, dict)):
                        if isinstance(result, dict) and 'data' in result:
                            result = result['data']
                        if isinstance(result, list) and result:
                            self.logger.info(f"✅ 从JavaScript提取到 {len(result)} 条数据")
                            return [{'raw_data': item, 'source': 'javascript'} for item in result]
                except:
                    continue

            return None

        except Exception as e:
            self.logger.debug(f"JavaScript数据提取失败: {e}")
            return None

    async def _extract_from_api_responses(self) -> Optional[List[Dict[str, Any]]]:
        """从API响应提取数据"""
        try:
            # 监听网络请求
            responses = []

            async def handle_response(response):
                if 'search' in response.url.lower() or 'data' in response.url.lower():
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            data = await response.json()
                            if data and isinstance(data, dict):
                                responses.append(data)
                    except:
                        pass

            self.page.on('response', handle_response)

            # 等待一段时间收集响应
            await asyncio.sleep(2)

            for response_data in responses:
                if isinstance(response_data, dict):
                    # 尝试多种数据路径
                    data_paths = [
                        'data',
                        'results',
                        'list',
                        'items',
                        'data.list',
                        'data.results',
                        'result.data'
                    ]

                    for path in data_paths:
                        try:
                            keys = path.split('.')
                            data = response_data
                            for key in keys:
                                data = data[key]

                            if isinstance(data, list) and data:
                                self.logger.info(f"✅ 从API响应提取到 {len(data)} 条数据")
                                return [{'raw_data': item, 'source': 'api'} for item in data]
                        except:
                            continue

            return None

        except Exception as e:
            self.logger.debug(f"API响应数据提取失败: {e}")
            return None

    async def _extract_from_page_text(self) -> Optional[List[Dict[str, Any]]]:
        """从页面文本提取数据"""
        try:
            # 获取页面文本
            page_text = await self.page.text_content('body')

            # 查找药品批准文号模式
            approval_pattern = r'国药准字([A-Z]\d{8})'
            approvals = re.findall(approval_pattern, page_text)

            if approvals:
                self.logger.info(f"✅ 从页面文本找到 {len(approvals)} 个批准文号")
                return [{'raw_data': {'approval': f'国药准字{approval}'}, 'source': 'text'} for approval in approvals]

            return None

        except Exception as e:
            self.logger.debug(f"页面文本数据提取失败: {e}")
            return None

    def process_raw_data(self, raw_results: List[Dict[str, Any]]) -> List[DrugRecord]:
        """处理原始数据"""
        processed_records = []

        for result in raw_results:
            try:
                raw_data = result.get('raw_data', {})

                # 根据数据源类型处理
                if isinstance(raw_data, list):
                    # 表格数据
                    record = self._process_table_row(raw_data)
                elif isinstance(raw_data, dict):
                    # JSON数据
                    record = self._process_json_data(raw_data)
                else:
                    # 文本数据
                    record = self._process_text_data(raw_data)

                if record:
                    processed_records.append(record)

            except Exception as e:
                self.logger.warning(f"数据处理失败: {e}")
                continue

        self.logger.info(f"✅ 数据处理完成，有效记录: {len(processed_records)} 条")
        return processed_records

    def _process_table_row(self, row_data: List[str]) -> Optional[DrugRecord]:
        """处理表格行数据"""
        try:
            if len(row_data) >= 3:
                # 假设格式: [药品名称, 批准文号, 生产单位, ...]
                name = self.data_cleaner.clean_drug_name(row_data[0])
                approval = row_data[1] if len(row_data) > 1 else ""
                company = self.data_cleaner.standardize_company(row_data[2]) if len(row_data) > 2 else ""

                if name and self.data_cleaner.validate_approval_number(approval):
                    return DrugRecord(
                        id=hashlib.md5(f"{approval}_{name}".encode()).hexdigest(),
                        name=name,
                        approval_number=approval,
                        company=company or "",
                        specification=row_data[3] if len(row_data) > 3 else "",
                        crawl_time=time.time(),
                        raw_data={'table_row': row_data}
                    )
        except:
            pass
        return None

    def _process_json_data(self, json_data: Dict[str, Any]) -> Optional[DrugRecord]:
        """处理JSON数据"""
        try:
            # 尝试多种字段名
            name_fields = ['name', 'drugName', 'productName', 'title']
            approval_fields = ['approvalNumber', 'approval', 'licenseNumber', 'permitNumber']
            company_fields = ['company', 'manufacturer', 'producer', 'orgName']

            name = None
            for field in name_fields:
                if field in json_data and json_data[field]:
                    name = self.data_cleaner.clean_drug_name(json_data[field])
                    break

            approval = None
            for field in approval_fields:
                if field in json_data and json_data[field]:
                    approval = json_data[field]
                    break

            company = None
            for field in company_fields:
                if field in json_data and json_data[field]:
                    company = self.data_cleaner.standardize_company(json_data[field])
                    break

            if name and approval and self.data_cleaner.validate_approval_number(approval):
                return DrugRecord(
                    id=json_data.get('id', hashlib.md5(f"{approval}_{name}".encode()).hexdigest()),
                    name=name,
                    approval_number=approval,
                    company=company or "",
                    specification=json_data.get('specification', ''),
                    crawl_time=time.time(),
                    raw_data=json_data
                )
        except:
            pass
        return None

    def _process_text_data(self, text_data: Any) -> Optional[DrugRecord]:
        """处理文本数据"""
        try:
            if isinstance(text_data, str):
                approval_match = re.search(r'国药准字([A-Z]\d{8})', text_data)
                if approval_match:
                    approval = f"国药准字{approval_match.group(1)}"
                    return DrugRecord(
                        id=hashlib.md5(approval.encode()).hexdigest(),
                        name="未知药品",
                        approval_number=approval,
                        company="",
                        specification="",
                        crawl_time=time.time(),
                        raw_data={'text': text_data}
                    )
        except:
            pass
        return None

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[DrugRecord]:
        """执行完整的爬取任务"""
        self.logger.info(f"🚀 开始爬取任务: {dataset} - {code_prefix}")

        all_records = []
        max_pages = self.config.get('max_pages', 3)

        for page in range(1, max_pages + 1):
            self.logger.info(f"📄 爬取第 {page} 页...")

            # 搜索药品
            raw_results = await self.search_drugs(code_prefix)

            if not raw_results:
                self.logger.info(f"第 {page} 页无数据，停止")
                break

            # 处理数据
            processed_records = self.process_raw_data(raw_results)

            if processed_records:
                # 添加额外信息
                for record in processed_records:
                    record.dataset = dataset
                    record.code_prefix = code_prefix
                    record.page = page

                all_records.extend(processed_records)
                self.logger.info(f"第 {page} 页完成: {len(processed_records)} 条记录")

            # 随机延迟
            delay = random.uniform(3, 8)
            self.logger.debug(f"等待 {delay:.1f} 秒...")
            await asyncio.sleep(delay)

        self.logger.info(f"🎉 爬取任务完成: {dataset} - {code_prefix}, 共 {len(all_records)} 条")

        # 显示性能统计
        stats = self.monitor.get_stats()
        self.logger.info(f"📊 性能统计: {stats}")

        return all_records

    async def stop(self):
        """停止爬虫引擎"""
        self.logger.info("🛑 正在停止爬虫引擎...")

        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.logger.info("✅ 爬虫引擎已停止")

        except Exception as e:
            self.logger.error(f"❌ 停止引擎时出错: {e}")


async def create_advanced_crawler(config: Dict[str, Any]) -> AdvancedNMPACrawler:
    """创建高级爬虫实例"""
    crawler = AdvancedNMPACrawler(config)
    await crawler.start()
    return crawler


if __name__ == "__main__":
    # 测试代码
    async def test_advanced_crawler():
        config = {
            'headless': True,
            'max_pages': 2,
            'log_level': 'INFO'
        }

        crawler = await create_advanced_crawler(config)

        try:
            records = await crawler.crawl_job('domestic', '国药准字H', 'outputs')
            print(f"测试完成，获取到 {len(records)} 条记录")

            for i, record in enumerate(records[:5]):
                print(f"{i+1}. {record.name} - {record.approval_number}")

        finally:
            await crawler.stop()

    asyncio.run(test_advanced_crawler())