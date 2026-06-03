"""
求职管线编排器 — 串联岗位解析 → 匹配 → 优化 → 技能规划全流程。

用法:
  from pipeline import CareerPipeline
  cp = CareerPipeline()
  cp.run_full("resume.pdf", city="北京", keywords=["Python后端"])

命令行:
  python pipeline.py --resume resume.txt --city 北京
"""
import argparse
import json
import time
import os
from typing import Any

from spider import fetch_jobs
from clean_data import clean_and_store
from job_parser import parse_job_description, parse_resume
from matcher import compute_match
from resume_optimizer import generate_optimization
from skill_navigator import generate_skill_plan
from scrapers.integrations import fetch_with_jobspy, fetch_v2ex_jobs, fetch_xhiring_jobs, fetch_dianya_jobs

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


class CareerPipeline:
    """四步求职管线编排器。"""

    def __init__(self):
        self.status: dict[str, str] = {}  # step -> pending/running/done/error
        self.results: dict[str, Any] = {}
        self._steps = ["parse_resume", "crawl_jobs", "match_jobs", "optimize", "skill_plan"]
        for s in self._steps:
            self.status[s] = "pending"

    # ----- Step 1: 解析简历 -----

    def step_1_parse_resume(self, resume_path: str) -> dict:
        """解析上传的简历文件（PDF 或 TXT）。"""
        self.status["parse_resume"] = "running"
        try:
            resume_text = _read_resume_file(resume_path)
            parsed = parse_resume(resume_text)
            keywords = parsed["skills"]["hard"][:6] or ["python"]
            result = {
                "resume_text": resume_text,
                "parsed": parsed,
                "keywords": keywords,
            }
            self.results["parse_resume"] = result
            self.status["parse_resume"] = "done"
            return result
        except Exception as e:
            self.status["parse_resume"] = "error"
            raise

    # ----- Step 2: 爬取岗位 -----

    def step_2_crawl_jobs(
        self,
        keywords: list[str],
        city: str = "北京",
        max_pages: int = 2,
        proxies_list: list[str] | None = None,
    ) -> list[dict]:
        """多源爬取岗位。"""
        self.status["crawl_jobs"] = "running"

        all_jobs: list[dict] = []
        seen_urls: set[str] = set()

        def _dedup(jobs, source=""):
            added = 0
            for job in jobs:
                url = job.get("url") or f"{job.get('title','')}|{job.get('company','')}|{source}"
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                job["source"] = job.get("source", source)
                all_jobs.append(job)
                added += 1
            return added

        # 1) jobspy（多站点聚合）
        try:
            _dedup(fetch_with_jobspy(keywords, city, max_pages, proxies_list), "jobspy")
        except Exception as e:
            print(f"  jobspy: {e}")

        # 2) 社区抓取
        for kw in keywords:
            for fetcher, name in [
                (fetch_v2ex_jobs, "V2EX"),
                (fetch_xhiring_jobs, "X-Hiring"),
                (fetch_dianya_jobs, "电鸭"),
            ]:
                try:
                    jobs = fetcher(kw, max_pages=1, proxies_list=proxies_list)
                    _dedup(jobs, name)
                except Exception:
                    pass

        # 3) BOSS直聘
        for kw in keywords:
            try:
                jobs = fetch_jobs(kw, city=city, max_pages=max_pages)
                _dedup(jobs, "BOSS直聘")
            except Exception as e:
                print(f"  BOSS直聘({kw}): {e}")
            time.sleep(1)

        self.results["crawl_jobs"] = all_jobs
        self.status["crawl_jobs"] = "done"

        # 入库
        try:
            clean_and_store(all_jobs)
        except Exception as e:
            print(f"  入库失败: {e}")

        print(f"共收集 {len(all_jobs)} 条岗位")
        return all_jobs

    # ----- Step 3: 批量匹配 -----

    def step_3_match_jobs(self, resume_text: str, jobs: list[dict], top_n: int = 50) -> list[dict]:
        """批量匹配所有岗位与简历。"""
        self.status["match_jobs"] = "running"
        resume_parsed = parse_resume(resume_text)
        analyzed = []

        for job in jobs:
            try:
                job_text = _build_job_text(job)
                job_parsed = parse_job_description(job_text)
                match = compute_match(resume_parsed, job_parsed)
                match["job_raw"] = job
                match["job_parsed"] = job_parsed
                analyzed.append(match)
            except Exception as e:
                print(f"  匹配失败: {job.get('title','')}: {e}")

        analyzed.sort(key=lambda x: x.get("score", 0), reverse=True)
        top = analyzed[:top_n]

        self.results["match_jobs"] = top
        self.status["match_jobs"] = "done"

        print(f"匹配完成，top-{len(top)}:")
        for i, item in enumerate(top[:5], 1):
            j = item.get("job_raw", {})
            print(f"  {i}. {j.get('title')} @ {j.get('company')} — {item['score']}分")

        return top

    # ----- Step 4: 简历优化 -----

    def step_4_optimize(self, resume_text: str, job_index: int) -> dict:
        """为指定岗位生成简历优化建议。"""
        self.status["optimize"] = "running"
        top = self.results.get("match_jobs", [])
        if not top or job_index >= len(top):
            raise IndexError(f"岗位索引 {job_index} 超出范围")
        item = top[job_index]
        job_parsed = item.get("job_parsed", {})
        result = generate_optimization(resume_text, job_parsed, item)
        self.results["optimize"] = {"job_index": job_index, "result": result}
        self.status["optimize"] = "done"
        return result

    # ----- Step 5: 技能规划 -----

    def step_5_skill_plan(self, resume_text: str, job_index: int) -> dict:
        """为指定岗位生成技能提升计划。"""
        self.status["skill_plan"] = "running"
        top = self.results.get("match_jobs", [])
        if not top or job_index >= len(top):
            raise IndexError(f"岗位索引 {job_index} 超出范围")
        item = top[job_index]
        job_parsed = item.get("job_parsed", {})
        existing = item.get("matched_skills", [])
        missing = item.get("missing_skills", [])
        result = generate_skill_plan(missing, existing, job_parsed, item, resume_text)
        self.results["skill_plan"] = {"job_index": job_index, "result": result}
        self.status["skill_plan"] = "done"
        return result

    # ----- 全流程 -----

    def run_full(
        self,
        resume_path: str,
        city: str = "北京",
        keywords: list[str] | None = None,
        max_pages: int = 2,
        top_n: int = 20,
        proxies_list: list[str] | None = None,
    ) -> dict:
        """运行全流程：解析 → 爬取 → 匹配，返回结构化结果。"""
        # Step 1
        parsed = self.step_1_parse_resume(resume_path)
        resume_text = parsed["resume_text"]
        if not keywords:
            keywords = parsed["keywords"]

        print(f"搜索关键词: {keywords}")

        # Step 2
        jobs = self.step_2_crawl_jobs(keywords, city, max_pages, proxies_list)

        if not jobs:
            return {"status": "no_jobs_found", "message": "未找到相关岗位，请尝试更换关键词或城市"}

        # Step 3
        top = self.step_3_match_jobs(resume_text, jobs, top_n)

        return {
            "status": "done",
            "resume": parsed,
            "top_jobs": top,
            "job_count": len(jobs),
        }


