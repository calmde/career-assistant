import random
import requests

# 内置 User-Agent 列表（可扩展或替换）
DEFAULT_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
]


def random_user_agent(extra_list=None):
    pool = DEFAULT_UAS[:]
    if extra_list:
        pool.extend(extra_list)
    return random.choice(pool)


def choose_proxy(proxies_list):
    """从proxy字符串列表中随机选择一个，字符串格式支持 http://ip:port 或 ip:port"""
    if not proxies_list:
        return None
    p = random.choice(proxies_list).strip()
    if not p:
        return None
    if not p.startswith('http'):
        p = 'http://' + p
    return {
        'http': p,
        'https': p
    }


def safe_get(url, headers=None, proxies=None, timeout=15):
    hdrs = headers or {}
    try:
        r = requests.get(url, headers=hdrs, proxies=proxies, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception:
        return None
