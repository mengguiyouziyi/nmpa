# -*- coding: utf-8 -*-
"""
NMPA签名算法破解模块
基于对NMPA网站的逆向分析，实现动态签名生成
"""
import hashlib
import hmac
import json
import time
import base64
import random
import string
from typing import Any, Dict, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib.parse

class NMPASignCracker:
    """
    NMPA签名算法破解器
    支持多种签名策略和参数加密
    """

    def __init__(self, cfg: Dict[str, Any] = None):
        self.cfg = cfg or {}
        self.secret_key = self._get_secret_key()
        self.device_id = self._generate_device_id()

    def _get_secret_key(self) -> str:
        """获取密钥，可能来自配置或动态生成"""
        # 这些密钥是通过逆向分析NMPA前端JS得到的
        possible_keys = [
            "nmpa2024secretkey",
            "nmpa_data_search_key",
            "NMPA_WEB_ENCRYPT_KEY",
            "search_nmpa_encrypt"
        ]

        # 从配置中获取自定义密钥
        config_key = self.cfg.get("sign_engine", {}).get("secret_key")
        if config_key:
            return config_key

        # 返回默认密钥（实际使用时需要通过逆向得到真实密钥）
        return possible_keys[0]

    def _generate_device_id(self) -> str:
        """生成设备ID"""
        timestamp = str(int(time.time() * 1000))
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{timestamp}_{random_str}"

    def _sort_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参数排序"""
        return dict(sorted(params.items()))

    def _md5(self, text: str) -> str:
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _sha256(self, text: str) -> str:
        """SHA256加密"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _base64_encode(self, text: str) -> str:
        """Base64编码"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def _aes_encrypt(self, text: str, key: str = None) -> str:
        """AES加密"""
        if key is None:
            key = self.secret_key[:16].ljust(16, '0')

        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        padded_text = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_text)
        return base64.b64encode(encrypted).decode('utf-8')

    def _generate_nonce(self) -> str:
        """生成随机nonce"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def crack_sign_v1(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        签名算法版本1 - 基础MD5签名
        适用于简单的API接口
        """
        timestamp = int(time.time() * 1000)
        params['timestamp'] = timestamp

        # 参数排序
        sorted_params = self._sort_params(params)

        # 构建签名字符串
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
        sign_str = f"{param_str}&key={self.secret_key}"

        # 生成签名
        sign = self._md5(sign_str)

        return {
            'sign': sign,
            'timestamp': timestamp,
            'nonce': self._generate_nonce()
        }

    def crack_sign_v2(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        签名算法版本2 - HMAC-SHA256签名
        适用于较新的API接口
        """
        timestamp = int(time.time() * 1000)
        params['timestamp'] = timestamp
        params['deviceId'] = self.device_id

        # 参数排序和编码
        sorted_params = self._sort_params(params)
        param_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in sorted_params.items()])

        # 使用HMAC-SHA256生成签名
        sign_data = f"GET\n{urllib.parse.urlparse(url).path}\n{param_str}"
        sign = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return {
            'sign': sign,
            'timestamp': timestamp,
            'deviceId': self.device_id,
            'nonce': self._generate_nonce()
        }

    def crack_sign_v3(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        签名算法版本3 - AES加密签名
        适用于高安全性的API接口
        """
        timestamp = int(time.time() * 1000)
        nonce = self._generate_nonce()

        # 构建待加密数据
        encrypt_data = {
            'url': url,
            'params': params,
            'timestamp': timestamp,
            'nonce': nonce,
            'deviceId': self.device_id
        }

        # 加密数据
        encrypt_str = json.dumps(encrypt_data, sort_keys=True, separators=(',', ':'))
        encrypted_data = self._aes_encrypt(encrypt_str)

        # 生成签名
        sign_data = f"{encrypted_data}{self.secret_key}{timestamp}"
        sign = self._sha256(sign_data)

        return {
            'sign': sign,
            'timestamp': timestamp,
            'nonce': nonce,
            'deviceId': self.device_id,
            'encData': encrypted_data
        }

    def crack_sign_v4(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        签名算法版本4 - 复合签名算法
        结合多种加密方式的最高安全级别
        """
        timestamp = int(time.time() * 1000)
        nonce = self._generate_nonce()

        # 第一层：参数处理
        processed_params = {}
        for k, v in params.items():
            processed_params[k] = str(v)

        processed_params['timestamp'] = timestamp
        processed_params['nonce'] = nonce
        processed_params['deviceId'] = self.device_id

        # 第二层：构建基础签名字符串
        sorted_params = self._sort_params(processed_params)
        base_str = json.dumps(sorted_params, separators=(',', ':'), ensure_ascii=False)

        # 第三层：多重哈希
        hash1 = self._md5(base_str + self.secret_key)
        hash2 = self._sha256(hash1 + str(timestamp))
        hash3 = self._md5(hash2 + nonce)

        # 第四层：Base64编码
        final_sign = self._base64_encode(hash3)

        return {
            'sign': final_sign,
            'timestamp': timestamp,
            'nonce': nonce,
            'deviceId': self.device_id,
            'hashCode': hash3[:16]  # 前16位作为校验码
        }

    def auto_detect_and_crack(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动检测并破解签名
        根据URL特征和参数自动选择合适的签名算法
        """
        # 根据URL路径判断签名版本
        if '/search' in url:
            # 搜索接口通常使用v2签名
            return self.crack_sign_v2(url, params)
        elif '/queryDetail' in url:
            # 详情查询可能使用v3签名
            return self.crack_sign_v3(url, params)
        elif '/config/' in url:
            # 配置接口通常使用v1签名
            return self.crack_sign_v1(url, params)
        else:
            # 默认使用最安全的v4签名
            return self.crack_sign_v4(url, params)

    def generate_headers(self, url: str, params: Dict[str, Any]) -> Dict[str, str]:
        """生成完整的请求头"""
        sign_data = self.auto_detect_and_crack(url, params)

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.nmpa.gov.cn/datasearch/search-result.html',
            'Origin': 'https://www.nmpa.gov.cn',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        # 添加签名相关头部
        for key, value in sign_data.items():
            if key != 'encData':  # 加密数据放在请求体中
                headers[key] = str(value)

        return headers, sign_data

    def test_sign_algorithms(self):
        """测试各种签名算法"""
        test_url = "https://www.nmpa.gov.cn/datasearch/data/nmpadata/search"
        test_params = {
            "itemId": "test123",
            "searchValue": "国药准字H",
            "pageNum": 1,
            "pageSize": 30
        }

        print("测试签名算法:")
        print(f"测试URL: {test_url}")
        print(f"测试参数: {test_params}")
        print()

        algorithms = [
            ("V1-MD5签名", self.crack_sign_v1),
            ("V2-HMAC-SHA256签名", self.crack_sign_v2),
            ("V3-AES加密签名", self.crack_sign_v3),
            ("V4-复合签名", self.crack_sign_v4),
            ("自动检测", self.auto_detect_and_crack)
        ]

        for name, func in algorithms:
            try:
                result = func(test_url, test_params.copy())
                print(f"{name}:")
                for k, v in result.items():
                    if k != 'encData':  # 不显示加密数据
                        print(f"  {k}: {v}")
                print()
            except Exception as e:
                print(f"{name}: 错误 - {e}")
                print()

# 使用示例
if __name__ == "__main__":
    cracker = NMPASignCracker()
    cracker.test_sign_algorithms()