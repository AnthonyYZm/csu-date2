"""
邮箱验证服务 — 基于 Resend
验证码存储在内存中（带 TTL），生产环境可换 Redis。
"""

import os
import random
import time
from typing import Optional

import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY", "")

# 发件地址：域名验证通过后可用任意前缀
FROM_EMAIL = os.getenv("FROM_EMAIL", "verify@csudate.com")

# ── 验证码存储（内存版，重启后清空）──
# 格式: { "email": {"code": "123456", "expires": timestamp, "attempts": 0} }
_store = {}

from config import CODE_COOLDOWN, CODE_MAX_ATTEMPTS, CODE_TTL

MAX_ATTEMPTS = CODE_MAX_ATTEMPTS
COOLDOWN = CODE_COOLDOWN


def _clean_expired():
    """清理过期条目。"""
    now = time.time()
    expired = [k for k, v in _store.items() if v["expires"] < now]
    for k in expired:
        del _store[k]


def can_send(email: str):
    """检查是否可以发送验证码。返回 (可以发, 原因)。"""
    _clean_expired()
    entry = _store.get(email)
    if entry and entry["expires"] > time.time():
        elapsed = time.time() - (entry["expires"] - CODE_TTL)
        if elapsed < COOLDOWN:
            remaining = int(COOLDOWN - elapsed)
            return False, f"请 {remaining} 秒后再试"
    return True, ""


def generate_and_send(email: str):
    """生成验证码并通过 Resend 发送邮件。返回 (成功, 消息)。"""
    ok, reason = can_send(email)
    if not ok:
        return False, reason

    code = f"{random.randint(100000, 999999)}"

    _store[email] = {
        "code": code,
        "expires": time.time() + CODE_TTL,
        "attempts": 0,
    }

    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [email],
            "subject": "【CSU Date】邮箱验证码",
            "html": f"""
            <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:480px;margin:0 auto;padding:40px 24px;color:#1a1a2e">
              <h2 style="margin:0 0 8px;font-size:22px">CSU Date 邮箱验证</h2>
              <p style="color:#666;margin:0 0 24px;font-size:14px">你正在注册 CSU Date 账号，请使用以下验证码完成验证：</p>
              <div style="background:#f5f3ee;border-radius:12px;padding:24px;text-align:center;margin:0 0 24px">
                <span style="font-size:36px;font-weight:700;letter-spacing:8px;color:#1a1a2e">{code}</span>
              </div>
              <p style="color:#999;font-size:12px;margin:0">验证码 10 分钟内有效，请勿泄露给他人。</p>
              <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
              <p style="color:#bbb;font-size:11px;margin:0">如非本人操作请忽略此邮件。<br>CSU Date · 岳麓山下的匹配实验</p>
            </div>
            """,
        })
        return True, "验证码已发送"
    except Exception as e:
        # 发送失败时清除存储的验证码
        _store.pop(email, None)
        return False, f"邮件发送失败: {e}"


def verify_code(email: str, code: str):
    """验证码校验。返回 (正确, 消息)。"""
    _clean_expired()
    entry = _store.get(email)
    if not entry:
        return False, "验证码已过期或未发送，请重新获取"

    if entry["expires"] < time.time():
        _store.pop(email, None)
        return False, "验证码已过期，请重新获取"

    entry["attempts"] += 1
    if entry["attempts"] > MAX_ATTEMPTS:
        _store.pop(email, None)
        return False, "验证次数过多，请重新获取验证码"

    if entry["code"] != code.strip():
        remaining = MAX_ATTEMPTS - entry["attempts"]
        return False, f"验证码错误，还剩 {remaining} 次机会"

    # 验证成功，清除
    _store.pop(email, None)
    return True, "验证成功"
