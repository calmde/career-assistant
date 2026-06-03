"""
技能导航器 — 针对缺失技能生成可执行的学习提升计划。

功能：技能重要性分级 / 缺口等级评估 / 学习资源推荐 / LLM增强学习路径 / 替代岗位推荐。
"""
import re
from llm_client import call_llm, make_cache_key, get_cached, set_cache, is_llm_available

# ============================================================
# 学习资源库（本地离线数据，50+ 技能）
# ============================================================

LEARNING_RESOURCES: dict[str, dict] = {
    "python": {
        "courses": ["Python官方教程 (docs.python.org)", "廖雪峰Python教程", "CS50 Python"],
        "books": ["《Python编程：从入门到实践》", "《流畅的Python》"],
        "projects": ["用Flask/Django搭建个人博客", "爬虫数据采集实战", "自动化脚本工具"],
        "duration": "4-8周",
    },
    "java": {
        "courses": ["Java SE官方教程", "尚硅谷Java教程"],
        "books": ["《Java核心技术》", "《Effective Java》"],
        "projects": ["Spring Boot REST API", "学生管理系统"],
        "duration": "8-12周",
    },
    "javascript": {
        "courses": ["MDN Web Docs", "freeCodeCamp JavaScript"],
        "books": ["《JavaScript高级程序设计》", "《你不知道的JavaScript》"],
        "projects": ["Todo应用", "天气查询Web App", "个人博客前端"],
        "duration": "4-8周",
    },
    "react": {
        "courses": ["React官方文档 (react.dev)", "Udemy React教程"],
        "books": [],
        "projects": ["个人作品集网站", "电商购物车", "后台管理面板"],
        "duration": "4-6周",
    },
    "vue": {
        "courses": ["Vue.js官方文档", "Vue Mastery"],
        "books": [],
        "projects": ["任务管理应用", "社区论坛前端"],
        "duration": "3-5周",
    },
    "django": {
        "courses": ["Django官方教程", "Django for Everybody"],
        "books": ["《Django Web开发指南》"],
        "projects": ["博客系统", "在线问答平台", "REST API服务"],
        "duration": "4-6周",
    },
    "docker": {
        "courses": ["Docker官方文档", "Play with Docker"],
        "books": ["《Docker技术入门与实战》"],
        "projects": ["容器化个人项目", "多容器应用部署"],
        "duration": "2-3周",
    },
    "kubernetes": {
        "courses": ["Kubernetes官方教程", "kube.academy"],
        "books": ["《Kubernetes权威指南》"],
        "projects": ["部署微服务到K8s集群", "搭建本地开发环境"],
        "duration": "4-8周",
    },
    "mysql": {
        "courses": ["MySQL官方文档", "SQLZoo练习"],
        "books": ["《高性能MySQL》"],
        "projects": ["设计电商数据库", "慢查询优化实战"],
        "duration": "2-4周",
    },
    "redis": {
        "courses": ["Redis官方文档", "Redis University"],
        "books": ["《Redis设计与实现》"],
        "projects": ["缓存系统设计", "排行榜实现", "分布式锁"],
        "duration": "2-3周",
    },
    "git": {
        "courses": ["Git官方文档", "Learn Git Branching"],
        "books": ["《Pro Git》"],
        "projects": ["参与开源项目", "团队协作模拟"],
        "duration": "1-2周",
    },
    "linux": {
        "courses": ["Linux Journey", "鸟哥的Linux私房菜"],
        "books": ["《鸟哥的Linux私房菜》"],
        "projects": ["搭建个人服务器", "Shell脚本自动化"],
        "duration": "3-6周",
    },
    "machine learning": {
        "courses": ["吴恩达机器学习 (Coursera)", "李宏毅机器学习"],
        "books": ["《机器学习》(周志华)", "《统计学习方法》(李航)"],
        "projects": ["房价预测", "手写数字识别", "文本分类"],
        "duration": "8-16周",
    },
    "deep learning": {
        "courses": ["吴恩达深度学习 (Coursera)", "fast.ai"],
        "books": ["《深度学习》(Ian Goodfellow)"],
        "projects": ["图像分类", "文本生成", "目标检测"],
        "duration": "8-16周",
    },
    "pytorch": {
        "courses": ["PyTorch官方教程", "d2l.ai《动手学深度学习》"],
        "books": ["《动手学深度学习》"],
        "projects": ["图像分类器", "语言模型训练"],
        "duration": "4-8周",
    },
    "nlp": {
        "courses": ["CS224n (Stanford)", "HuggingFace NLP Course"],
        "books": ["《自然语言处理综论》"],
        "projects": ["情感分析", "文本摘要", "聊天机器人"],
        "duration": "8-16周",
    },
    "spark": {
        "courses": ["Spark官方文档", "Databricks Academy"],
        "books": ["《Spark快速大数据分析》"],
        "projects": ["日志分析", "用户行为分析", "ETL管道"],
        "duration": "4-8周",
    },
    "kafka": {
        "courses": ["Kafka官方文档", "Confluent教程"],
        "books": ["《Kafka权威指南》"],
        "projects": ["消息队列应用", "事件驱动架构实践"],
        "duration": "2-4周",
    },
    "aws": {
        "courses": ["AWS官方培训", "AWS Certified Cloud Practitioner"],
        "books": [],
        "projects": ["部署Web应用到EC2", "S3静态网站托管", "Lambda函数"],
        "duration": "4-8周",
    },
    "elasticsearch": {
        "courses": ["Elastic官方文档", "Elasticsearch Essential Training"],
        "books": ["《Elasticsearch权威指南》"],
        "projects": ["全文搜索引擎", "日志分析平台"],
        "duration": "2-4周",
    },
    "_default": {
        "courses": ["慕课网 (imooc.com)", "B站免费教程", "Coursera/edX"],
        "books": ["搜索相关技术书籍"],
        "projects": ["查找开源项目练习", "从零搭建一个Demo"],
        "duration": "视具体技能而定",
    },
}

