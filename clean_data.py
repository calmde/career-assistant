# clean_data.py
import pandas as pd
import sqlite3
import re
from datetime import datetime

def parse_salary(salary_str):
    if not salary_str:
        return None, None, None
    match = re.search(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*K", salary_str, re.IGNORECASE)
    if match:
        low = float(match.group(1)) * 1000
        high = float(match.group(2)) * 1000
        avg = (low + high) / 2
        return low, high, avg
    return None, None, None

def clean_and_store(jobs_list, db_path="jobs.db"):
    if not jobs_list:
        print("无数据，跳过入库")
        return

    df = pd.DataFrame(jobs_list)
    # 去重
    df = df.drop_duplicates(subset=["title", "company", "city"])

    # ---- 关键修复：把列表字段转为纯文本 ----
    if 'skills' in df.columns:
        df['skills'] = df['skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x) if pd.notna(x) else '')
    if 'welfare' in df.columns:
        df['welfare'] = df['welfare'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x) if pd.notna(x) else '')
    # --------------------------------

    # 解析薪资
    salary_info = df["salary"].apply(parse_salary)
    df["salary_min"] = salary_info.apply(lambda x: x[0])
    df["salary_max"] = salary_info.apply(lambda x: x[1])
    df["salary_avg"] = salary_info.apply(lambda x: x[2])

    # 填充缺失值
    df["education"] = df["education"].fillna("学历不限")
    df["experience"] = df["experience"].fillna("经验不限")
    if "company_stage" not in df.columns:
        df["company_stage"] = ""
    if "contact_person" not in df.columns:
        df["contact_person"] = ""
    if "contact_title" not in df.columns:
        df["contact_title"] = ""
    df["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 写入数据库（如果表不存在会自动创建）
    conn = sqlite3.connect(db_path)
    df.to_sql("jobs", conn, if_exists="append", index=False)
    conn.close()
    print(f"成功入库 {len(df)} 条数据")