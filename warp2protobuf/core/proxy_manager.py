# protobuf2openai/proxy_manager.py
import asyncio
import random
import httpx
from datetime import datetime, timedelta
from typing import Optional
import logging
import sys
import os

# 添加根目录到 Python 路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config

logger = logging.getLogger(__name__)


class AsyncProxyManager:
    """异步代理管理器"""

    def __init__(self):
        self.used_identifiers = {}
        self.lock = asyncio.Lock()

    async def cleanup_expired_identifiers(self):
        """清理过期的IP标识"""
        current_time = datetime.now()
        async with self.lock:
            expired_keys = [k for k, v in self.used_identifiers.items() if v < current_time]
            for key in expired_keys:
                del self.used_identifiers[key]

    async def get_proxy(self) -> Optional[str]:
        """获取代理IP - 从配置文件读取"""
        proxy_url = getattr(config, 'PROXY_URL', None)
        
        # 处理空字符串的情况
        if proxy_url == "":
            return None
            
        return proxy_url

    def format_proxy_for_httpx(self, proxy_str: str) -> Optional[str]:
        """格式化代理为httpx格式"""
        if not proxy_str:
            return None

        try:
            # 如果已经是完整的URL格式（http://或socks5://），直接返回
            if proxy_str.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
                return proxy_str
            
            # 否则按照旧逻辑处理（兼容性）
            if '@' in proxy_str:
                credentials, host_port = proxy_str.split('@')
                user, password = credentials.split(':')
                host, port = host_port.split(':')
                return f"socks5://{user}:{password}@{host}:{port}"
            else:
                parts = proxy_str.split(':')
                if len(parts) == 2:
                    host, port = parts
                    return f"socks5://{host}:{port}"
                else:
                    logger.error(f"代理格式无法识别: {proxy_str}")
                    return None
        except Exception as e:
            logger.error(f"格式化代理失败: {e}", exc_info=True)
            return None
