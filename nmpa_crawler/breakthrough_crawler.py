# -*- coding: utf-8 -*-
"""
突破性NMPA爬虫 - 基于成功项目的核心突破技术
整合nimua/NMPA_spider、QueenOfBugs/scxk.nmpa、magical_spider的成功经验
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

class BreakthroughCrawler:
    """突破性NMPA爬虫 - 基于GitHub成功项目"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None
        self.session = requests.Session()

        # 基于成功项目的API端点
        self.api_endpoints = {
            # 生产许可证 - QueenOfBugs/scxk.nmpa项目成功端点
            'license_list': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'license_detail': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsById'
        }

        # 基于magical_spider的签名密钥
        self.secret_key = 'nmpasecret2020'

        # nimua/NMPA_spider项目的成功配置
        self.success_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    async def start(self):
        """启动爬虫 - 使用DrissionPage"""
        rprint("[bold blue]启动突破性NMPA爬虫（基于GitHub成功项目）[/]")

        try:
            # nimua/NMPA_spider项目的DrissionPage配置
            chromium_options = ChromiumOptions()
            chromium_options.headless(self.config.get('headless', True))
            chromium_options.set_user_agent(self.success_headers['User-Agent'])

            # 关键的反检测配置
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

            # 设置浏览器窗口大小
            chromium_options.set_argument('--window-size=1920,1080')

            # 修复Linux系统连接问题
            if chromium_options.headless:
                chromium_options.set_argument('--headless=new')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ DrissionPage初始化成功（nimua项目配置）[/]")

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

    def human_like_delay(self, min_seconds: float = 3.0, max_seconds: float = 10.0):
        """人类行为延迟 - nimua项目的10秒策略"""
        delay = random.uniform(min_seconds, max_seconds)
        rprint(f"[yellow]人类行为延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    def generate_signature(self, params: Dict) -> str:
        """magical_spider项目的签名算法"""
        # 参数排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接
        param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        # 添加密钥
        sign_string = param_string + self.secret_key
        # MD5
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def access_nmpa_homepage(self):
        """访问NMPA首页 - 建立正常会话"""
        rprint("[cyan]访问NMPA首页，建立正常会话[/]")

        try:
            # 访问NMPA首页
            self.drission_page.get('https://www.nmpa.gov.cn/')
            self.human_like_delay(5, 8)

            # 访问数据查询页面
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.human_like_delay(3, 5)

            rprint("[green]✓ 成功建立NMPA会话[/]")
            return True
        except Exception as e:
            rprint(f"[red]建立会话失败: {e}[/]")
            return False

    async def crawl_license_data_breakthrough(self, page: int = 1) -> List[Dict]:
        """
        突破性爬取生产许可证数据
        基于QueenOfBugs/scxk.nmpa项目的成功实现
        """
        rprint(f"[bold cyan]突破性爬取生产许可证数据[/] 第{page}页")

        # 首先建立正常会话
        if not await self.access_nmpa_homepage():
            rprint("[red]无法建立正常会话，跳过许可证数据爬取[/]")
            return []

        # 访问生产许可证查询页面
        try:
            self.drission_page.get('http://scxk.nmpa.gov.cn:81/xk/')
            self.human_like_delay(5, 8)
        except Exception as e:
            rprint(f"[yellow]访问许可证页面失败: {e}[/]")

        url = self.api_endpoints['license_list']

        # QueenOfBugs/scxk.nmpa项目的请求参数
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

        # 生成签名
        sign = self.generate_signature(params)
        params['sign'] = sign

        # 设置请求头 - 模拟真实浏览器
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
            'Origin': 'http://scxk.nmpa.gov.cn:81'
        }

        try:
            rprint(f"[blue]发送请求到: {url}[/]")
            rprint(f"[blue]参数: {params}[/]")

            # 获取DrissionPage的Cookie用于requests
            cookies = {}
            if self.drission_page:
                try:
                    # 从DrissionPage获取cookies
                    for cookie in self.drission_page.cookies:
                        cookies[cookie['name']] = cookie['value']
                except:
                    pass

            # 关键：使用requests发送POST请求，结合DrissionPage的会话
            response = self.session.post(url, data=params, headers=headers, cookies=cookies, timeout=60)

            rprint(f"[blue]响应状态: {response.status_code}[/]")

            if response.status_code == 200:
                content = response.text
                rprint(f"[blue]响应内容长度: {len(content)}[/]")

                if content and len(content) > 10:
                    try:
                        data = json.loads(content)
                        rprint(f"[blue]解析JSON成功: {list(data.keys())}[/]")

                        if data.get('status') == '200' and data.get('list'):
                            license_list = data['list']
                            rprint(f"[green]🎉 突破成功！获取 {len(license_list)} 条真实生产许可证数据！[/]")

                            # 显示第一条数据作为验证
                            if license_list:
                                first_item = license_list[0]
                                rprint(f"[green]✓ 示例数据: {first_item.get('productName', 'N/A')} - {first_item.get('licenseSn', 'N/A')}[/]")

                            return license_list
                        else:
                            rprint(f"[yellow]API返回状态: {data.get('status')}, 消息: {data.get('msg', 'N/A')}[/]")

                    except json.JSONDecodeError as e:
                        rprint(f"[red]JSON解析失败: {e}[/]")
                        rprint(f"[red]原始内容: {content[:200]}...[/]")
                else:
                    rprint(f"[yellow]响应内容为空或过短[/]")
            else:
                rprint(f"[red]HTTP错误: {response.status_code}[/]")

        except Exception as e:
            rprint(f"[red]请求异常: {e}[/]")

        rprint("[red]生产许可证数据爬取失败[/]")
        return []

    async def crawl_drug_data_breakthrough(self, keyword: str) -> List[Dict]:
        """
        突破性爬取药品数据
        基于多个成功项目的综合策略
        """
        rprint(f"[bold cyan]突破性爬取药品数据[/] 关键词: {keyword}")

        # 访问药品查询页面
        try:
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.human_like_delay(3, 5)

            # 模拟搜索操作
            search_input = self.drission_page.ele('input[placeholder*="请输入"], input[type="search"]', timeout=5)
            if search_input:
                search_input.input(keyword)
                self.human_like_delay(1, 2)

                search_btn = self.drission_page.ele('button:contains("搜索"), .search-btn', timeout=5)
                if search_btn:
                    search_btn.click()
                    self.human_like_delay(5, 8)

        except Exception as e:
            rprint(f"[yellow]页面操作失败: {e}[/]")

        # 尝试直接API调用
        url = 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search'

        # 基于我们之前的分析
        item_ids = {
            'domestic': 'ff80808183cad75001840881f848179f',
            'imported': 'ff80808183cad75001840881f84817a0'
        }

        if keyword.startswith('国药准字H'):
            item_id = item_ids['domestic']
        elif keyword.startswith('国药准字S'):
            item_id = item_ids['domestic']
        elif keyword.startswith('国药准字J'):
            item_id = item_ids['imported']
        else:
            item_id = item_ids['domestic']

        timestamp = int(time.time() * 1000)
        params = {
            'itemId': item_id,
            'searchValue': keyword,
            'pageNum': 1,
            'pageSize': 10,
            'isSenior': 'N',
            'timestamp': timestamp
        }

        # 尝试多种签名方式
        for attempt in range(3):
            try:
                # 生成签名
                sign_params = params.copy()
                sign = self.generate_signature(sign_params)
                params['sign'] = sign

                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json',
                    'Referer': 'https://www.nmpa.gov.cn/datasearch/home?htmlType=1',
                    'Origin': 'https://www.nmpa.gov.cn'
                }

                rprint(f"[blue]尝试药品API请求 (第{attempt+1}次)[/]")

                # 获取DrissionPage的Cookie
                cookies = {}
                if self.drission_page:
                    try:
                        for cookie in self.drission_page.cookies:
                            cookies[cookie['name']] = cookie['value']
                    except:
                        pass

                response = self.session.post(url, json=params, headers=headers, cookies=cookies, timeout=60)

                if response.status_code == 200:
                    content = response.text
                    if content:
                        try:
                            data = json.loads(content)
                            if data.get('code') == 200 and data.get('data'):
                                drug_list = data['data'].get('list', [])
                                if drug_list:
                                    rprint(f"[green]🎉 药品数据突破成功！获取 {len(drug_list)} 条真实药品数据！[/]")

                                    # 显示第一条数据
                                    if drug_list:
                                        first_item = drug_list[0]
                                        rprint(f"[green]✓ 示例药品: {first_item.get('productName', 'N/A')} - {first_item.get('approvalNumber', 'N/A')}[/]")

                                    return drug_list
                                else:
                                    rprint(f"[yellow]药品数据为空: {data}[/]")
                            else:
                                rprint(f"[yellow]药品API响应: {data}[/]")
                        except json.JSONDecodeError:
                            rprint(f"[yellow]药品API响应非JSON格式[/]")
                else:
                    rprint(f"[yellow]药品API HTTP {response.status_code}[/]")

                # 如果失败，等待更长时间
                if attempt < 2:
                    self.human_like_delay(8, 15)

            except Exception as e:
                rprint(f"[yellow]药品API请求异常 (第{attempt+1}次): {e}[/]")
                if attempt < 2:
                    self.human_like_delay(5, 10)

        rprint("[red]药品数据爬取失败[/]")
        return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行突破性爬取任务"""
        rprint(f"[bold green]开始突破性数据爬取任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 策略1：生产许可证数据（成功率最高）
        if dataset in ['license', 'domestic']:
            license_records = await self.crawl_license_data_breakthrough(page=1)
            if license_records:
                rprint(f"[green]✓ 成功突破生产许可证API，获取 {len(license_records)} 条真实数据[/]")
                for record in license_records:
                    standard_record = {
                        'name': record.get('productName', record.get('产品名称', '')),
                        'approval_number': record.get('licenseSn', record.get('许可证号', '')),
                        'company': record.get('companyName', record.get('企业名称', '')),
                        'specification': record.get('productSpec', record.get('规格', '')),
                        'dosage_form': record.get('productForm', record.get('剂型', '')),
                        'approval_date': record.get('validDate', record.get('有效期至', '')),
                        'source': 'breakthrough_license_api',
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 策略2：药品数据
        if dataset in ['domestic', 'imported']:
            drug_records = await self.crawl_drug_data_breakthrough(code_prefix)
            if drug_records:
                rprint(f"[green]✓ 成功突破药品API，获取 {len(drug_records)} 条真实数据[/]")
                for record in drug_records:
                    standard_record = {
                        'name': record.get('productName', record.get('name', '')),
                        'approval_number': record.get('approvalNumber', record.get('code', '')),
                        'company': record.get('manufacturer', record.get('company', '')),
                        'specification': record.get('specification', record.get('spec', '')),
                        'dosage_form': record.get('dosageForm', record.get('form', '')),
                        'approval_date': record.get('approvalDate', record.get('date', '')),
                        'source': 'breakthrough_drug_api',
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 如果没有获取到真实数据，抛出异常
        if not all_records:
            rprint("[red]❌ 突破失败，未能获取到任何真实数据[/]")
            raise RuntimeError("无法突破NMPA反爬虫机制，未能获取真实数据")

        # 保存突破性数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.breakthrough.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉 突破性任务完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_breakthrough_crawler(config: Dict[str, Any]) -> BreakthroughCrawler:
    """创建突破性爬虫"""
    crawler = BreakthroughCrawler(config)
    await crawler.start()
    return crawler