"""
数据清洗与入库 — 将爬取的岗位数据清洗后写入 SQLite。

纯标准库实现（sqlite3），不依赖 pandas。
"""
import sqlite3
import re
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 与 app.py / seed_data.py 保持一致的数据库路径
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")


def parse_salary(salary_str: str) -> tuple[float | None, float | None, float | None]:
    """解析薪资字符串，返回 (min, max, avg)。"""
    if not salary_str:
        return None, None, None
    match = re.search(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*K", salary_str, re.IGNORECASE)
    if match:
        low = float(match.group(1)) * 1000
        high = float(match.group(2)) * 1000
        avg = (low + high) / 2
        return low, high, avg
    return None, None, None


def _ensure_list_field(value) -> str:
    """将列表字段转为逗号分隔的字符串。"""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def clean_and_store(jobs_list: list[dict], db_path: str | None = None) -> int:
    """清洗岗位数据并写入 SQLite 数据库。

    Args:
        jobs_list: 岗位字典列表
        db_path: 数据库路径，默认使用项目根目录的 jobs.db

    Returns:
        成功入库的记录数
    """
    if not jobs_list:
        logger.info("无数据，跳过入库")
        return 0

    if db_path is None:
        db_path = DEFAULT_DB_PATH

    # ---- 去重 ----
    seen = set()
    deduped = []
    for job in jobs_list:
        key = (job.get("title", ""), job.get("company", ""), job.get("city", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(job)

    # ---- 建表（如不存在）----
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            title TEXT, company TEXT, salary TEXT, city TEXT, district TEXT,
            experience TEXT, education TEXT, skills TEXT, company_size TEXT,
            company_stage TEXT, industry TEXT, welfare TEXT,
            contact_person TEXT, contact_title TEXT,
            url TEXT, source TEXT,
            salary_min REAL, salary_max REAL, salary_avg REAL, crawl_time TEXT
        )
    """)

    # ---- 逐条写入 ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0

    for job in deduped:
        salary_min, salary_max, salary_avg = parse_salary(job.get("salary", ""))

        cur.execute(
            """INSERT INTO jobs
               (title, company, salary, city, district, experience, education,
                skills, company_size, company_stage, industry, welfare,
                contact_person, contact_title, url, source,
                salary_min, salary_max, salary_avg, crawl_time)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job.get("title", ""),
                job.get("company", ""),
                job.get("salary", ""),
                job.get("city", ""),
                job.get("district", ""),
                job.get("experience", ""),
                job.get("education", ""),
                _ensure_list_field(job.get("skills")),
                job.get("company_size", ""),
                job.get("company_stage", ""),
                job.get("industry", ""),
                _ensure_list_field(job.get("welfare")),
                job.get("contact_person", ""),
                job.get("contact_title", ""),
                job.get("url", ""),
                job.get("source", ""),
                salary_min,
                salary_max,
                salary_avg,
                now,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    logger.info("成功入库 %d 条数据", inserted)
    return inserted
