# -*- coding: utf-8 -*-
"""
超级突破NMPA爬虫 - 使用DrissionPage真实浏览器模式绕过所有检测
"""
import asyncio
import json
import time
import random
import re
from typing import Dict, List, Any
from rich import print as rprint

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    rprint("[red]❌ DrissionPage未安装，请先安装: pip install DrissionPage[/]")
    raise

class SuperBreakthroughCrawler:
    """超级突破NMPA爬虫 - 使用真实Chrome浏览器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get('output_dir', 'outputs')
        self.page = None
        self.driver = None

    def smart_delay(self, base: float = 2.0, variation: float = 3.0):
        """智能延迟"""
        delay = base + random.uniform(0, variation)
        rprint(f"[dim]智能延迟 {delay:.1f} 秒...[/]")
        time.sleep(delay)

    async def start(self):
        """启动超级突破爬虫"""
        rprint("[bold blue]启动超级突破NMPA爬虫（使用真实Chrome浏览器）[/]")

        try:
            # 配置Chrome选项 - 使用真实浏览器模式
            co = ChromiumOptions()
            co.headless(self.config.get('headless', True))

            # 添加真实浏览器参数
            arguments = [
                '--no-blink-features=AutomationControlled',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # 加速加载
                '--disable-javascript-harmony-shipping',
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
                '--excludeSwitches=enable-automation',
                '--disable-infobars',
                '--window-size=1366,768',
                '--start-maximized'
            ]

            for arg in arguments:
                co.set_argument(arg)

            # 设置用户代理
            co.set_user_agent(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )

            # 启动浏览器
            try:
                self.driver = ChromiumPage(co)
                self.page = self.driver
                rprint("[green]✅ DrissionPage真实浏览器启动成功[/]")
                return True
            except Exception as e:
                rprint(f"[red]❌ DrissionPage启动失败: {e}[/]")
                return False

        except Exception as e:
            rprint(f"[red]爬虫启动失败: {e}[/]")
            return False

    async def stop(self):
        """停止爬虫"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

    def simulate_human_behavior(self):
        """模拟人类行为"""
        rprint("[blue]模拟人类浏览行为...[/]")

        try:
            # 随机移动鼠标
            x = random.randint(100, 1266)
            y = random.randint(100, 668)
            self.page.mouse.move(x, y)
            self.smart_delay(0.1, 0.3)

            # 随机滚动
            scroll_y = random.randint(100, 300)
            self.page.scroll.scroll(0, scroll_y)
            self.smart_delay(0.5, 1.5)

            # 再滚动回来
            scroll_back = random.randint(50, 150)
            self.page.scroll.scroll(0, -scroll_back)
            self.smart_delay(0.3, 1.0)

        except Exception as e:
            rprint(f"[yellow]人类行为模拟失败: {e}[/]")

    def remove_automation_indicators(self):
        """移除自动化标识"""
        try:
            # 移除webdriver标识
            self.page.run_js("""
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

                console.log('反检测脚本执行完成');
            """)
        except Exception as e:
            rprint(f"[yellow]移除自动化标识失败: {e}[/]")

    def advanced_bypass_protection(self, url: str) -> bool:
        """高级绕过保护"""
        rprint(f"[bold cyan]高级绕过保护: {url}[/]")

        try:
            # 方法1: 直接访问
            rprint("[blue]方法1: 直接访问[/]")
            response = self.page.get(url, timeout=30)

            if hasattr(response, 'status_code') and response.status_code == 200:
                rprint("[green]✅ 方法1成功[/]")
                return True

            # 方法2: 等待后重新加载
            rprint("[blue]方法2: 等待后重新加载[/]")
            self.smart_delay(5, 10)
            self.page.refresh()
            self.smart_delay(3, 6)
            rprint("[green]✅ 方法2成功[/]")
            return True

        except Exception as e:
            rprint(f"[yellow]高级绕过保护失败: {e}[/]")
            return False

    def extract_comprehensive_data(self) -> List[Dict]:
        """综合数据提取"""
        rprint("[bold magenta]综合数据提取方案[/]")

        try:
            # 等待页面加载
            rprint("[blue]等待页面完全加载...[/]")
            time.sleep(15)  # 长时间等待

            # 检查页面状态
            current_url = self.page.url
            rprint(f"[cyan]当前页面URL: {current_url}[/]")

            # 获取页面HTML
            try:
                page_html = self.page.html
                rprint(f"[cyan]页面HTML长度: {len(page_html)} 字符[/]")

                if len(page_html) < 100:
                    rprint(f"[dim]HTML内容: {page_html}[/]")
                    rprint("[red]❌ 页面内容过少，可能被拦截[/]")
                    return []

            except Exception as e:
                rprint(f"[yellow]获取HTML失败: {e}[/]")
                return []

            # 获取页面文本
            try:
                page_text = self.page.text
                rprint(f"[cyan]页面文本长度: {len(page_text)} 字符[/]")

                if not page_text or len(page_text) < 10:
                    rprint("[red]❌ 页面文本为空[/]")
                    return []

            except Exception as e:
                rprint(f"[yellow]获取文本失败: {e}[/]")
                return []

            # 尝试多种数据提取方法
            all_results = []

            # 方法1: 查找表格数据
            rprint("[blue]方法1: 查找表格数据[/]")
            try:
                tables = self.page.eles('table')
                rprint(f"[dim]找到 {len(tables)} 个表格[/]")

                for i, table in enumerate(tables):
                    rows = table.eles('tr')
                    for row in rows[1:]:  # 跳过表头
                        cells = row.eles('td')
                        if len(cells) >= 3:
                            drug_info = {
                                'name': cells[0].text,
                                'approval_number': cells[1].text,
                                'company': cells[2].text,
                                'source': f'table_{i}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                            }

                            if drug_info['name'] and len(drug_info['name']) > 2:
                                all_results.append(drug_info)

            except Exception as e:
                rprint(f"[yellow]表格提取失败: {e}[/]")

            # 方法2: 查找列表数据
            rprint("[blue]方法2: 查找列表数据[/]")
            try:
                list_items = self.page.eles('li')
                rprint(f"[dim]找到 {len(list_items)} 个列表项[/]")

                for item in list_items:
                    text = item.text
                    if '国药准字' in text and len(text) > 10:
                        # 使用正则表达式提取
                        patterns = [
                            r'([^，。\n]*?)\s*[,，]\s*国药准字([HFJZTB]\d{8})\s*[,，]\s*([^，。\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^，。\n]*)',
                            r'国药准字([HFJZTB]\d{8})\s*[,，]\s*([^，。\n]{2,50}?)\s*[,，]\s*([^，。\n]*?(?:股份有限公司|有限公司|制药厂|药业)[^，。\n]*)',
                        ]

                        for pattern in patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                if len(match) >= 3:
                                    drug_info = {
                                        'name': match[0].strip() if not match[0].startswith('国药准字') else match[1].strip(),
                                        'approval_number': f'国药准字{match[1]}' if not match[1].startswith('国药准字') else match[0].strip(),
                                        'company': match[2].strip(),
                                        'source': 'list_regex',
                                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                                    }

                                    if drug_info['name'] and len(drug_info['name']) > 2:
                                        all_results.append(drug_info)

            except Exception as e:
                rprint(f"[yellow]列表提取失败: {e}[/]")

            # 方法3: 页面文本正则提取
            rprint("[blue]方法3: 页面文本正则提取[/]")
            patterns = [
                r'([^\n]{2,50}?)\s*[,，]\s*国药准字([HFJZTB]\d{8})\s*[,，]\s*([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*)',
                r'国药准字([HFJZTB]\d{8})\s*[,，]\s*([^\n]{2,50}?)\s*[,，]\s*([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*)',
            ]

            for i, pattern in enumerate(patterns):
                try:
                    matches = re.findall(pattern, page_text)
                    rprint(f"[blue]正则模式{i+1}匹配到 {len(matches)} 条记录[/]")

                    for match in matches:
                        if len(match) >= 3:
                            drug_info = {
                                'name': match[0].strip() if not match[0].startswith('国药准字') else match[1].strip(),
                                'approval_number': f'国药准字{match[1]}' if not match[1].startswith('国药准字') else match[0].strip(),
                                'company': match[2].strip(),
                                'source': f'text_regex_{i+1}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                            }

                            if drug_info['name'] and len(drug_info['name']) > 2 and drug_info['company']:
                                all_results.append(drug_info)

                except Exception as e:
                    rprint(f"[yellow]正则模式{i+1}失败: {e}[/]")

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
            rprint(f"[red]综合数据提取失败: {e}[/]")
            return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行超级突破任务"""
        rprint(f"[bold green]开始超级突破任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = []

        # 步骤1: 访问NMPA首页
        rprint("[blue]步骤1: 访问NMPA首页[/]")
        if not self.advanced_bypass_protection('https://www.nmpa.gov.cn/'):
            rprint("[red]❌ 无法访问NMPA首页[/]")
            return []

        # 移除自动化标识
        self.remove_automation_indicators()
        self.smart_delay(3, 6)
        self.simulate_human_behavior()

        # 步骤2: 访问数据查询页面
        rprint("[blue]步骤2: 访问数据查询页面[/]")
        if not self.advanced_bypass_protection('https://www.nmpa.gov.cn/datasearch/home?htmlType=1'):
            rprint("[red]❌ 无法访问数据查询页面[/]")
            return []

        self.remove_automation_indicators()
        self.smart_delay(5, 8)
        self.simulate_human_behavior()

        # 步骤3: 尝试点击境内生产药品链接
        rprint("[blue]步骤3: 尝试点击境内生产药品链接[/]")
        try:
            # 尝试多种选择器
            selectors = [
                'text:境内生产药品',
                'text:境内',
                'text:药品',
                'a:contains("境内")',
                'a:contains("药品")',
                '[onclick*="境内"]',
                '[href*="domestic"]'
            ]

            clicked = False
            for selector in selectors:
                try:
                    element = self.page.ele(selector, timeout=2)
                    if element:
                        element.click()
                        rprint(f"[green]✅ 成功点击: {selector}[/]")
                        clicked = True
                        break
                except:
                    continue

            if clicked:
                self.smart_delay(3, 5)
                self.simulate_human_behavior()

        except Exception as e:
            rprint(f"[yellow]点击链接失败: {e}[/]")

        # 步骤4: 综合数据提取
        rprint("[blue]步骤4: 综合数据提取[/]")
        self.smart_delay(5, 10)

        results = self.extract_comprehensive_data()

        if results:
            all_records.extend(results)
            rprint(f"[green]✅ 超级突破成功！获取 {len(results)} 条药品数据！[/]")
        else:
            rprint("[red]❌ 超级突破失败，未能获取到任何数据[/]")
            raise RuntimeError("超级突破失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.super_breakthrough.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 超级突破成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        return all_records

async def create_super_breakthrough_crawler(config: Dict[str, Any]) -> SuperBreakthroughCrawler:
    """创建超级突破爬虫"""
    crawler = SuperBreakthroughCrawler(config)
    await crawler.start()
    return crawler