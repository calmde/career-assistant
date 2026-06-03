"""
岗位描述与简历结构化解析器。

将非结构化文本转化为标准化需求标签，供 matcher / optimizer / skill_navigator 消费。
"""
import re
import jieba
from difflib import get_close_matches

# ============================================================
# 技能词表（200+ 条目 + 别名归一化）
# 键为规范名，值为别名列表（含自身）
# ============================================================

SKILL_ALIASES: dict[str, list[str]] = {
    # --- 编程语言 ---
    "python":         ["python", "python3", "py", "python开发"],
    "java":           ["java", "java8", "java11", "java开发", "java se", "java ee", "spring"],
    "javascript":     ["javascript", "js", "es6", "es7", "ecmascript", "nodejs", "node.js", "node"],
    "typescript":     ["typescript", "ts"],
    "go":             ["go", "golang", "go语言"],
    "rust":           ["rust", "rs"],
    "c++":            ["c++", "cpp", "c plus plus"],
    "c":              ["c语言", "c programming"],
    "csharp":         ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "ruby":           ["ruby", "ror", "ruby on rails"],
    "php":            ["php", "php7", "php8", "laravel"],
    "swift":          ["swift", "swiftui", "ios开发"],
    "kotlin":         ["kotlin", "android开发"],
    "scala":          ["scala"],
    "r":              ["r语言", "r programming"],
    "matlab":         ["matlab"],

    # --- 前端 ---
    "react":          ["react", "react.js", "reactjs", "react native", "react-native", "rn"],
    "vue":            ["vue", "vue.js", "vuejs", "vue2", "vue3", "vuex", "pinia"],
    "angular":        ["angular", "angularjs", "angular2+", "ng"],
    "html":           ["html", "html5", "h5"],
    "css":            ["css", "css3", "scss", "sass", "less", "stylus", "tailwind", "bootstrap"],
    "jquery":         ["jquery"],
    "webpack":        ["webpack", "vite", "rollup", "esbuild"],
    "electron":       ["electron"],

    # --- 后端框架 ---
    "django":         ["django", "django rest", "drf"],
    "flask":          ["flask", "flask-restful"],
    "fastapi":        ["fastapi"],
    "spring boot":    ["spring boot", "spring cloud", "spring mvc", "springboot"],
    "express":        ["express", "express.js"],
    "gin":            ["gin", "gin-gonic"],
    "mybatis":        ["mybatis", "mybatis-plus"],
    "hibernate":      ["hibernate", "jpa"],

    # --- 数据库 ---
    "mysql":          ["mysql", "mariadb"],
    "postgresql":     ["postgresql", "postgres", "pg"],
    "mongodb":        ["mongodb", "mongo"],
    "redis":          ["redis", "redis集群"],
    "elasticsearch":  ["elasticsearch", "es", "elastic"],
    "sqlite":         ["sqlite", "sqlite3"],
    "oracle":         ["oracle", "oracle database", "pl/sql"],
    "sqlserver":      ["sqlserver", "sql server", "mssql", "t-sql"],
    "cassandra":      ["cassandra"],
    "neo4j":          ["neo4j", "图数据库"],
    "hbase":          ["hbase"],
    "clickhouse":     ["clickhouse"],
    "tidb":           ["tidb"],

    # --- 云 & DevOps ---
    "aws":            ["aws", "amazon web services", "s3", "ec2", "lambda"],
    "azure":          ["azure", "microsoft azure"],
    "gcp":            ["gcp", "google cloud", "google cloud platform"],
    "docker":         ["docker", "docker compose", "容器化"],
    "kubernetes":     ["kubernetes", "k8s", "kube", "容器编排"],
    "jenkins":        ["jenkins", "ci/cd", "持续集成"],
    "gitlab-ci":      ["gitlab ci", "gitlab-ci", "gitlab cicd"],
    "github actions": ["github actions", "gh actions", "cicd"],
    "terraform":      ["terraform", "iac", "基础设施即代码"],
    "ansible":        ["ansible"],
    "nginx":          ["nginx", "nginx配置"],
    "prometheus":     ["prometheus", "grafana"],
    "elk":            ["elk", "elk stack", "elastic stack"],
    "linux":          ["linux", "ubuntu", "centos", "debian", "shell"],

    # --- 大数据 ---
    "hadoop":         ["hadoop", "hdfs", "mapreduce", "yarn"],
    "spark":          ["spark", "apache spark", "pyspark", "spark sql", "spark streaming"],
    "flink":          ["flink", "apache flink"],
    "kafka":          ["kafka", "apache kafka", "消息队列"],
    "hive":           ["hive", "apache hive", "hql"],
    "airflow":        ["airflow", "apache airflow"],
    "flume":          ["flume"],
    "zookeeper":      ["zookeeper", "zk"],

    # --- AI / 机器学习 ---
    "machine learning":   ["machine learning", "机器学习", "ml"],
    "deep learning":      ["deep learning", "深度学习", "dl"],
    "nlp":                ["nlp", "自然语言处理", "自然语言"],
    "computer vision":    ["computer vision", "计算机视觉", "cv", "图像识别", "目标检测"],
    "pytorch":            ["pytorch", "torch"],
    "tensorflow":         ["tensorflow", "tf", "keras"],
    "scikit-learn":       ["scikit-learn", "sklearn", "scikit learn"],
    "pandas":             ["pandas", "数据处理"],
    "numpy":              ["numpy", "数值计算"],
    "scipy":              ["scipy"],
    "transformer":        ["transformer", "attention", "bert", "gpt", "llm", "大模型", "大语言模型"],
    "opencv":             ["opencv", "cv2"],
    "langchain":          ["langchain", "langchain应用"],
    "huggingface":        ["huggingface", "hugging face", "transformers库"],

    # --- 数据分析 ---
    "data analysis":      ["data analysis", "数据分析", "da"],
    "excel":              ["excel", "电子表格"],
    "tableau":            ["tableau"],
    "power bi":           ["power bi", "powerbi", "pbi"],
    "sql":                ["sql", "结构化查询"],
    "spss":               ["spss"],
    "sas":                ["sas"],

    # --- 通用工具 ---
    "git":                ["git", "版本控制", "github", "gitlab", "gitee"],
    "rest api":           ["rest api", "restful", "restful api", "api开发"],
    "grpc":               ["grpc", "protobuf"],
    "graphql":            ["graphql", "gql"],
    "websocket":          ["websocket", "ws"],
    "oauth":              ["oauth", "oauth2", "oidc", "jwt"],
    "rabbitmq":           ["rabbitmq", "rabbit mq"],
    "celery":             ["celery", "异步任务"],
    "unittest":           ["unittest", "单元测试", "pytest", "jest", "mocha", "测试"],
    "agile":              ["agile", "敏捷", "scrum", "kanban"],

    # --- 中文技能 ---
    "后端开发":           ["后端", "后端开发", "服务端", "后台开发"],
    "前端开发":           ["前端", "前端开发", "web前端"],
    "全栈开发":           ["全栈", "全栈开发", "fullstack"],
    "爬虫":               ["爬虫", "数据采集", "网络爬虫", "scrapy", "selenium爬虫"],
    "微服务":             ["微服务", "microservices", "服务网格", "spring cloud"],
    "小程序":             ["小程序", "微信小程序", "小程序开发", "uniapp", "taro"],
    "移动端":             ["移动端", "app开发", "android", "ios", "flutter", "react native"],
}

