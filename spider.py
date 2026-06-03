"""
BOSS直聘爬虫 — 使用 DrissionPage 浏览器自动化，增强反反爬。

首次使用需要手动扫码登录BOSS直聘，之后复用登录态。
"""
import time
import random
import json
import logging
import os
import io
import base64

logger = logging.getLogger(__name__)

COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boss_cookies.json")

CITY_CODE_MAP = {
    "北京": "101010100", "上海": "101020100", "广州": "101280100",
    "深圳": "101280600", "杭州": "101210100", "成都": "101270100",
    "武汉": "101200100", "南京": "101190100", "西安": "101110100",
    "苏州": "101190400", "天津": "101030100", "重庆": "101040100",
    "长沙": "101250100", "合肥": "101220100", "郑州": "101180100",
    "厦门": "101230200", "福州": "101230100", "济南": "101120100",
    "青岛": "101120200", "大连": "101070200",
}

# 真实的 User-Agent 列表
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# 注入 JS 隐藏 webdriver 特征
HIDE_WEBDRIVER_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
window.chrome = { runtime: {} };
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
"""


def _random_delay(min_s=1.0, max_s=4.0):
    time.sleep(random.uniform(min_s, max_s))


def _simulate_human_scroll(page):
    """模拟人类滚动行为"""
    try:
        for _ in range(random.randint(1, 3)):
            scroll_y = random.randint(200, 600)
            page.run_js(f"window.scrollBy(0, {scroll_y})")
            time.sleep(random.uniform(0.5, 1.5))
    except Exception:
        pass


def fetch_jobs(keyword, city="北京", max_pages=2):
    """从 BOSS直聘爬取职位列表。"""
    city_code = CITY_CODE_MAP.get(city)
    if not city_code:
        print(f"  不支持的城市: {city}，使用默认城市北京")
        city_code = CITY_CODE_MAP["北京"]
        city = "北京"

    print(f"  BOSS直聘: 关键词='{keyword}', 城市='{city}', 页数={max_pages}")

    all_jobs = []

    try:
        from DrissionPage import ChromiumPage, ChromiumOptions

        co = ChromiumOptions()

        # 基础反检测参数
        co.set_argument("--disable-blink-features=AutomationControlled")
        co.set_argument("--disable-infobars")
        co.set_argument("--disable-dev-shm-usage")
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")
        co.set_argument("--disable-background-networking")
        co.set_argument("--disable-sync")

        # 随机 UA
        ua = random.choice(UA_LIST)
        co.set_argument(f"--user-agent={ua}")

        # 设置窗口大小（模拟正常用户）
        co.set_argument("--window-size=1366,768")

        dp = ChromiumPage(co)

        # 通过 CDP 注入反检测脚本
        try:
            dp.run_cdp("Page.addScriptToEvaluateOnNewDocument", source=HIDE_WEBDRIVER_JS)
        except Exception:
            pass

        # 恢复 cookie
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                dp.set.cookies(cookies)
                print("  已加载登录缓存")
            except Exception:
                pass

        dp.listen.start("wapi/zpgeek/search/joblist.json")

        target_url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city_code}"
        dp.get(target_url)

        _random_delay(3, 6)

        # 模拟人类行为
        _simulate_human_scroll(dp)

        # 检测登录状态
        current_url = dp.url.lower()
        if "login" in current_url or "geek" not in current_url:
            print("  BOSS直聘需要登录，请在浏览器窗口中手动扫码...")
            for i in range(30):
                time.sleep(2)
                try:
                    current_url = dp.url.lower()
                except Exception:
                    current_url = ""
                if "geek" in current_url and "login" not in current_url:
                    # 等待页面加载
                    time.sleep(2)
                    print("  登录成功，继续爬取...")
                    break
                if i % 5 == 0 and i > 0:
                    print(f"    等待登录中... ({i * 2}s)")
            else:
                print("  登录超时，跳过BOSS直聘")
                _save_cookies(dp)
                dp.quit()
                return []

        # 逐页采集
        for page in range(1, max_pages + 1):
            print(f"    正在采集第{page}页...")
            try:
                resp = dp.listen.wait(timeout=30)
                json_data = resp.response.body

                if not json_data:
                    print(f"    第{page}页无数据")
                    break

                job_list = json_data.get("zpData", {}).get("jobList", [])
                if not job_list:
                    print(f"    本页无职位数据")
                    break

                for job in job_list:
                    skills = job.get("skills", [])
                    if isinstance(skills, list):
                        skills = ", ".join(skills[:5])
                    welfare = job.get("welfareList", "")
                    if isinstance(welfare, list):
                        welfare = ", ".join(welfare)
                    all_jobs.append({
                        "title": job.get("jobName", ""),
                        "company": job.get("brandName", ""),
                        "salary": job.get("salaryDesc", ""),
                        "city": job.get("cityName", city),
                        "district": job.get("areaDistrict", ""),
                        "experience": job.get("jobExperience", ""),
                        "education": job.get("jobDegree", ""),
                        "skills": skills,
                        "company_size": job.get("brandScaleName", ""),
                        "company_stage": job.get("brandStageName", ""),
                        "industry": job.get("brandIndustry", ""),
                        "welfare": welfare,
                        "contact_person": job.get("bossName", ""),
                        "contact_title": job.get("bossTitle", ""),
                        "url": f"https://www.zhipin.com/job_detail/{job.get('encryptJobId', '')}.html",
                        "source": "BOSS直聘",
                    })

                print(f"    第{page}页获取 {len(job_list)} 条，累计 {len(all_jobs)} 条")

                if page < max_pages:
                    _random_delay(3, 6)
                    _simulate_human_scroll(dp)

            except Exception as e:
                print(f"    第{page}页失败: {e}")
                break

        _save_cookies(dp)
        dp.quit()
        print(f"  BOSS直聘完成，共 {len(all_jobs)} 条")

    except ImportError:
        print("  DrissionPage 未安装，跳过BOSS直聘")
    except Exception as e:
        print(f"  BOSS直聘异常: {type(e).__name__}: {e}")

    return all_jobs


def _save_cookies(dp):
    try:
        cookies = dp.get.cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False)
    except Exception:
        pass


if __name__ == "__main__":
    jobs = fetch_jobs("python", city="北京", max_pages=1)
    if jobs:
        from clean_data import clean_and_store
        clean_and_store(jobs)
    else:
        print("未获取到任何岗位")
