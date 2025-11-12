# -*- coding: utf-8 -*-
"""
配置常量 - 完全复制自 yiya-crawler
"""

SITE_CONFIG = {
    "nmpa": {
        "code": "LG0001",
        "domain": "www.nmpa.gov.cn",
        "secondary_domain": "nmpa.gov.cn",
        "name": "国家药品监督管理局",
        "pageList": [
            # 药品
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html", # 监管工作
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html", # 公告通知
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",# 法规文件
            "https://www.nmpa.gov.cn/yaopin/ypzhcjd/index.html", # 政策解读
            "https://www.nmpa.gov.cn/xxgk/kpzhsh/kpzhshyp/index.html", # 药品科普
            # 政策服务 - 政务服务门户首页
            "https://www.nmpa.gov.cn/zwfw/zwfwgggs/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwjfxx/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwpjfbzs/index.html",
            "https://www.nmpa.gov.cn/zwfw/pjyjzs/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwbstj/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwfwpj/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwsjxz/index.html",
            # 政策服务 - 政策资讯
            "https://www.nmpa.gov.cn/xxgk/zhcjd/index.html", # 政策解读： 图、视频
            # 网站首页
            "https://www.nmpa.gov.cn/xxgk/zhqyj/index.html" #  征求意见
        ],
        "oneTimePageList": [
            # 政策服务 - 热点服务
            "https://zwfw.nmpa.gov.cn/web/index/hotserver",# 热点服务
        ]
    }
}

SPIDER_SITE_TYPE = {
    "page": "PAGE",
    "file": "FILE"
}