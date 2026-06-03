"""
DEPRECATED: 本模块已废弃，委托到 pipeline.py。保留向后兼容。

用法: 建议使用 python pipeline.py --resume resume.txt --city 北京
"""
import argparse

from pipeline import CareerPipeline, pipeline as _new_pipeline


def pipeline(resume_path, city="北京", keywords=None, max_pages=2, top_n=50, out_path=None, proxies_file=None):
    """委托到 pipeline.CareerPipeline。"""
    return _new_pipeline(resume_path, city, keywords, max_pages, top_n, out_path, proxies_file)


def main():
    parser = argparse.ArgumentParser(description="从简历出发爬取并筛选相关岗位（已废弃，请使用 pipeline.py）")
    parser.add_argument("--resume", required=True, help="简历文本文件路径")
    parser.add_argument("--city", default="北京", help="城市")
    parser.add_argument("--keywords", help="逗号分隔的搜索关键词")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", help="筛选结果输出 JSON 文件")
    parser.add_argument("--proxies-file", help="代理文件路径")
    args = parser.parse_args()

    kws = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    pipeline(args.resume, city=args.city, keywords=kws, max_pages=args.max_pages,
             top_n=args.top, out_path=args.out, proxies_file=args.proxies_file)


if __name__ == "__main__":
    main()
