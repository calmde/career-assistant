"""
简历优化器 — 针对目标岗位生成简历改进建议。

功能：关键词布局 / 项目描述量化改写 / 多版本自我介绍 / ATS 友好检测。
LLM 优先，不可用时降级为规则建议。
"""
from llm_client import call_llm, make_cache_key, get_cached, set_cache, is_llm_available

# ============================================================
# Prompt 模板（硬编码，绝不拼接用户输入）
# ============================================================

SYSTEM_PROMPT = "你是一位专业的简历优化顾问，擅长帮助求职者改进简历以提高通过率。用中文回答，简洁具体。"

KEYWORD_PROMPT = """请根据以下信息，给出简历关键词布局建议。

【目标岗位】
{job_text}

【求职者简历】
{resume_text}

【缺失的关键词】
{missing_keywords}

【已有匹配技能】
{matched_skills}

请输出：
1. 每个缺失关键词应放在简历的哪个部分（技能列表 / 项目经历 / 自我评价）
2. 如何在现有内容中自然地融入这些关键词（给1-2个具体例子）
3. 每个关键词的优先级标注（高/中/低）
"""

QUANTIFIED_PROMPT = """请根据以下信息，帮助将简历中的项目描述改写得更量化、更有说服力。

【目标岗位】
{job_text}

【求职者简历原文】
{resume_text}

【岗位看重的技能】
{required_skills}

请输出：
1. 挑出简历中2-3个可以量化改进的项目描述，给出改写前和改写后对比
2. 如果是"做了XX系统"改成"用XX技术完成XX系统，支撑YY用户/请求，性能提升ZZ%"
3. 如果没有可量化的内容，建议可以补充哪些量化指标
"""

SELF_INTRO_PROMPT = """请根据以下信息，为求职者生成3个版本的自我介绍（每个版本2-3句话）。

【目标岗位】
{job_text}

【求职者背景】
{resume_text}

【岗位最看重的技能】
{required_skills}

请生成：
版本1 — 偏技术型（突出技术栈和项目经验）
版本2 — 偏综合型（技术+软技能+学习能力）
版本3 — 偏匹配型（针对该岗位定制，强调匹配度）
"""

ATS_PROMPT = """请分析以下简历的ATS（简历筛选系统）友好度。

【目标岗位】
{job_text}

【简历内容】
{resume_text}

【岗位高频关键词】
{required_skills}

请分析：
1. 简历关键词覆盖度评分（百分比）
2. 哪些关键词缺失会影响ATS筛选通过
3. 简历格式或措辞上可能被ATS忽略/误判的风险点
3个以内建议用中文简洁输出。
"""

# ============================================================
# 本地降级建议（LLM 不可用时使用）
# ============================================================

_LOCAL_KEYWORD_TIPS = """简历关键词优化建议（本地规则）：

1. 技术技能请放在简历顶部的【专业技能】区域，用逗号分隔
2. 行业术语请融入【项目经历】中，结合具体场景描述
3. 软技能请放在【自我评价】中，用实例支撑

优先级排序建议：
- 岗位JD中重复出现的关键词 > 只出现一次的关键词 > 加分项关键词"""

_LOCAL_QUANTIFIED_TIPS = """项目描述量化改写建议（本地规则）：

请检查你的项目描述：
- 是否有具体数字？（用户量、数据量、性能提升百分比）
- 是否描述了使用的技术栈？（用什么工具/框架完成）
- 是否说明了个人贡献？（独立完成 / 团队中负责XX模块）

示例改写：
  原：「做了一个后台管理系统」
  改：「使用 Django + Vue 开发后台管理系统，支撑日均 1000+ 用户访问，接口响应时间 < 200ms」"""

_LOCAL_SELF_INTRO_TEMPLATE = """自我介绍模板建议（本地规则）：

版本1 — 技术型：
「{skills}相关开发经验 {exp_years} 年，熟练掌握 {top_skills}，曾参与 {project_hint}。
对技术有持续热情，关注行业前沿动态。」

版本2 — 综合型：
「{edu_bg} 背景，{exp_years} 年 {role} 经验，擅长 {core_skill}。
具备良好的沟通协作能力，能快速学习新技术并应用于实际项目。」

版本3 — 匹配型：
「我的技术栈 {matched_skills} 与该岗位要求高度匹配。
{extra_skill_hint}方面也有实践经验，能快速融入团队并产出价值。」"""

_LOCAL_ATS_TIPS = """ATS友好度分析（本地规则）：

1. 确保简历中包含了JD关键技能词的"精确写法"（不要缩写）
2. 使用标准章节标题：教育背景、工作经历、项目经历、专业技能
3. 避免表格、图片、特殊符号 — ATS可能无法解析
4. PDF格式保存，确保文字可选中复制（有些PDF扫描件ATS读不了）"""


# ============================================================
# 本地降级生成
# ============================================================

