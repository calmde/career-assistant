"""
四步求职助手 — Flask Web 应用。

流程: 上传简历 → 爬取岗位（或手动粘贴JD）→ 匹配评分 → 简历优化 → 技能规划
"""
import io
import json
import logging
import os
import secrets
import sqlite3
import threading
import time as _time

from flask import Flask, request, jsonify, render_template, session

from job_parser import parse_job_description, parse_resume
from matcher import compute_match
from resume_optimizer import generate_optimization
from skill_navigator import generate_skill_plan

# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("career_assistant")

# ============================================================
# Flask init
# ============================================================

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

# ============================================================
# 服务端存储
# ============================================================

_user_sessions: dict[str, dict] = {}
_tasks: dict[str, dict] = {}


def _get_user_data() -> dict:
    token = session.get("_token")
    if not token or token not in _user_sessions:
        token = secrets.token_hex(16)
        session["_token"] = token
        _user_sessions[token] = {"resume_text": "", "parsed": {}, "keywords": [], "matches": [], "jobs": []}
    return _user_sessions[token]


def _query_db(sql: str, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/jobs")
def browse_jobs():
    data = _get_user_data()
    return render_template("jobs.html", city=data.get("city", ""))


@app.route("/match/<int:job_index>")
def view_match(job_index: int):
    data = _get_user_data()
    matches = data.get("matches", [])
    if not matches or job_index >= len(matches):
        return render_template("match.html", error="未找到匹配数据，请先上传简历"), 404
    return render_template("match.html", match=matches[job_index], job_index=job_index, total=len(matches))


@app.route("/optimize/<int:job_index>")
def view_optimize(job_index: int):
    data = _get_user_data()
    matches = data.get("matches", [])
    resume_text = data.get("resume_text", "")
    if not matches or job_index >= len(matches):
        return render_template("optimize.html", error="未找到匹配数据"), 404
    item = matches[job_index]
    result = generate_optimization(resume_text, item.get("job_parsed", {}), item)
    return render_template("optimize.html", optimization=result, job=item.get("job_raw", {}), job_index=job_index)


@app.route("/skill-plan/<int:job_index>")
def view_skill_plan(job_index: int):
    data = _get_user_data()
    matches = data.get("matches", [])
    resume_text = data.get("resume_text", "")
    if not matches or job_index >= len(matches):
        return render_template("skill_plan.html", error="未找到匹配数据"), 404
    item = matches[job_index]
    result = generate_skill_plan(
        item.get("missing_skills", []),
        item.get("matched_skills", []),
        item.get("job_parsed", {}),
        item,
        resume_text,
    )
    return render_template("skill_plan.html", plan=result, job=item.get("job_raw", {}), job_index=job_index)


# ============================================================
# 文件解析
# ============================================================

def _read_uploaded_file(f) -> tuple[str | None, str | None]:
    content = f.read()
    if f.filename and f.filename.lower().endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = [p.extract_text() or "" for p in reader.pages]
            text = "\n".join(pages)
            if not text.strip():
                return None, "PDF 无法提取文字，可能为扫描件"
            return text, None
        except Exception as e:
            return None, f"PDF 解析失败: {e}"
    for enc in ["utf-8", "gbk", "gb2312"]:
        try:
            return content.decode(enc), None
        except Exception:
            continue
    return None, "文件编码不支持"


def _match_resume_to_jobs(resume_text, job_list):
    """通用：把简历和岗位列表做匹配，返回排序后的结果。"""
    resume_parsed = parse_resume(resume_text)
    analyzed = []
    for job in job_list:
        try:
            parts = [str(job.get(k, "")) for k in ["title", "company", "skills", "experience", "education", "welfare"] if job.get(k)]
            jd_text = "\n".join(parts)
            jp = parse_job_description(jd_text)
            match = compute_match(resume_parsed, jp)
            match["job_raw"] = job
            match["job_parsed"] = jp
            analyzed.append(match)
        except Exception:
            pass
    analyzed.sort(key=lambda x: x.get("score", 0), reverse=True)
    return analyzed


# ============================================================
# API: 上传简历 + 后台爬取
# ============================================================

@app.route("/api/upload", methods=["POST"])
def api_upload_resume():
    if "file" not in request.files:
        return jsonify({"code": -1, "msg": "请上传简历文件"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"code": -1, "msg": "文件名为空"}), 400

    resume_text, err = _read_uploaded_file(f)
    if err:
        return jsonify({"code": -1, "msg": err}), 400
    if len(resume_text.strip()) < 20:
        return jsonify({"code": -1, "msg": "简历内容过短（少于20字）"}), 400

    try:
        parsed = parse_resume(resume_text)
        keywords = parsed["skills"]["hard"][:6] or ["python"]
    except Exception as e:
        return jsonify({"code": -1, "msg": f"简历解析失败: {e}"}), 400

    city = request.form.get("city", "北京")
    max_pages = int(request.form.get("max_pages", 2))

    data = _get_user_data()
    data["resume_text"] = resume_text
    data["parsed"] = parsed
    data["keywords"] = keywords
    data["city"] = city
    data["matches"] = []
    data["jobs"] = []

    task_id = secrets.token_hex(8)
    _tasks[task_id] = {"status": "running", "progress": 5, "message": "正在启动浏览器爬取BOSS直聘..."}

    def _crawl_and_match():
        try:
            _do_crawl(task_id, keywords, city, max_pages, resume_text, data)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            _tasks[task_id] = {"status": "error", "progress": 0, "message": f"异常: {ex}"}

    threading.Thread(target=_crawl_and_match, daemon=True).start()

    return jsonify({"code": 0, "data": {"task_id": task_id, "keywords": keywords}})


def _do_crawl(task_id, keywords, city, max_pages, resume_text, data):
    all_jobs = []
    seen = set()

    def _add(jobs, src=""):
        c = 0
        for j in jobs:
            url = j.get("url", f"{j.get('title','')}|{j.get('company','')}|{src}")
            if url in seen:
                continue
            seen.add(url)
            j["source"] = j.get("source", src or "未知")
            all_jobs.append(j)
            c += 1
        if c:
            logger.info("[%s] +%d 条", src, c)

    # ---- BOSS直聘 ----
    _tasks[task_id]["message"] = "正在打开浏览器访问BOSS直聘...\n（浏览器窗口会弹出，如需要登录请手动扫码，60秒超时）"
    _tasks[task_id]["progress"] = 10
    for kw in keywords:
        try:
            from spider import fetch_jobs
            jobs = fetch_jobs(kw, city=city, max_pages=max_pages)
            _add(jobs, "BOSS直聘")
        except Exception as ex:
            logger.info("BOSS直聘(%s) 跳过: %s", kw, type(ex).__name__)
        _time.sleep(1)

    _tasks[task_id]["progress"] = 60
    _tasks[task_id]["message"] = f"爬取完成，共 {len(all_jobs)} 条岗位"

    # ---- 入库 ----
    if all_jobs:
        try:
            from clean_data import clean_and_store
            clean_and_store(all_jobs)
        except Exception as ex:
            logger.warning("入库失败: %s", ex)

    # ---- 回退到数据库（关键词 + 城市匹配）----
    if not all_jobs:
        _tasks[task_id]["message"] = "未爬取到新岗位，匹配数据库已有岗位..."
        try:
            # 优先按城市 + 关键词筛选
            params = [f"%{city}%"]
            conditions = []
            for kw in keywords:
                conditions.append("(title LIKE ? OR skills LIKE ?)")
                params.extend([f"%{kw}%", f"%{kw}%"])
            kw_clauses = " OR ".join(conditions)
            sql = f"SELECT * FROM jobs WHERE city LIKE ? AND ({kw_clauses}) ORDER BY salary_avg DESC LIMIT 100"
            all_jobs = _query_db(sql, params)
            # 仅按城市回退
            if not all_jobs:
                all_jobs = _query_db("SELECT * FROM jobs WHERE city LIKE ? ORDER BY salary_avg DESC LIMIT 50", (f"%{city}%",))
            # 全库回退
            if not all_jobs:
                all_jobs = _query_db("SELECT * FROM jobs ORDER BY salary_avg DESC LIMIT 50")
        except Exception:
            all_jobs = []

    if not all_jobs:
        _tasks[task_id] = {
            "status": "done", "progress": 100,
            "message": "没有找到任何岗位。请尝试：1) 更换关键词 2) 使用「手动粘贴JD」功能",
            "result": {"keywords": keywords, "job_count": 0, "match_count": 0, "top_score": 0},
        }
        return

    # ---- 匹配 ----
    _tasks[task_id]["message"] = f"正在匹配 {len(all_jobs)} 条岗位..."
    _tasks[task_id]["progress"] = 80

    analyzed = _match_resume_to_jobs(resume_text, all_jobs)

    data["matches"] = analyzed[:50]
    data["jobs"] = [m.get("job_raw", {}) for m in analyzed[:50]]

    _tasks[task_id] = {
        "status": "done", "progress": 100,
        "message": f"完成！{len(all_jobs)} 条岗位，有效匹配 {len(analyzed)} 条",
        "result": {
            "keywords": keywords,
            "job_count": len(all_jobs),
            "match_count": len(analyzed),
            "top_score": analyzed[0]["score"] if analyzed else 0,
        },
    }


@app.route("/api/crawl-status")
def api_crawl_status():
    task_id = request.args.get("task_id", "")
    if not task_id or task_id not in _tasks:
        return jsonify({"code": -1, "msg": "无效的任务ID"}), 400
    task = _tasks[task_id]
    resp = {"code": 0, "data": {"status": task["status"], "progress": task["progress"], "message": task["message"]}}
    if task.get("result"):
        resp["data"].update(task["result"])
    return jsonify(resp)


# ============================================================
# API: 手动粘贴 JD
# ============================================================

@app.route("/api/paste-jd", methods=["POST"])
def api_paste_jd():
    """手动粘贴岗位描述进行匹配。"""
    body = request.get_json(force=True) or {}
    jd_text = (body.get("jd_text") or "").strip()
    if len(jd_text) < 20:
        return jsonify({"code": -1, "msg": "岗位描述过短（少于20字）"}), 400

    data = _get_user_data()
    resume_text = data.get("resume_text", "")
    if not resume_text:
        return jsonify({"code": -1, "msg": "请先上传简历"}), 400

    # 把粘贴的JD当作单条岗位
    job = {
        "title": body.get("title", "手动粘贴岗位"),
        "company": body.get("company", ""),
        "city": body.get("city", ""),
        "salary": body.get("salary", ""),
        "experience": "",
        "education": "",
        "skills": "",
        "source": "手动粘贴",
        "url": "",
        "welfare": "",
        "industry": "",
        "company_stage": "",
        "contact_person": "",
        "contact_title": "",
    }

    analyzed = _match_resume_to_jobs(resume_text, [job])
    if not analyzed:
        return jsonify({"code": -1, "msg": "匹配失败"}), 500

    data["matches"] = analyzed
    data["jobs"] = [job]

    return jsonify({
        "code": 0,
        "data": {
            "score": analyzed[0]["score"],
            "matched_skills": analyzed[0]["matched_skills"],
            "missing_skills": analyzed[0]["missing_skills"],
            "highlights": analyzed[0]["highlights"],
            "risks": analyzed[0]["risks"],
        },
    })


# ============================================================
# API: 岗位搜索
# ============================================================

@app.route("/api/jobs")
def search_jobs():
    city = request.args.get("city", "").strip()
    keyword = request.args.get("keyword", "").strip()
    salary_min = request.args.get("salary_min", type=int, default=0)
    salary_max = request.args.get("salary_max", type=int, default=1000000)
    company = request.args.get("company", "").strip()
    education = request.args.get("education", "").strip()
    experience = request.args.get("experience", "").strip()

    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if city:
        sql += " AND city LIKE ?"
        params.append(f"%{city}%")
    if keyword:
        sql += " AND (title LIKE ? OR company LIKE ? OR skills LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    if salary_min > 0:
        sql += " AND salary_max >= ?"
        params.append(salary_min)
    if salary_max < 1000000:
        sql += " AND salary_min <= ?"
        params.append(salary_max)
    if company:
        sql += " AND company LIKE ?"
        params.append(f"%{company}%")
    if education:
        sql += " AND education LIKE ?"
        params.append(f"%{education}%")
    if experience:
        sql += " AND experience LIKE ?"
        params.append(f"%{experience}%")

    sql += " ORDER BY salary_avg DESC LIMIT 100"

    try:
        data = _query_db(sql, params)
        return jsonify({"code": 0, "data": data, "total": len(data)})
    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)}), 500


# ============================================================
# 错误处理
# ============================================================

@app.errorhandler(400)
def _bad_request(e):
    return jsonify({"code": -1, "msg": "请求参数错误"}), 400


@app.errorhandler(404)
def _not_found(e):
    return jsonify({"code": -1, "msg": "资源不存在"}), 404


@app.errorhandler(500)
def _server_error(e):
    logger.error("服务器内部错误: %s", e, exc_info=True)
    return jsonify({"code": -1, "msg": "服务器内部错误，请稍后重试"}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug, port=port)