# ============================================================
# 替代岗位推荐矩阵
# ============================================================

ALTERNATIVE_PATHS: dict[str, list[dict]] = {
    "backend": [
        {"title": "全栈开发", "reason": "后端+前端基础即可转型，市场需求大"},
        {"title": "数据开发", "reason": "SQL和数据处理基础相通"},
        {"title": "DevOps/SRE", "reason": "如果对部署运维感兴趣可以转型"},
    ],
    "frontend": [
        {"title": "全栈开发", "reason": "加学一门后端语言即可"},
        {"title": "移动端开发", "reason": "React Native/Flutter技术栈相近"},
        {"title": "UI/UX设计", "reason": "如果对视觉设计有天赋"},
    ],
    "algorithm": [
        {"title": "数据分析", "reason": "数理基础相通，门槛较低"},
        {"title": "后端开发", "reason": "转向AI工程化方向"},
    ],
    "data": [
        {"title": "后端开发", "reason": "数据处理技能对后端很有价值"},
        {"title": "算法工程师", "reason": "升级技能即可转向"},
    ],
    "testing": [
        {"title": "后端开发", "reason": "代码能力提升后可以转开发"},
        {"title": "DevOps", "reason": "自动化测试与CI/CD紧密相关"},
    ],
    "ops": [
        {"title": "后端开发", "reason": "已有基础设施视角，加应用开发技能"},
        {"title": "安全工程师", "reason": "运维基础对安全有帮助"},
    ],
}

# ============================================================
# Prompt 模板
# ============================================================

SKILL_PLAN_PROMPT = """你是一位职业规划师。请为以下情况生成学习计划。

【目标岗位】{job_title}
【已有技能】{existing_skills}
【缺失技能（按优先级排序）】{missing_skills}
【缺口等级】{gap_level}

请输出：
1. 分阶段学习计划（每阶段1-2周，具体到每周目标和里程碑）
2. 推荐的在线课程和书籍（具体名称）
3. 2-3个可放入简历的练手项目描述
4. 总计预计学习周期
5. 如果缺口太大（critical），推荐3个更匹配的替代岗位方向

用中文回答，分步清晰。"""

ALTERNATIVE_JOB_PROMPT = """你是一位职业规划师。求职者的技能与目标岗位差距较大。

【目标岗位】{job_title}
【求职者已有技能】{existing_skills}
【目标岗位要求技能】{required_skills}

请推荐3个更适合该求职者当前技能水平的岗位方向，并说明每个方向的推荐理由。用中文回答。"""

# ============================================================
# 技能重要性分类（本地规则）
# ============================================================

