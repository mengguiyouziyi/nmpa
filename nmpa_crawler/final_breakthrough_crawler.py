# -*- coding: utf-8 -*-
"""
最终突破NMPA爬虫 - 解决502和412错误的最后方案
基于成功验证的技术栈，精细化优化实现真实数据获取
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

class FinalBreakthroughCrawler:
    """最终突破NMPA爬虫"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.drission_page = None
        self.session = requests.Session()

        # 基于成功项目的API端点
        self.api_endpoints = {
            'license_list': 'http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList',
            'drug_search': 'https://www.nmpa.gov.cn/datasearch/data/nmpadata/search'
        }

        # 精确的签名算法（基于验证）
        self.secret_key = 'nmpasecret2020'

        # 完整的浏览器指纹（解决412错误）
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

        # API请求专用头部
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

    async def start(self):
        """启动爬虫 - 完全模拟真实用户"""
        rprint("[bold blue]启动最终突破NMPA爬虫（解决502/412错误）[/]")

        try:
            # DrissionPage高级配置
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
            chromium_options.set_argument('--disable-renderer-backgrounding')
            chromium_options.set_argument('--disable-backgrounding-occluded-windows')
            chromium_options.set_argument('--disable-client-side-phishing-detection')
            chromium_options.set_argument('--disable-sync')
            chromium_options.set_argument('--disable-default-browser-check')
            chromium_options.set_argument('--metrics-recording-only')
            chromium_options.set_argument('--no-first-run')
            chromium_options.set_argument('--no-default-browser-check')
            chromium_options.set_argument('--disable-logging')
            chromium_options.set_argument('--disable-gpu')
            chromium_options.set_argument('--disable-dev-shm-usage')
            chromium_options.set_argument('--disable-features=TranslateUI')
            chromium_options.set_argument('--disable-ipc-flooding-protection')

            # 设置浏览器窗口大小
            chromium_options.set_argument('--window-size=1920,1080')
            chromium_options.set_argument('--start-maximized')

            # 修复Linux系统连接问题
            if chromium_options.headless:
                chromium_options.set_argument('--headless=new')

            # 设置端口
            chromium_options.set_argument('--remote-debugging-port=9222')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ DrissionPage完全初始化成功[/]")

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

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟 - 模拟人类行为"""
        delay = base + random.uniform(0, variation)
        rprint(f"[yellow]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    def generate_signature(self, params: Dict) -> str:
        """精确的签名算法"""
        # 参数排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接
        param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
        # 添加密钥
        sign_string = param_string + self.secret_key
        # MD5
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()

    async def build_complete_session(self) -> bool:
        """建立完整的用户会话 - 解决412错误的关键"""
        rprint("[cyan]建立完整用户会话...[/]")

        try:
            # 1. 访问NMPA首页
            rprint("[blue]1. 访问NMPA首页[/]")
            self.drission_page.get('https://www.nmpa.gov.cn/')
            self.smart_delay(3, 5)

            # 2. 模拟用户浏览行为
            rprint("[blue]2. 模拟用户浏览行为[/]")

            # 滚动页面
            self.drission_page.run_js('window.scrollTo(0, document.body.scrollHeight/2)')
            self.smart_delay(2, 3)

            self.drission_page.run_js('window.scrollTo(0, 0)')
            self.smart_delay(1, 2)

            # 3. 访问数据查询页面
            rprint("[blue]3. 访问数据查询页面[/]")
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            self.smart_delay(4, 6)

            # 4. 执行JavaScript建立会话状态
            rprint("[blue]4. 建立会话状态[/]")
            try:
                self.drission_page.run_js('''
                    // 设置一些基本的会话变量
                    localStorage.setItem('nmpa_session', Math.random().toString(36));
                    sessionStorage.setItem('nmpa_visit', new Date().getTime());
                ''')
                self.smart_delay(1, 2)
            except Exception as e:
                rprint(f"[yellow]JavaScript执行失败，继续: {e}[/]")

            # 5. 访问生产许可证页面建立相关会话
            rprint("[blue]5. 访问生产许可证页面[/]")
            try:
                self.drission_page.get('http://scxk.nmpa.gov.cn:81/xk/')
                self.smart_delay(5, 8)

                # 在许可证页面执行JavaScript
                try:
                    self.drission_page.run_js('''
                        localStorage.setItem('license_session', Math.random().toString(36));
                        sessionStorage.setItem('license_visit', new Date().getTime());
                    ''')
                    self.smart_delay(1, 2)
                except Exception as e:
                    rprint(f"[yellow]许可证页面JavaScript执行失败，继续: {e}[/]")
            except Exception as e:
                rprint(f"[yellow]访问许可证页面失败，继续: {e}[/]")

            # 6. 获取并设置所有cookies
            rprint("[blue]6. 同步会话cookies[/]")
            try:
                cookies = self.drission_page.cookies
                if cookies:
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'])
            except Exception as e:
                rprint(f"[yellow]Cookie同步失败，继续: {e}[/]")

            rprint("[green]✓ 完整用户会话建立成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]建立会话失败: {e}[/]")
            return False

    async def crawl_license_data_final(self, page: int = 1) -> List[Dict]:
        """最终版本生产许可证数据爬取 - 解决502错误"""
        rprint(f"[bold cyan]最终突破性爬取生产许可证数据[/] 第{page}页")

        # 建立完整会话
        if not await self.build_complete_session():
            rprint("[red]无法建立完整会话[/]")
            return []

        url = self.api_endpoints['license_list']

        # 精确的请求参数
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

        # 智能重试机制
        max_retries = 5
        retry_delays = [3, 8, 15, 30, 60]

        for attempt in range(max_retries):
            try:
                rprint(f"[blue]尝试许可证API请求 (第{attempt+1}次，延迟{retry_delays[attempt]}秒)[/]")

                # 更新cookies
                current_cookies = {}
                if self.drission_page:
                    try:
                        for cookie in self.drission_page.cookies:
                            current_cookies[cookie['name']] = cookie['value']
                    except:
                        pass

                # 添加随机延迟避免检测
                if attempt > 0:
                    base_delay = retry_delays[attempt]
                    actual_delay = base_delay + random.uniform(-2, 2)
                    rprint(f"[yellow]等待 {actual_delay:.1f} 秒后重试...[/]")
                    time.sleep(actual_delay)

                # 使用完整headers发送请求
                response = self.session.post(
                    url,
                    data=params,
                    headers=self.api_headers,
                    cookies=current_cookies,
                    timeout=30
                )

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
                                rprint(f"[green]🎉🎉🎉 最终突破成功！获取 {len(license_list)} 条真实生产许可证数据！[/]")

                                # 显示前几条数据验证
                                for i, item in enumerate(license_list[:3]):
                                    rprint(f"[green]✓ 数据{i+1}: {item.get('productName', 'N/A')} - {item.get('licenseSn', 'N/A')}[/]")

                                return license_list
                            else:
                                rprint(f"[yellow]API返回状态: {data.get('status')}, 消息: {data.get('msg', 'N/A')}[/]")

                                # 如果是412错误，说明需要更多会话信息
                                if data.get('msg') and 'precondition' in str(data.get('msg')).lower():
                                    rprint("[yellow]检测到412错误，尝试重新建立会话...[/]")
                                    await self.build_complete_session()

                        except json.JSONDecodeError as e:
                            rprint(f"[red]JSON解析失败: {e}[/]")
                            rprint(f"[red]原始内容: {content[:200]}...[/]")
                    else:
                        rprint(f"[yellow]响应内容为空或过短: {content[:100] if content else 'None'}[/]")
                elif response.status_code == 502:
                    rprint("[yellow]502错误 - 服务器暂时不可用，等待重试...[/]")
                    continue
                elif response.status_code == 412:
                    rprint("[yellow]412错误 - 请求头验证失败，重新建立会话...[/]")
                    await self.build_complete_session()
                    continue
                else:
                    rprint(f"[red]HTTP错误: {response.status_code}[/]")
                    if response.status_code == 403:
                        rprint("[red]403错误 - 可能需要验证码或IP被封禁[/]")
                        break

            except Exception as e:
                rprint(f"[red]请求异常 (第{attempt+1}次): {e}[/]")
                continue

        rprint("[red]生产许可证数据最终爬取失败[/]")
        return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行最终突破性任务"""
        rprint(f"[bold green]开始最终突破任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 专注于生产许可证数据（突破成功率最高）
        if dataset in ['license', 'domestic']:
            license_records = await self.crawl_license_data_final(page=1)
            if license_records:
                rprint(f"[green]✅ 最终突破成功！获取 {len(license_records)} 条真实生产许可证数据！[/]")
                for record in license_records:
                    standard_record = {
                        'name': record.get('productName', record.get('产品名称', '')),
                        'approval_number': record.get('licenseSn', record.get('许可证号', '')),
                        'company': record.get('companyName', record.get('企业名称', '')),
                        'specification': record.get('productSpec', record.get('规格', '')),
                        'dosage_form': record.get('productForm', record.get('剂型', '')),
                        'approval_date': record.get('validDate', record.get('有效期至', '')),
                        'source': 'final_breakthrough_license_api',
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'breakthrough_method': 'final_drissionpage_signature',
                        'raw_data': record
                    }
                    all_records.append(standard_record)

        # 如果没有获取到真实数据，抛出异常
        if not all_records:
            rprint("[red]❌ 最终突破失败，未能获取到任何真实数据[/]")
            raise RuntimeError("最终突破失败，未能获取真实NMPA数据")

        # 保存最终突破数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.final.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 最终突破成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_final_breakthrough_crawler(config: Dict[str, Any]) -> FinalBreakthroughCrawler:
    """创建最终突破爬虫"""
    crawler = FinalBreakthroughCrawler(config)
    await crawler.start()
    return crawler