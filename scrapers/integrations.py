"""
第三方岗位抓取器 — V2EX / jobspy 等。
纯 HTTP 请求，不依赖浏览器。
"""
import re
import time
import random

import requests
from bs4 import BeautifulSoup

from utils.anti_scrape import random_user_agent

HEADERS = {
    "User-Agent": random_user_agent(),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _safe_get(url, **kwargs):
    try:
        return requests.get(url, headers=HEADERS, timeout=15, **kwargs)
    except Exception:
        return None


# ============================================================
# V2EX 招聘节点
# ============================================================

V2EX_JOBS_URL = "https://www.v2ex.com/go/jobs"


def fetch_v2ex_jobs(keyword, max_pages=1, proxies_list=None, **__):
    """从 V2EX 招聘节点抓取相关帖子。"""
    out = []
    kw_lower = keyword.lower()

    for page in range(1, max_pages + 1):
        url = f"{V2EX_JOBS_URL}?p={page}"
        r = _safe_get(url)
        if not r:
            continue

        soup = BeautifulSoup(r.text, "lxml")

        for cell in soup.select("div.cell.item"):
            try:
                title_el = cell.select_one("span.item_title a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")

                # 关键词匹配
                text_lower = (title + " " + cell.get_text()).lower()
                if kw_lower not in text_lower:
                    # 检查是否包含该技能相关词
                    name_parts = kw_lower.replace(" ", "").lower()
                    if name_parts not in text_lower.replace(" ", "").lower():
                        continue

                # 提取公司名（通常标题格式： [城市] 公司名 招聘 XX）
                company = "V2EX招聘"
                city_match = re.search(r"\[(.+?)\]", title)
                city = city_match.group(1) if city_match else ""

                out.append({
                    "title": title,
                    "company": company,
                    "salary": "",
                    "city": city,
                    "district": "",
                    "experience": "",
                    "education": "",
                    "skills": keyword,
                    "company_size": "",
                    "company_stage": "",
                    "industry": "互联网",
                    "welfare": "",
                    "contact_person": "",
                    "contact_title": "",
                    "url": f"https://www.v2ex.com{href}" if href.startswith("/") else href,
                    "source": "V2EX",
                })
            except Exception:
                continue

        time.sleep(random.uniform(1, 2))

    return out


# ============================================================
# V2EX 搜索（补充）
# ============================================================

def fetch_v2ex_search_jobs(keyword, max_pages=1, proxies_list=None, **__):
    """V2EX 搜索作为补充。"""
    out = []
    for page in range(1, max_pages + 1):
        url = f"https://www.v2ex.com/search?q={keyword}&p={page}"
        r = _safe_get(url)
        if not r:
            continue

        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.select("a[href^='/t/']"):
            try:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 4:
                    continue
                if keyword.lower() not in title.lower():
                    continue
                out.append({
                    "title": title,
                    "company": "V2EX",
                    "salary": "",
                    "city": "",
                    "district": "",
                    "experience": "",
                    "education": "",
                    "skills": keyword,
                    "company_size": "",
                    "company_stage": "",
                    "industry": "互联网",
                    "welfare": "",
                    "contact_person": "",
                    "contact_title": "",
                    "url": f"https://www.v2ex.com{href}",
                    "source": "V2EX",
                })
            except Exception:
                continue

        time.sleep(random.uniform(1, 2))

    return out


# ============================================================
# jobspy 集成
# ============================================================

def fetch_with_jobspy(keywords, city="北京", max_pages=2, proxies_list=None, **__):
    """尝试使用 jobspy 库。"""
    try:
        import jobspy
    except Exception:
        return []

    results = []
    for kw in keywords[:3]:
        try:
            rsp = jobspy.search(keyword=kw, city=city, pages=max_pages)
            for item in rsp:
                results.append(dict(item) if hasattr(item, "__iter__") else {"title": str(item)})
        except Exception:
            continue
    return results


# ============================================================
# 占位（保留兼容）
# ============================================================

def fetch_xhiring_jobs(keyword, max_pages=1, proxies_list=None, **__):
    return []


def fetch_dianya_jobs(keyword, max_pages=1, proxies_list=None, **__):
    return []