def classify_skill_importance(
    missing_skills: list[str],
    job_raw_text: str,
    existing_skills: list[str],
) -> list[dict]:
    """根据岗位描述文本判断每个缺失技能的重要性级别（core / nice_to_have）。

    规则：
    - 出现在JD前30%位置 或 重复2次以上 → core
    - 出现在JD末尾 或 含"优先"/"preferred"/"bonus"/"加分" → nice_to_have
    - 其他 → 根据位置判断
    """
    if not missing_skills:
        return []

    text_lower = job_raw_text.lower()
    results = []

    for skill in missing_skills:
        skill_lower = skill.lower()
        # 查找skill在文本中的所有出现位置
        positions = [m.start() for m in re.finditer(re.escape(skill_lower), text_lower)]
        count = len(positions)

        # 核心判断
        is_core = False
        is_nice = False

        # 复现次数 >= 2 → core
        if count >= 2:
            is_core = True
        # 出现在JD前30%
        elif positions:
            first_pos_pct = positions[0] / max(len(text_lower), 1)
            if first_pos_pct < 0.3:
                is_core = True

        # "优先"关键词检测
        for pos in positions:
            context_start = max(0, pos - 30)
            context_end = min(len(text_lower), pos + len(skill_lower) + 30)
            context = text_lower[context_start:context_end]
            if any(kw in context for kw in ["优先", "preferred", "bonus", "加分", "更好"]):
                is_nice = True
                break

        if is_nice:
            importance = "nice_to_have"
        elif is_core:
            importance = "core"
        else:
            importance = "core"  # 默认为核心，JD中提到的技能都重要

        results.append({
            "skill": skill,
            "importance": importance,
            "occurrences": count,
        })

    # 按core优先排序
    results.sort(key=lambda x: (0 if x["importance"] == "core" else 1, -x["occurrences"]))
    return results


