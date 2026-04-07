"""
集中管理所有可配置常量，避免硬编码散落在各模块中。
优先从环境变量读取，否则使用默认值。
"""

import os

# ── 教育邮箱（支持多所高校）──
EDU_DOMAINS = [
    "@csu.edu.cn",      # 中南大学
    "@hnu.edu.cn",      # 湖南大学
    "@hunnu.edu.cn",    # 湖南师范大学
]
# 兼容旧代码的默认域名（学号自动补全时使用）
EDU_DOMAIN = os.getenv("EDU_DOMAIN", "@csu.edu.cn")

# ── 教育邮箱验证 ──
EDU_VERIFY_DAYS = int(os.getenv("EDU_VERIFY_DAYS", "3"))

# ── JWT / 认证 ──
SECRET_KEY = os.getenv("CSU_DATE_SECRET", "dev-csu-date-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

# ── 管理员密钥（用于 admin 接口鉴权）──
ADMIN_TOKEN = os.getenv("CSU_DATE_ADMIN_TOKEN", "")

# ── 问卷锁定时间（UTC+8）──
QUIZ_LOCK_WEEKDAY = int(os.getenv("QUIZ_LOCK_WEEKDAY", "3"))      # 0=Mon, 3=Thu
QUIZ_LOCK_HOUR_START = int(os.getenv("QUIZ_LOCK_HOUR_START", "16"))
QUIZ_LOCK_HOUR_END = int(os.getenv("QUIZ_LOCK_HOUR_END", "21"))

# ── 匹配引擎默认值 ──
DEFAULT_HEIGHT_CM = float(os.getenv("DEFAULT_HEIGHT_CM", "170.0"))
DEFAULT_HEIGHT_PREF_MIN = float(os.getenv("DEFAULT_HEIGHT_PREF_MIN", "150.0"))
DEFAULT_HEIGHT_PREF_MAX = float(os.getenv("DEFAULT_HEIGHT_PREF_MAX", "190.0"))
SCORE_SCALE_FACTOR = 100.0  # 将 0-1 分数转为 0-100

# ── 邮件验证码 ──
CODE_TTL = int(os.getenv("CODE_TTL", "600"))
CODE_MAX_ATTEMPTS = int(os.getenv("CODE_MAX_ATTEMPTS", "5"))
CODE_COOLDOWN = int(os.getenv("CODE_COOLDOWN", "60"))

# ── LLM 叙事 ──
NARRATIVE_WORKERS = int(os.getenv("NARRATIVE_WORKERS", "5"))


def is_edu_email(email: str) -> bool:
    """判断邮箱是否为支持的教育邮箱。"""
    e = email.strip().lower()
    return any(e.endswith(d) for d in EDU_DOMAINS)
