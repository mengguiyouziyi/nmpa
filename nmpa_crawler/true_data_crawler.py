# -*- coding: utf-8 -*-
"""
真实数据NMPA爬虫 - 专门获取真实NMPA数据
基于GitHub项目的成功突破，不使用备用数据
"""
import asyncio
import json
import time
import hashlib
import requests
import random
from typing import Dict, List, Any
from rich import print as rprint
from DrissionPage import ChromiumPage, ChromiumOptions

class TrueDataCrawler:
    """真实数据NMPA爬虫 - 只获取真实数据"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None
        self.session = requests.Session()

        # 基于GitHub项目的真实API端点
        self.api_endpoints = {
            # 生产许可证API - scxk.nmpa项目的成功端点
            'license_list': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'license_detail': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsById',

            # 药品数据库API - 基于多个项目的综合分析
            'drug_search': 'https://app1.nmpa.gov.cn/data/search',  # 主要查询接口
            'drug_detail': 'https://app1.nmpa.gov.cn/data/detail',  # 详情接口
            'drug_api': 'https://api.nmpa.gov.cn/ypbhwss/v1/druginfo',  # API接口

            # 新发现的端点
            'nmpa_search': 'https://search.nmpa.gov.cn/api/search',
            'nmpa_data': 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search'
        }

        # 基于GitHub项目的多种签名密钥
        self.secret_keys = [
            'nmpasecret2020',      # magical_spider项目
            'nmpa_data_2024',     # 备用密钥1
            'china_nmpa_key',     # 备用密钥2
            'datasearch2024',     # 备用密钥3
            'nmpa_key_2024',      # 备用密钥4
            'cfda_2024_key',      # 备用密钥5
            'search_nmpa_2024',   # 备用密钥6
            'medical_data_2024'   # 备用密钥7
        ]

        # 高级请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nmpa.gov.cn/',
            'Origin': 'https://www.nmpa.gov.cn',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }

    async def start(self):
        """启动爬虫"""
        rprint("[bold blue]启动真实数据NMPA爬虫（只获取真实数据）[/]")

        # 初始化DrissionPage
        try:
            chromium_options = ChromiumOptions()
            chromium_options.headless(self.config.get('headless', True))
            chromium_options.set_user_agent(self.headers['User-Agent'])

            # 反检测配置
            chromium_options.set_argument('--disable-blink-features=AutomationControlled')
            chromium_options.set_argument('--disable-dev-shm-usage')
            chromium_options.set_argument('--no-sandbox')
            chromium_options.set_argument('--disable-web-security')
            chromium_options.set_argument('--allow-running-insecure-content')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ DrissionPage初始化成功[/]")
        except Exception as e:
            rprint(f"[red]DrissionPage初始化失败: {e}[/]")

        # 初始化requests session
        self.session.headers.update(self.headers)

    async def stop(self):
        """停止爬虫"""
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass
        if self.session:
            self.session.close()

    def generate_signature_v1(self, params: Dict, secret_key: str) -> str:
        """magical_spider项目的签名算法"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        sign_string = param_string + secret_key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def generate_signature_v2(self, params: Dict, secret_key: str) -> str:
        """标准URL参数签名"""
        param_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_string = param_string + '&' + secret_key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def generate_signature_v3(self, params: Dict, secret_key: str) -> str:
        """时间戳签名算法"""
        timestamp = params.get('timestamp', int(time.time() * 1000))
        sign_string = f"timestamp={timestamp}&secret={secret_key}"
        for k, v in sorted(params.items()):
            if k != 'timestamp':
                sign_string += f"&{k}={v}"
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def crawl_license_data(self, page: int = 1) -> List[Dict]:
        """
        爬取生产许可证真实数据
        基于scxk.nmpa项目的成功实现
        """
        rprint(f"[cyan]爬取生产许可证真实数据[/] 第{page}页")

        url = self.api_endpoints['license_list']

        # 基于项目的请求参数
        timestamp = int(time.time() * 1000)
        base_params = {
            'on': 'true',
            'page': str(page),
            'pageSize': '15',
            'productName': '',
            'conditionType': '1',
            'applyname': '',
            'applysn': '',
            '_': str(timestamp)
        }

        # 尝试所有签名算法和密钥组合
        for secret_key in self.secret_keys:
            for sign_func in [self.generate_signature_v1, self.generate_signature_v2, self.generate_signature_v3]:
                params = base_params.copy()

                try:
                    sign = sign_func(params, secret_key)
                    params['sign'] = sign

                    # 策略1：使用DrissionPage（更接近真实浏览器）
                    if self.drission_page:
                        try:
                            # 设置请求头
                            self.drission_page.set_headers({
                                'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                            })

                            # 发送POST请求
                            response = self.drission_page.post(url, data=params, timeout=30)

                            if response.status_code == 200:
                                content = response.text
                                if content:
                                    try:
                                        data = json.loads(content)
                                        if data.get('status') == '200' and data.get('list'):
                                            rprint(f"[green]✓ DrissionPage成功！密钥: {secret_key}, 算法: {sign_func.__name__}[/]")
                                            rprint(f"[green]✓ 获取 {len(data['list'])} 条真实许可证数据[/]")
                                            return data['list']
                                        else:
                                            rprint(f"[yellow]DrissionPage返回: {data.get('msg', '未知错误')}[/]")
                                    except json.JSONDecodeError:
                                        rprint(f"[yellow]DrissionPage返回非JSON: {content[:100]}[/]")
                            else:
                                rprint(f"[yellow]DrissionPage HTTP {response.status_code}[/]")
                        except Exception as e:
                            rprint(f"[yellow]DrissionPage异常: {e}[/]")

                    # 策略2：使用requests（备用）
                    try:
                        headers = {
                            'User-Agent': self.headers['User-Agent'],
                            'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                        }

                        response = self.session.post(url, data=params, headers=headers, timeout=30)

                        if response.status_code == 200:
                            data = response.json()
                            if data.get('status') == '200' and data.get('list'):
                                rprint(f"[green]✓ Requests成功！密钥: {secret_key}, 算法: {sign_func.__name__}[/]")
                                rprint(f"[green]✓ 获取 {len(data['list'])} 条真实许可证数据[/]")
                                return data['list']
                            else:
                                rprint(f"[yellow]Requests返回: {data.get('msg', '未知错误')}[/]")
                        else:
                            rprint(f"[yellow]Requests HTTP {response.status_code}[/]")

                    except Exception as e:
                        rprint(f"[yellow]Requests异常: {e}[/]")

                except Exception as e:
                    rprint(f"[red]签名尝试失败: {e}[/]")
                    continue

        rprint("[red]生产许可证数据爬取失败[/]")
        return []

    async def crawl_drug_data(self, keyword: str, page: int = 1) -> List[Dict]:
        """
        爬取药品真实数据
        基于多个GitHub项目的综合分析
        """
        rprint(f"[cyan]爬取药品真实数据[/] 关键词: {keyword}")

        # 尝试多个API端点
        endpoints_to_try = [
            ('nmpa_data', self.api_endpoints['nmpa_data']),
            ('drug_search', self.api_endpoints['drug_search']),
            ('drug_api', self.api_endpoints['drug_api']),
            ('nmpa_search', self.api_endpoints['nmpa_search'])
        ]

        for endpoint_name, url in endpoints_to_try:
            rprint(f"[cyan]尝试端点[/] {endpoint_name}: {url}")

            # 多种参数格式
            param_formats = []

            if endpoint_name == 'nmpa_data':
                # 格式1：基于我们之前的分析
                item_ids = {
                    'domestic': 'ff80808183cad75001840881f848179f',
                    'imported': 'ff80808183cad75001840881f84817a0'
                }

                # 根据关键词确定itemId
                if keyword.startswith('国药准字H'):
                    item_id = item_ids['domestic']
                elif keyword.startswith('国药准字S'):
                    item_id = item_ids['domestic']
                elif keyword.startswith('国药准字J'):
                    item_id = item_ids['imported']
                else:
                    item_id = item_ids['domestic']

                timestamp = int(time.time() * 1000)
                param_formats.append({
                    'itemId': item_id,
                    'searchValue': keyword,
                    'pageNum': page,
                    'pageSize': 10,
                    'isSenior': 'N',
                    'timestamp': timestamp
                })

            elif endpoint_name == 'drug_search':
                # 格式2：通用搜索格式
                param_formats.append({
                    'keyword': keyword,
                    'page': page,
                    'size': 10,
                    'type': 'drug'
                })

            elif endpoint_name == 'drug_api':
                # 格式3：API格式
                param_formats.append({
                    'productName': keyword,
                    'pageNo': page,
                    'pageSize': 10
                })

            elif endpoint_name == 'nmpa_search':
                # 格式4：搜索API格式
                param_formats.append({
                    'q': keyword,
                    'page': page,
                    'pageSize': 10,
                    'tab': 'drug'
                })

            # 尝试每种参数格式
            for params in param_formats:
                # 尝试所有签名算法
                for secret_key in self.secret_keys[:5]:  # 先尝试前5个密钥
                    for sign_func in [self.generate_signature_v1, self.generate_signature_v2]:
                        try:
                            test_params = params.copy()

                            # 添加时间戳（如果没有）
                            if 'timestamp' not in test_params:
                                test_params['timestamp'] = int(time.time() * 1000)

                            # 生成签名
                            sign = sign_func(test_params, secret_key)
                            test_params['sign'] = sign

                            # 尝试DrissionPage
                            if self.drission_page:
                                try:
                                    if endpoint_name in ['nmpa_data', 'drug_search']:
                                        response = self.drission_page.post(url, json=test_params, timeout=30)
                                    else:
                                        response = self.drission_page.post(url, data=test_params, timeout=30)

                                    if response.status_code == 200:
                                        content = response.text
                                        if content:
                                            try:
                                                data = json.loads(content)
                                                # 检查响应格式
                                                data_list = []
                                                if data.get('code') == 200 and data.get('data'):
                                                    data_list = data['data'].get('list', [])
                                                elif data.get('status') == '200' and data.get('list'):
                                                    data_list = data['list']
                                                elif data.get('data'):
                                                    if isinstance(data['data'], list):
                                                        data_list = data['data']
                                                    elif isinstance(data['data'], dict) and data['data'].get('list'):
                                                        data_list = data['data']['list']

                                                if data_list:
                                                    rprint(f"[green]✓ DrissionPage药品数据成功！[/]")
                                                    rprint(f"[green]✓ 端点: {endpoint_name}, 密钥: {secret_key}[/]")
                                                    rprint(f"[green]✓ 获取 {len(data_list)} 条真实药品数据[/]")
                                                    return data_list
                                                else:
                                                    rprint(f"[yellow]DrissionPage返回空数据: {data}[/]")
                                            except json.JSONDecodeError:
                                                rprint(f"[yellow]DrissionPage返回非JSON[/]")
                                    else:
                                        rprint(f"[yellow]DrissionPage HTTP {response.status_code}[/]")
                                except Exception as e:
                                    rprint(f"[yellow]DrissionPage异常: {e}[/]")

                            # 尝试requests
                            try:
                                if endpoint_name in ['nmpa_data', 'drug_search']:
                                    response = self.session.post(url, json=test_params, timeout=30)
                                else:
                                    response = self.session.post(url, data=test_params, timeout=30)

                                if response.status_code == 200:
                                    data = response.json()
                                    # 检查响应格式
                                    data_list = []
                                    if data.get('code') == 200 and data.get('data'):
                                        data_list = data['data'].get('list', [])
                                    elif data.get('status') == '200' and data.get('list'):
                                        data_list = data['list']
                                    elif data.get('data'):
                                        if isinstance(data['data'], list):
                                            data_list = data['data']
                                        elif isinstance(data['data'], dict) and data['data'].get('list'):
                                            data_list = data['data']['list']

                                    if data_list:
                                        rprint(f"[green]✓ Requests药品数据成功！[/]")
                                        rprint(f"[green]✓ 端点: {endpoint_name}, 密钥: {secret_key}[/]")
                                        rprint(f"[green]✓ 获取 {len(data_list)} 条真实药品数据[/]")
                                        return data_list
                                    else:
                                        rprint(f"[yellow]Requests返回空数据: {data}[/]")
                                else:
                                    rprint(f"[yellow]Requests HTTP {response.status_code}[/]")
                            except Exception as e:
                                rprint(f"[yellow]Requests异常: {e}[/]")

                        except Exception as e:
                            rprint(f"[red]参数尝试失败: {e}[/]")
                            continue

        rprint("[red]药品数据爬取失败[/]")
        return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行真实数据爬取任务"""
        rprint(f"[bold green]开始真实数据爬取任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 策略1：爬取生产许可证数据
        if dataset in ['license', 'domestic']:
            license_records = await self.crawl_license_data(page=1)
            if license_records:
                rprint(f"[green]✓ 成功获取 {len(license_records)} 条真实生产许可证数据[/]")
                for record in license_records:
                    standard_record = {
                        'name': record.get('productName', record.get('产品名称', '')),
                        'approval_number': record.get('licenseSn', record.get('许可证号', '')),
                        'company': record.get('companyName', record.get('企业名称', '')),
                        'specification': record.get('productSpec', record.get('规格', '')),
                        'dosage_form': record.get('productForm', record.get('剂型', '')),
                        'approval_date': record.get('validDate', record.get('有效期至', '')),
                        'source': 'real_nmpa_license_api',
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 策略2：爬取药品数据
        if dataset in ['domestic', 'imported']:
            drug_records = await self.crawl_drug_data(code_prefix, page=1)
            if drug_records:
                rprint(f"[green]✓ 成功获取 {len(drug_records)} 条真实药品数据[/]")
                for record in drug_records:
                    standard_record = {
                        'name': record.get('productName', record.get('name', '')),
                        'approval_number': record.get('approvalNumber', record.get('code', '')),
                        'company': record.get('manufacturer', record.get('company', '')),
                        'specification': record.get('specification', record.get('spec', '')),
                        'dosage_form': record.get('dosageForm', record.get('form', '')),
                        'approval_date': record.get('approvalDate', record.get('date', '')),
                        'source': 'real_nmpa_drug_api',
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 如果没有获取到真实数据，抛出异常而不是生成备用数据
        if not all_records:
            rprint("[red]❌ 未能获取到任何真实数据[/]")
            raise RuntimeError("无法获取真实NMPA数据，请检查API端点或签名算法")

        # 保存真实数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.true.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]✅ 真实数据任务完成[/] 共获取 {len(all_records)} 条真实记录，保存至 {raw_file}")

        return all_records

async def create_true_data_crawler(config: Dict[str, Any]) -> TrueDataCrawler:
    """创建真实数据爬虫"""
    crawler = TrueDataCrawler(config)
    await crawler.start()
    return crawler