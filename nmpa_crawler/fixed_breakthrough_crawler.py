# -*- coding: utf-8 -*-
"""
修复版突破NMPA爬虫 - 修复语法错误并优化412绕过
"""
import asyncio
import json
import time
import random
import re
from typing import Dict, List, Any
from rich import print as rprint

class FixedBreakthroughCrawler:
    """修复版突破NMPA爬虫"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None

        # 生成真实的浏览器指纹
        self.browser_fingerprint = self.generate_browser_fingerprint()

    def generate_browser_fingerprint(self) -> Dict:
        """生成真实浏览器指纹"""
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept_language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'accept_encoding': 'gzip, deflate, br, zstd',
            'platform': 'Win32',
            'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec_ch_ua_mobile': '?0',
            'sec_ch_ua_platform': '"Windows"',
            'viewport': {'width': 1366, 'height': 768},
            'timezone': 'Asia/Shanghai',
            'geolocation': {'latitude': 39.9042, 'longitude': 116.4074},  # 北京
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
            'reduced_motion': 'reduce'
        }

    async def start(self):
        """启动修复版爬虫"""
        rprint("[bold blue]启动修复版突破NMPA爬虫（绕过412反爬虫）[/]")

        try:
            # 安装并导入Playwright
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                rprint("[yellow]安装Playwright...[/]")
                import subprocess
                subprocess.run(['python', '-m', 'pip', 'install', 'playwright'], check=True)
                subprocess.run(['playwright', 'install', 'chromium'], check=True)
                from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            # 启动真实Chrome浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-extensions-except',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    # '--disable-javascript',  # 需要JavaScript来渲染页面内容
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-background-networking',
                    '--disable-default-browser-check',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-client-side-phishing-detection',
                    '--disable-sync',
                    '--disable-default-apps',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--disable-background-logging',
                    '--disable-logging',
                    '--disable-gpu',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--enable-automation=false',
                    '--excludeSwitches=enable-automation',
                    '--disable-infobars',
                    '--window-size=1366,768',
                    '--start-maximized'
                ]
            )

            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport=self.browser_fingerprint['viewport'],
                user_agent=self.browser_fingerprint['user_agent'],
                locale='zh-CN',
                timezone_id=self.browser_fingerprint['timezone'],
                permissions=self.browser_fingerprint['permissions'],
                geolocation=self.browser_fingerprint['geolocation'],
                color_scheme=self.browser_fingerprint['color_scheme'],
                reduced_motion=self.browser_fingerprint['reduced_motion'],
                extra_http_headers={
                    'Accept-Language': self.browser_fingerprint['accept_language'],
                    'Accept-Encoding': self.browser_fingerprint['accept_encoding'],
                    'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                    'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                    'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                }
            )

            # 添加反检测脚本
            await self.context.add_init_script("""
                // 移除webdriver标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 移除自动化标识
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

                // 伪造Chrome对象
                window.chrome = {
                    runtime: {
                        onConnect: undefined,
                        onMessage: undefined,
                    },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: {}
                };

                console.log('反检测脚本加载完成');
            """)

            # 创建页面
            self.page = await self.context.new_page()

            # 启用JavaScript并设置头部
            await self.context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': self.browser_fingerprint['accept_language'],
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': self.browser_fingerprint['sec_ch_ua'],
                'sec-ch-ua-mobile': self.browser_fingerprint['sec_ch_ua_mobile'],
                'sec-ch-ua-platform': self.browser_fingerprint['sec_ch_ua_platform'],
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive'
            })

            rprint("[green]✅ 修复版突破爬虫启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]爬虫启动失败: {e}[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[dim]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def simulate_human_behavior(self):
        """模拟人类行为"""
        rprint("[blue]模拟人类浏览行为...[/]")

        # 随机移动鼠标
        await self.page.mouse.move(
            random.randint(100, 1266),
            random.randint(100, 668)
        )
        self.smart_delay(0.1, 0.3)

        # 随机滚动
        await self.page.evaluate(f'window.scrollBy(0, {random.randint(100, 300)})')
        self.smart_delay(0.5, 1.5)

        # 再滚动回来
        await self.page.evaluate(f'window.scrollBy(0, -{random.randint(50, 150)})')
        self.smart_delay(0.3, 1.0)

    async def bypass_412_protection(self, url: str) -> bool:
        """绕过412保护"""
        rprint(f"[bold cyan]绕过412保护: {url}[/]")

        try:
            # 方法1: 直接访问
            rprint("[blue]方法1: 直接访问[/]")
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response and response.status == 200:
                rprint("[green]✅ 方法1成功 - 直接访问成功[/]")
                return True

            # 方法2: 添加随机延迟访问
            rprint("[blue]方法2: 延迟访问[/]")
            self.smart_delay(5, 10)
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response and response.status == 200:
                rprint("[green]✅ 方法2成功 - 延迟访问成功[/]")
                return True

            # 方法3: 通过JavaScript跳转
            rprint("[blue]方法3: JavaScript跳转[/]")
            await self.page.evaluate(f'window.location.href = "{url}"')
            await self.page.wait_for_load_state('domcontentloaded', timeout=30000)

            current_url = self.page.url
            if url in current_url:
                rprint("[green]✅ 方法3成功 - JavaScript跳转成功[/]")
                return True

        except Exception as e:
            rprint(f"[yellow]绕过412保护失败: {e}[/]")
            return False

    async def extract_page_data_directly(self) -> List[Dict]:
        """直接提取页面数据"""
        rprint("[bold magenta]终极方案：直接提取页面所有药品数据[/]")

        try:
            # 等待页面完全加载
            rprint("[blue]等待页面内容加载...[/]")
            await self.page.wait_for_timeout(15000)  # 增加等待时间到15秒

            # 检查页面URL和状态
            current_url = self.page.url
            rprint(f"[cyan]当前页面URL: {current_url}[/]")

            # 尝试等待特定元素出现
            try:
                await self.page.wait_for_selector('body', timeout=10000)
                rprint("[green]✅ 页面body元素已加载[/]")
            except:
                rprint("[yellow]⚠️ 等待body元素超时[/]")

            # 获取页面HTML内容用于调试
            page_html = await self.page.evaluate("""
                () => {
                    try {
                        return document.documentElement.outerHTML || '';
                    } catch (e) {
                        return 'Error getting HTML: ' + e.message;
                    }
                }
            """)

            rprint(f"[cyan]页面HTML长度: {len(page_html)} 字符[/]")
            rprint(f"[dim]HTML内容预览: {page_html[:200]}...[/]")

            # 获取页面全部文本
            page_text = await self.page.evaluate("""
                () => {
                    try {
                        return document.body.innerText || document.body.textContent || '';
                    } catch (e) {
                        return '';
                    }
                }
            """)

            rprint(f"[cyan]页面总文本长度: {len(page_text)} 字符[/]")

            if not page_text:
                rprint("[red]❌ 页面内容为空，无法提取数据[/]")
                return []

            # 使用正则表达式提取药品信息
            patterns = [
                # 标准格式：药品名 + 国药准字 + 公司
                r'([^\\n]{2,50}?)\\s*[,，\\s]*\\s*国药准字([HFJZTB]\\d{8})\\s*[,，\\s]*\\s*([^\\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]*?)',
                # 反向格式：国药准字 + 药品名 + 公司
                r'国药准字([HFJZTB]\\d{8})\\s*[,，\\s]*\\s*([^\\n]{2,50}?)\\s*[,，\\s]*\\s*([^\\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]*?)',
                # 宽松匹配
                r'国药准字([HFJZTB]\\d{8})[^\\n]{0,200}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]{0,200}',
                r'([^\\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]{0,200})[^\\n]{0,200}国药准字([HFJZTB]\\d{8})'
            ]

            all_results = []

            for i, pattern in enumerate(patterns):
                try:
                    matches = re.findall(pattern, page_text)
                    rprint(f"[blue]模式{i+1}匹配到 {len(matches)} 条记录[/]")

                    for match in matches:
                        if len(match) >= 3:
                            drug_info = {
                                'name': match[1].strip() if not match[1].startswith('国药准字') else match[0].strip(),
                                'approval_number': f'国药准字{match[1]}' if not match[1].startswith('国药准字') else match[0].strip(),
                                'company': match[2].strip(),
                                'source': f'regex_pattern_{i+1}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                            }

                            if drug_info['name'] and len(drug_info['name']) > 2 and drug_info['company']:
                                all_results.append(drug_info)

                        elif len(match) >= 2:
                            drug_info = {
                                'approval_number': f'国药准字{match[0]}' if not match[0].startswith('国药准字') else match[0].strip(),
                                'name': match[1].strip(),
                                'company': '',
                                'source': f'regex_pattern_{i+1}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                            }

                            if len(drug_info['name']) > 2:
                                all_results.append(drug_info)

                except Exception as e:
                    rprint(f"[yellow]模式{i+1}执行失败: {e}[/]")
                    continue

            # 去重
            unique_results = []
            seen = set()

            for result in all_results:
                key = (result.get('approval_number', ''), result.get('name', ''))
                if key not in seen and key != ('', ''):
                    seen.add(key)
                    unique_results.append(result)

            rprint(f"[green]✅ 提取成功！去重后共 {len(unique_results)} 条药品数据[/]")

            # 显示前几条数据
            for i, result in enumerate(unique_results[:5]):
                rprint(f"[green]✓ 药品{i+1}: {result.get('name', 'N/A')} - {result.get('approval_number', 'N/A')}[/]")

            return unique_results

        except Exception as e:
            rprint(f"[red]页面数据提取失败: {e}[/]")
            return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行修复版突破任务"""
        rprint(f"[bold green]开始修复版突破任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 步骤1: 访问NMPA首页
        rprint("[blue]步骤1: 访问NMPA首页[/]")
        if not await self.bypass_412_protection('https://www.nmpa.gov.cn/'):
            rprint("[red]❌ 无法访问NMPA首页[/]")
            return []

        self.smart_delay(3, 6)
        await self.simulate_human_behavior()

        # 步骤2: 访问数据查询页面
        rprint("[blue]步骤2: 访问数据查询页面[/]")
        if not await self.bypass_412_protection('https://www.nmpa.gov.cn/datasearch/home?htmlType=1'):
            rprint("[red]❌ 无法访问数据查询页面[/]")
            return []

        self.smart_delay(5, 8)
        await self.simulate_human_behavior()

        # 步骤3: 尝试搜索功能
        rprint("[blue]步骤3: 尝试搜索功能[/]")
        self.smart_delay(5, 10)

        # 尝试在搜索框中输入关键词
        try:
            # 查找搜索框
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="查询"]',
                'input[type="search"]',
                'input[name*="search"]',
                'input[id*="search"]',
                '.search-input',
                '#search'
            ]

            search_found = False
            for selector in search_selectors:
                try:
                    search_box = await self.page.query_selector(selector)
                    if search_box:
                        rprint(f"[green]✅ 找到搜索框: {selector}[/]")

                        # 清空搜索框并输入关键词
                        await search_box.clear()
                        await search_box.type("阿司匹林", delay=random.uniform(50, 150))
                        rprint("[blue]输入搜索关键词: 阿司匹林[/]")

                        # 查找搜索按钮
                        button_selectors = [
                            'button[type="submit"]',
                            'input[type="submit"]',
                            'button:has-text("搜索")',
                            'button:has-text("查询")',
                            '.search-btn',
                            '#searchBtn'
                        ]

                        for btn_selector in button_selectors:
                            try:
                                search_btn = await self.page.query_selector(btn_selector)
                                if search_btn:
                                    await search_btn.click()
                                    rprint(f"[green]✅ 点击搜索按钮: {btn_selector}[/]")
                                    search_found = True
                                    break
                            except:
                                continue

                        if search_found:
                            break

                except Exception as e:
                    rprint(f"[dim]搜索框选择器 {selector} 失败: {e}[/]")
                    continue

            if search_found:
                # 等待搜索结果加载
                self.smart_delay(8, 12)
                await self.simulate_human_behavior()

        except Exception as e:
            rprint(f"[yellow]搜索功能失败: {e}[/]")

        # 步骤4: 尝试点击境内生产药品
        rprint("[blue]步骤4: 尝试点击境内生产药品[/]")
        try:
            link_selectors = [
                'text=境内生产药品',
                'text=境内药品',
                'text=化药',
                'a:has-text("境内")',
                'a:has-text("药品")'
            ]

            for selector in link_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        rprint(f"[green]✅ 点击链接: {selector}[/]")
                        self.smart_delay(5, 8)
                        await self.simulate_human_behavior()
                        break
                except:
                    continue

        except Exception as e:
            rprint(f"[yellow]点击链接失败: {e}[/]")

        # 步骤5: 直接提取数据
        rprint("[blue]步骤5: 直接提取数据[/]")
        self.smart_delay(5, 10)

        results = await self.extract_page_data_directly()

        if results:
            all_records.extend(results)
            rprint(f"[green]✅ 修复版突破成功！获取 {len(results)} 条药品数据！[/]")
        else:
            rprint("[red]❌ 修复版突破失败，未能获取到任何数据[/]")
            raise RuntimeError("修复版突破失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.fixed_breakthrough.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 修复版突破成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_fixed_breakthrough_crawler(config: Dict[str, Any]) -> FixedBreakthroughCrawler:
    """创建修复版突破爬虫"""
    crawler = FixedBreakthroughCrawler(config)
    await crawler.start()
    return crawler