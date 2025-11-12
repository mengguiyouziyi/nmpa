#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_nmpa_access():
    print("开始测试NMPA网站访问...")

    # 配置Chrome选项
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-images")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
    options.add_argument("--accept-language=zh-CN,zh;q=0.9,en;q=0.8")
    options.add_argument("--referer=https://www.nmpa.gov.cn/")

    try:
        print("启动Chrome浏览器...")
        driver = uc.Chrome(version_main=140, options=options)

        print("访问NMPA数据查询页面...")
        url = "https://www.nmpa.gov.cn/datasearch/home-index.html"
        driver.get(url)

        print("等待页面加载...")
        # 等待页面标题加载
        WebDriverWait(driver, 30).until(
            lambda d: d.title != ""
        )

        print(f"页面标题: {driver.title}")
        print(f"当前URL: {driver.current_url}")

        # 检查是否有axios
        try:
            has_axios = driver.execute_script("return !!window.axios;")
            print(f"页面是否有axios: {has_axios}")
        except Exception as e:
            print(f"检查axios时出错: {e}")

        # 检查页面内容
        try:
            page_source_length = len(driver.page_source)
            print(f"页面源代码长度: {page_source_length} 字符")

            # 检查是否包含关键内容
            if "数据查询" in driver.page_source:
                print("✅ 页面包含'数据查询'内容")
            else:
                print("❌ 页面不包含'数据查询'内容")

            if "国家药品监督管理局" in driver.page_source:
                print("✅ 页面包含'国家药品监督管理局'内容")
            else:
                print("❌ 页面不包含'国家药品监督管理局'内容")

        except Exception as e:
            print(f"检查页面内容时出错: {e}")

        print("测试完成！")
        driver.quit()

    except Exception as e:
        print(f"测试失败: {e}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    test_nmpa_access()