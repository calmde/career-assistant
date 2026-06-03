"""
简历-岗位多维匹配引擎。

评分维度: 技能(40%) + 经验(20%) + 学历(20%) + 岗位类别(10%) + 行业(10%)
支持可选的 LLM 语义复核。

保持与原有 analyze_match.py 的接口兼容。
"""
from job_parser import (
    parse_job_description,
    parse_resume as jp_parse_resume,
    DEGREE_RANK,
    get_related_industries,
    get_role_relatedness,
    extract_skills,
    extract_experience,
    extract_education,
)
from llm_client import call_llm, make_cache_key, get_cached, set_cache, is_llm_available

# ============================================================
# 评分权重
# ============================================================

DEFAULT_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.20,
    "education": 0.20,
    "role_category": 0.10,
    "industry": 0.10,
}


def _redistribute_weights(weights: dict, job_parsed: dict) -> dict:
    """若某维度无数据，将其权重均分给其余维度。"""
    w = dict(weights)

    if not job_parsed["skills"]["hard"]:
        freed = w.pop("skills", 0)
        remaining = sum(w.values()) or 1.0
        for k in w:
            w[k] += freed / len(w)
        w["skills"] = 0.0

    if not job_parsed["role_category"]["primary"]:
        freed = w.pop("role_category", 0)
        remaining = sum(w.values()) or 1.0
        for k in w:
            w[k] += freed / len(w)
        w["role_category"] = 0.0

    if not job_parsed["industry"]["primary"]:
        freed = w.pop("industry", 0)
        remaining = sum(w.values()) or 1.0
        for k in w:
            w[k] += freed / len(w)
        w["industry"] = 0.0

    return w


# ============================================================
# 各维度评分
# ============================================================

def _score_skills(job_skills: list[str], resume_skills: list[str]) -> tuple[float, list[str], list[str]]:
    """技能维度评分。"""
    req = set(job_skills)
    res = set(resume_skills)
    matched = sorted(req & res)
    missing = sorted(req - res)
    if req:
        ratio = len(matched) / len(req)
    else:
        ratio = 1.0
    return ratio, matched, missing


def _score_experience(job_exp: dict, resume_exp: dict) -> float:
    """经验维度评分。"""
    req = job_exp.get("max_years")
    res = resume_exp.get("max_years")
    if req is None:
        return 1.0
    if res is None:
        return 0.0
    return min(res / max(req, 1), 1.0)


def _score_education(job_edu: dict, resume_edu: dict) -> float:
    """学历维度评分。"""
    req_rank = job_edu.get("rank", -1)
    res_rank = resume_edu.get("rank", -1)
    if req_rank <= 0:
        return 1.0
    if res_rank >= req_rank:
        return 1.0
    if res_rank == req_rank - 1:
        return 0.5
    return 0.0


def _score_role_category(job_role: dict, resume_role: dict) -> float:
    """岗位类别匹配评分。"""
    jp = job_role.get("primary")
    rp = resume_role.get("primary")
    if not jp or not rp:
        return 0.5
    return get_role_relatedness(jp, rp)


def _score_industry(job_ind: dict, resume_ind: dict) -> float:
    """行业匹配评分。"""
    jp = job_ind.get("primary")
    rp = resume_ind.get("primary")
    if not jp or not rp:
        return 0.5
    if jp == rp:
        return 1.0
    adj = get_related_industries(jp)
    if rp in adj:
        return 0.5
    return 0.0


# ============================================================
# 综合评价
# ============================================================

def compute_match(resume_parsed: dict, job_parsed: dict) -> dict:
    """规则评分，返回完整匹配报告。"""
    skills_r, matched, missing = _score_skills(
        job_parsed["skills"]["hard"], resume_parsed["skills"]["hard"]
    )
    exp_r = _score_experience(job_parsed["experience"], resume_parsed["experience"])
    edu_r = _score_education(job_parsed["education"], resume_parsed["education"])
    role_r = _score_role_category(job_parsed["role_category"], resume_parsed["role_category"])
    ind_r = _score_industry(job_parsed["industry"], resume_parsed["industry"])

    weights = _redistribute_weights(DEFAULT_WEIGHTS, job_parsed)

    overall = (
        weights["skills"] * skills_r
        + weights["experience"] * exp_r
        + weights["education"] * edu_r
        + weights.get("role_category", 0) * role_r
        + weights.get("industry", 0) * ind_r
    )
    score = int(round(overall * 100))

    highlights, risks, suggestions = _build_insights(
        job_parsed, resume_parsed, matched, missing,
        skills_r, exp_r, edu_r, score
    )

    return {
        "score": score,
        "skill_ratio": round(skills_r, 3),
        "experience_ratio": round(exp_r, 3),
        "education_ratio": round(edu_r, 3),
        "role_category_ratio": round(role_r, 3),
        "industry_ratio": round(ind_r, 3),
        "matched_skills": matched,
        "missing_skills": missing,
        "matched_soft_skills": sorted(
            set(job_parsed["skills"]["soft"]) & set(resume_parsed["skills"]["soft"])
        ),
        "missing_soft_skills": sorted(
            set(job_parsed["skills"]["soft"]) - set(resume_parsed["skills"]["soft"])
        ),
        "highlights": highlights,
        "risks": risks,
        "suggestions": suggestions,
        "used_llm": False,
    }


