# -*- coding: utf-8 -*-
"""
终极真实数据NMPA爬虫 - 绝不使用备用数据，只获取真实数据
基于已验证的技术栈，实现多种突破策略
"""
import asyncio
import json
import time
import random
import hashlib
import requests
from typing import Dict, List, Any
from rich import print as rprint
from DrissionPage import ChromiumPage, ChromiumOptions

class UltimateTrueCrawler:
    """终极真实数据爬虫 - 只获取真实数据"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None
        self.session = requests.Session()

        # 基于GitHub验证的API端点
        self.api_endpoints = {
            # 生产许可证 - QueenOfBugs项目验证成功
            'license_list': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'license_detail': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkkzsById',

            # 新发现的API端点
            'license_search': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'license_alt': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do',

            # 药品数据库
            'drug_search': 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search',
            'drug_alt': 'https://search.nmpa.gov.cn/api/search',

            # 其他可能的端点
            'backup_1': 'http://www.nmpa.gov.cn/datasearch/data/nmpadata/search',
            'backup_2': 'https://app1.nmpa.gov.cn/data/search'
        }

        # 基于验证的签名算法
        self.secret_keys = [
            'nmpasecret2020',    # magical_spider项目验证
            'datasearch2024',    # 备用密钥1
            'china_nmpa_key',    # 备用密钥2
            'nmpa_key_2024',     # 备用密钥3
            'cfda_2024_key'      # 备用密钥4
        ]

        # 高级请求头配置
        self.headers_v1 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        self.headers_v2 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
            'Origin': 'http://scxk.nmpa.gov.cn:81'
        }

    async def start(self):
        """启动爬虫"""
        rprint("[bold blue]启动终极真实数据NMPA爬虫（绝对只获取真实数据）[/]")

        try:
            chromium_options = ChromiumOptions()
            chromium_options.headless(self.config.get('headless', True))
            chromium_options.set_user_agent(self.headers_v1['User-Agent'])

            # 高级反检测配置
            chromium_options.set_argument('--disable-blink-features=AutomationControlled')
            chromium_options.set_argument('--disable-dev-shm-usage')
            chromium_options.set_argument('--no-sandbox')
            chromium_options.set_argument('--disable-web-security')
            chromium_options.set_argument('--allow-running-insecure-content')
            chromium_options.set_argument('--disable-features=VizDisplayCompositor')
            chromium_options.set_argument('--disable-extensions')
            chromium_options.set_argument('--disable-plugins')
            chromium_options.set_argument('--disable-background-timer-throttling')
            chromium_options.set_argument('--disable-backgrounding-occluded-windows')
            chromium_options.set_argument('--disable-renderer-backgrounding')
            chromium_options.set_argument('--disable-field-trial-config')
            chromium_options.set_argument('--disable-back-forward-cache')
            chromium_options.set_argument('--disable-component-extensions-with-background-pages')
            chromium_options.set_argument('--disable-background-networking')
            chromium_options.set_argument('--disable-default-apps')
            chromium_options.set_argument('--disable-extensions-file-access-check')
            chromium_options.set_argument('--disable-ipc-flooding-protection')
            chromium_options.set_argument('--disable-client-side-phishing-detection')
            chromium_options.set_argument('--disable-sync')
            chromium_options.set_argument('--disable-default-browser-check')
            chromium_options.set_argument('--metrics-recording-only')
            chromium_options.set_argument('--no-first-run')
            chromium_options.set_argument('--no-default-browser-check')
            chromium_options.set_argument('--disable-logging')
            chromium_options.set_argument('--disable-gpu')
            chromium_options.set_argument('--window-size=1920,1080')
            chromium_options.set_argument('--start-maximized')

            if chromium_options.headless:
                chromium_options.set_argument('--headless=new')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ DrissionPage高级初始化成功[/]")

        except Exception as e:
            rprint(f"[red]DrissionPage初始化失败: {e}[/]")
            raise

    async def stop(self):
        """停止爬虫"""
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass
        if self.session:
            self.session.close()

    def smart_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """智能延迟"""
        delay = min_seconds + random.uniform(0, max_seconds - min_seconds)
        rprint(f"[yellow]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    def generate_signature(self, params: Dict, secret_key: str) -> str:
        """多种签名算法"""
        # 算法1：参数排序 + 密钥
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        sign_string = param_string + secret_key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def generate_signature_v2(self, params: Dict, secret_key: str) -> str:
        """算法2：URL编码格式"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_string = param_string + '&' + secret_key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    def generate_signature_v3(self, params: Dict, secret_key: str) -> str:
        """算法3：时间戳优先"""
        timestamp = params.get('timestamp', int(time.time() * 1000))
        sign_string = f"timestamp={timestamp}"
        for k, v in sorted(params.items()):
            if k != 'timestamp':
                sign_string += f"&{k}={v}"
        sign_string += secret_key
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def build_advanced_session(self, url: str) -> Dict:
        """建立高级会话"""
        rprint(f"[cyan]为 {url} 建立高级会话...[/]")

        try:
            # 访问页面
            self.drission_page.get(url)
            self.smart_delay(3, 5)

            # 模拟真实用户行为
            rprint("[blue]模拟用户浏览行为...[/]")
            self.drission_page.run_js('window.scrollTo(0, document.body.scrollHeight/3)')
            self.smart_delay(2, 3)
            self.drission_page.run_js('window.scrollTo(0, 0)')
            self.smart_delay(1, 2)

            # 获取cookies
            cookies = {}
            try:
                for cookie in self.drission_page.cookies:
                    cookies[cookie['name']] = cookie['value']
            except:
                pass

            # 获取页面内容分析
            page_content = self.drission_page.html
            has_forms = 'form' in page_content.lower()
            has_search = 'search' in page_content.lower()

            rprint(f"[green]✓ 会话建立成功 - Cookies: {len(cookies)}, Forms: {has_forms}, Search: {has_search}[/]")
            return {'cookies': cookies, 'has_forms': has_forms, 'has_search': has_search}

        except Exception as e:
            rprint(f"[red]会话建立失败: {e}[/]")
            return {'cookies': {}, 'has_forms': False, 'has_search': False}

    async def try_license_api_multiple_ways(self) -> List[Dict]:
        """多种方式尝试许可证API"""
        rprint("[bold cyan]多策略尝试生产许可证API...[/]")

        # 策略1：主API - POST请求
        results = await self.try_main_license_api()
        if results:
            return results

        # 策略2：备用API端点
        results = await self.try_alternative_license_apis()
        if results:
            return results

        # 策略3：GET请求方式
        results = await self.try_license_get_requests()
        if results:
            return results

        # 策略4：页面解析方式
        results = await self.try_page_scraping()
        if results:
            return results

        rprint("[red]所有许可证API策略都失败了[/]")
        return []

    async def try_main_license_api(self) -> List[Dict]:
        """主API策略"""
        rprint("[blue]策略1: 主API POST请求[/]")

        # 建立会话
        session_info = await self.build_advanced_session('http://scxk.nmpa.gov.cn:81/xk/')

        # 主API端点
        url = 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList'

        # 尝试多种参数组合
        param_variations = [
            # 标准参数
            {
                'on': 'true',
                'page': '1',
                'pageSize': '15',
                'productName': '',
                'conditionType': '1',
                'applyname': '',
                'applysn': ''
            },
            # 无过滤参数
            {
                'page': '1',
                'pageSize': '10'
            },
            # 简化参数
            {
                'page': '1'
            }
        ]

        for params_base in param_variations:
            timestamp = int(time.time() * 1000)
            params = params_base.copy()
            params['_'] = str(timestamp)

            # 尝试多种密钥和算法组合
            for secret_key in self.secret_keys:
                for sign_func in [self.generate_signature, self.generate_signature_v2, self.generate_signature_v3]:
                    try:
                        test_params = params.copy()
                        sign = sign_func(test_params, secret_key)
                        test_params['sign'] = sign

                        # 发送请求
                        response = self.session.post(
                            url,
                            data=test_params,
                            headers=self.headers_v2,
                            cookies=session_info['cookies'],
                            timeout=30
                        )

                        if response.status_code == 200:
                            content = response.text
                            if content and len(content) > 10:
                                try:
                                    data = json.loads(content)
                                    if data.get('status') == '200' and data.get('list'):
                                        license_list = data['list']
                                        rprint(f"[green]🎉 主API成功！获取 {len(license_list)} 条真实数据！[/]")
                                        rprint(f"[green]✓ 签名算法: {sign_func.__name__}, 密钥: {secret_key}[/]")
                                        return license_list
                                    else:
                                        rprint(f"[yellow]API响应: {data.get('status')}, 消息: {data.get('msg', 'N/A')}[/]")
                                except json.JSONDecodeError:
                                    rprint(f"[yellow]非JSON响应: {content[:100]}...[/]")
                        else:
                            rprint(f"[yellow]HTTP {response.status_code}[/]")

                    except Exception as e:
                        rprint(f"[yellow]参数组合失败: {e}[/]")
                        continue

        return []

    async def try_alternative_license_apis(self) -> List[Dict]:
        """备用API策略"""
        rprint("[blue]策略2: 备用API端点[/]")

        # 备用端点列表
        alternative_endpoints = [
            'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do',
            'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList&on=true&page=1&pageSize=10'
        ]

        for url in alternative_endpoints:
            rprint(f"[blue]尝试备用端点: {url}[/]")

            # 建立会话
            session_info = await self.build_advanced_session('http://scxk.nmpa.gov.cn:81/xk/')

            # 尝试不同请求方式
            for method in ['POST', 'GET']:
                try:
                    if method == 'POST':
                        response = self.session.post(
                            url,
                            data={'page': '1', 'pageSize': '10'},
                            headers=self.headers_v2,
                            cookies=session_info['cookies'],
                            timeout=30
                        )
                    else:
                        response = self.session.get(
                            url,
                            headers=self.headers_v1,
                            cookies=session_info['cookies'],
                            timeout=30
                        )

                    if response.status_code == 200:
                        content = response.text
                        if content and len(content) > 10:
                            try:
                                data = json.loads(content)
                                if data.get('list') or data.get('data'):
                                    list_data = data.get('list', data.get('data', []))
                                    if isinstance(list_data, list) and len(list_data) > 0:
                                        rprint(f"[green]🎉 备用端点成功！获取 {len(list_data)} 条数据！[/]")
                                        return list_data
                            except json.JSONDecodeError:
                                rprint(f"[yellow]响应格式: {content[:100]}...[/]")
                    else:
                        rprint(f"[yellow]HTTP {response.status_code}[/]")

                except Exception as e:
                    rprint(f"[yellow]请求失败: {e}[/]")

        return []

    async def try_license_get_requests(self) -> List[Dict]:
        """GET请求策略"""
        rprint("[blue]策略3: GET请求方式[/]")

        # GET参数端点
        get_endpoints = [
            'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList&on=true&page=1&pageSize=10',
            'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?page=1&pageSize=20'
        ]

        for url in get_endpoints:
            rprint(f"[blue]尝试GET端点: {url}[/]")

            # 建立会话
            session_info = await self.build_advanced_session('http://scxk.nmpa.gov.cn:81/xk/')

            try:
                response = self.session.get(
                    url,
                    headers=self.headers_v1,
                    cookies=session_info['cookies'],
                    timeout=30
                )

                if response.status_code == 200:
                    content = response.text
                    if content and len(content) > 10:
                        try:
                            data = json.loads(content)
                            if data.get('list') or data.get('data'):
                                list_data = data.get('list', data.get('data', []))
                                if isinstance(list_data, list) and len(list_data) > 0:
                                    rprint(f"[green]🎉 GET请求成功！获取 {len(list_data)} 条数据！[/]")
                                    return list_data
                        except json.JSONDecodeError:
                            rprint(f"[yellow]响应内容: {content[:100]}...[/]")
                else:
                    rprint(f"[yellow]HTTP {response.status_code}[/]")

            except Exception as e:
                rprint(f"[yellow]GET请求失败: {e}[/]")

        return []

    async def try_page_scraping(self) -> List[Dict]:
        """页面解析策略"""
        rprint("[blue]策略4: 页面解析提取数据[/]")

        try:
            # 访问生产许可证页面
            session_info = await self.build_advanced_session('http://scxk.nmpa.gov.cn:81/xk/')

            # 等待页面完全加载
            self.smart_delay(5, 8)

            # 查找表格数据
            tables = self.drission_page.eles('table')
            if tables:
                for table in tables:
                    rows = table.eles('tr')
                    if len(rows) > 1:  # 有数据行
                        data_list = []
                        headers = []

                        # 提取表头
                        header_cells = rows[0].eles('th, td')
                        for cell in header_cells:
                            headers.append(cell.text.strip())

                        # 提取数据行
                        for row in rows[1:]:  # 跳过表头
                            cells = row.eles('td')
                            if len(cells) >= len(headers):
                                record = {}
                                for i, cell in enumerate(cells[:len(headers)]):
                                    record[headers[i] if i < len(headers) else f'column_{i}'] = cell.text.strip()
                                data_list.append(record)

                        if data_list:
                            rprint(f"[green]🎉 页面解析成功！提取 {len(data_list)} 条数据！[/]")
                            return data_list

            # 查找列表数据
            list_items = self.drission_page.eles('.list-item, .result-item, .data-item, .search-result')
            if list_items:
                data_list = []
                for item in list_items[:10]:  # 取前10个
                    try:
                        # 尝试提取文本内容
                        content = item.text.strip()
                        if content:
                            # 简单的数据结构
                            record = {
                                'content': content,
                                'html': item.html
                            }
                            data_list.append(record)
                    except:
                        continue

                if data_list:
                    rprint(f"[green]🎉 列表解析成功！提取 {len(data_list)} 条数据！[/]")
                    return data_list

        except Exception as e:
            rprint(f"[red]页面解析失败: {e}[/]")

        return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行真实数据爬取任务"""
        rprint(f"[bold green]开始真实数据爬取任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 专注于生产许可证数据
        if dataset in ['license', 'domestic']:
            rprint(f"[cyan]开始爬取生产许可证真实数据...[/]")

            license_records = await self.try_license_api_multiple_ways()
            if license_records:
                rprint(f"[green]✅ 成功获取 {len(license_records)} 条真实生产许可证数据！[/]")

                # 转换为标准格式
                for record in license_records:
                    # 处理不同的数据格式
                    if isinstance(record, dict):
                        standard_record = {
                            'name': record.get('productName', record.get('产品名称', record.get('content', ''))),
                            'approval_number': record.get('licenseSn', record.get('许可证号', record.get('编号', ''))),
                            'company': record.get('companyName', record.get('企业名称', record.get('公司', ''))),
                            'specification': record.get('productSpec', record.get('规格', '')),
                            'dosage_form': record.get('productForm', record.get('剂型', '')),
                            'approval_date': record.get('validDate', record.get('有效期至', record.get('批准日期', ''))),
                            'source': 'ultimate_true_crawler',
                            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'method': 'breakthrough',
                            'raw_data': record
                        }
                        all_records.append(standard_record)

        # 如果没有获取到真实数据，抛出异常
        if not all_records:
            rprint("[red]❌ 未能获取到任何真实数据，拒绝生成备用数据[/]")
            raise RuntimeError("未能获取真实NMPA数据，所有策略都失败了")

        # 保存真实数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.ultimate.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 真实数据任务完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_ultimate_true_crawler(config: Dict[str, Any]) -> UltimateTrueCrawler:
    """创建终极真实数据爬虫"""
    crawler = UltimateTrueCrawler(config)
    await crawler.start()
    return crawler