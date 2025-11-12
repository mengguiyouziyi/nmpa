# -*- coding: utf-8 -*-
"""
增强版NMPA爬虫 - 基于实时网站分析发现的真实session和token数据
利用DrissionPage深度分析结果，实现更精确的反检测技术
"""
import asyncio
import json
import time
import random
import hashlib
import requests
import re
from typing import Dict, List, Any
from rich import print as rprint
from DrissionPage import ChromiumPage, ChromiumOptions

class EnhancedNMPACrawler:
    """增强版NMPA爬虫"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None
        self.session = requests.Session()

        # 基于分析发现的API端点
        self.api_endpoints = {
            'license_list': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'drug_search': 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search'
        }

        # 基于真实分析的浏览器头部
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"'
        }

        # API请求专用头部（基于真实分析）
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
            'Origin': 'http://scxk.nmpa.gov.cn:81',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }

        # 从分析中获得的真实数据
        self.discovered_tokens = {}

    async def start(self):
        """启动增强爬虫"""
        rprint("[bold blue]启动增强版NMPA爬虫（基于实时分析）[/]")

        try:
            # 高级DrissionPage配置
            chromium_options = ChromiumOptions()
            chromium_options.headless(self.config.get('headless', True))
            chromium_options.set_user_agent(self.browser_headers['User-Agent'])

            # 完整的反检测配置
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
            chromium_options.set_argument('--remote-debugging-port=9226')

            if chromium_options.headless:
                chromium_options.set_argument('--headless=new')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ 增强版DrissionPage启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]增强版DrissionPage启动失败: {e}[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass
        if self.session:
            self.session.close()

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[yellow]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def collect_real_tokens(self) -> bool:
        """收集真实的token和session数据"""
        rprint("[cyan]收集真实token和session数据...[/]")

        try:
            # 访问NMPA主站建立初始session
            rprint("[blue]1. 访问NMPA主站[/]")
            self.drission_page.get('https://www.nmpa.gov.cn/')
            self.smart_delay(3, 5)

            # 获取主站token
            try:
                main_storage = self.drission_page.run_js('return Object.assign({}, localStorage);')
                main_session = self.drission_page.run_js('return Object.assign({}, sessionStorage);')

                self.discovered_tokens['main'] = {
                    'local_storage': main_storage,
                    'session_storage': main_session,
                    'cookies': self.drission_page.cookies
                }

                rprint(f"[green]✓ 获取主站tokens: localStorage={len(main_storage)}, sessionStorage={len(main_session)}[/]")
            except Exception as e:
                rprint(f"[yellow]获取主站tokens失败: {e}[/]")

            # 访问数据查询页面
            rprint("[blue]2. 访问数据查询页面[/]")
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.smart_delay(4, 6)

            # 获取数据查询页面token
            try:
                data_storage = self.drission_page.run_js('return Object.assign({}, localStorage);')
                data_session = self.drission_page.run_js('return Object.assign({}, sessionStorage);')

                self.discovered_tokens['data_search'] = {
                    'local_storage': data_storage,
                    'session_storage': data_session,
                    'cookies': self.drission_page.cookies
                }

                rprint(f"[green]✓ 获取数据查询tokens: localStorage={len(data_storage)}, sessionStorage={len(data_session)}[/]")
            except Exception as e:
                rprint(f"[yellow]获取数据查询tokens失败: {e}[/]")

            # 访问生产许可证网站（最关键）
            rprint("[blue]3. 访问生产许可证网站[/]")
            self.drission_page.get('http://scxk.nmpa.gov.cn:81/xk/')
            self.smart_delay(5, 8)

            # 获取许可证网站token
            try:
                license_storage = self.drission_page.run_js('return Object.assign({}, localStorage);')
                license_session = self.drission_page.run_js('return Object.assign({}, sessionStorage);')

                self.discovered_tokens['license'] = {
                    'local_storage': license_storage,
                    'session_storage': license_session,
                    'cookies': self.drission_page.cookies
                }

                rprint(f"[green]✓ 获取许可证网站tokens: localStorage={len(license_storage)}, sessionStorage={len(license_session)}[/]")

                # 提取关键token
                self.extract_critical_tokens(license_storage, license_session)

            except Exception as e:
                rprint(f"[yellow]获取许可证网站tokens失败: {e}[/]")

            # 同步cookies到requests session
            await self.sync_cookies_to_session()

            rprint("[green]✓ 真实token和session数据收集完成[/]")
            return True

        except Exception as e:
            rprint(f"[red]收集token数据失败: {e}[/]")
            return False

    def extract_critical_tokens(self, local_storage: Dict, session_storage: Dict):
        """提取关键token"""
        rprint("[blue]提取关键token...[/]")

        # 从localStorage提取关键数据
        critical_keys = ['_$rc', 'nmpa_session', '$_YWTU', 'aria']
        for key in critical_keys:
            if key in local_storage:
                self.discovered_tokens[f'localStorage_{key}'] = local_storage[key]
                rprint(f"[green]✓ 找到关键token localStorage.{key}[/]")

        # 从sessionStorage提取关键数据
        session_keys = ['$_YWTU', '$_YVTX', 'nmpa_session']
        for key in session_keys:
            if key in session_storage:
                self.discovered_tokens[f'sessionStorage_{key}'] = session_storage[key]
                rprint(f"[green]✓ 找到关键token sessionStorage.{key}[/]")

    async def sync_cookies_to_session(self):
        """同步cookies到requests session"""
        rprint("[blue]同步cookies到HTTP session...[/]")

        try:
            # 同步所有网站的cookies
            for site_name, site_data in self.discovered_tokens.items():
                if 'cookies' in site_data:
                    for cookie in site_data['cookies']:
                        if isinstance(cookie, dict):
                            name = cookie.get('name', '')
                            value = cookie.get('value', '')
                            if name and value:
                                self.session.cookies.set(name, value, domain='.nmpa.gov.cn')
                                rprint(f"[green]✓ 同步cookie: {name}[/]")

        except Exception as e:
            rprint(f"[yellow]Cookie同步失败: {e}[/]")

    def generate_enhanced_signature(self, params: Dict) -> str:
        """基于分析的增强签名算法"""
        # 使用发现的token作为签名密钥的一部分
        base_key = 'nmpasecret2020'

        # 如果发现了关键token，加入签名计算
        if 'localStorage__$rc' in self.discovered_tokens:
            base_key += self.discovered_tokens['localStorage__$rc'][:16]  # 取前16位

        # 参数排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接
        param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        # 添加密钥和发现的token
        sign_string = param_string + base_key

        # 如果有session token，也加入签名
        if 'sessionStorage_$_YWTU' in self.discovered_tokens:
            sign_string += self.discovered_tokens['sessionStorage_$_YWTU']

        # MD5
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def crawl_license_data_enhanced(self, page: int = 1) -> List[Dict]:
        """增强版生产许可证数据爬取"""
        rprint(f"[bold cyan]增强版爬取生产许可证数据[/] 第{page}页")

        # 收集真实token
        if not await self.collect_real_tokens():
            rprint("[red]无法收集真实token数据[/]")
            return []

        url = self.api_endpoints['license_list']

        # 基于真实分析的请求参数
        timestamp = int(time.time() * 1000)
        params = {
            'on': 'true',
            'page': str(page),
            'pageSize': '15',
            'productName': '',
            'conditionType': '1',
            'applyname': '',
            'applysn': '',
            '_': str(timestamp)
        }

        # 使用增强签名算法
        sign = self.generate_enhanced_signature(params)
        params['sign'] = sign

        # 添加发现的token到请求中
        if 'localStorage__$rc' in self.discovered_tokens:
            params['_rc'] = self.discovered_tokens['localStorage__$rc']

        if 'sessionStorage_$_YWTU' in self.discovered_tokens:
            params['_ywtu'] = self.discovered_tokens['sessionStorage_$_YWTU']

        # 高级重试机制
        max_retries = 5
        retry_delays = [5, 12, 25, 45, 90]

        for attempt in range(max_retries):
            try:
                rprint(f"[blue]尝试增强版API请求 (第{attempt+1}次，延迟{retry_delays[attempt]}秒)[/]")

                # 更新cookies
                current_cookies = {}
                try:
                    for cookie in self.drission_page.cookies:
                        if isinstance(cookie, dict):
                            current_cookies[cookie.get('name', '')] = cookie.get('value', '')
                except:
                    pass

                # 添加发现的token作为cookie
                if 'localStorage_nmpa_session' in self.discovered_tokens:
                    current_cookies['nmpa_session'] = self.discovered_tokens['localStorage_nmpa_session']

                # 智能延迟
                if attempt > 0:
                    base_delay = retry_delays[attempt]
                    actual_delay = base_delay + random.uniform(-3, 3)
                    rprint(f"[yellow]等待 {actual_delay:.1f} 秒后重试...[/]")
                    time.sleep(actual_delay)

                # 发送增强请求
                response = self.session.post(
                    url,
                    data=params,
                    headers=self.api_headers,
                    cookies=current_cookies,
                    timeout=45
                )

                rprint(f"[blue]响应状态: {response.status_code}[/]")
                rprint(f"[blue]响应头: {dict(response.headers)}[/]")

                if response.status_code == 200:
                    content = response.text
                    rprint(f"[blue]响应内容长度: {len(content)}[/]")

                    if content and len(content) > 10:
                        try:
                            data = json.loads(content)
                            rprint(f"[blue]解析JSON成功: {list(data.keys())}[/]")

                            if data.get('status') == '200' and data.get('list'):
                                license_list = data['list']
                                rprint(f"[green]🎉🎉🎉 增强版爬取成功！获取 {len(license_list)} 条真实生产许可证数据！[/]")

                                # 显示前几条数据验证
                                for i, item in enumerate(license_list[:3]):
                                    rprint(f"[green]✓ 数据{i+1}: {item.get('productName', 'N/A')} - {item.get('licenseSn', 'N/A')}[/]")

                                return license_list
                            else:
                                rprint(f"[yellow]API返回状态: {data.get('status')}, 消息: {data.get('msg', 'N/A')}[/]")

                                # 分析错误原因
                                msg = data.get('msg', '').lower()
                                if 'precondition' in msg or '412' in msg:
                                    rprint("[yellow]检测到412错误，重新收集tokens...[/]")
                                    await self.collect_real_tokens()
                                elif 'sign' in msg or 'signature' in msg:
                                    rprint("[yellow]检测到签名错误，尝试不同签名算法...[/]")
                                    # 可以在这里尝试不同的签名算法

                        except json.JSONDecodeError as e:
                            rprint(f"[red]JSON解析失败: {e}[/]")
                            rprint(f"[red]原始内容前500字符: {content[:500]}...[/]")
                    else:
                        rprint(f"[yellow]响应内容为空或过短: {content[:100] if content else 'None'}[/]")
                elif response.status_code == 502:
                    rprint("[yellow]502错误 - 服务器暂时不可用，等待重试...[/]")
                    continue
                elif response.status_code == 412:
                    rprint("[yellow]412错误 - 请求头验证失败，重新收集tokens...[/]")
                    await self.collect_real_tokens()
                    continue
                else:
                    rprint(f"[red]HTTP错误: {response.status_code}[/]")
                    rprint(f"[red]响应头: {dict(response.headers)}[/]")
                    if response.status_code == 403:
                        rprint("[red]403错误 - 可能需要验证码或IP被封禁[/]")
                        break

            except Exception as e:
                rprint(f"[red]请求异常 (第{attempt+1}次): {e}[/]")
                continue

        rprint("[red]增强版生产许可证数据爬取失败[/]")
        return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行增强版任务"""
        rprint(f"[bold green]开始增强版任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 专注于生产许可证数据
        if dataset in ['license', 'domestic']:
            license_records = await self.crawl_license_data_enhanced(page=1)
            if license_records:
                rprint(f"[green]✅ 增强版爬取成功！获取 {len(license_records)} 条真实生产许可证数据！[/]")
                for record in license_records:
                    standard_record = {
                        'name': record.get('productName', record.get('产品名称', '')),
                        'approval_number': record.get('licenseSn', record.get('许可证号', '')),
                        'company': record.get('companyName', record.get('企业名称', '')),
                        'specification': record.get('productSpec', record.get('规格', '')),
                        'dosage_form': record.get('productForm', record.get('剂型', '')),
                        'approval_date': record.get('validDate', record.get('有效期至', '')),
                        'source': 'enhanced_license_api',
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'breakthrough_method': 'enhanced_drissionpage_tokens',
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 如果没有获取到真实数据，抛出异常
        if not all_records:
            rprint("[red]❌ 增强版爬取失败，未能获取到任何真实数据[/]")
            raise RuntimeError("增强版爬取失败，未能获取真实NMPA数据")

        # 保存增强版数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.enhanced.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 增强版爬取成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_enhanced_crawler(config: Dict[str, Any]) -> EnhancedNMPACrawler:
    """创建增强版爬虫"""
    crawler = EnhancedNMPACrawler(config)
    await crawler.start()
    return crawler