def _build_insights(job_parsed, resume_parsed, matched, missing, skills_r, exp_r, edu_r, score):
    highlights = []
    risks = []
    suggestions = []

    job_skills = job_parsed["skills"]["hard"]
    job_exp = job_parsed["experience"]
    job_edu = job_parsed["education"]
    resume_exp = resume_parsed["experience"]
    resume_edu = resume_parsed["education"]

    if matched:
        highlights.append(f"匹配技能: {', '.join(matched)}")
    if missing:
        risks.append(f"缺少技能: {', '.join(missing)}")
        for s in missing[:5]:
            suggestions.append(f"建议学习: {s}")

    req_exp = job_exp.get("max_years")
    res_exp = resume_exp.get("max_years")
    if req_exp and res_exp is None:
        risks.append(f"岗位要求约 {req_exp} 年经验，简历中未明确标注")
        suggestions.append("在简历中补充相关工作年限与成果")
    elif req_exp and res_exp < req_exp:
        risks.append(f"经验不足: 简历 {res_exp} 年，要求 {req_exp} 年")
        suggestions.append("强调高质量项目成果，或寻找初级岗位")

    req_rank = job_edu.get("rank", -1)
    res_rank = resume_edu.get("rank", -1)
    if req_rank > 0 and res_rank >= req_rank:
        highlights.append(f"学历满足要求: {resume_edu.get('degree') or '已匹配'}")
    elif req_rank > 0 and res_rank == req_rank - 1:
        risks.append(f"学历略低于要求: 要求 {job_edu.get('degree')}")

    return highlights, risks, suggestions


# ============================================================
# LLM 语义复核
# ============================================================

LLM_REVIEW_PROMPT = """你是一位资深招聘顾问。请对比以下岗位要求和求职者简历，做语义层面的深度分析。

【岗位要求】
{job_text}

【求职者简历】
{resume_text}

【本地规则评分参考】
{local_match_summary}

请分析:
1. 求职者是否有未在简历中明确写出但可能具备的相关技能？（从项目经验推断）
2. 岗位要求中哪些是"硬门槛"、哪些是"加分项"？
3. 用2-3句话总结该求职者与岗位的匹配程度。

用中文回答，简洁直接。"""


def llm_review(resume_text: str, job_text: str, local_match: dict) -> dict | None:
    """LLM 语义复核，失败返回 None。"""
    if not is_llm_available():
        return None

    cache_key = make_cache_key(job_text, resume_text, "match_review")
    cached = get_cached(cache_key)
    if cached:
        return {"insights": cached, "adjusted_score": local_match["score"]}

    summary = (
        f"技能匹配: {local_match.get('skill_ratio', 0):.0%}, "
        f"缺失技能: {', '.join(local_match.get('missing_skills', [])[:5]) or '无'}"
    )
    prompt = LLM_REVIEW_PROMPT.format(
        job_text=job_text[:3000],
        resume_text=resume_text[:3000],
        local_match_summary=summary,
    )

    response = call_llm(prompt, system_prompt="你是一位专业招聘顾问。")
    if response is None:
        return None

    set_cache(cache_key, response)

    adjustment = min(10, len(local_match.get("matched_skills", [])) * 2)
    return {
        "insights": response,
        "adjusted_score": min(100, local_match["score"] + adjustment),
    }


# ============================================================
# 便捷接口（保持与 analyze_match.py 兼容）
# ============================================================

def analyze(job_text: str, resume_text: str) -> dict:
    """单岗位 vs 单简历匹配。签名兼容 analyze_match.analyze()。"""
    job = parse_job_description(job_text)
    resume = jp_parse_resume(resume_text)
    return compute_match(resume, job)


def analyze_jobs_in_dir(jobs_dir: str, resume_text: str, top_n: int = 10) -> list[dict]:
    """批量目录匹配。签名兼容 analyze_match.analyze_jobs_in_dir()。"""
    import os
    results = []
    resume = jp_parse_resume(resume_text)
    for fn in sorted(os.listdir(jobs_dir)):
        path = os.path.join(jobs_dir, fn)
        if not os.path.isfile(path) or not fn.lower().endswith((".txt", ".md")):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                job_text = f.read()
        except Exception:
            continue
        job = parse_job_description(job_text)
        res = compute_match(resume, job)
        res["job_file"] = fn
        res["job_snippet"] = "\n".join(job_text.splitlines()[:3])
        results.append(res)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:top_n]