# 反向索引：别名 → 规范名
CANONICAL_SKILL: dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    for alias in aliases:
        alias_lower = alias.lower()
        if alias_lower not in CANONICAL_SKILL or len(alias_lower) > len(canonical):
            CANONICAL_SKILL[alias_lower] = canonical

# ============================================================
# 学历映射（从 analyze_match.py 迁移，扩展）
# ============================================================
DEGREE_RANK: dict[str, int] = {
    'phd': 4, '博士': 4, '博士研究生': 4, 'ph.d': 4,
    'master': 3, '硕士': 3, '硕士研究生': 3, 'ms': 3, 'm.s.': 3,
    'bachelor': 2, '本科': 2, '学士': 2, 'ba': 2, 'bs': 2, 'b.s.': 2, 'b.a.': 2,
    'associate': 1, '大专': 1, '专科': 1,
    'high school': 0, '中学': 0, '高中': 0,
    '统招本科': 2, '全日制本科': 2, '全日制硕士': 3, '985': 2, '211': 2,
}

# ============================================================
# 岗位类别分类器
# ============================================================
ROLE_CATEGORIES: dict[str, list[str]] = {
    "backend": [
        "后端", "后台", "服务端", "java开发", "python开发", "go开发", "c++开发",
        "php开发", "ruby开发", "dotnet", ".net", "spring", "django", "flask",
        "gin", "fastapi", "laravel", "mybatis", "hibernate", "微服务",
    ],
    "frontend": [
        "前端", "web前端", "h5", "html5", "react", "vue", "angular", "js",
        "javascript", "typescript", "css", "ui开发", "小程序", "uniapp", "taro",
        "flutter", "electron",
    ],
    "algorithm": [
        "算法", "机器学习", "深度学习", "nlp", "自然语言处理", "cv", "计算机视觉",
        "推荐算法", "搜索算法", "广告算法", "pytorch", "tensorflow", "transformer",
        "bert", "gpt", "llm", "大模型", "数据挖掘", "模式识别", "语音识别",
    ],
    "data": [
        "数据分析", "数据分析师", "数据开发", "数据工程", "etl", "sql",
        "excel", "tableau", "power bi", "bi", "hadoop", "spark", "flink",
        "hive", "clickhouse", "数据仓库", "数据湖", "数据治理",
    ],
    "testing": [
        "测试", "qa", "质量", "自动化测试", "selenium", "appium", "jmeter",
        "性能测试", "接口测试", "压力测试", "安全测试", "渗透测试",
    ],
    "ops": [
        "运维", "devops", "sre", "docker", "kubernetes", "k8s", "jenkins",
        "linux", "监控", "prometheus", "grafana", "ansible", "terraform",
        "网络", "安全", "系统管理员",
    ],
    "product": [
        "产品经理", "产品", "pm", "prd", "需求分析", "axure", "墨刀",
        "用户体验", "ux", "交互设计", "figma",
    ],
}

