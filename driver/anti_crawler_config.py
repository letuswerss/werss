# === 浏览器兼容配置文件 ===

import random
import os
from typing import Dict, List, Optional

class AntiCrawlerConfig:
    """浏览器兼容配置管理类"""
    
    # 浏览器User-Agent池
    USER_AGENTS = {
        'desktop': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ],
        'mobile': [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
    }
    
    # 视口分辨率池
    VIEWPORTS = {
        'desktop': [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1600, "height": 900},
            {"width": 1280, "height": 720}
        ],
        'mobile': [
            {"width": 375, "height": 667},  # iPhone SE
            {"width": 375, "height": 812},  # iPhone X/11/12
            {"width": 414, "height": 896},  # iPhone XR/11
            {"width": 390, "height": 844},  # iPhone 12/13
            {"width": 393, "height": 851},  # Android常见
            {"width": 360, "height": 640},  # Android小屏
            {"width": 412, "height": 915}   # Android大屏
        ]
    }
    
    # HTTP请求头池
    HEADERS = {
        'accept': [
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        ],
        'accept_language': [
            "zh-CN,zh;q=0.9,en;q=0.8",
            "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        ],
        'cache_control': ["no-cache", "max-age=0", "no-store"],
        'sec_ch_ua': [
            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            '"Google Chrome";v="120", "Chromium";v="120", "Not=A?Brand";v="99"',
            '"Chromium";v="120", "Google Chrome";v="120", "Not=A?Brand";v="99"'
        ]
    }
    
    # 时区配置
    TIMEZONES = [
        "Asia/Shanghai",
        "Asia/Beijing", 
        "Asia/Hong_Kong",
        "Asia/Taipei"
    ]
    
    # 语言配置
    LOCALES = [
        "zh-CN",
        "zh-TW", 
        "zh-HK"
    ]
    
    # 颜色方案
    COLOR_SCHEMES = ["light", "dark", "no-preference"]
    
    # 动画偏好
    REDUCED_MOTIONS = ["reduce", "no-preference"]
    
    @classmethod
    def get_random_user_agent(cls, mobile: bool = False) -> str:
        """获取随机User-Agent"""
        pool = cls.USER_AGENTS['mobile'] if mobile else cls.USER_AGENTS['desktop']
        return random.choice(pool)
    
    @classmethod
    def get_random_viewport(cls, mobile: bool = False) -> Dict[str, int]:
        """获取随机视口大小"""
        pool = cls.VIEWPORTS['mobile'] if mobile else cls.VIEWPORTS['desktop']
        viewport = random.choice(pool).copy()
        # 添加随机偏移
        viewport["width"] += random.randint(-20, 20)
        viewport["height"] += random.randint(-20, 20)
        return viewport
    
    @classmethod
    def get_random_headers(cls, mobile: bool = False) -> Dict[str, str]:
        """获取随机HTTP请求头"""
        headers = {
            "Accept": random.choice(cls.HEADERS['accept']),
            "Accept-Language": random.choice(cls.HEADERS['accept_language']),
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": random.choice(cls.HEADERS['cache_control']),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": random.choice(cls.HEADERS['sec_ch_ua']),
            "Sec-Ch-Ua-Mobile": "?1" if mobile else "?0",
            "Sec-Ch-Ua-Platform": '"Android"' if mobile else '"Windows"',
            "DNT": "1",
            "Connection": "keep-alive"
        }
        
        # 移动端特殊头部
        if mobile:
            headers.update({
                "X-Requested-With": random.choice(["com.tencent.mm", "com.tencent.mobileqq", "null"]),
                "Origin": "https://mp.weixin.qq.com",
                "Referer": "https://mp.weixin.qq.com/"
            })
        
        return headers
    
    @classmethod
    def get_random_timezone(cls) -> str:
        """获取随机时区"""
        return random.choice(cls.TIMEZONES)
    
    @classmethod
    def get_random_locale(cls) -> str:
        """获取随机语言环境"""
        return random.choice(cls.LOCALES)
    
    @classmethod
    def get_random_color_scheme(cls) -> str:
        """获取随机颜色方案"""
        return random.choice(cls.COLOR_SCHEMES)
    
    @classmethod
    def get_random_reduced_motion(cls) -> str:
        """获取随机动画偏好"""
        return random.choice(cls.REDUCED_MOTIONS)
    
    @classmethod
    def get_device_scale_factor(cls) -> float:
        """获取设备缩放因子"""
        return random.choice([1.0, 1.25, 1.5, 2.0])
    
    @classmethod
    def get_random_permissions(cls) -> List[str]:
        """获取随机权限列表"""
        # Playwright支持的权限
        all_permissions = ["geolocation", "notifications"]
        num_permissions = random.randint(0, len(all_permissions))
        if num_permissions == 0:
            return []
        return random.sample(all_permissions, num_permissions)
    
    @classmethod
    def get_hardware_concurrency(cls) -> int:
        """获取随机CPU核心数"""
        return random.randint(4, 12)
    
    @classmethod
    def get_device_memory(cls) -> int:
        """获取随机设备内存"""
        return random.choice([4, 8, 16])
    
    @classmethod
    def get_screen_properties(cls) -> Dict[str, int]:
        """获取屏幕属性"""
        return {
            "width": random.choice([1920, 1366, 1440, 1536, 1600, 1280]),
            "height": random.choice([1080, 768, 900, 864, 900, 720]),
            "color_depth": 24,
            "pixel_depth": 24
        }
    
    @classmethod
    def get_connection_properties(cls) -> Dict[str, any]:
        """获取网络连接属性"""
        return {
            "effective_type": random.choice(["4g", "3g", "2g"]),
            "rtt": random.randint(50, 300),
            "downlink": round(random.uniform(1.0, 50.0), 1),
            "save_data": random.choice([True, False])
        }
    
    @classmethod
    def get_battery_properties(cls) -> Dict[str, float]:
        """获取电池属性"""
        return {
            "charging": random.choice([True, False]),
            "charging_time": random.uniform(0, 3600),
            "discharging_time": random.uniform(3600, 7200),
            "level": round(random.uniform(0.2, 1.0), 2)
        }
    
    @classmethod
    def get_anti_detection_config(cls, mobile: bool = False) -> Dict[str, any]:
        """获取完整的反检测配置"""
        return {
            "user_agent": cls.get_random_user_agent(mobile),
            "viewport": cls.get_random_viewport(mobile),
            "device_scale_factor": cls.get_device_scale_factor(),
            "is_mobile": mobile,
            "has_touch": mobile,
            "extra_http_headers": cls.get_random_headers(mobile),
            "locale": cls.get_random_locale(),
            "permissions": cls.get_random_permissions(),
            "ignore_https_errors": True,
            "bypass_csp": True,
            "color_scheme": cls.get_random_color_scheme(),
            "reduced_motion": cls.get_random_reduced_motion(),
            "screen": cls.get_screen_properties(),
        }

# 环境变量配置
ENV_CONFIG = {
    "ENABLE_STEALTH": os.getenv("ENABLE_STEALTH", "true").lower() == "true",
    "ENABLE_BEHAVIOR_SIMULATION": os.getenv("ENABLE_BEHAVIOR_SIMULATION", "true").lower() == "true",
    "ENABLE_ADVANCED_DETECTION": os.getenv("ENABLE_ADVANCED_DETECTION", "true").lower() == "true",
    "DETECTION_SENSITIVITY": float(os.getenv("DETECTION_SENSITIVITY", "0.8")),
    "MAX_DETECTION_ATTEMPTS": int(os.getenv("MAX_DETECTION_ATTEMPTS", "10")),
    "BEHAVIOR_SIMULATION_INTERVAL": int(os.getenv("BEHAVIOR_SIMULATION_INTERVAL", "2000")),
    "RANDOM_DELAY_MIN": int(os.getenv("RANDOM_DELAY_MIN", "100")),
    "RANDOM_DELAY_MAX": int(os.getenv("RANDOM_DELAY_MAX", "500"))
}