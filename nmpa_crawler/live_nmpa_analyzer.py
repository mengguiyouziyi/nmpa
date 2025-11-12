# -*- coding: utf-8 -*-
"""
NMPA网站实时分析器 - 深度分析真实网站的JavaScript、参数、接口和数据结构
基于DrissionPage实现，结合GitHub项目优化技术方案
"""
import asyncio
import json
import time
import re
from typing import Dict, List, Any
from rich import print as rprint
from DrissionPage import ChromiumPage, ChromiumOptions

class LiveNMPAAnalyzer:
    """NMPA网站实时分析器"""

    def __init__(self):
        self.drission_page = None
        self.analysis_results = {
            'pages': {},
            'apis': {},
            'javascript': {},
            'cookies': {},
            'headers': {},
            'forms': {},
            'data_structures': {}
        }

    async def start(self):
        """启动DrissionPage进行实时分析"""
        rprint("[bold blue]启动NMPA网站实时分析器[/]")

        try:
            # 高级DrissionPage配置
            chromium_options = ChromiumOptions()
            chromium_options.headless(True)  # 使用headless模式
            chromium_options.set_argument('--disable-blink-features=AutomationControlled')
            chromium_options.set_argument('--disable-dev-shm-usage')
            chromium_options.set_argument('--no-sandbox')
            chromium_options.set_argument('--disable-web-security')
            chromium_options.set_argument('--window-size=1920,1080')
            chromium_options.set_argument('--remote-debugging-port=9225')
            chromium_options.set_argument('--headless=new')

            self.drission_page = ChromiumPage(chromium_options)
            rprint("[green]✓ DrissionPage分析器启动成功[/]")
            return True

        except Exception as e:
            rprint(f"[red]DrissionPage启动失败: {e}[/]")
            return False

    async def analyze_nmpa_main_site(self):
        """分析NMPA主站"""
        rprint("[bold cyan]分析NMPA主站...[/]")

        try:
            # 访问主站
            self.drission_page.get('https://www.nmpa.gov.cn/')
            time.sleep(5)

            page_info = {
                'title': self.drission_page.title,
                'url': self.drission_page.url,
                'cookies': self.get_cookies_analysis(),
                'local_storage': self.get_local_storage(),
                'session_storage': self.get_session_storage(),
                'scripts': self.get_page_scripts(),
                'forms': self.get_page_forms(),
                'meta_tags': self.get_meta_tags()
            }

            self.analysis_results['pages']['main'] = page_info
            rprint(f"[green]✓ 主站分析完成: {page_info['title']}[/]")

            # 分析JavaScript代码
            await self.analyze_javascript_patterns()

            # 查找API端点
            await self.find_api_endpoints()

        except Exception as e:
            rprint(f"[red]主站分析失败: {e}[/]")

    async def analyze_data_search_page(self):
        """分析数据查询页面"""
        rprint("[bold cyan]分析数据查询页面...[/]")

        try:
            # 访问数据查询页面
            self.drission_page.get('https://www.nmpa.gov.cn/datasearch/home?htmlType=1')
            time.sleep(8)

            page_info = {
                'title': self.drission_page.title,
                'url': self.drission_page.url,
                'cookies': self.get_cookies_analysis(),
                'local_storage': self.get_local_storage(),
                'session_storage': self.get_session_storage(),
                'scripts': self.get_page_scripts(),
                'forms': self.get_page_forms()
            }

            self.analysis_results['pages']['data_search'] = page_info
            rprint(f"[green]✓ 数据查询页面分析完成: {page_info['title']}[/]")

            # 模拟用户操作
            await self.simulate_user_interactions()

            # 监听网络请求
            await self.monitor_network_requests()

        except Exception as e:
            rprint(f"[red]数据查询页面分析失败: {e}[/]")

    async def analyze_license_site(self):
        """分析生产许可证网站"""
        rprint("[bold cyan]分析生产许可证网站...[/]")

        try:
            # 访问生产许可证网站
            self.drission_page.get('http://scxk.nmpa.gov.cn:81/xk/')
            time.sleep(10)

            page_info = {
                'title': self.drission_page.title,
                'url': self.drission_page.url,
                'status_code': self.get_page_status(),
                'cookies': self.get_cookies_analysis(),
                'local_storage': self.get_local_storage(),
                'session_storage': self.get_session_storage(),
                'scripts': self.get_page_scripts(),
                'forms': self.get_page_forms()
            }

            self.analysis_results['pages']['license'] = page_info
            rprint(f"[green]✓ 生产许可证网站分析完成: {page_info['title']}[/]")

            # 查找关键JavaScript函数
            await self.find_key_javascript_functions()

            # 分析API调用模式
            await self.analyze_api_patterns()

        except Exception as e:
            rprint(f"[red]生产许可证网站分析失败: {e}[/]")

    def get_cookies_analysis(self) -> Dict:
        """分析Cookies"""
        try:
            cookies = self.drission_page.cookies
            cookie_analysis = {
                'count': len(cookies),
                'cookies': []
            }

            for cookie in cookies:
                cookie_analysis['cookies'].append({
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'domain': cookie.get('domain', ''),
                    'path': cookie.get('path', ''),
                    'httpOnly': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False)
                })

            return cookie_analysis
        except Exception as e:
            rprint(f"[yellow]Cookie分析失败: {e}[/]")
            return {'count': 0, 'cookies': []}

    def get_local_storage(self) -> Dict:
        """获取LocalStorage"""
        try:
            return self.drission_page.run_js('return Object.assign({}, localStorage);')
        except:
            return {}

    def get_session_storage(self) -> Dict:
        """获取SessionStorage"""
        try:
            return self.drission_page.run_js('return Object.assign({}, sessionStorage);')
        except:
            return {}

    def get_page_scripts(self) -> List[str]:
        """获取页面脚本"""
        try:
            scripts = self.drission_page.eles('script')
            script_sources = []

            for script in scripts[:20]:  # 限制数量
                src = script.attr('src')
                if src:
                    script_sources.append(src)

            return script_sources
        except:
            return []

    def get_page_forms(self) -> List[Dict]:
        """获取页面表单"""
        try:
            forms = self.drission_page.eles('form')
            form_info = []

            for form in forms:
                form_data = {
                    'action': form.attr('action') or '',
                    'method': form.attr('method') or 'GET',
                    'inputs': []
                }

                inputs = form.eles('input')
                for inp in inputs:
                    form_data['inputs'].append({
                        'name': inp.attr('name') or '',
                        'type': inp.attr('type') or 'text',
                        'id': inp.attr('id') or ''
                    })

                form_info.append(form_data)

            return form_info
        except:
            return []

    def get_meta_tags(self) -> List[Dict]:
        """获取Meta标签"""
        try:
            metas = self.drission_page.eles('meta')
            meta_info = []

            for meta in metas:
                meta_info.append({
                    'name': meta.attr('name') or meta.attr('property') or '',
                    'content': meta.attr('content') or ''
                })

            return meta_info
        except:
            return []

    def get_page_status(self) -> int:
        """获取页面状态码"""
        try:
            # 通过JavaScript获取状态码
            status = self.drission_page.run_js('''
                var xhr = new XMLHttpRequest();
                xhr.open('HEAD', window.location.href, false);
                xhr.send();
                return xhr.status;
            ''')
            return status or 0
        except:
            return 0

    async def analyze_javascript_patterns(self):
        """分析JavaScript模式"""
        rprint("[blue]分析JavaScript模式...[/]")

        try:
            # 查找关键JavaScript代码
            js_patterns = {
                'sign_functions': [],
                'api_calls': [],
                'ajax_requests': [],
                'encryption': [],
                'timestamp_generation': []
            }

            # 执行JavaScript查找关键函数
            js_code = '''
            // 查找签名相关函数
            var signPatterns = [];

            // 查找包含sign、signature、md5等关键词的函数
            var scripts = document.getElementsByTagName('script');
            for (var i = 0; i < scripts.length; i++) {
                if (scripts[i].textContent) {
                    var content = scripts[i].textContent;
                    if (content.includes('sign') || content.includes('signature') ||
                        content.includes('md5') || content.includes('encrypt')) {
                        signPatterns.push({
                            type: 'script',
                            content: content.substring(0, 500) + '...',
                            index: i
                        });
                    }
                }
            }

            // 查找全局函数
            var globalFuncs = [];
            for (var key in window) {
                if (typeof window[key] === 'function' &&
                    (key.includes('sign') || key.includes('encrypt') || key.includes('hash'))) {
                    globalFuncs.push(key);
                }
            }

            return {
                signPatterns: signPatterns,
                globalFunctions: globalFuncs
            };
            '''

            result = self.drission_page.run_js(js_code)
            self.analysis_results['javascript']['patterns'] = result

            rprint(f"[green]✓ 发现 {len(result.get('globalFunctions', []))} 个可疑函数[/]")

        except Exception as e:
            rprint(f"[yellow]JavaScript模式分析失败: {e}[/]")

    async def find_api_endpoints(self):
        """查找API端点"""
        rprint("[blue]查找API端点...[/]")

        try:
            # 通过查找JavaScript中的API端点
            js_code = '''
            var endpoints = [];
            var scripts = document.getElementsByTagName('script');

            for (var i = 0; i < scripts.length; i++) {
                if (scripts[i].textContent) {
                    var content = scripts[i].textContent;
                    // 查找API端点模式
                    var urlPatterns = content.match(/https?:\\/\\/[^\\s"']+/g) || [];
                    urlPatterns.forEach(function(url) {
                        if (url.includes('api') || url.includes('data') || url.includes('search')) {
                            endpoints.push({
                                url: url,
                                context: 'script_' + i
                            });
                        }
                    });
                }
            }

            return endpoints;
            '''

            endpoints = self.drission_page.run_js(js_code)
            self.analysis_results['apis']['endpoints'] = endpoints

            rprint(f"[green]✓ 发现 {len(endpoints)} 个API端点[/]")

        except Exception as e:
            rprint(f"[yellow]API端点查找失败: {e}[/]")

    async def simulate_user_interactions(self):
        """模拟用户交互"""
        rprint("[blue]模拟用户交互...[/]")

        try:
            # 滚动页面
            self.drission_page.run_js('window.scrollTo(0, document.body.scrollHeight/2);')
            time.sleep(2)

            # 点击可能的搜索按钮
            search_buttons = self.drission_page.eles('button, input[type="button"], a')
            for btn in search_buttons[:5]:
                text = btn.text.lower()
                if '搜索' in text or 'search' in text or '查询' in text:
                    rprint(f"[blue]找到搜索按钮: {text}[/]")
                    # 不实际点击，只记录
                    break

        except Exception as e:
            rprint(f"[yellow]用户交互模拟失败: {e}[/]")

    async def monitor_network_requests(self):
        """监听网络请求"""
        rprint("[blue]监听网络请求...[/]")

        try:
            # 设置网络监听
            self.drission_page.run_js('''
                // 拦截XMLHttpRequest
                var originalXHR = window.XMLHttpRequest;
                var interceptedRequests = [];

                window.XMLHttpRequest = function() {
                    var xhr = new originalXHR();
                    var originalOpen = xhr.open;
                    var originalSend = xhr.send;

                    xhr.open = function(method, url, async, user, pass) {
                        this._method = method;
                        this._url = url;
                        return originalOpen.call(this, method, url, async, user, pass);
                    };

                    xhr.send = function(data) {
                        interceptedRequests.push({
                            method: this._method,
                            url: this._url,
                            data: data,
                            timestamp: Date.now()
                        });
                        return originalSend.call(this, data);
                    };

                    return xhr;
                };

                window.interceptedRequests = interceptedRequests;
            ''')

            # 等待一段时间收集请求
            time.sleep(5)

            # 获取拦截的请求
            requests = self.drission_page.run_js('return window.interceptedRequests || [];')
            self.analysis_results['apis']['requests'] = requests

            rprint(f"[green]✓ 拦截到 {len(requests)} 个网络请求[/]")

        except Exception as e:
            rprint(f"[yellow]网络请求监听失败: {e}[/]")

    async def find_key_javascript_functions(self):
        """查找关键JavaScript函数"""
        rprint("[blue]查找关键JavaScript函数...[/]")

        try:
            # 查找特定的JavaScript函数
            js_code = '''
            var keyFunctions = {};

            // 查找签名函数
            if (typeof generateSign === 'function') {
                keyFunctions.generateSign = generateSign.toString();
            }

            // 查找加密函数
            if (typeof encrypt === 'function') {
                keyFunctions.encrypt = encrypt.toString();
            }

            // 查找时间戳生成
            if (typeof getTimestamp === 'function') {
                keyFunctions.getTimestamp = getTimestamp.toString();
            }

            // 查找所有全局函数中包含关键词的
            var suspiciousFuncs = [];
            for (var key in window) {
                if (typeof window[key] === 'function') {
                    var funcStr = window[key].toString();
                    if (funcStr.includes('sign') || funcStr.includes('encrypt') ||
                        funcStr.includes('timestamp') || funcStr.includes('md5')) {
                        suspiciousFuncs.push({
                            name: key,
                            code: funcStr.substring(0, 200) + '...'
                        });
                    }
                }
            }

            keyFunctions.suspicious = suspiciousFuncs;

            return keyFunctions;
            '''

            functions = self.drission_page.run_js(js_code)
            self.analysis_results['javascript']['functions'] = functions

            rprint(f"[green]✓ 发现 {len(functions.get('suspicious', []))} 个可疑函数[/]")

        except Exception as e:
            rprint(f"[yellow]关键函数查找失败: {e}[/]")

    async def analyze_api_patterns(self):
        """分析API调用模式"""
        rprint("[blue]分析API调用模式...[/]")

        try:
            # 查找API调用相关的代码
            js_code = '''
            var apiPatterns = {
                ajaxCalls: [],
                fetchCalls: [],
                formSubmissions: []
            };

            // 查找AJAX调用
            var scripts = document.getElementsByTagName('script');
            for (var i = 0; i < scripts.length; i++) {
                if (scripts[i].textContent) {
                    var content = scripts[i].textContent;

                    // 查找$.ajax调用
                    var ajaxMatches = content.match(/\\$\\.ajax\\([^)]+\\)/g);
                    if (ajaxMatches) {
                        apiPatterns.ajaxCalls = apiPatterns.ajaxCalls.concat(ajaxMatches);
                    }

                    // 查找fetch调用
                    var fetchMatches = content.match(/fetch\\([^)]+\\)/g);
                    if (fetchMatches) {
                        apiPatterns.fetchCalls = apiPatterns.fetchCalls.concat(fetchMatches);
                    }
                }
            }

            return apiPatterns;
            '''

            patterns = self.drission_page.run_js(js_code)
            self.analysis_results['apis']['patterns'] = patterns

            rprint(f"[green]✓ 分析了 {len(patterns.get('ajaxCalls', []))} 个AJAX调用[/]")

        except Exception as e:
            rprint(f"[yellow]API模式分析失败: {e}[/]")

    async def stop(self):
        """停止分析器"""
        if self.drission_page:
            try:
                self.drission_page.quit()
            except:
                pass

    def save_analysis_results(self, filename: str = 'nmpa_live_analysis.json'):
        """保存分析结果"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            rprint(f"[green]✓ 分析结果已保存到 {filename}[/]")
        except Exception as e:
            rprint(f"[red]保存分析结果失败: {e}[/]")

async def run_live_analysis():
    """运行实时分析"""
    analyzer = LiveNMPAAnalyzer()

    try:
        if await analyzer.start():
            # 分析各个页面
            await analyzer.analyze_nmpa_main_site()
            await analyzer.analyze_data_search_page()
            await analyzer.analyze_license_site()

            # 保存结果
            analyzer.save_analysis_results()

            # 显示摘要
            rprint("\n[bold green]=== NMPA网站分析摘要 ===[/]")
            pages = analyzer.analysis_results.get('pages', {})
            for page_name, page_info in pages.items():
                rprint(f"[cyan]页面:[/] {page_name}")
                rprint(f"  - 标题: {page_info.get('title', 'N/A')}")
                rprint(f"  - Cookies: {page_info.get('cookies', {}).get('count', 0)}")
                rprint(f"  - 脚本: {len(page_info.get('scripts', []))}")
                rprint(f"  - 表单: {len(page_info.get('forms', []))}")

            apis = analyzer.analysis_results.get('apis', {})
            rprint(f"[cyan]API端点:[/] {len(apis.get('endpoints', []))}")
            rprint(f"[cyan]网络请求:[/] {len(apis.get('requests', []))}")

            js = analyzer.analysis_results.get('javascript', {})
            functions = js.get('functions', {})
            rprint(f"[cyan]可疑函数:[/] {len(functions.get('suspicious', []))}")

    finally:
        await analyzer.stop()

if __name__ == "__main__":
    asyncio.run(run_live_analysis())