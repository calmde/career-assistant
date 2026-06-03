from spider import fetch_jobs
from clean_data import clean_and_store

if __name__ == "__main__":
    keyword = input("请输入搜索关键词（如 python）：").strip()
    city = input("请输入城市（如 北京）：").strip()
    pages = int(input("爬取页数：").strip() or "2")
    jobs = fetch_jobs(keyword, city, max_pages=pages)
    clean_and_store(jobs)
    print("数据已入库！")