# -*- coding: utf-8 -*-
import random, time, re, json, os, sys
from typing import Any, Dict, Iterable, List, Tuple, Union

def sleep_jitter(min_ms: int, max_ms: int):
    t = random.randint(min_ms, max_ms) / 1000.0
    time.sleep(t)

def deep_find_item_id(config_json: Any, keyword: str) -> str:
    """
    在 NMPA_DATA.json 中递归查找包含 `keyword` 的数据库 itemId/ID。
    返回第一个匹配的 id 字符串；若未找到，返回空串。
    """
    def _walk(node):
        if isinstance(node, dict):
            # 优先检查常见字段
            name = None
            for k in ('name', 'dbName', 'title', 'itemName', 'label', 'cnName'):
                if k in node and isinstance(node[k], str):
                    name = node[k]
                    break
            if name and keyword in name:
                # 常见 id 字段候选
                for ik in ('itemId', 'id', 'nmpaItem', 'value', 'dbId'):
                    v = node.get(ik)
                    if isinstance(v, str) and len(v) > 16:
                        return v

            # 继续递归
            for v in node.values():
                res = _walk(v)
                if res:
                    return res
        elif isinstance(node, list):
            for v in node:
                res = _walk(v)
                if res:
                    return res
        return ''
    return _walk(config_json)

def flatten_kv(obj: Any) -> Dict[str, str]:
    """
    将详情 JSON 各种结构拍平成  key -> value 形式，便于按中文字段名抽取。
    常见结构：
      - {'label':'产品名称（中文）', 'value':'阿莫西林'}
      - {'field':'productName', 'value':'阿莫西林'}
      - {'产品名称':'阿莫西林', '英文名称':'Amoxicillin'}
      - 嵌套 list / dict
    """
    out = {}

    def _walk(x):
        if isinstance(x, dict):
            # 规范化若包含 label/value
            label = x.get('label')
            value = x.get('value')
            if isinstance(label, str) and value is not None:
                out[label.strip()] = str(value).strip()
            # field+value 模式
            field = x.get('field')
            if isinstance(field, str) and value is not None:
                out[field.strip()] = str(value).strip()
            # 加入所有 str->str 的键值
            for k, v in x.items():
                if isinstance(k, str) and isinstance(v, (str, int, float)):
                    out[k.strip()] = str(v).strip()
                elif isinstance(v, (dict, list)):
                    _walk(v)
        elif isinstance(x, list):
            for it in x:
                _walk(it)
        else:
            pass
    _walk(obj)
    return out

ALIASES = {
    # 通用
    "product_name_cn": ["产品名称（中文）","产品名称","通用名称","药品名称","中文名称","中文品名"],
    "product_name_en": ["产品名称（英文）","英文名称","英文品名","英文通用名称","enProductName"],
    "brand_name_cn": ["商品名（中文）","商品名","商品名称（中文）","中文商品名"],
    "brand_name_en": ["商品名（英文）","英文商品名","商品名称（英文）","英文商品名"],
}

def pick_first(data: Dict[str,str], keys: List[str]) -> str:
    for k in keys:
        if k in data and data[k]:
            return data[k]
        # 部分站点会去掉括号
        k2 = k.replace('（','(').replace('）',')')
        if k2 in data and data[k2]:
            return data[k2]
    return ''

def extract_required_fields(detail_json: Any, dataset: str) -> Dict[str, str]:
    """
    dataset: 'domestic' or 'imported'
    根据不同库抽取需要字段。其余字段保留在 raw 里。
    """
    flat = flatten_kv(detail_json)
    if dataset == 'domestic':
        return {
            "产品名称（中文）": pick_first(flat, ALIASES["product_name_cn"]),
            "产品名称（英文）": pick_first(flat, ALIASES["product_name_en"]),
        }
    else:
        return {
            "产品名称（中文）": pick_first(flat, ALIASES["product_name_cn"]),
            "产品名称（英文）": pick_first(flat, ALIASES["product_name_en"]),
            "商品名（中文）": pick_first(flat, ALIASES["brand_name_cn"]),
            "商品名（英文）": pick_first(flat, ALIASES["brand_name_en"]),
        }