def _local_keyword_suggestions(missing_keywords: list[str], matched_skills: list[str]) -> list[dict]:
    if not missing_keywords:
        return []
    results = []
    priorities = ["高"] * min(2, len(missing_keywords)) + ["中"] * min(3, max(0, len(missing_keywords) - 2))
    placements = ["技能列表", "项目经历", "项目经历", "自我评价", "技能列表"]
    for i, kw in enumerate(missing_keywords[:5]):
        results.append({
            "keyword": kw,
            "placement": placements[i % len(placements)],
            "priority": priorities[i] if i < len(priorities) else "低",
            "suggestion": f"将 {kw} 加入简历{'技能' if i == 0 else '项目描述' if i < 3 else '自我评价'}部分",
        })
    return results


def _local_quantified_rewrites(resume_text: str) -> list[dict]:
    lines = [l.strip() for l in resume_text.split("\n") if l.strip() and len(l.strip()) > 10]
    rewrites = []
    for line in lines[:3]:
        rewrites.append({
            "original": line[:80],
            "rewritten": f"（建议量化）{line[:60]} — 建议补充：技术栈/数据指标/个人贡献",
        })
    if not rewrites:
        rewrites.append({
            "original": "（未检测到项目描述）",
            "rewritten": "建议在简历中添加2-3个具体项目，每个项目包含：技术栈、量化成果、个人角色",
        })
    return rewrites


def _local_self_intro(resume_parsed: dict) -> list[dict]:
    skills = resume_parsed["skills"]["hard"][:5] or ["相关技术"]
    exp = resume_parsed["experience"].get("max_years") or 1
    edu = resume_parsed["education"].get("degree") or "相关专业"
    role = resume_parsed["role_category"].get("primary") or "开发"

    return [
        {
            "target_role": "技术型",
            "intro": f"{', '.join(skills)}相关开发经验 {exp} 年，熟练掌握 {'、'.join(skills[:3])}，对技术有持续热情，关注行业前沿动态。",
        },
        {
            "target_role": "综合型",
            "intro": f"{edu} 背景，{exp} 年 {role} 经验，擅长 {'、'.join(skills[:2])}。具备良好的沟通协作能力，能快速学习新技术并应用于实际项目。",
        },
        {
            "target_role": "匹配型",
            "intro": f"我的技术栈 {', '.join(skills[:3])} 与该岗位要求高度匹配。有相关项目实践经验，能快速融入团队并产出价值。",
        },
    ]


def _local_ats_check(job_skills: list[str], resume_skills: list[str]) -> dict:
    if not job_skills:
        return {"keyword_density": {}, "issues": ["岗位未明确技能要求，无法分析ATS"]}

    density = {}
    for s in job_skills:
        in_resume = s in resume_skills
        density[s] = "已覆盖" if in_resume else "缺失"

    missing = [k for k, v in density.items() if v == "缺失"]
    issues = []
    if missing:
        issues.append(f"缺失关键词: {', '.join(missing[:5])} — 可能影响ATS筛选")
    issues.append("确保简历使用标准章节标题，避免表格和图片")

    return {"keyword_density": density, "issues": issues}


# ============================================================
# 公共接口
# ============================================================

def generate_optimization(
    resume_text: str,
    job_parsed: dict,
    match_report: dict,
    job_id: str = "",
    sections: list[str] | None = None,
) -> dict:
    """生成简历优化建议。

    Args:
        resume_text: 简历原文
        job_parsed: 岗位结构化数据
        match_report: 匹配报告（来自 matcher.compute_match）
        job_id: 岗位标识（用于缓存）
        sections: 需生成的模块，默认全部

    Returns:
        dict with keyword_suggestions, quantified_rewrites, self_intro_versions, ats_check
    """
    if sections is None:
        sections = ["keywords", "quantified", "self_intro", "ats"]

    job_text = job_parsed.get("raw_text", "")
    missing_skills = match_report.get("missing_skills", [])
    matched_skills = match_report.get("matched_skills", [])
    required_skills = job_parsed["skills"]["hard"]
    use_llm = is_llm_available()

    result = {"used_llm": use_llm, "error": None}

    # --- 关键词建议 ---
    if "keywords" in sections:
        result["keyword_suggestions"] = _get_keyword_suggestions(
            use_llm, job_text, resume_text, missing_skills, matched_skills,
            job_parsed, job_id
        )

    # --- 量化改写 ---
    if "quantified" in sections:
        result["quantified_rewrites"] = _get_quantified_rewrites(
            use_llm, job_text, resume_text, required_skills, job_parsed, job_id
        )

    # --- 自我介绍 ---
    if "self_intro" in sections:
        result["self_intro_versions"] = _get_self_intro(
            use_llm, job_text, resume_text, required_skills, job_parsed, job_id
        )

    # --- ATS 检测 ---
    if "ats" in sections:
        result["ats_check"] = _get_ats_check(
            use_llm, job_text, resume_text, required_skills,
            job_parsed, job_id, missing_skills, matched_skills
        )

    return result