# ============================================================
# 行业分类器
# ============================================================
INDUSTRY_CATEGORIES: dict[str, list[str]] = {
    "internet":    ["互联网", "移动互联网", "电商", "o2o", "社交", "社区", "内容", "信息流"],
    "finance":     ["金融", "银行", "证券", "保险", "基金", "风控", "支付", "借贷", "量化", "征信"],
    "education":   ["教育", "培训", "在线教育", "k12", "steam", "慕课", "课程"],
    "games":       ["游戏", "手游", "页游", "unity", "unreal", "ue4", "ue5", "cocos", "棋牌"],
    "ecommerce":   ["电商", "电子商务", "跨境电商", "新零售", "零售", "o2o"],
    "enterprise":  ["企业服务", "saas", "paas", "erp", "crm", "人力资源", "协同办公", "oa"],
    "healthcare":  ["医疗", "医药", "健康", "医院", "远程医疗", "医疗器械", "基因"],
    "auto":        ["汽车", "自动驾驶", "新能源", "智能驾驶", "车联网", "adas"],
    "media":       ["媒体", "广告", "短视频", "直播", "影视", "娱乐"],
    "hardware":    ["硬件", "芯片", "半导体", "物联网", "iot", "机器人", "智能硬件"],
    "realestate":  ["房地产", "房产", "物业", "装修"],
    "logistics":   ["物流", "快递", "供应链", "仓储"],
}

# 行业邻接矩阵（用于匹配引擎部分匹配评分）
INDUSTRY_ADJACENCY: dict[str, set[str]] = {
    "internet":    {"ecommerce", "media", "enterprise", "education"},
    "ecommerce":   {"internet", "logistics"},
    "finance":     {"enterprise", "internet"},
    "enterprise":  {"internet", "finance", "logistics"},
    "education":   {"internet", "media"},
    "games":       {"internet", "media"},
    "media":       {"internet", "games", "ecommerce"},
}

# ============================================================
# 软技能词表
# ============================================================
SOFT_SKILLS: list[str] = [
    "沟通能力", "沟通", "表达", "团队协作", "团队合作", "协作", "项目管理",
    "领导力", "领导", "管理", "抗压", "抗压能力", "解决问题", "学习能力",
    "自驱", "主动", "主动性", "自驱力", "owner", "责任心", "负责",
    "逻辑思维", "逻辑", "创新", "创新力", "执行力", "执行", "时间管理",
    "适应能力", "适应", "跨部门", "协调", "组织", "英语", "文档",
]

# ============================================================
# 福利标签词表
# ============================================================
WELFARE_TAGS: list[str] = [
    "双休", "弹性工作", "远程办公", "远程", "六险一金", "五险一金",
    "年终奖", "年终", "股票期权", "期权", "股权", "带薪年假", "年假",
    "餐补", "房补", "交通补贴", "交通补助", "团建", "定期体检", "体检",
    "加班补助", "零食", "下午茶", "健身房", "补充医疗",
]

# ============================================================
# 中文数字映射
# ============================================================
_CN_NUM_MAP: dict[str, int] = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def _parse_chinese_number(text: str) -> int | None:
    """解析中文数字词（如 三、五、十）为整数。"""
    if text in _CN_NUM_MAP:
        return _CN_NUM_MAP[text]
    return None


# ============================================================
# 公共工具函数
# ============================================================

