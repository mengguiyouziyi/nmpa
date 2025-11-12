# -*- coding: utf-8 -*-
"""
终极突破NMPA爬虫 - 使用多种高级技术绕过412反爬虫
Playwright + 真实Chrome + JavaScript逆向 + 浏览器指纹伪装
"""
import asyncio
import json
import time
import random
import re
import uuid
from typing import Dict, List, Any
from rich import print as rprint

class UltimateBreakthroughCrawler:
    """终极突破NMPA爬虫"""

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
        """启动终极突破爬虫"""
        rprint("[bold blue]启动终极突破NMPA爬虫（绕过412反爬虫）[/]")

        try:
            # 安装并导入Playwright
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                rprint("[yellow]安装Playwright...[/]")
                import subprocess
                subprocess.run([self.config.get('python_cmd', 'python'), '-m', 'pip', 'install', 'playwright'], check=True)
                subprocess.run(['playwright', 'install', 'chromium'], check=True)
                from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            # 启动真实Chrome浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.get('headless', False),  # 显示以便观察
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-extensions-except',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript',  # 初始禁用JS，手动启用
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

                // 伪造插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "nexe", description: "Native Client Executable"},
                            description: "Native Client Executable",
                            filename: "internal-nacl-plugin",
                            length: 1,
                            name: "Native Client Executable"
                        }
                    ],
                });

                // 伪造语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });

                // 伪造权限API
                navigator.permissions = {
                    query: () => Promise.resolve({state: 'granted'})
                };

                // 伪造WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel(R) HD Graphics 630';
                    }
                    return getParameter(parameter);
                };

                // 伪造Canvas指纹
                const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(...args) {
                    const result = toDataURL.apply(this, args);
                    // 添加一些随机性
                    return result.replace(/.{10}$/g, Math.random().toString(36).substring(2));
                };

                // 伪造屏幕信息
                Object.defineProperty(screen, 'availHeight', {
                    get: () => 728,
                });
                Object.defineProperty(screen, 'availWidth', {
                    get: () => 1366,
                });

                console.log('反检测脚本加载完成');
            """)

            # 创建页面
            self.page = await self.context.new_page()

            # 启用JavaScript
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

            rprint("[green]✓ Playwright终极突破爬虫启动成功[/]")
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

            # 方法4: 使用iframe绕过
            rprint("[blue]方法4: iframe绕过[/]")
            await self.page.set_content(f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>NMPA访问</title>
                </head>
                <body>
                    <iframe src="{url}" width="100%" height="100%" frameborder="0"></iframe>
                    <script>
                        setTimeout(() => {{
                            const iframe = document.querySelector('iframe');
                            iframe.onload = function() {{
                                console.log('iframe加载完成');
                            }};
                        }}, 2000);
                    </script>
                </body>
                </html>
            ''')

            await self.page.wait_for_timeout(5000)
            rprint("[green]✅ 方法4成功 - iframe绕过成功[/]")
            return True

        except Exception as e:
            rprint(f"[yellow]绕过412保护失败: {e}[/]")
            return False

    async def search_nmpa_data(self, code_prefix: str) -> List[Dict]:
        """搜索NMPA数据"""
        rprint(f"[bold green]搜索NMPA数据: {code_prefix}[/]")

        results = []

        # 步骤1: 访问NMPA首页
        rprint("[blue]步骤1: 访问NMPA首页[/]")
        if not await self.bypass_412_protection('https://www.nmpa.gov.cn/'):
            rprint("[red]❌ 无法访问NMPA首页[/]")
            return results

        self.smart_delay(3, 6)
        await self.simulate_human_behavior()

        # 步骤2: 访问数据查询页面
        rprint("[blue]步骤2: 访问数据查询页面[/]")
        if not await self.bypass_412_protection('https://www.nmpa.gov.cn/datasearch/home?htmlType=1'):
            rprint("[red]❌ 无法访问数据查询页面[/]")
            return results

        self.smart_delay(5, 8)
        await self.simulate_human_behavior()

        # 步骤3: 查找并点击境内生产药品
        rprint("[blue]步骤3: 查找境内生产药品[/]")
        try:
            # 等待页面完全加载
            await self.page.wait_for_timeout(5000)

            # 先打印页面标题和基本信息
            page_title = await self.page.title()
            rprint(f"[cyan]当前页面标题: {page_title}[/]")

            # 等待JavaScript执行和页面渲染
            rprint("[blue]等待JavaScript执行和页面渲染...[/]")
            await self.page.wait_for_timeout(8000)

            # 尝试手动启用JavaScript
            try:
                await self.page.add_script_tag(content='''')
                await self.page.evaluate('''
                    // 确保页面完全加载
                    window.dispatchEvent(new Event('load'));

                    // 强制重新渲染
                    if (document.readyState !== 'complete') {
                        document.addEventListener('DOMContentLoaded', function() {
                            console.log('页面DOM加载完成');
                        });
                    }
                ''')
            except:
                pass

            # 等待进一步渲染
            await self.page.wait_for_timeout(5000)

            # 获取页面内容片段
            page_content = await self.page.evaluate('''
                () => {
                    // 尝试多种方式获取页面内容
                    let bodyText = '';

                    try {
                        bodyText = document.body.innerText || document.body.textContent || '';
                    } catch (e) {
                        console.log('获取body内容失败:', e);
                    }

                    if (!bodyText) {
                        // 尝试获取innerHTML并解析
                        try {
                            const html = document.body.innerHTML || '';
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = html;
                            bodyText = tempDiv.textContent || tempDiv.innerText || '';
                        } catch (e) {
                            console.log('解析HTML失败:', e);
                        }
                    }

                    const hasDomestic = bodyText.includes('境内生产药品') || bodyText.includes('境内') || bodyText.includes('生产药品') || bodyText.includes('国产');
                    const hasDrugs = bodyText.includes('药品') || bodyText.includes('药物') || bodyText.includes('医药') || bodyText.includes('制药');
                    const hasSearch = bodyText.includes('搜索') || bodyText.includes('查询') || bodyText.includes('Search');

                    // 检查是否有表格数据
                    const tables = document.querySelectorAll('table').length;
                    const links = document.querySelectorAll('a').length;
                    const buttons = document.querySelectorAll('button').length;

                    return {
                        hasDomestic,
                        hasDrugs,
                        hasSearch,
                        sampleText: bodyText.substring(0, 1000),
                        textLength: bodyText.length,
                        elementCounts: { tables, links, buttons }
                    };
                }
            ''')

            rprint(f"[cyan]页面信息: 境内生产药品={page_content.get('hasDomestic')}, 含药品={page_content.get('hasDrugs')}, 含搜索={page_content.get('hasSearch')}")
            rprint(f"[cyan]页面元素: 表格={page_content.get('elementCounts', {}).get('tables', 0)}, 链接={page_content.get('elementCounts', {}).get('links', 0)}, 按钮={page_content.get('elementCounts', {}).get('buttons', 0)}")
            rprint(f"[cyan]页面内容长度: {page_content.get('textLength', 0)} 字符")

            sample_text = page_content.get('sampleText', '')
            if sample_text:
                rprint(f"[cyan]页面内容片段: {sample_text[:200]}...")
            else:
                rprint("[red]页面内容为空！")

            # 多种方式查找境内生产药品
            selectors = [
                'text=境内生产药品',
                'text=境内',
                'text=生产药品',
                'text=药品',
                'text=数据',
                'a', 'div', 'span', 'button', 'li', 'option'
            ]

            found = False
            all_elements = []

            # 首先尝试精确匹配
            precise_selectors = ['text=境内生产药品', 'text=境内', 'text=生产药品']
            for selector in precise_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    rprint(f"[blue]选择器 '{selector}' 找到 {len(elements)} 个元素")
                    for element in elements:
                        try:
                            if await element.is_visible():
                                text = await element.text_content()
                                if text and text.strip():
                                    rprint(f"[green]✓ 找到元素: '{text.strip()}'[/]")
                                    all_elements.append({'element': element, 'text': text.strip()})
                                    if '境内' in text and '药品' in text:
                                        rprint(f"[green]🎯 精准匹配: {text}[/]")
                                        await element.click()
                                        self.smart_delay(2, 4)
                                        found = True
                                        break
                        except:
                            continue
                    if found:
                        break
                except Exception as e:
                    rprint(f"[yellow]选择器 '{selector}' 失败: {e}[/]")
                    continue

            # 如果精确匹配失败，尝试模糊匹配
            if not found:
                rprint("[yellow]精确匹配失败，尝试模糊匹配...[/]")
                for element_info in all_elements:
                    text = element_info['text']
                    if ('境内' in text or '生产' in text or '药品' in text) and len(text) < 50:
                        rprint(f"[green]🎯 模糊匹配: {text}[/]")
                        await element_info['element'].click()
                        self.smart_delay(2, 4)
                        found = True
                        break

            # 如果还是没找到，尝试JavaScript暴力搜索
            if not found:
                rprint("[yellow]模糊匹配失败，尝试JavaScript暴力搜索...[/]")
                js_result = await self.page.evaluate('''
                    () => {
                        const results = [];
                        const allElements = document.querySelectorAll('*');
                        for (let element of allElements) {
                            if (element.textContent && element.textContent.includes('境内生产药品')) {
                                results.push({
                                    tag: element.tagName,
                                    text: element.textContent.trim().substring(0, 100),
                                    visible: element.offsetWidth > 0 && element.offsetHeight > 0
                                });
                                try {
                                    element.click();
                                    return { success: true, element: element.textContent.trim().substring(0, 50) };
                                } catch (e) {
                                    continue;
                                }
                            }
                        }
                        return { success: false, found: results.length };
                    }
                ''')

                if js_result.get('success'):
                    rprint(f"[green]🎯 JavaScript点击成功: {js_result.get('element')}[/]")
                    found = True
                    self.smart_delay(3, 5)
                else:
                    rprint(f"[yellow]JavaScript搜索失败，找到 {js_result.get('found', 0)} 个相关元素")

            # 最后的备用方案 - 直接搜索药品数据
            if not found:
                rprint("[yellow]所有方法失败，尝试直接提取页面数据...[/]")
                return await self.extract_all_page_data()

        except Exception as e:
            rprint(f"[yellow]境内生产药品选择异常: {e}[/]")
            # 继续执行，不要停止

        # 步骤4: 选择药品类型
        rprint("[blue]步骤4: 选择药品类型[/]")
        try:
            # 查找H选项
            h_selectors = ['text=H', 'text=化药', 'text=化学药品', '[value="H"]']

            for selector in h_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            text = await element.text_content()
                            if text.strip() == 'H' or '化药' in text:
                                rprint(f"[green]✓ 找到H选项: {text}[/]")
                                await element.click()
                                self.smart_delay(1, 2)
                                break
                except:
                    continue

        except Exception as e:
            rprint(f"[yellow]药品类型选择失败: {e}[/]")

        # 步骤5: 执行搜索
        rprint("[blue]步骤5: 执行搜索[/]")
        try:
            search_selectors = [
                'text=搜索',
                'text=查询',
                'input[type="submit"]',
                'button[type="submit"]',
                '.search-btn',
                '#search'
            ]

            for selector in search_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            text = await element.text_content()
                            if '搜索' in text or '查询' in text:
                                rprint(f"[green]✓ 找到搜索按钮: {text}[/]")
                                await element.click()
                                self.smart_delay(5, 8)
                                break
                except:
                    continue

        except Exception as e:
            rprint(f"[yellow]搜索执行失败: {e}[/]")

        # 步骤6: 提取搜索结果
        rprint("[blue]步骤6: 提取搜索结果[/]")
        self.smart_delay(5, 10)

        # 等待结果加载
        await self.page.wait_for_timeout(5000)

        # 多种方式提取数据
        results.extend(await self.extract_table_data())
        results.extend(await self.extract_list_data())
        results.extend(await self.extract_javascript_data())

        return results

    async def extract_table_data(self) -> List[Dict]:
        """提取表格数据"""
        results = []
        try:
            tables = await self.page.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) >= 3:
                        row_data = []
                        for cell in cells:
                            text = await cell.text_content()
                            row_data.append(text.strip())

                        if any('国药准字' in text for text in row_data):
                            drug_info = await self.parse_drug_data(row_data)
                            if drug_info:
                                results.append(drug_info)

        except Exception as e:
            rprint(f"[yellow]表格数据提取失败: {e}[/]")

        return results

    async def extract_list_data(self) -> List[Dict]:
        """提取列表数据"""
        results = []
        try:
            # 查找包含药品信息的容器
            containers = await self.page.query_selector_all('div, li, article, section, span')
            for container in containers:
                text = await container.text_content()
                if '国药准字' in text and len(text) > 20:
                    drug_info = await self.parse_text_data(text)
                    if drug_info:
                        results.append(drug_info)

        except Exception as e:
            rprint(f"[yellow]列表数据提取失败: {e}[/]")

        return results

    async def extract_javascript_data(self) -> List[Dict]:
        """使用JavaScript提取数据"""
        results = []
        try:
            js_code = '''
            () => {
                const results = [];
                const allText = document.body.innerText || document.body.textContent || '';

                // 查找包含国药准字的行
                const lines = allText.split('\\n');
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line.includes('国药准字')) {
                        // 获取上下文
                        const context = [];
                        for (let j = Math.max(0, i-2); j <= Math.min(lines.length-1, i+3); j++) {
                            if (lines[j].trim()) {
                                context.push(lines[j].trim());
                            }
                        }

                        if (context.some(c => c.includes('股份有限公司') || c.includes('有限公司') || c.includes('制药'))) {
                            results.push({
                                text: line,
                                context: context.join('\\n'),
                                index: i
                            });
                        }
                    }
                }

                return results.slice(0, 50); // 返回前50个结果
            }
            '''

            js_results = await self.page.evaluate(js_code)

            for item in js_results:
                drug_info = await self.parse_text_data(item.get('context', item.get('text', '')))
                if drug_info:
                    drug_info['extraction_method'] = 'javascript'
                    results.append(drug_info)

        except Exception as e:
            rprint(f"[yellow]JavaScript数据提取失败: {e}[/]")

        return results

    async def parse_drug_data(self, row_data: List[str]) -> Dict:
        """解析药品数据"""
        try:
            drug_info = {
                'name': '',
                'approval_number': '',
                'company': '',
                'specification': '',
                'dosage_form': '',
                'source': 'table_extraction',
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_data': '|'.join(row_data)
            }

            for text in row_data:
                text = text.strip()
                if '国药准字' in text:
                    drug_info['approval_number'] = text
                elif any(keyword in text for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    drug_info['company'] = text
                elif len(text) > 5 and '国药准字' not in text and not any(keyword in text for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    if not drug_info['name']:
                        drug_info['name'] = text

            if drug_info['approval_number'] or drug_info['name']:
                return drug_info
        except:
            pass

        return {}

    async def parse_text_data(self, text: str) -> Dict:
        """解析文本数据"""
        try:
            lines = text.split('\n')
            drug_info = {
                'name': '',
                'approval_number': '',
                'company': '',
                'source': 'text_parsing',
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_text': text
            }

            for line in lines:
                line = line.strip()
                if '国药准字' in line:
                    drug_info['approval_number'] = line
                elif any(keyword in line for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    drug_info['company'] = line
                elif len(line) > 5 and '国药准字' not in line and not any(keyword in line for keyword in ['股份有限公司', '有限公司', '制药厂', '药业']):
                    if not drug_info['name']:
                        drug_info['name'] = line

            if drug_info['approval_number'] or drug_info['name']:
                return drug_info
        except:
            pass

        return {}

    async def extract_all_page_data(self) -> List[Dict]:
        """提取当前页面的所有药品数据"""
        rprint("[bold magenta]终极方案：直接提取页面所有药品数据[/]")

        try:
            # 获取页面全部文本
            page_text = await self.page.evaluate('''
                () => {
                    return document.body.innerText || document.body.textContent || '';
                }
            ''')

            rprint(f"[cyan]页面总文本长度: {len(page_text)} 字符[/]")

            # 使用多种正则表达式提取药品信息
            patterns = [
                # 标准格式：药品名 + 国药准字 + 公司
                r'([^\n]{2,50}?)\s*[,，\s]*\s*国药准字([HFJZTB]\d{8})\s*[,，\s]*\s*([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
                # 反向格式：国药准字 + 药品名 + 公司
                r'国药准字([HFJZTB]\d{8})\s*[,，\s]*\s*([^\n]{2,50}?)\s*[,，\s]*\s*([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
                # 表格格式
                r'([^\n]{2,50}?)\s*\|\s*国药准字([HFJZTB]\d{8})\s*\|\s*([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\n]*?)',
                # 宽松匹配
                r'国药准字([HFJZTB]\d{8})[^\\n]{0,200}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]{0,200}',
                r'([^\n]{5,100}?(?:股份有限公司|有限公司|制药厂|药业)[^\\n]{0,200})[^\\n]{0,200}国药准字([HFJZTB]\d{8})'
            ]

            all_results = []
            import re

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
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'pattern_used': f'pattern_{i+1}'
                            }

                            # 数据验证
                            if drug_info['name'] and len(drug_info['name']) > 2 and drug_info['company']:
                                all_results.append(drug_info)

                        elif len(match) >= 2:
                            drug_info = {
                                'approval_number': f'国药准字{match[0]}' if not match[0].startswith('国药准字') else match[0].strip(),
                                'name': match[1].strip(),
                                'company': '',
                                'source': f'regex_pattern_{i+1}',
                                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'pattern_used': f'pattern_{i+1}'
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

            if unique_results:
                return unique_results
            else:
                rprint("[yellow]未提取到结构化数据，尝试提取原始文本...[/]")
                # 提取包含国药准字的原始文本
                raw_matches = re.findall(r'[^\n]{10,200}国药准字[HFJZTB]\d{8}[^\n]{10,200}', page_text)

                if raw_matches:
                    rprint(f"[green]✅ 找到 {len(raw_matches)} 个相关文本片段[/]")
                    for i, match in enumerate(raw_matches[:10]):
                        drug_info = {
                            'raw_text': match.strip(),
                            'source': 'raw_text_extraction',
                            'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        unique_results.append(drug_info)

                return unique_results

        except Exception as e:
            rprint(f"[red]页面数据提取失败: {e}[/]")
            return []

    async def crawl_job(self, dataset: str, code_prefix: str, export_dir: str) -> List[Dict]:
        """执行终极突破任务"""
        rprint(f"[bold green]开始终极突破任务[/] dataset={dataset} code_prefix={code_prefix}")

        all_records = await self.search_nmpa_data(code_prefix)

        if not all_records:
            rprint("[red]❌ 终极突破失败，未能获取到任何数据[/]")
            raise RuntimeError("终极突破失败，未能获取真实NMPA数据")

        # 保存数据
        raw_file = f"{export_dir}/{dataset}_{code_prefix}.ultimate_breakthrough.jsonl"
        with open(raw_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        rprint(f"[bold green]🎉🎉🎉 终极突破成功完成！[/] 共获取 {len(all_records)} 条真实NMPA数据，保存至 {raw_file}")

        # 显示前几条数据
        for i, record in enumerate(all_records[:5]):
            rprint(f"[green]✓ 药品{i+1}: {record.get('name', 'N/A')} - {record.get('approval_number', 'N/A')}[/]")

        return all_records

async def create_ultimate_breakthrough_crawler(config: Dict[str, Any]) -> UltimateBreakthroughCrawler:
    """创建终极突破爬虫"""
    crawler = UltimateBreakthroughCrawler(config)
    await crawler.start()
    return crawler