def _get_keyword_suggestions(use_llm, job_text, resume_text, missing, matched, parsed, job_id):
    if not missing:
        return [{"keyword": "无缺失技能", "placement": "N/A", "priority": "N/A", "suggestion": "你的技能匹配度很高，建议继续保持，关注岗位描述的细节要求"}]

    if use_llm:
        cache_key = make_cache_key(job_text, resume_text, "optimize_keywords")
        cached = get_cached(cache_key)
        if cached:
            return _parse_llm_keywords(cached)

        prompt = KEYWORD_PROMPT.format(
            job_text=job_text[:3000],
            resume_text=resume_text[:3000],
            missing_keywords=", ".join(missing[:10]),
            matched_skills=", ".join(matched[:10]),
        )
        resp = call_llm(prompt, SYSTEM_PROMPT)
        if resp:
            set_cache(cache_key, resp)
            return _parse_llm_keywords(resp)

    return _local_keyword_suggestions(missing, matched)


def _parse_llm_keywords(text: str) -> list[dict]:
    suggestions = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        for kw in ["Python", "Java", "React", "Docker", "Kubernetes", "MySQL", "Redis",
                    "Spring", "Django", "Flask", "Vue", "Git", "Linux", "AWS", "Go",
                    "Node", "TypeScript", "C++", "Spark", "Hadoop"]:
            if kw.lower() in line.lower():
                suggestions.append({"keyword": kw, "placement": "按LLM建议", "priority": "参考LLM", "suggestion": line[:200]})
                break
        else:
            if len(suggestions) < 5:
                suggestions.append({"keyword": "参考建议", "placement": "综合", "priority": "中", "suggestion": line[:200]})
    return suggestions if suggestions else _local_keyword_suggestions([], [])


def _get_quantified_rewrites(use_llm, job_text, resume_text, required_skills, parsed, job_id):
    if use_llm:
        cache_key = make_cache_key(job_text, resume_text, "optimize_quantified")
        cached = get_cached(cache_key)
        if cached:
            return _parse_llm_rewrites(cached)

        prompt = QUANTIFIED_PROMPT.format(
            job_text=job_text[:2500],
            resume_text=resume_text[:2500],
            required_skills=", ".join(required_skills[:10]),
        )
        resp = call_llm(prompt, SYSTEM_PROMPT)
        if resp:
            set_cache(cache_key, resp)
            return _parse_llm_rewrites(resp)

    return _local_quantified_rewrites(resume_text)


def _parse_llm_rewrites(text: str) -> list[dict]:
    # 简单解析：拆分段落
    parts = text.split("\n\n")
    rewrites = []
    for p in parts[:3]:
        lines = p.strip().split("\n")
        original = lines[0][:100] if lines else ""
        rewritten = lines[1][:200] if len(lines) > 1 else p[:200]
        rewrites.append({"original": original, "rewritten": rewritten})
    return rewrites if rewrites else [{"original": "LLM返回", "rewritten": text[:300]}]


def _get_self_intro(use_llm, job_text, resume_text, required_skills, parsed, job_id):
    if use_llm:
        cache_key = make_cache_key(job_text, resume_text, "optimize_self_intro")
        cached = get_cached(cache_key)
        if cached:
            return _parse_llm_intros(cached)

        prompt = SELF_INTRO_PROMPT.format(
            job_text=job_text[:2500],
            resume_text=resume_text[:2500],
            required_skills=", ".join(required_skills[:10]),
        )
        resp = call_llm(prompt, SYSTEM_PROMPT)
        if resp:
            set_cache(cache_key, resp)
            return _parse_llm_intros(resp)

    return _local_self_intro(parsed)


def _parse_llm_intros(text: str) -> list[dict]:
    versions = []
    current_role = ""
    current_text = []
    for line in text.split("\n"):
        if "版本" in line and ("1" in line or "2" in line or "3" in line or "技术" in line or "综合" in line or "匹配" in line):
            if current_text:
                versions.append({"target_role": current_role or "未知", "intro": "\n".join(current_text)})
            current_role = line.strip()[:20]
            current_text = []
        else:
            current_text.append(line.strip())
    if current_text:
        versions.append({"target_role": current_role or "未知", "intro": "\n".join(current_text)})
    return versions if versions else _local_self_intro({"skills": {"hard": []}, "experience": {}, "education": {}, "role_category": {}})


def _get_ats_check(use_llm, job_text, resume_text, required_skills, parsed, job_id, missing, matched):
    if use_llm:
        cache_key = make_cache_key(job_text, resume_text, "optimize_ats")
        cached = get_cached(cache_key)
        if cached:
            return _parse_llm_ats(cached)

        prompt = ATS_PROMPT.format(
            job_text=job_text[:3000],
            resume_text=resume_text[:3000],
            required_skills=", ".join(required_skills[:10]),
        )
        resp = call_llm(prompt, SYSTEM_PROMPT)
        if resp:
            set_cache(cache_key, resp)
            return _parse_llm_ats(resp)

    return _local_ats_check(required_skills, matched)


def _parse_llm_ats(text: str) -> dict:
    return {"keyword_density": {}, "issues": [text[:500]]}
