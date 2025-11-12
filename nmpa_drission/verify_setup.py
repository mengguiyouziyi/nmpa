#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMPA DrissionPage 安装验证脚本
快速验证 DrissionPage 和自动化脚本是否正常工作
"""

import sys
from DrissionPage import ChromiumPage, ChromiumOptions


def test_drission_import():
    """测试 DrissionPage 导入"""
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        print("✓ DrissionPage 导入成功")
        return True
    except ImportError as e:
        print(f"✗ DrissionPage 导入失败：{e}")
        return False


def test_browser_launch():
    """测试浏览器启动"""
    try:
        print("正在测试浏览器启动...")
        co = ChromiumOptions()
        co.headless(True)  # 无头模式用于测试
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')

        page = ChromiumPage(addr_or_opts=co)
        print("✓ 浏览器启动成功")
        page.quit()
        return True
    except Exception as e:
        print(f"✗ 浏览器启动失败：{e}")
        return False


def test_automation_import():
    """测试自动化脚本导入"""
    try:
        import automation
        print("✓ automation.py 导入成功")

        # 测试参数解析
        args = automation.parse_args(['--once'])
        print(f"✓ 参数解析成功，once={args.once}")

        # 测试 DrissionActor 实例化
        actor = automation.DrissionActor(keywords=['测试'], interval=60)
        print(f"✓ DrissionActor 创建成功，关键词={actor.keywords}")

        return True
    except Exception as e:
        print(f"✗ automation.py 测试失败：{e}")
        return False


def main():
    print("=== NMPA DrissionPage 安装验证 ===\n")

    tests = [
        ("DrissionPage 导入", test_drission_import),
        ("浏览器启动", test_browser_launch),
        ("自动化脚本", test_automation_import),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n[{passed+1}/{total}] 测试：{name}")
        if test_func():
            passed += 1
        else:
            print("  该测试失败，请检查安装配置")

    print(f"\n=== 验证结果 ===")
    print(f"通过：{passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过！可以运行自动化脚本了。")
        print("\n推荐启动命令：")
        print("python automation.py --once --log-file test.log")
        return 0
    else:
        print("❌ 存在问题，请检查失败项。")
        return 1


if __name__ == "__main__":
    sys.exit(main())