"""
种子数据 — 预设真实招聘数据，确保系统在爬虫失效时仍可演示。
运行: python seed_data.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

JOBS = [
    # ===== Python 后端 =====
    {"title": "Python后端开发工程师", "company": "字节跳动", "salary": "25-50K·15薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "本科", "skills": "Python, Django, Flask, MySQL, Redis, Docker, Kubernetes", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 补充医疗, 免费三餐, 健身房, 弹性工作", "contact_person": "张先生", "contact_title": "技术总监", "url": "https://www.zhipin.com/job_detail/seed_001.html", "source": "种子数据"},
    {"title": "Python开发工程师", "company": "阿里巴巴", "salary": "20-40K·16薪", "city": "杭州", "district": "余杭区", "experience": "1-3年", "education": "本科", "skills": "Python, FastAPI, PostgreSQL, MongoDB, RabbitMQ, Linux", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 股票期权, 带薪年假, 年度旅游", "contact_person": "李女士", "contact_title": "HR", "url": "https://www.zhipin.com/job_detail/seed_002.html", "source": "种子数据"},
    {"title": "Python全栈工程师", "company": "美团", "salary": "22-45K·15薪", "city": "北京", "district": "朝阳区", "experience": "3-5年", "education": "本科", "skills": "Python, React, Vue.js, Django, PostgreSQL, AWS", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 餐补, 交通补贴, 弹性工作", "contact_person": "王先生", "contact_title": "部门负责人", "url": "https://www.zhipin.com/job_detail/seed_003.html", "source": "种子数据"},
    {"title": "高级Python开发", "company": "腾讯", "salary": "30-60K·16薪", "city": "深圳", "district": "南山区", "experience": "5-10年", "education": "本科", "skills": "Python, Go, 微服务, gRPC, MySQL, Redis, 分布式系统", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 免费早餐, 股票期权, 年终奖", "contact_person": "赵女士", "contact_title": "招聘HR", "url": "https://www.zhipin.com/job_detail/seed_004.html", "source": "种子数据"},
    {"title": "Python开发（AI方向）", "company": "百度", "salary": "25-50K·16薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "硕士", "skills": "Python, PyTorch, TensorFlow, NLP, 深度学习, CUDA", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 补充公积金, 弹性工作, 健身房", "contact_person": "陈先生", "contact_title": "AI技术负责人", "url": "https://www.zhipin.com/job_detail/seed_005.html", "source": "种子数据"},
    {"title": "Python自动化测试", "company": "网易", "salary": "18-35K·14薪", "city": "广州", "district": "天河区", "experience": "1-3年", "education": "本科", "skills": "Python, Selenium, pytest, Jenkins, Docker, Linux", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 双休, 免费三餐, 零食下午茶", "contact_person": "刘女士", "contact_title": "测试经理", "url": "https://www.zhipin.com/job_detail/seed_006.html", "source": "种子数据"},

    # ===== Java 后端 =====
    {"title": "Java开发工程师", "company": "阿里巴巴", "salary": "20-40K·16薪", "city": "杭州", "district": "余杭区", "experience": "1-3年", "education": "本科", "skills": "Java, Spring Boot, MyBatis, MySQL, Redis, Kafka, 微服务", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 股票期权, 带薪年假, 年度旅游", "contact_person": "李女士", "contact_title": "HR", "url": "https://www.zhipin.com/job_detail/seed_007.html", "source": "种子数据"},
    {"title": "高级Java工程师", "company": "京东", "salary": "30-55K·16薪", "city": "北京", "district": "亦庄", "experience": "5-10年", "education": "本科", "skills": "Java, Spring Cloud, JVM调优, MySQL, Elasticsearch, Kubernetes", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 商业保险, 饭补, 班车", "contact_person": "周先生", "contact_title": "架构师", "url": "https://www.zhipin.com/job_detail/seed_008.html", "source": "种子数据"},
    {"title": "Java后端开发", "company": "拼多多", "salary": "25-50K·16薪", "city": "上海", "district": "长宁区", "experience": "3-5年", "education": "本科", "skills": "Java, Spring, MyBatis, MySQL, Redis, 高并发", "company_size": "10000人以上", "company_stage": "已上市", "industry": "电商", "welfare": "五险一金, 年终奖, 弹性工作, 双休", "contact_person": "吴女士", "contact_title": "HRBP", "url": "https://www.zhipin.com/job_detail/seed_009.html", "source": "种子数据"},
    {"title": "初级Java开发", "company": "中软国际", "salary": "8-15K", "city": "成都", "district": "高新区", "experience": "应届生", "education": "本科", "skills": "Java, Spring Boot, MySQL, Git, Linux基础", "company_size": "1000-9999人", "company_stage": "已上市", "industry": "IT服务", "welfare": "五险一金, 双休, 培训机会", "contact_person": "郑先生", "contact_title": "招聘专员", "url": "https://www.zhipin.com/job_detail/seed_010.html", "source": "种子数据"},
    {"title": "Java架构师", "company": "快手", "salary": "40-70K·15薪", "city": "北京", "district": "海淀区", "experience": "5-10年", "education": "本科", "skills": "Java, 系统架构, 分布式, 高可用, 性能优化, 团队管理", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 股票期权, 免费三餐, 健身房", "contact_person": "孙先生", "contact_title": "技术VP", "url": "https://www.zhipin.com/job_detail/seed_011.html", "source": "种子数据"},

    # ===== 前端 =====
    {"title": "前端开发工程师", "company": "字节跳动", "salary": "25-50K·15薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "本科", "skills": "React, TypeScript, Webpack, Node.js, CSS, 性能优化", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 补充医疗, 免费三餐, 弹性工作", "contact_person": "张先生", "contact_title": "前端Leader", "url": "https://www.zhipin.com/job_detail/seed_012.html", "source": "种子数据"},
    {"title": "React前端开发", "company": "小米", "salary": "20-40K·14薪", "city": "北京", "district": "海淀区", "experience": "1-3年", "education": "本科", "skills": "React, JavaScript, TypeScript, Ant Design, Git, Webpack", "company_size": "10000人以上", "company_stage": "已上市", "industry": "智能硬件", "welfare": "五险一金, 餐补, 期权, 双休", "contact_person": "钱女士", "contact_title": "HR", "url": "https://www.zhipin.com/job_detail/seed_013.html", "source": "种子数据"},
    {"title": "Vue前端工程师", "company": "携程", "salary": "18-35K·15薪", "city": "上海", "district": "长宁区", "experience": "1-3年", "education": "本科", "skills": "Vue.js, JavaScript, Element UI, Webpack, Git, RESTful API", "company_size": "10000人以上", "company_stage": "已上市", "industry": "旅游", "welfare": "五险一金, 员工旅游优惠, 弹性工作", "contact_person": "杨先生", "contact_title": "前端负责人", "url": "https://www.zhipin.com/job_detail/seed_014.html", "source": "种子数据"},
    {"title": "高级前端工程师", "company": "腾讯", "salary": "30-60K·16薪", "city": "深圳", "district": "南山区", "experience": "5-10年", "education": "本科", "skills": "React, TypeScript, Node.js, 前端架构, 性能优化, 团队管理", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 股票期权, 免费早餐", "contact_person": "赵女士", "contact_title": "招聘HR", "url": "https://www.zhipin.com/job_detail/seed_015.html", "source": "种子数据"},
    {"title": "前端开发（应届）", "company": "哔哩哔哩", "salary": "12-20K·14薪", "city": "上海", "district": "杨浦区", "experience": "应届生", "education": "本科", "skills": "HTML, CSS, JavaScript, React, Vue.js, Git", "company_size": "1000-9999人", "company_stage": "已上市", "industry": "文娱", "welfare": "五险一金, 免费午餐, 健身房, 双休", "contact_person": "黄女士", "contact_title": "校招HR", "url": "https://www.zhipin.com/job_detail/seed_016.html", "source": "种子数据"},
    {"title": "Web前端开发", "company": "滴滴", "salary": "22-40K·15薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "本科", "skills": "React, Vue.js, TypeScript, 小程序, Webpack, Node.js", "company_size": "10000人以上", "company_stage": "已上市", "industry": "出行", "welfare": "五险一金, 弹性工作, 带薪年假", "contact_person": "马先生", "contact_title": "前端总监", "url": "https://www.zhipin.com/job_detail/seed_017.html", "source": "种子数据"},

    # ===== 数据/算法 =====
    {"title": "数据分析师", "company": "美团", "salary": "18-35K·15薪", "city": "北京", "district": "朝阳区", "experience": "1-3年", "education": "本科", "skills": "SQL, Python, Tableau, Excel, 统计分析, A/B测试", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 餐补, 弹性工作", "contact_person": "王先生", "contact_title": "数据分析主管", "url": "https://www.zhipin.com/job_detail/seed_018.html", "source": "种子数据"},
    {"title": "算法工程师", "company": "商汤科技", "salary": "30-60K·14薪", "city": "上海", "district": "徐汇区", "experience": "3-5年", "education": "硕士", "skills": "Python, PyTorch, 计算机视觉, 深度学习, CUDA, ONNX", "company_size": "1000-9999人", "company_stage": "D轮及以上", "industry": "人工智能", "welfare": "六险一金, 股票期权, 免费午餐, 论文发表支持", "contact_person": "林先生", "contact_title": "算法总监", "url": "https://www.zhipin.com/job_detail/seed_019.html", "source": "种子数据"},
    {"title": "数据分析工程师", "company": "字节跳动", "salary": "25-45K·15薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "本科", "skills": "Python, SQL, Spark, Hive, 数据仓库, 数据可视化", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 免费三餐, 健身房", "contact_person": "张先生", "contact_title": "数据负责人", "url": "https://www.zhipin.com/job_detail/seed_020.html", "source": "种子数据"},
    {"title": "机器学习工程师", "company": "蚂蚁集团", "salary": "30-55K·16薪", "city": "杭州", "district": "西湖区", "experience": "3-5年", "education": "硕士", "skills": "Python, TensorFlow, XGBoost, 推荐系统, SQL, 特征工程", "company_size": "10000人以上", "company_stage": "D轮及以上", "industry": "金融科技", "welfare": "六险一金, 股票期权, 年终奖", "contact_person": "胡先生", "contact_title": "ML团队Lead", "url": "https://www.zhipin.com/job_detail/seed_021.html", "source": "种子数据"},
    {"title": "大数据开发工程师", "company": "华为", "salary": "20-40K·14薪", "city": "深圳", "district": "龙岗区", "experience": "3-5年", "education": "本科", "skills": "Hadoop, Spark, Flink, Hive, Java, Scala, 数据仓库", "company_size": "10000人以上", "company_stage": "不需要融资", "industry": "通信", "welfare": "五险一金, 年终奖, 补充医疗, 双休", "contact_person": "何先生", "contact_title": "大数据架构师", "url": "https://www.zhipin.com/job_detail/seed_022.html", "source": "种子数据"},
    {"title": "NLP算法工程师", "company": "科大讯飞", "salary": "25-45K·14薪", "city": "合肥", "district": "高新区", "experience": "3-5年", "education": "硕士", "skills": "Python, NLP, Transformer, BERT, PyTorch, 大模型", "company_size": "1000-9999人", "company_stage": "已上市", "industry": "人工智能", "welfare": "五险一金, 员工公寓, 餐补, 双休", "contact_person": "余女士", "contact_title": "NLP研究员", "url": "https://www.zhipin.com/job_detail/seed_023.html", "source": "种子数据"},

    # ===== 测试/运维 =====
    {"title": "软件测试工程师", "company": "华为", "salary": "15-30K·14薪", "city": "深圳", "district": "龙岗区", "experience": "1-3年", "education": "本科", "skills": "测试用例, 自动化测试, Python, Selenium, JIRA, Linux", "company_size": "10000人以上", "company_stage": "不需要融资", "industry": "通信", "welfare": "五险一金, 年终奖, 双休", "contact_person": "何先生", "contact_title": "测试经理", "url": "https://www.zhipin.com/job_detail/seed_024.html", "source": "种子数据"},
    {"title": "测试开发工程师", "company": "字节跳动", "salary": "25-45K·15薪", "city": "北京", "district": "海淀区", "experience": "3-5年", "education": "本科", "skills": "Python, Go, 自动化测试, CI/CD, Docker, Kubernetes", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 免费三餐, 弹性工作", "contact_person": "张先生", "contact_title": "QA架构师", "url": "https://www.zhipin.com/job_detail/seed_025.html", "source": "种子数据"},
    {"title": "DevOps工程师", "company": "网易", "salary": "20-40K·14薪", "city": "广州", "district": "天河区", "experience": "3-5年", "education": "本科", "skills": "Linux, Docker, Kubernetes, Jenkins, Terraform, Python, AWS", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 双休, 免费三餐", "contact_person": "刘女士", "contact_title": "SRE经理", "url": "https://www.zhipin.com/job_detail/seed_026.html", "source": "种子数据"},
    {"title": "运维开发工程师", "company": "阿里云", "salary": "20-40K·16薪", "city": "杭州", "district": "余杭区", "experience": "3-5年", "education": "本科", "skills": "Python, Ansible, Docker, Kubernetes, Prometheus, Grafana, Linux", "company_size": "10000人以上", "company_stage": "已上市", "industry": "云计算", "welfare": "六险一金, 股票期权, 带薪年假", "contact_person": "李女士", "contact_title": "HR", "url": "https://www.zhipin.com/job_detail/seed_027.html", "source": "种子数据"},

    # ===== 产品/其他 =====
    {"title": "产品经理（技术方向）", "company": "腾讯", "salary": "25-50K·16薪", "city": "深圳", "district": "南山区", "experience": "3-5年", "education": "本科", "skills": "需求分析, 数据分析, SQL, 原型设计, 项目管理, 技术背景", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 免费早餐, 股票期权", "contact_person": "赵女士", "contact_title": "产品总监", "url": "https://www.zhipin.com/job_detail/seed_028.html", "source": "种子数据"},
    {"title": "Golang开发工程师", "company": "字节跳动", "salary": "25-50K·15薪", "city": "上海", "district": "徐汇区", "experience": "3-5年", "education": "本科", "skills": "Go, 微服务, gRPC, MySQL, Redis, Kubernetes, Linux", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 免费三餐, 弹性工作", "contact_person": "张先生", "contact_title": "后端负责人", "url": "https://www.zhipin.com/job_detail/seed_029.html", "source": "种子数据"},
    {"title": "C++开发工程师", "company": "大疆", "salary": "25-50K·14薪", "city": "深圳", "district": "南山区", "experience": "3-5年", "education": "本科", "skills": "C++, Linux, 嵌入式, RTOS, 多线程, STL", "company_size": "10000人以上", "company_stage": "D轮及以上", "industry": "智能硬件", "welfare": "五险一金, 年终奖, 双休, 健身房", "contact_person": "梁先生", "contact_title": "嵌入式TL", "url": "https://www.zhipin.com/job_detail/seed_030.html", "source": "种子数据"},
    {"title": "Python爬虫工程师", "company": "小红书", "salary": "18-35K·15薪", "city": "上海", "district": "黄浦区", "experience": "1-3年", "education": "本科", "skills": "Python, Scrapy, 反爬虫, Selenium, MongoDB, Redis", "company_size": "1000-9999人", "company_stage": "D轮及以上", "industry": "社交", "welfare": "五险一金, 弹性工作, 双休, 零食下午茶", "contact_person": "朱女士", "contact_title": "数据采集组长", "url": "https://www.zhipin.com/job_detail/seed_031.html", "source": "种子数据"},
    {"title": "后端开发实习生", "company": "字节跳动", "salary": "6-10K", "city": "北京", "district": "海淀区", "experience": "应届生", "education": "本科", "skills": "Python或Go, 计算机基础, 数据结构, 算法, Linux", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "五险一金, 免费三餐, 转正机会", "contact_person": "张先生", "contact_title": "校招负责人", "url": "https://www.zhipin.com/job_detail/seed_032.html", "source": "种子数据"},
    {"title": "前端开发实习生", "company": "小红书", "salary": "5-8K", "city": "上海", "district": "黄浦区", "experience": "应届生", "education": "本科", "skills": "HTML, CSS, JavaScript, React, Vue.js, Git", "company_size": "1000-9999人", "company_stage": "D轮及以上", "industry": "社交", "welfare": "弹性工作, 零食下午茶, 转正机会", "contact_person": "朱女士", "contact_title": "校招HR", "url": "https://www.zhipin.com/job_detail/seed_033.html", "source": "种子数据"},
    {"title": "数据分析实习生", "company": "滴滴", "salary": "5-8K", "city": "北京", "district": "海淀区", "experience": "应届生", "education": "本科", "skills": "SQL, Python, Excel, 统计学, 数据可视化", "company_size": "10000人以上", "company_stage": "已上市", "industry": "出行", "welfare": "五险一金, 弹性工作, 转正机会", "contact_person": "马先生", "contact_title": "数据分析师", "url": "https://www.zhipin.com/job_detail/seed_034.html", "source": "种子数据"},
    {"title": "Java开发实习生", "company": "阿里巴巴", "salary": "6-10K", "city": "杭州", "district": "余杭区", "experience": "应届生", "education": "本科", "skills": "Java, Spring, MySQL, 数据结构, 算法, 计算机网络", "company_size": "10000人以上", "company_stage": "已上市", "industry": "互联网", "welfare": "六险一金, 餐补, 转正机会, 导师制", "contact_person": "李女士", "contact_title": "校招HR", "url": "https://www.zhipin.com/job_detail/seed_035.html", "source": "种子数据"},
]


def seed():
    conn = sqlite3.connect(DB_PATH)
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

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for j in JOBS:
        salary_min = salary_max = salary_avg = None
        import re
        s = j.get("salary", "")
        m = re.search(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*K", s, re.IGNORECASE)
        if m:
            salary_min = float(m.group(1)) * 1000
            salary_max = float(m.group(2)) * 1000
            salary_avg = (salary_min + salary_max) / 2

        cur.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                j["title"], j["company"], j["salary"], j["city"], j.get("district", ""),
                j["experience"], j["education"], j["skills"], j.get("company_size", ""),
                j.get("company_stage", ""), j["industry"], j.get("welfare", ""),
                j.get("contact_person", ""), j.get("contact_title", ""),
                j["url"], j["source"],
                salary_min, salary_max, salary_avg, now,
            ),
        )

    conn.commit()
    conn.close()
    print(f"已写入 {len(JOBS)} 条种子数据到 {DB_PATH}")


if __name__ == "__main__":
    seed()
