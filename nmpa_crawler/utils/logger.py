# -*- coding: utf-8 -*-
"""
Logger 工具 - 复制自 yiya-crawler
"""

import logging
from rich.logging import RichHandler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)