def assess_gap_level(match_report: dict) -> dict:
    """评估技能缺口等级。

    Returns: {'level': 'edge'|'significant'|'critical', 'core_missing': int, 'total_missing': int, 'advice': str}
    """
    total_missing = len(match_report.get("missing_skills", []))
    # 简单估计：前50%的缺失技能为核心缺失
    core_missing = max(0, total_missing // 2) if total_missing <= 4 else total_missing - 2

    if total_missing <= 2:
        level = "edge"
        advice = "技能缺口很小，通过1-2周的集中学习即可补齐。可以同时投递简历。"
    elif total_missing <= 5:
        level = "significant"
        advice = "有一定技能缺口，建议边学习边投递，重点关注缺口较小的岗位。"
    else:
        level = "critical"
        advice = "技能缺口较大，建议优先系统学习，同时考虑替代岗位方向。"

    return {
        "level": level,
        "core_missing_count": core_missing,
        "total_missing_count": total_missing,
        "advice": advice,
    }


# ============================================================
# 本地降级生成
# ============================================================

def _local_weekly_plan(skill_importance: list[dict]) -> list[dict]:
    """生成本地学习计划。"""
    if not skill_importance:
        return []

    weeks = []
    core_skills = [s for s in skill_importance if s["importance"] == "core"]
    nice_skills = [s for s in skill_importance if s["importance"] == "nice_to_have"]

    for i, s in enumerate(core_skills[:3]):
        skill_name = s["skill"]
        res = LEARNING_RESOURCES.get(skill_name, LEARNING_RESOURCES["_default"])
        weeks.append({
            "week": i + 1,
            "goal": f"掌握 {skill_name} 基础",
            "resources": res["courses"][:2] + res["books"][:1],
            "project": res["projects"][:1] if res["projects"] else [],
        })

    if nice_skills:
        skill_name = nice_skills[0]["skill"]
        res = LEARNING_RESOURCES.get(skill_name, LEARNING_RESOURCES["_default"])
        weeks.append({
            "week": len(weeks) + 1,
            "goal": f"学习 {skill_name}（加分项）",
            "resources": res["courses"][:1],
            "project": res["projects"][:1] if res["projects"] else [],
        })

    return weeks


def _local_alternative_jobs(job_parsed: dict) -> list[dict]:
    """本地替代岗位推荐。"""
    role = job_parsed["role_category"]["primary"]
    default = [
        {"title": "建议扩大搜索范围", "reason": "当前岗位缺口较大，可尝试投递相关方向"},
    ]
    return ALTERNATIVE_PATHS.get(role, default)


# ============================================================
# 公共接口
# ============================================================

def generate_skill_plan(
    missing_skills: list[str],
    existing_skills: list[str],
    job_parsed: dict,
    match_report: dict,
    resume_text: str = "",
    job_id: str = "",
) -> dict:
    """生成技能提升计划。

    Returns:
        dict: {
            'skill_importance': [...],
            'gap_assessment': {...},
            'learning_plan': {'weekly_plan': [...], 'total_duration': str, 'recommended_resources': [...]},
            'alternative_jobs': [...],
            'used_llm': bool,
        }
    """
    job_text = job_parsed.get("raw_text", "")
    use_llm = is_llm_available()

    # 1. 技能重要性分级（本地规则，不依赖LLM）
    importance = classify_skill_importance(missing_skills, job_text, existing_skills)

    # 2. 缺口评估（本地规则）
    gap = assess_gap_level(match_report)

    # 3. 学习计划
    learning_plan = _get_learning_plan(use_llm, job_parsed, existing_skills, missing_skills, gap, job_text, resume_text, job_id, importance)

    # 4. 替代岗位
    alt_jobs = _get_alternative_jobs(use_llm, job_parsed, existing_skills, gap, job_text, resume_text, job_id)

    # 零缺失技能的特殊情况
    if not missing_skills:
        learning_plan = {
            "weekly_plan": [],
            "total_duration": "无需补缺",
            "recommended_resources": [],
            "message": "你的技能与岗位要求匹配度很高！可以考虑学习更高级的技能来增强竞争力。",
        }
        alt_jobs = []

    return {
        "skill_importance": importance,
        "gap_assessment": gap,
        "learning_plan": learning_plan,
        "alternative_jobs": alt_jobs,
        "used_llm": use_llm,
        "error": None,
    }


def _get_learning_plan(use_llm, job_parsed, existing, missing, gap, job_text, resume_text, job_id, importance):
    if use_llm and gap["level"] != "critical":
        cache_key = make_cache_key(job_text, resume_text, "skill_plan")
        cached = get_cached(cache_key)
        if cached:
            return {"weekly_plan": [], "total_duration": "参考LLM分析", "recommended_resources": [], "llm_insights": cached}

        prompt = SKILL_PLAN_PROMPT.format(
            job_title=job_text.split("\n")[0][:100] if job_text else "未知岗位",
            existing_skills=", ".join(existing[:10]),
            missing_skills=", ".join(missing[:10]),
            gap_level=gap["level"],
        )
        resp = call_llm(prompt)
        if resp:
            set_cache(cache_key, resp)
            return {"weekly_plan": [], "total_duration": "参考LLM分析", "recommended_resources": [], "llm_insights": resp}

    weekly = _local_weekly_plan(importance)
    resources = []
    for s_info in importance[:3]:
        skill_name = s_info["skill"]
        r = LEARNING_RESOURCES.get(skill_name, LEARNING_RESOURCES["_default"])
        resources.append({"skill": skill_name, "courses": r["courses"][:2], "books": r["books"][:1], "duration": r["duration"]})

    total_duration = _estimate_total_duration(importance)
    return {
        "weekly_plan": weekly,
        "total_duration": total_duration,
        "recommended_resources": resources,
    }


def _get_alternative_jobs(use_llm, job_parsed, existing, gap, job_text, resume_text, job_id):
    if gap["level"] == "critical":
        if use_llm:
            cache_key = make_cache_key(job_text, resume_text, "alt_jobs")
            cached = get_cached(cache_key)
            if cached:
                return [{"title": "LLM推荐", "reason": cached}]

            prompt = ALTERNATIVE_JOB_PROMPT.format(
                job_title=job_text[:200] if job_text else "未知岗位",
                existing_skills=", ".join(existing[:10]),
                required_skills=", ".join(job_parsed["skills"]["hard"][:10]),
            )
            resp = call_llm(prompt)
            if resp:
                set_cache(cache_key, resp)
                return [{"title": "LLM推荐", "reason": resp[:500]}]

        return _local_alternative_jobs(job_parsed)

    return []


def _estimate_total_duration(importance: list[dict]) -> str:
    """估算总学习周期。"""
    total_weeks = 0
    for s in importance:
        if s["importance"] == "core":
            total_weeks += 3
        else:
            total_weeks += 1
    if total_weeks <= 2:
        return "1-2周"
    elif total_weeks <= 6:
        return f"{total_weeks}周"
    else:
        return f"{total_weeks}周（建议分阶段学习）"
