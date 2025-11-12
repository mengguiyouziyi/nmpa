#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试手动搜索，模拟真实用户操作
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

def test_manual_search():
    """测试手动搜索，模拟真实用户操作"""

    # 配置Chrome选项
    opts = uc.ChromeOptions()
    # opts.add_argument("--headless=new")  # 先不使用无头模式，便于观察
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    print("🔍 启动浏览器进行手动搜索测试...")

    # 创建driver
    driver = uc.Chrome(version_main=140, options=opts)

    try:
        print("📖 访问NMPA数据搜索页面...")
        driver.get("https://www.nmpa.gov.cn/datasearch/home-index.html")

        # 等待页面加载
        time.sleep(5)

        print("🔍 查找搜索相关元素...")

        # 查找搜索框
        try:
            # 尝试多种可能的搜索框定位方式
            search_inputs = []

            # 通过各种属性查找搜索框
            selectors = [
                "input[placeholder*='搜索']",
                "input[placeholder*='输入']",
                "input[type='text']",
                ".search-input",
                "#searchInput",
                "input[name*='search']",
                "input[aria-label*='搜索']"
            ]

            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_inputs.append(element)
                            print(f"找到搜索框: {selector}")
                except:
                    continue

            if not search_inputs:
                print("❌ 未找到搜索框，尝试其他方式...")
                # 查找所有input元素
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for i, inp in enumerate(all_inputs):
                    try:
                        if inp.is_displayed() and inp.is_enabled():
                            print(f"Input {i}: type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}, name={inp.get_attribute('name')}")
                    except:
                        continue
            else:
                # 使用第一个找到的搜索框
                search_input = search_inputs[0]
                print(f"✅ 使用搜索框: {search_input.get_attribute('outerHTML')[:100]}...")

                # 输入搜索内容
                search_value = "国药准字H"
                print(f"📝 输入搜索内容: {search_value}")

                search_input.clear()
                time.sleep(1)
                search_input.send_keys(search_value)
                time.sleep(1)

                # 查找搜索按钮
                search_buttons = []
                button_selectors = [
                    "button[type='submit']",
                    ".search-btn",
                    ".btn-search",
                    "button[aria-label*='搜索']",
                    "input[type='submit']",
                    ".search-button"
                ]

                for selector in button_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                search_buttons.append(element)
                                print(f"找到搜索按钮: {selector}")
                    except:
                        continue

                if search_buttons:
                    search_button = search_buttons[0]
                    print(f"✅ 点击搜索按钮")
                    search_button.click()
                else:
                    print("⚠️ 未找到搜索按钮，尝试按Enter键")
                    search_input.send_keys(Keys.RETURN)

                # 等待搜索结果
                time.sleep(5)

                print("🔍 检查搜索结果...")
                # 查找结果相关元素
                results_selectors = [
                    ".result-item",
                    ".search-result",
                    ".data-list",
                    ".result-list",
                    "table",
                    ".table"
                ]

                found_results = False
                for selector in results_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            print(f"找到结果元素: {selector}, 数量: {len(elements)}")
                            found_results = True
                            break
                    except:
                        continue

                if not found_results:
                    print("❌ 未找到搜索结果元素")
                    # 打印当前页面的一些信息
                    print(f"当前URL: {driver.current_url}")
                    print(f"页面标题: {driver.title}")

                    # 查看是否有错误信息
                    try:
                        error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .message")
                        for error in error_elements:
                            if error.is_displayed():
                                print(f"错误信息: {error.text}")
                    except:
                        pass

                # 检查网络请求
                print("\n📊 尝试执行JavaScript搜索...")

                # 执行直接的API请求
                js_result = driver.execute_script("""
                    // 尝试直接调用API
                    return fetch('/datasearch/data/nmpadata/search', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Content-Type': 'application/json'
                        },
                        credentials: 'include'
                    }).then(response => response.json())
                    .catch(error => ({error: error.message}));
                """)

                print(f"直接API调用结果: {js_result}")

        except Exception as e:
            print(f"❌ 搜索过程出错: {e}")
            import traceback
            traceback.print_exc()

        # 等待更长时间观察
        print("\n⏳ 等待10秒进行观察...")
        time.sleep(10)

    finally:
        # 保存截图
        try:
            screenshot_path = "/home/langchao6/projects/taya/nmpa/nmpa_crawler/debug_screenshot.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 已保存截图: {screenshot_path}")
        except:
            pass

        driver.quit()
        print("\n✅ 测试完成")

if __name__ == "__main__":
    test_manual_search()