def normalize(text: str) -> str:
    return text.lower()


def extract_skills(text: str) -> dict[str, list[str]]:
    """从文本提取硬技能和软技能。
    Returns: {'hard': [canonical_names], 'soft': [names]}
    """
    t = text.lower()
    found_hard: set[str] = set()
    found_soft: set[str] = set()

    # 硬技能匹配：遍历所有别名
    for alias, canonical in CANONICAL_SKILL.items():
        if len(alias) < 3:
            # 短别名用词边界匹配，避免"go"误匹配"dialog"等
            if re.search(rf"\b{re.escape(alias)}\b", t):
                found_hard.add(canonical)
        else:
            if alias in t:
                found_hard.add(canonical)

    # 分词后近似匹配（jieba）
    try:
        tokens = list(jieba.cut(text))
    except Exception:
        tokens = []

    for tok in tokens:
        tok_lower = tok.lower().strip()
        if len(tok_lower) < 2:
            continue
        # 精确匹配别名
        if tok_lower in CANONICAL_SKILL:
            found_hard.add(CANONICAL_SKILL[tok_lower])
            continue
        # difflib 近似匹配
        matches = get_close_matches(tok_lower, list(CANONICAL_SKILL.keys()), n=1, cutoff=0.92)
        if matches:
            found_hard.add(CANONICAL_SKILL[matches[0]])

    # 软技能匹配
    for s in SOFT_SKILLS:
        if s in text:
            found_soft.add(s)

    # 英文单词提取兜底
    eng_tokens = re.findall(r"[A-Za-z+#]{2,}(?:[-.][A-Za-z+#]+)*", text)
    for tok in eng_tokens:
        tok_l = tok.lower()
        if tok_l in CANONICAL_SKILL:
            found_hard.add(CANONICAL_SKILL[tok_l])

    return {
        "hard": sorted(found_hard),
        "soft": sorted(found_soft),
    }


def extract_experience(text: str) -> dict:
    """提取经验要求。
    Returns: {'min_years': int|None, 'max_years': int|None, 'level': str, 'raw': str}
    """
    t = text

    # 应届/无经验
    if re.search(r"应届|校招|经验不限|无经验|实习生|毕业生|培训生", t):
        return {"min_years": 0, "max_years": 1, "level": "entry", "raw": "应届/不限"}

    years_vals: list[int] = []

    # 英文/数字格式：3 years / 3+ years / 3-5 years
    for m in re.findall(r"(\d+)\+?\s*(?:years|年)", t, flags=re.I):
        try:
            years_vals.append(int(m))
        except ValueError:
            pass

    # 中文数字格式：三年以上 / 五到十年
    cn_patterns = [
        r"([一二两三四五六七八九十])\s*年\s*(?:以上|及以上)",
        r"([一二两三四五六七八九十])\s*[到至\-~]\s*([一二两三四五六七八九十])\s*年",
    ]
    for m in re.findall(cn_patterns[0], t):
        num = _parse_chinese_number(m)
        if num is not None:
            years_vals.append(num)
    for m in re.findall(cn_patterns[1], t):
        a, b = _parse_chinese_number(m[0]), _parse_chinese_number(m[1])
        if a is not None and b is not None:
            years_vals.append(b)  # 取上界

    # 范围格式：3-5年 / 3到5年
    range_m = re.findall(r"(\d+)\s*[到\-~]\s*(\d+)\s*年", t)
    for lo, hi in range_m:
        try:
            years_vals.append(int(hi))
        except ValueError:
            pass

    # 纯数字年份：X年（不在范围模式中已匹配的）
    single_m = re.findall(r"(\d+)\+?\s*年", t)
    for m in single_m:
        try:
            years_vals.append(int(m))
        except ValueError:
            pass

    if not years_vals:
        return {"min_years": None, "max_years": None, "level": "unknown", "raw": ""}

    max_y = max(years_vals)

    # 分级
    if max_y <= 1:
        level = "junior"
    elif max_y <= 3:
        level = "junior"
    elif max_y <= 5:
        level = "mid"
    elif max_y <= 8:
        level = "senior"
    else:
        level = "staff"

    return {
        "min_years": min(years_vals) if len(years_vals) > 1 else None,
        "max_years": max_y,
        "level": level,
        "raw": f"约{max_y}年",
    }


