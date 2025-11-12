#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试签名算法是否与真实API匹配
"""

import hashlib
import time
import json
import urllib.parse
from sign_engine import NMPASignEngine


def test_signature_algorithm():
    """测试签名算法"""
    print("=== NMPA签名算法测试 ===")

    # 真实抓包的参数
    real_params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "isSenior": "N",
        "searchValue": "国药准字H",
        "pageNum": 2,
        "pageSize": 10
    }

    real_timestamp = 1760172844000
    real_sign = "b161b8f6d69cdcbbf0aa2dd61c5b8cc2"

    print(f"真实请求参数:")
    for key, value in real_params.items():
        print(f"  {key}: {value}")
    print(f"真实时间戳: {real_timestamp}")
    print(f"真实签名: {real_sign}")
    print()

    # 测试我们的签名算法
    engine = NMPASignEngine()

    # 尝试不同的密钥来匹配真实签名
    test_keys = [
        "nmpa_secret_key_2024",
        "nmpa_md5_key_v1",
        "NMPA_2024_V1",
        "nmpa_2024",
        "ff80808183cad75001840881f848179f",  # 使用itemId作为密钥
        "search_2024",
        "nmpa_api_key",
        "",  # 空密钥
        "nmpa",  # 简单密钥
        "NMPA",  # 大写
        "key",  # 通用密钥
        "secret",  # 通用密钥
        "123456",  # 数字密钥
        "nmpa2024",  # 无下划线
        "NMPA_KEY",  # 下划线变体
        "nmpasecret",  # 组合词
        "NMPA_SECRET_KEY",  # 全大写
    ]

    print("测试不同密钥生成的签名:")
    for key in test_keys:
        engine.secret_keys['v1'] = key

        # 重新生成签名
        sign_string = f"itemId={real_params['itemId']}"
        sign_string += f"isSenior={real_params['isSenior']}"
        sign_string += f"searchValue={real_params['searchValue']}"
        sign_string += f"pageNum={real_params['pageNum']}"
        sign_string += f"pageSize={real_params['pageSize']}"
        sign_string += f"timestamp={real_timestamp}"
        sign_string += key

        calculated_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

        match = calculated_sign == real_sign
        print(f"  密钥: {key}")
        print(f"   计算签名: {calculated_sign}")
        print(f"  是否匹配: {'✅' if match else '❌'}")
        print()

        if match:
            print(f"🎉 找到匹配的密钥: {key}")
            break

    # 如果还没找到，尝试不同的签名字符串结构
    if not any([hashlib.md5((f"itemId={real_params['itemId']}" + f"isSenior={real_params['isSenior']}" + f"searchValue={real_params['searchValue']}" + f"pageNum={real_params['pageNum']}" + f"pageSize={real_params['pageSize']}" + f"timestamp={real_timestamp}" + key).encode('utf-8')).hexdigest() == real_sign for key in test_keys]):
        print("\n尝试不同的签名字符串结构:")

        # 尝试不同的参数顺序
        structures = [
            # 原始结构
            lambda: f"itemId={real_params['itemId']}isSenior={real_params['isSenior']}searchValue={real_params['searchValue']}pageNum={real_params['pageNum']}pageSize={real_params['pageSize']}timestamp={real_timestamp}",

            # 添加分隔符
            lambda: f"itemId={real_params['itemId']}&isSenior={real_params['isSenior']}&searchValue={real_params['searchValue']}&pageNum={real_params['pageNum']}&pageSize={real_params['pageSize']}&timestamp={real_timestamp}",

            # 参数值顺序不同
            lambda: f"timestamp={real_timestamp}itemId={real_params['itemId']}isSenior={real_params['isSenior']}searchValue={real_params['searchValue']}pageNum={real_params['pageNum']}pageSize={real_params['pageSize']}",

            # 按字母顺序排列参数
            lambda: f"itemId={real_params['itemId']}&pageNum={real_params['pageNum']}&pageSize={real_params['pageSize']}&searchValue={real_params['searchValue']}&timestamp={real_timestamp}&isSenior={real_params['isSenior']}",

            # JSON格式
            lambda: json.dumps([real_params['itemId'], real_params['isSenior'], real_params['searchValue'], real_params['pageNum'], real_params['pageSize'], real_timestamp], separators=(',', ':')),

            # 只用核心参数
            lambda: f"itemId={real_params['itemId']}searchValue={real_params['searchValue']}timestamp={real_timestamp}",

            # 使用URL编码
            lambda: f"itemId={urllib.parse.quote(real_params['itemId'])}&searchValue={urllib.parse.quote(real_params['searchValue'])}&timestamp={real_timestamp}",
        ]

        for i, structure_func in enumerate(structures):
            base_string = structure_func()
            print(f"\n结构 {i+1}: {base_string[:50]}...")

            for key in ["nmpa_secret_key_2024", "", "nmpa", "key", "secret"]:
                sign_string = base_string + key
                calculated_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
                match = calculated_sign == real_sign
                print(f"  密钥 '{key}': {calculated_sign} {'✅' if match else '❌'}")

                if match:
                    print(f"🎉 找到匹配！结构 {i+1}, 密钥: {key}")
                    return

    # 测试时间戳变化
    print("\n测试时间戳对签名的影响:")
    for i in range(3):
        timestamp = real_timestamp + i * 1000
        sign_string = f"itemId={real_params['itemId']}"
        sign_string += f"isSenior={real_params['isSenior']}"
        sign_string += f"searchValue={real_params['searchValue']}"
        sign_string += f"pageNum={real_params['pageNum']}"
        sign_string += f"pageSize={real_params['pageSize']}"
        sign_string += f"timestamp={timestamp}"
        sign_string += "nmpa_secret_key_2024"

        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        print(f"  时间戳 {timestamp}: {sign}")

    print()
    print("=== 签名算法分析完成 ===")


if __name__ == "__main__":
    test_signature_algorithm()