# ============================================================
# 工具函数
# ============================================================

def _read_resume_file(path: str) -> str:
    """读取简历文件（PDF或TXT）。"""
    if path.lower().endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("缺少 PyPDF2，请 pip install PyPDF2")
        reader = PdfReader(path)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n".join(pages)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def _build_job_text(job: dict) -> str:
    """将岗位字典拼接为可解析文本。"""
    parts = []
    for k in ["title", "company", "skills", "experience", "education", "welfare", "industry", "url"]:
        v = job.get(k)
        if v:
            parts.append(str(v))
    return "\n".join(parts)


# ============================================================
# 向后兼容包装器（兼容 find_jobs_from_resume.pipeline()）
# ============================================================

def pipeline(
    resume_path,
    city="北京",
    keywords=None,
    max_pages=2,
    top_n=50,
    out_path=None,
    proxies_file=None,
):
    """向后兼容的管线函数。参见 find_jobs_from_resume.py 文档。"""
    proxies_list = None
    if proxies_file and os.path.exists(proxies_file):
        with open(proxies_file, "r", encoding="utf-8") as f:
            proxies_list = [l.strip() for l in f.readlines() if l.strip()]

    cp = CareerPipeline()
    result = cp.run_full(resume_path, city, keywords, max_pages, top_n, proxies_list)

    top = result.get("top_jobs", [])
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(top, f, ensure_ascii=False, indent=2)
            print("已写出筛选结果到", out_path)
        except Exception as e:
            print("写出文件失败:", e)

    return top


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="从简历出发爬取并筛选相关岗位")
    parser.add_argument("--resume", required=True, help="简历文件路径（PDF/TXT）")
    parser.add_argument("--city", default="北京", help="城市")
    parser.add_argument("--keywords", help="逗号分隔的搜索关键词")
    parser.add_argument("--max-pages", type=int, default=2, help="每关键词爬取页数")
    parser.add_argument("--top", type=int, default=20, help="显示前 N 条结果")
    parser.add_argument("--out", help="筛选结果输出 JSON 文件")
    parser.add_argument("--proxies-file", help="代理文件路径")
    args = parser.parse_args()

    kws = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    pipeline(args.resume, city=args.city, keywords=kws, max_pages=args.max_pages,
             top_n=args.top, out_path=args.out, proxies_file=args.proxies_file)


if __name__ == "__main__":
    main()
