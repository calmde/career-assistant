"""
岗位描述与简历匹配分析脚本 (兼容层)
用法:
  python analyze_match.py --job job.txt --resume resume.txt

注意：本模块保留向后兼容。新代码请使用 matcher.py + job_parser.py。
"""
import argparse
import json

# 委托到新模块
from job_parser import (
    extract_skills,
    extract_experience,
    extract_education,
    DEGREE_RANK,
    parse_job_description as parse_job_requirements,
    parse_resume,
)
from matcher import (
    compute_match,
    analyze,
    analyze_jobs_in_dir,
)

# 重新导出以保持兼容
__all__ = [
    "DEGREE_RANK",
    "extract_skills",
    "extract_experience",
    "extract_education",
    "parse_job_requirements",
    "parse_resume",
    "compute_match",
    "analyze",
    "analyze_jobs_in_dir",
]


def main():
    parser = argparse.ArgumentParser(description="岗位与简历匹配分析工具")
    parser.add_argument("--job", help="岗位描述文本文件路径")
    parser.add_argument("--resume", help="简历或技能清单文本文件路径")
    parser.add_argument("--jobs-dir", help="包含多个岗位描述的目录（.txt/.md）")
    parser.add_argument("--top", type=int, default=10, help="批量匹配时显示前 N 个结果")
    parser.add_argument("--out", help="将批量匹配结果写入 JSON 文件路径")
    args = parser.parse_args()

    if args.job and args.resume and not args.jobs_dir:
        with open(args.job, "r", encoding="utf-8") as f:
            job_text = f.read()
        with open(args.resume, "r", encoding="utf-8") as f:
            resume_text = f.read()
        res = analyze(job_text, resume_text)
        print("\n匹配分析结果:")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    if args.jobs_dir and args.resume:
        with open(args.resume, "r", encoding="utf-8") as f:
            resume_text = f.read()
        ranked = analyze_jobs_in_dir(args.jobs_dir, resume_text, top_n=args.top)
        print(f"\n批量匹配结果（按匹配度降序，显示前 {len(ranked)} 个）:")
        for i, item in enumerate(ranked, start=1):
            print(f"{i}. {item.get('job_file')} — 分数: {item.get('score')}")
            if item.get("highlights"):
                print("   亮点:", "; ".join(item.get("highlights")))
            if item.get("missing_skills"):
                print("   缺失:", ", ".join(item.get("missing_skills")[:5]))
        if args.out:
            try:
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(ranked, f, ensure_ascii=False, indent=2)
                print(f"已写入: {args.out}")
            except Exception as e:
                print("写出文件失败:", e)
        return

    # 交互式粘贴输入
    print("请粘贴岗位描述（以空行结束）:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "" and lines:
            break
        lines.append(line)
    job_text = "\n".join(lines)

    print("\n请粘贴简历或技能清单（以空行结束）:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "" and lines:
            break
        lines.append(line)
    resume_text = "\n".join(lines)

    res = analyze(job_text, resume_text)
    print("\n匹配分析结果:")
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
