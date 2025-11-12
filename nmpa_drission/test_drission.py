#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DrissionPage 测试脚本
用于验证 DrissionPage 是否正常工作
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def test_drission_page():
    """测试 DrissionPage 基本功能"""
    try:
        print("正在配置 DrissionPage...")

        # 配置浏览器选项
        co = ChromiumOptions()
        co.headless(True)  # 无头模式，适合服务器环境
        co.no_imgs(True)   # 不加载图片，提高速度
        co.set_argument('--disable-gpu')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')

        print("正在启动 DrissionPage...")

        # 创建页面对象
        page = ChromiumPage(addr_or_opts=co)

        print("DrissionPage 启动成功！")

        # 访问一个简单的网页进行测试
        print("正在访问百度首页...")
        page.get("https://www.baidu.com")

        # 等待页面加载
        time.sleep(3)

        # 获取页面标题
        title = page.title
        print(f"页面标题：{title}")

        # 关闭浏览器
        page.quit()

        print("测试完成！DrissionPage 工作正常。")
        return True

    except Exception as e:
        print(f"测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_page():
    """简单测试是否能创建页面对象"""
    try:
        print("测试基本页面对象创建...")
        page = ChromiumPage()
        print("页面对象创建成功！")
        page.quit()
        return True
    except Exception as e:
        print(f"简单测试失败：{e}")
        return False

if __name__ == "__main__":
    print("=== DrissionPage 测试 ===")

    # 首先尝试简单测试
    print("\n=== 简单测试 ===")
    if test_simple_page():
        print("基本功能正常")
    else:
        print("基本功能异常，尝试带配置启动...")

        # 如果简单测试失败，尝试带配置的测试
        print("\n=== 配置测试 ===")
        test_drission_page()