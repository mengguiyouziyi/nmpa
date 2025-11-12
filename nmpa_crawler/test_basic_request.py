#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基础HTTP请求，找出绕过412错误的方法
"""

import requests
import time
import random
import json
from urllib.parse import urljoin

def test_basic_requests():
    """测试不同的请求方法"""
    base_url = "https://www.nmpa.gov.cn"
    search_url = urljoin(base_url, "/datasearch/data/nmpadata/search")

    # 真实参数
    params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "isSenior": "N",
        "searchValue": "国药准字H",
        "pageNum": 1,
        "pageSize": 10
    }

    # 测试不同的User-Agent
    user_agents = [
        # 真实浏览器
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

        # 移动设备
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",

        # 较老版本
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    # 测试不同的请求头组合
    header_sets = [
        # 最小请求头
        {
            "User-Agent": user_agents[0],
            "Accept": "application/json, text/plain, */*",
        },

        # 标准浏览器请求头
        {
            "User-Agent": user_agents[0],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nmpa.gov.cn/datasearch/search-result.html",
        },

        # 完整请求头（模拟真实抓包）
        {
            "User-Agent": user_agents[0],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nmpa.gov.cn/datasearch/search-result.html",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Google Chrome";v="120", "Not?A_Brand";v="8", "Chromium";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        },

        # 移动设备请求头
        {
            "User-Agent": user_agents[3],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nmpa.gov.cn/datasearch/search-result.html",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Google Chrome";v="120", "Not?A_Brand";v="8", "Chromium";v="120"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
        }
    ]

    print("🔍 测试基础HTTP请求以绕过412错误")
    print(f"目标URL: {search_url}")
    print(f"测试参数: {params}")
    print()

    success_count = 0
    total_tests = len(user_agents) * len(header_sets)

    for i, ua in enumerate(user_agents):
        for j, headers in enumerate(header_sets):
            print(f"--- 测试 {i*len(header_sets) + j + 1}/{total_tests}: User-Agent {i+1}, 请求头 {j+1} ---")

            # 更新User-Agent
            test_headers = headers.copy()
            test_headers["User-Agent"] = ua

            try:
                # 添加随机延迟
                time.sleep(random.uniform(1, 3))

                # 发起请求
                response = requests.get(search_url, params=params, headers=test_headers, timeout=15)

                print(f"状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")

                if response.status_code == 200:
                    print("✅ 请求成功!")
                    try:
                        data = response.json()
                        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                        success_count += 1

                        # 如果成功，保存这个配置
                        with open("successful_config.json", "w", encoding="utf-8") as f:
                            json.dump({
                                "headers": test_headers,
                                "params": params,
                                "url": search_url,
                                "response_sample": data
                            }, f, ensure_ascii=False, indent=2)
                        print("💾 成功配置已保存到 successful_config.json")

                    except json.JSONDecodeError:
                        print(f"响应内容（非JSON）: {response.text[:200]}...")

                elif response.status_code == 412:
                    print("❌ 412 Precondition Failed - 签名或反爬检测")
                    print(f"响应内容: {response.text[:200]}...")

                elif response.status_code == 403:
                    print("❌ 403 Forbidden - 访问被拒绝")

                elif response.status_code == 404:
                    print("❌ 404 Not Found - 页面不存在")

                else:
                    print(f"⚠️ 其他状态码: {response.status_code}")
                    print(f"响应内容: {response.text[:200]}...")

            except requests.exceptions.Timeout:
                print("⏰ 请求超时")
            except requests.exceptions.ConnectionError:
                print("🌐 连接错误")
            except Exception as e:
                print(f"❌ 请求异常: {e}")

            print()

    print("="*60)
    print(f"📊 测试总结:")
    print(f"  总测试数: {total_tests}")
    print(f"  成功数: {success_count}")
    print(f"  成功率: {success_count/total_tests*100:.1f}%")

    if success_count > 0:
        print("✅ 找到了可用的请求配置!")
        print("📁 查看 successful_config.json 获取成功的请求配置")
    else:
        print("❌ 所有请求都失败了")
        print("💡 可能的原因:")
        print("   1. 网站有严格的反爬机制")
        print("   2. 需要特定的签名算法")
        print("   3. 需要Cookie或Session")
        print("   4. IP被限制")

if __name__ == "__main__":
    test_basic_requests()