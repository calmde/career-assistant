"""
LLM API 客户端 — 统一的 LLM 调用基础设施。

供 matcher / resume_optimizer / skill_navigator 共用。
- OpenAI 兼容接口（DeepSeek / 通义千问 等）
- 失败不回抛异常（fail-open），返回 None
- SQLite 结果缓存，24h TTL
- 绝不记录 prompt / response / API key
"""
import os
import hashlib
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("llm_client")
logger.addHandler(logging.NullHandler())

# ============================================================
# 配置
# ============================================================

LLM_CONFIG = {
    "api_key": os.getenv("LLM_API_KEY", ""),
    "api_base": os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1"),
    "model": os.getenv("LLM_MODEL", "deepseek-chat"),
    "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
}

CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_cache.db")
CACHE_TTL_HOURS = 24


def _get_cache_db() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS llm_cache (
            cache_key TEXT PRIMARY KEY,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


# ============================================================
# 公共 API
# ============================================================

def is_llm_available() -> bool:
    return bool(LLM_CONFIG["api_key"])


def call_llm(prompt: str, system_prompt: str = "", max_tokens: int = 2048) -> str | None:
    """调用 LLM API，失败返回 None（绝不抛异常）。"""
    if not is_llm_available():
        logger.warning("LLM_API_KEY not set, skipping LLM call")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed")
        return None

    try:
        client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["api_base"],
            timeout=LLM_CONFIG["timeout"],
        )
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        content = response.choices[0].message.content
        if content and len(content.strip()) >= 10:
            return content.strip()

        logger.warning("LLM returned empty or too-short response")
        return None

    except Exception as e:
        logger.warning(f"LLM call failed: {type(e).__name__}")
        return None


def get_cached(cache_key: str) -> str | None:
    """查询缓存，TTL 内有效。"""
    try:
        conn = _get_cache_db()
        row = conn.execute(
            "SELECT result, created_at FROM llm_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        conn.close()

        if row is None:
            return None

        result, created_at = row
        created_dt = datetime.fromisoformat(created_at)
        if datetime.now() - created_dt > timedelta(hours=CACHE_TTL_HOURS):
            _delete_cache(cache_key)
            return None

        return result
    except Exception:
        return None


def set_cache(cache_key: str, result: str) -> None:
    """写入缓存。"""
    try:
        conn = _get_cache_db()
        conn.execute(
            "INSERT OR REPLACE INTO llm_cache (cache_key, result, created_at) VALUES (?, ?, ?)",
            (cache_key, result, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _delete_cache(cache_key: str) -> None:
    try:
        conn = _get_cache_db()
        conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
        conn.close()
    except Exception:
        pass


def make_cache_key(job_text: str, resume_text: str, prompt_type: str) -> str:
    """为 (岗位 + 简历 + 用途) 组合生成缓存键。"""
    payload = f"{job_text[:2000]}|||{resume_text[:2000]}|||{prompt_type}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
