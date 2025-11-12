#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试浏览器请求，观察真实的API调用格式
"""

import json
import time
from seleniumwire import webdriver
import undetected_chromedriver as uc

def debug_browser_requests():
    """调试浏览器请求，拦截并分析网络请求"""

    # 配置Chrome选项
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

    # 创建selenium-wire选项
    seleniumwire_options = {
        'request_storage': 'memory'
    }

    print("🔍 启动浏览器调试模式...")

    # 创建driver
    driver = uc.Chrome(
        version_main=140,
        options=opts,
        seleniumwire_options=seleniumwire_options
    )

    try:
        print("📖 访问NMPA数据搜索页面...")
        driver.get("https://www.nmpa.gov.cn/datasearch/home-index.html")

        # 等待页面加载
        time.sleep(5)

        print("⏳ 等待axios加载...")
        # 等待axios加载
        for i in range(30):
            if driver.execute_script("return !!window.axios;"):
                print("✅ axios已加载")
                break
            time.sleep(1)
        else:
            print("❌ axios未加载")
            return

        print("🌐 执行搜索请求...")
        # 执行搜索请求
        js = """
        const url = '/datasearch/data/nmpadata/search';
        const params = {
            itemId: 'ff80808183cad75001840881f848179f',
            isSenior: 'N',
            searchValue: '国药准字H',
            pageNum: 1,
            pageSize: 10,
            timestamp: Date.now()
        };

        return axios.get(url, { params })
            .then(response => {
                return { data: response.data, status: response.status };
            })
            .catch(error => {
                return { error: error.message, response: error.response?.data };
            });
        """

        result = driver.execute_async_script("""
            const done = arguments[arguments.length - 1];
            (async () => {
                try {
                    """ + js + """
                } catch(err) {
                    done({error: String(err)});
                }
            })();
        """)

        print(f"📊 搜索结果: {result}")

        # 检查拦截的请求
        print("\n🔍 分析拦截的网络请求...")
        requests = driver.requests

        nmpa_requests = []
        for request in requests:
            if 'nmpa.gov.cn' in request.url and 'search' in request.url:
                nmpa_requests.append(request)

        print(f"📋 找到 {len(nmpa_requests)} 个NMPA搜索请求")

        for i, request in enumerate(nmpa_requests):
            print(f"\n--- 请求 {i+1} ---")
            print(f"URL: {request.url}")
            print(f"方法: {request.method}")
            print(f"状态码: {request.response.status_code if request.response else 'N/A'}")

            if request.headers:
                print("请求头:")
                for key, value in request.headers.items():
                    if key.lower() in ['user-agent', 'accept', 'referer', 'sign', 'timestamp']:
                        print(f"  {key}: {value}")

            if request.response and request.response.headers:
                print("响应头:")
                for key, value in request.response.headers.items():
                    if key.lower() in ['content-type', 'set-cookie']:
                        print(f"  {key}: {value}")

            if request.response:
                try:
                    response_text = request.response.body.decode('utf-8')
                    print(f"响应内容: {response_text[:500]}...")
                except:
                    print("响应内容: [无法解码]")

        # 尝试手动添加签名的请求
        print("\n🧪 尝试手动签名请求...")

        # 先获取当前时间戳
        timestamp = driver.execute_script("return Date.now();")
        print(f"当前时间戳: {timestamp}")

        # 尝试不同的签名组合
        test_signs = [
            "test_sign",
            "nmpa_sign",
            hashlib.md5(f"ff80808183cad75001840881f848179fN国药准字H110{timestamp}nmpa".encode()).hexdigest(),
        ]

        for i, sign in enumerate(test_signs):
            print(f"\n--- 测试签名 {i+1}: {sign[:20]}... ---")

            js_with_sign = f"""
            const url = '/datasearch/data/nmpadata/search';
            const params = {{
                itemId: 'ff80808183cad75001840881f848179f',
                isSenior: 'N',
                searchValue: '国药准字H',
                pageNum: 1,
                pageSize: 10,
                timestamp: {timestamp},
                sign: '{sign}'
            }};

            return axios.get(url, {{ params }})
                .then(response => {{
                    return {{ data: response.data, status: response.status }};
                }})
                .catch(error => {{
                    return {{ error: error.message, response: error.response?.data }};
                }});
            """

            result = driver.execute_async_script(f"""
                const done = arguments[arguments.length - 1];
                (async () => {{
                    try {{
                        """ + js_with_sign + """
                    }} catch(err) {{
                        done({{error: String(err)}});
                    }}
                }})();
            """)

            print(f"结果: {result}")

    finally:
        driver.quit()
        print("\n✅ 调试完成")

if __name__ == "__main__":
    import hashlib
    debug_browser_requests()