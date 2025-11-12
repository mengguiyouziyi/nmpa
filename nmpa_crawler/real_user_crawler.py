# -*- coding: utf-8 -*-
"""
真实用户NMPA爬虫 - 基于用户能正常访问的事实
直接使用requests模拟真实浏览器请求，绕过DrissionPage的问题
"""
import asyncio
import json
import time
import random
import hashlib
import requests
from typing import Dict, List, Any
from rich import print as rprint

class RealUserNMPACrawler:
    """真实用户NMPA爬虫"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.session = requests.Session()

        # 完全模拟真实Chrome浏览器的请求头
        self.real_browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        # API请求头部（模拟真实AJAX）
        self.ajax_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置session headers
        self.session.headers.update(self.real_browser_headers)

        # 基于用户访问的真实API端点
        self.base_urls = {
            'main': 'https://www.nmpa.gov.cn',
            'datasearch': 'https://www.nmpa.gov.cn/datasearch',
            'api': 'https://www.nmpa.gov.cn/datasearch/data/nmpadata'
        }

    async def start(self):
        """启动爬虫"""
        rprint("[bold blue]启动真实用户NMPA爬虫[/]")

        # 模拟真实用户访问流程建立session
        success = await self.establish_real_session()

        if success:
            rprint("[green]✓ 真实用户session建立成功[/]")
            return True
        else:
            rprint("[red]❌ 真实用户session建立失败[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        if self.session:
            self.session.close()

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[dim]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def establish_real_session(self) -> bool:
        """建立真实用户session"""
        rprint("[cyan]建立真实用户session...[/]")

        try:
            # 步骤1: 访问NMPA首页
            rprint("[blue]1. 访问NMPA首页[/]")
            response = self.session.get('https://www.nmpa.gov.cn/', timeout=30)

            if response.status_code == 200:
                rprint(f"[green]✓ 首页访问成功: {response.status_code}[/]")
                # 保存cookies
                rprint(f"[green]✓ 获取cookies: {len(self.session.cookies)}[/]")
                self.smart_delay(2, 4)
            else:
                rprint(f"[yellow]首页访问状态: {response.status_code}[/]")

            # 步骤2: 访问数据查询页面
            rprint("[blue]2. 访问数据查询页面[/]")
            response = self.session.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1', timeout=30)

            if response.status_code == 200:
                rprint(f"[green]✓ 数据查询页面访问成功: {response.status_code}[/]")
                rprint(f"[green]✓ 页面标题: {response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else 'N/A'}[/]")
                self.smart_delay(3, 5)
            else:
                rprint(f"[yellow]数据查询页面访问状态: {response.status_code}[/]")

            # 步骤3: 获取页面内容并分析
            await self.analyze_page_content(response.text)

            return True

        except Exception as e:
            rprint(f"[red]Session建立失败: {e}[/]")
            return False

    async def analyze_page_content(self, html_content: str):
        """分析页面内容，查找关键信息"""
        rprint("[blue]分析页面内容...[/]")

        # 查找关键JavaScript文件和API端点
        import re

        # 查找数据查询相关的API
        api_patterns = [
            r'/datasearch/data/[^"\s]+',
            r'/datasearch/api/[^"\s]+',
            r'action="([^"]+)"',
            r'url:\s*["\']([^"\']+)["\']'
        ]

        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if 'search' in match or 'data' in match:
                    found_apis.add(match)

        if found_apis:
            rprint(f"[green]✓ 发现潜在API端点: {len(found_apis)}[/]")
            for api in list(found_apis)[:5]:
                rprint(f"  - {api}")

        # 查找表单和参数
        form_patterns = [
            r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>',
            r'<select[^>]*name="([^"]*)"[^>]*>.*?</select>',
            r'<input[^>]*type="hidden"[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>'
        ]

        found_params = {}
        for pattern in form_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                if len(match) == 2:
                    found_params[match[0]] = match[1]

        if found_params:
            rprint(f"[green]✓ 发现表单参数: {len(found_params)}[/]")

    async def try_direct_search(self, code_prefix: str) -> List[Dict]:
        """尝试直接搜索"""
        rprint(f"[bold cyan]尝试直接搜索: {code_prefix}[/]")

        # 尝试多个可能的API端点
        api_endpoints = [
            'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search',
            'https://www.nmpa.gov.cn/datasearch/data/search',
            'https://www.nmpa.gov.cn/datasearch/api/search',
            'https://www.nmpa.gov.cn/datasearch/search/data',
            'https://search.nmpa.gov.cn/api/data'
        ]

        for i, api_url in enumerate(api_endpoints):
            rprint(f"[blue]尝试API端点 {i+1}: {api_url}[/]")

            try:
                # 构建搜索参数
                params = self.build_search_params(code_prefix)

                # 尝试POST请求
                response = self.session.post(api_url, data=params, headers=self.ajax_headers, timeout=30)

                rprint(f"[blue]POST响应状态: {response.status_code}[/]")

                if response.status_code == 200:
                    results = await self.parse_api_response(response.text, api_url)
                    if results:
                        return results

                # 如果POST失败，尝试GET请求
                response = self.session.get(api_url, params=params, headers=self.real_browser_headers, timeout=30)

                rprint(f"[blue]GET响应状态: {response.status_code}[/]")

                if response.status_code == 200:
                    results = await self.parse_api_response(response.text, api_url)
                    if results:
                        return results

            except Exception as e:
                rprint(f"[yellow]API端点 {i+1} 请求失败: {e}[/]")
                continue

            self.smart_delay(1, 3)

        return []

    def build_search_params(self, code_prefix: str) -> Dict:
        """构建搜索参数"""
        # 基于常见的数据查询参数
        base_params = {
            'pageNo': '1',
            'pageSize': '20',
            'searchValue': code_prefix,
            'searchType': '1'
        }

        # 尝试不同的参数组合
        param_variations = [
            {**base_params, 'tableName': 'TABLE25', 'viewTitle': 'TABLE25'},
            {**base_params, 'tableId': '25', 'viewType': 'domestic'},
            {**base_params, 'category': 'drug', 'type': 'domestic'},
            {**base_params, 'drugType': 'H', 'production': 'domestic'},
            base_params  # 基础参数
        ]

        return random.choice(param_variations)

    async def parse_api_response(self, response_text: str, api_url: str) -> List[Dict]:
        """解析API响应"""
        results = []

        try:
            # 尝试解析JSON
            data = json.loads(response_text)
            rprint(f"[green]✓ 成功解析JSON响应: {list(data.keys())}[/]")

            # 处理不同的JSON结构
            if isinstance(data, dict):
                if data.get('success') and data.get('data'):
                    items = data['data'].get('list', data['data'])
                    results = self.extract_drug_info_from_items(items)
                elif data.get('list'):
                    results = self.extract_drug_info_from_items(data['list'])
                elif data.get('items'):
                    results = self.extract_drug_info_from_items(data['items'])
                elif isinstance(data.get('data'), list):
                    results = self.extract_drug_info_from_items(data['data'])

        except json.JSONDecodeError:
            rprint(f"[yellow]响应不是JSON格式，尝试HTML解析...[/]")
            results = await self.parse_html_response(response_text)

        if results:
            rprint(f"[green]🎉 API解析成功！获取 {len(results)} 条药品数据[/]")
            return results

        return []

    def extract_drug_info_from_items(self, items: List) -> List[Dict]:
        """从数据项中提取药品信息"""
        results = []

        for item in items:
            if isinstance(item, dict):
                drug_info = {
                    'name': item.get('productName', item.get('name', item.get('title', ''))),
                    'approval_number': item.get('licenseNumber', item.get('approvalNumber', item.get('licenseSn', ''))),
                    'company': item.get('companyName', item.get('manufacturer', item.get('company', ''))),
                    'specification': item.get('specification', item.get('productSpec', '')),
                    'dosage_form': item.get('dosageForm', item.get('productForm', '')),
                    'approval_date': item.get('approvalDate', item.get('validDate', '')),
                    'source': 'api_extraction',
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': item
                }

                if drug_info['name'] or drug_info['approval_number']:
                    results.append(drug_info)

        return results

    async def parse_html_response(self, html_content: str) -> List[Dict]:
        """解析HTML响应"""
        results = []

        # 使用正则表达式提取药品信息
        import re

        patterns = [
            r'国药准字([HFJZTB]\d{8})\s+([^\n]+?)\s+([^\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
            r'([^\n]+?)\s+国药准字([HFJZTB]\d{8})\s+([^\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
            r'<td[^>]*>([^<]*国药准字[HFJZTB]\d{8}[^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if len(match) >= 3:
                    drug_info = {
                        'approval_number': match[0] if '国药准字' in match[0] else f'国药准字{match[1]}',
                        'name': match[1] if '国药准字' in match[0] else match[0],
                        'company': match[2],
                        'source': 'html_regex_extraction',
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    results.append(drug_info)

        if results:
            rprint(f"[green]✓ HTML解析成功！提取 {len(results)} 条药品数据[/]")

        return results

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行真实用户任务"""
        rprint(f"[bold green]开始真实用户任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 尝试直接搜索
        records = await self.try_direct_search(code_prefix)

        if records:
            all_records.extend(records)
            rprint(f"[green]✅ 直接搜索成功！获取 {len(records)} 条药品数据[/]")
        else:
            # 如果直接搜索失败，尝试其他方法
            rprint("[yellow]直接搜索失败，尝试其他方法...[/]")
            # 可以在这里添加其他搜索方法

        # 如果没有获取到数据，抛出异常
        if not all_records:
            rprint("[red]❌ 真实用户搜索失败，未能获取到任何数据[/]")
            raise RuntimeError("真实用户搜索失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.real_user.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 真实用户搜索成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        # 显示前几条数据
        for i, record in enumerate(all_records[:3]):
            rprint(f"[green]✓ 药品{i+1}: {record.get('name', 'N/A')} - {record.get('approval_number', 'N/A')}[/]")

        return all_records

async def create_real_user_crawler(config: Dict[str, Any]) -> RealUserNMPACrawler:
    """创建真实用户爬虫"""
    crawler = RealUserNMPACrawler(config)
    await crawler.start()
    return crawler