def extract_education(text: str) -> dict:
    """提取学历要求。
    Returns: {'degree': str|None, 'rank': int, 'raw': str}
    """
    t = text
    best_kw = None
    best_rank = -1
    for kw in DEGREE_RANK:
        if kw in t:
            r = DEGREE_RANK[kw]
            if r > best_rank:
                best_rank = r
                best_kw = kw

    # 检测 985/211
    elite = bool(re.search(r"985|211|双一流", t))

    return {
        "degree": best_kw,
        "rank": best_rank,
        "elite_preferred": elite,
        "raw": best_kw or "学历不限",
    }


def extract_role_category(text: str) -> dict:
    """分类岗位角色。
    Returns: {'primary': str|None, 'confidence': float}
    """
    scores: dict[str, int] = {}
    t_lower = text.lower()

    for category, keywords in ROLE_CATEGORIES.items():
        count = 0
        for kw in keywords:
            if kw.lower() in t_lower:
                count += 1
        if count > 0:
            scores[category] = count

    if not scores:
        return {"primary": None, "confidence": 0.0}

    total = sum(scores.values())
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return {"primary": best, "confidence": round(scores[best] / total, 2)}


def extract_industry(text: str) -> dict:
    """分类行业领域。
    Returns: {'primary': str|None, 'confidence': float}
    """
    scores: dict[str, int] = {}
    for category, keywords in INDUSTRY_CATEGORIES.items():
        count = 0
        for kw in keywords:
            if kw in text:
                count += 1
        if count > 0:
            scores[category] = count

    if not scores:
        return {"primary": None, "confidence": 0.0}

    total = sum(scores.values())
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return {"primary": best, "confidence": round(scores[best] / total, 2)}


def extract_welfare(text: str) -> list[str]:
    """提取福利标签。"""
    found = []
    for tag in WELFARE_TAGS:
        if tag in text:
            found.append(tag)
    return found


# ============================================================
# 公共接口
# ============================================================

def parse_job_description(text: str) -> dict:
    """解析岗位描述文本为结构化需求标签。"""
    if not text or not text.strip():
        return _empty_result()

    skills = extract_skills(text)
    exp = extract_experience(text)
    edu = extract_education(text)
    role = extract_role_category(text)
    industry = extract_industry(text)
    welfare = extract_welfare(text)

    return {
        "skills": {"hard": skills["hard"], "soft": skills["soft"]},
        "experience": exp,
        "education": edu,
        "role_category": role,
        "industry": industry,
        "welfare": welfare,
        "raw_text": text,
    }


def parse_resume(text: str) -> dict:
    """解析简历文本为结构化数据（与 parse_job_description 输出格式一致）。"""
    if not text or not text.strip():
        return _empty_result()

    skills = extract_skills(text)
    exp = extract_experience(text)
    edu = extract_education(text)
    role = extract_role_category(text)
    industry = extract_industry(text)
    welfare = extract_welfare(text)

    # 简历通常没有 welfare/role_category/industry（是申请人自己而非岗位）
    # 但保持接口一致

    return {
        "skills": {"hard": skills["hard"], "soft": skills["soft"]},
        "experience": exp,
        "education": edu,
        "role_category": role,
        "industry": industry,
        "welfare": welfare,
        "raw_text": text,
    }


def _empty_result() -> dict:
    """空输入时返回的空结果。"""
    return {
        "skills": {"hard": [], "soft": []},
        "experience": {"min_years": None, "max_years": None, "level": "unknown", "raw": ""},
        "education": {"degree": None, "rank": -1, "elite_preferred": False, "raw": "不限"},
        "role_category": {"primary": None, "confidence": 0.0},
        "industry": {"primary": None, "confidence": 0.0},
        "welfare": [],
        "raw_text": "",
    }


# ============================================================
# 行业邻接查询（供 matcher.py 使用）
# ============================================================

def get_related_industries(industry_name: str) -> set[str]:
    """返回给定行业的邻接行业集合。"""
    return INDUSTRY_ADJACENCY.get(industry_name, set())


# ============================================================
# 岗位类别相关度评分（供 matcher.py 使用）
# ============================================================

_ROLE_RELATED: dict[str, set[str]] = {
    "backend":  {"fullstack", "ops", "data"},
    "frontend": {"fullstack", "product"},
    "algorithm": {"data"},
    "data":     {"backend", "algorithm"},
    "testing":  {"ops"},
    "ops":      {"backend", "testing"},
    "product":  {"frontend"},
}


def get_role_relatedness(cat_a: str, cat_b: str) -> float:
    """返回两个岗位类别的相关度（0.0 ~ 1.0）。"""
    if not cat_a or not cat_b:
        return 0.5
    if cat_a == cat_b:
        return 1.0
    related = _ROLE_RELATED.get(cat_a, set())
    if cat_b in related:
        return 0.5
    return 0.0
