#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级签名算法破解工具
使用多种技术手段分析真实签名算法
"""

import hashlib
import hmac
import json
import time
import urllib.parse
import itertools
import base64
from sign_engine import NMPASignEngine


def analyze_real_signature():
    """分析真实签名的特征"""
    print("=== 真实签名特征分析 ===")

    real_sign = "b161b8f6d69cdcbbf0aa2dd61c5b8cc2"
    real_params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "isSenior": "N",
        "searchValue": "国药准字H",
        "pageNum": 2,
        "pageSize": 10
    }
    real_timestamp = 1760172844000

    print(f"真实签名: {real_sign}")
    print(f"签名长度: {len(real_sign)}")
    print(f"签名类型: MD5 (32位十六进制)")

    # 分析签名的可能来源
    print("\n=== 可能的签名来源分析 ===")

    # 1. 常见网站域名作为密钥
    domain_keys = [
        "nmpa.gov.cn",
        "www.nmpa.gov.cn",
        "datasearch.nmpa.gov.cn",
        "nmpa",
        "gov.cn",
        "nmpadata",
        "datasearch"
    ]

    # 2. 常见前端框架密钥
    frontend_keys = [
        "vue",
        "react",
        "angular",
        "jquery",
        "axios",
        "fetch",
        "xhr",
        "ajax"
    ]

    # 3. 时间相关密钥
    time_keys = [
        "2024",
        "2025",
        "2023",
        str(real_timestamp),
        str(int(real_timestamp / 1000)),
        str(real_timestamp)[:8],  # 前8位
        str(real_timestamp)[-8:],  # 后8位
    ]

    # 4. UUID/GUID相关
    uuid_keys = [
        "ff808081",  # itemId前8位
        real_params['itemId'][:8],
        real_params['itemId'][-8:],
        "83cad750",  # itemId中间部分
    ]

    # 5. 中英文关键词
    keyword_keys = [
        "药品",
        "药监",
        "查询",
        "search",
        "query",
        "medicine",
        "drug",
        "medical",
        "approval",
        "administration"
    ]

    # 6. 技术关键词
    tech_keys = [
        "api",
        "web",
        "http",
        "https",
        "json",
        "data",
        "list",
        "page",
        "token",
        "auth",
        "sign",
        "key",
        "secret"
    ]

    all_keys = domain_keys + frontend_keys + time_keys + uuid_keys + keyword_keys + tech_keys

    # 测试不同的签名字符串构建方式
    structures = [
        # 方式1: 直接拼接
        lambda params, ts, key: f"itemId={params['itemId']}isSenior={params['isSenior']}searchValue={params['searchValue']}pageNum={params['pageNum']}pageSize={params['pageSize']}timestamp={ts}{key}",

        # 方式2: &分隔
        lambda params, ts, key: f"itemId={params['itemId']}&isSenior={params['isSenior']}&searchValue={params['searchValue']}&pageNum={params['pageNum']}&pageSize={params['pageSize']}&timestamp={ts}&key={key}",

        # 方式3: 密钥在前
        lambda params, ts, key: f"{key}itemId={params['itemId']}isSenior={params['isSenior']}searchValue={params['searchValue']}pageNum={params['pageNum']}pageSize={params['pageSize']}timestamp={ts}",

        # 方式4: JSON格式
        lambda params, ts, key: json.dumps([params['itemId'], params['isSenior'], params['searchValue'], params['pageNum'], params['pageSize'], ts, key], separators=(',', ':')),

        # 方式5: 只核心参数
        lambda params, ts, key: f"itemId={params['itemId']}searchValue={params['searchValue']}timestamp={ts}{key}",

        # 方式6: 字母排序
        lambda params, ts, key: f"itemId={params['itemId']}&pageNum={params['pageNum']}&pageSize={params['pageSize']}&searchValue={params['searchValue']}&timestamp={ts}&isSenior={params['isSenior']}&key={key}",

        # 方式7: 时间戳在前
        lambda params, ts, key: f"timestamp={ts}itemId={params['itemId']}isSenior={params['isSenior']}searchValue={params['searchValue']}pageNum={params['pageNum']}pageSize={params['pageSize']}{key}",
    ]

    print(f"\n测试 {len(all_keys)} 个密钥 x {len(structures)} 种结构 = {len(all_keys) * len(structures)} 种组合")

    found_matches = []

    for i, structure_func in enumerate(structures):
        print(f"\n--- 结构 {i+1} ---")

        for key in all_keys:
            sign_string = structure_func(real_params, real_timestamp, key)

            # 测试MD5
            md5_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
            if md5_sign == real_sign:
                found_matches.append({
                    'algorithm': 'MD5',
                    'structure': i+1,
                    'key': key,
                    'sign_string': sign_string,
                    'method': f'结构{i+1}+MD5'
                })
                print(f"🎉 MD5匹配! 密钥: {key}")
                print(f"   签名字符串: {sign_string}")
                continue

            # 测试HMAC-MD5
            try:
                hmac_sign = hmac.new(key.encode('utf-8'), sign_string.encode('utf-8'), hashlib.md5).hexdigest()
                if hmac_sign == real_sign:
                    found_matches.append({
                        'algorithm': 'HMAC-MD5',
                        'structure': i+1,
                        'key': key,
                        'sign_string': sign_string,
                        'method': f'结构{i+1}+HMAC-MD5'
                    })
                    print(f"🎉 HMAC-MD5匹配! 密钥: {key}")
                    print(f"   签名字符串: {sign_string}")
                    continue
            except:
                pass

            # 测试SHA1
            sha1_sign = hashlib.sha1(sign_string.encode('utf-8')).hexdigest()
            if sha1_sign == real_sign:
                found_matches.append({
                    'algorithm': 'SHA1',
                    'structure': i+1,
                    'key': key,
                    'sign_string': sign_string,
                    'method': f'结构{i+1}+SHA1'
                })
                print(f"🎉 SHA1匹配! 密钥: {key}")
                print(f"   签名字符串: {sign_string}")
                continue

    print(f"\n=== 搜索结果 ===")
    if found_matches:
        print(f"找到 {len(found_matches)} 个匹配:")
        for match in found_matches:
            print(f"  ✅ {match['method']}")
            print(f"     密钥: {match['key']}")
            print(f"     签名字符串: {match['sign_string'][:100]}...")
            print()
    else:
        print("❌ 未找到匹配的算法组合")
        print("\n可能的解决方案:")
        print("1. 签名算法包含更复杂的逻辑（如加密、Base64等）")
        print("2. 密钥不在常见词库中")
        print("3. 签名使用了动态生成的密钥")
        print("4. 签名算法包含随机数或其他动态因素")

    return found_matches


def try_complex_algorithms():
    """尝试更复杂的算法组合"""
    print("\n=== 尝试复杂算法 ===")

    real_sign = "b161b8f6d69cdcbbf0aa2dd61c5b8cc2"
    real_params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "isSenior": "N",
        "searchValue": "国药准字H",
        "pageNum": 2,
        "pageSize": 10
    }
    real_timestamp = 1760172844000

    # 尝试Base64编码
    base_string = f"itemId={real_params['itemId']}isSenior={real_params['isSenior']}searchValue={real_params['searchValue']}pageNum={real_params['pageNum']}pageSize={real_params['pageSize']}timestamp={real_timestamp}"

    # Base64 + MD5
    try:
        b64_string = base64.b64encode(base_string.encode('utf-8')).decode('utf-8')
        for suffix in ['', 'nmpa', 'key', 'secret']:
            test_string = b64_string + suffix
            md5_sign = hashlib.md5(test_string.encode('utf-8')).hexdigest()
            if md5_sign == real_sign:
                print(f"🎉 Base64+MD5匹配! 后缀: {suffix}")
                return True
    except:
        pass

    # URL编码 + MD5
    try:
        url_string = urllib.parse.quote(base_string, safe='')
        for suffix in ['', 'nmpa', 'key', 'secret']:
            test_string = url_string + suffix
            md5_sign = hashlib.md5(test_string.encode('utf-8')).hexdigest()
            if md5_sign == real_sign:
                print(f"🎉 URL编码+MD5匹配! 后缀: {suffix}")
                return True
    except:
        pass

    # 双重MD5
    first_md5 = hashlib.md5(base_string.encode('utf-8')).hexdigest()
    for suffix in ['', 'nmpa', 'key', 'secret']:
        test_string = first_md5 + suffix
        second_md5 = hashlib.md5(test_string.encode('utf-8')).hexdigest()
        if second_md5 == real_sign:
            print(f"🎉 双重MD5匹配! 后缀: {suffix}")
            return True

    # MD5 + Base64
    md5_hash = hashlib.md5(base_string.encode('utf-8')).digest()
    try:
        b64_hash = base64.b64encode(md5_hash).decode('utf-8')
        if b64_hash.replace('+', '').replace('/', '').replace('=', '')[:32] == real_sign:
            print(f"🎉 MD5+Base64匹配!")
            return True
    except:
        pass

    print("❌ 复杂算法也未找到匹配")
    return False


def reverse_engineer_pattern():
    """逆向工程分析签名模式"""
    print("\n=== 逆向工程分析 ===")

    real_sign = "b161b8f6d69cdcbbf0aa2dd61c5b8cc2"

    # 分析签名的字符分布
    print(f"签名: {real_sign}")
    print(f"字符分析:")
    print(f"  数字: {sum(c.isdigit() for c in real_sign)}")
    print(f"  字母: {sum(c.isalpha() for c in real_sign)}")
    print(f"  a-f: {sum(c in 'abcdef' for c in real_sign)}")
    print(f"  0-9: {sum(c in '0123456789' for c in real_sign)}")

    # 尝试找到签名的模式
    print(f"\n签名分段:")
    print(f"  前8位: {real_sign[:8]}")
    print(f"  中16位: {real_sign[8:24]}")
    print(f"  后8位: {real_sign[24:]}")

    # 常见的MD5前缀/后缀
    common_prefixes = ["c4ca4238", "e10adc39", "202cb962"]  # "0", "123456", "123"的MD5
    common_suffixes = ["d41d8cd98f00b204e9800998ecf8427e", "0cc175b9c0f1b6a831c399e269772661"]  # "", "a"的MD5

    print(f"\n是否匹配常见模式:")
    for prefix in common_prefixes:
        if real_sign.startswith(prefix):
            print(f"  ✅ 匹配前缀: {prefix}")

    for suffix in common_suffixes:
        if real_sign.endswith(suffix):
            print(f"  ✅ 匹配后缀: {suffix}")


if __name__ == "__main__":
    print("🔍 启动高级签名算法破解分析")

    # 执行分析
    matches = analyze_real_signature()

    if not matches:
        try_complex_algorithms()
        reverse_engineer_pattern()

    print("\n" + "="*50)
    print("📋 分析总结:")
    if matches:
        print(f"✅ 成功找到 {len(matches)} 种签名算法")
        print("🎯 下一步: 集成找到的算法到 sign_engine.py")
    else:
        print("❌ 未能破解签名算法")
        print("💡 建议:")
        print("   1. 获取更多真实API样本")
        print("   2. 分析网站的JavaScript代码")
        print("   3. 使用浏览器调试工具监控签名生成过程")
        print("   4. 尝试其他技术路线（如浏览器自动化）")