"""
邮箱验证服务 — 基于 Resend，Resend 抑制时回退到 QQ 邮箱 SMTP。
验证码存储在内存中（带 TTL），生产环境可换 Redis。
"""

import logging
import os
import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import resend
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")

# 发件地址：域名验证通过后可用任意前缀
FROM_EMAIL = os.getenv("FROM_EMAIL", "verify@csudate.com")

# QQ 邮箱 SMTP 回退配置
QQ_SMTP_EMAIL = os.getenv("QQ_SMTP_EMAIL", "")
QQ_SMTP_AUTH_CODE = os.getenv("QQ_SMTP_AUTH_CODE", "")

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


def _build_code_html(code: str) -> str:
    """构建验证码邮件 HTML 内容。"""
    return f"""
    <div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:480px;margin:0 auto;padding:40px 24px;color:#1a1a2e">
      <h2 style="margin:0 0 8px;font-size:22px">YueluDate 邮箱验证</h2>
      <p style="color:#666;margin:0 0 24px;font-size:14px">你正在注册 YueluDate 账号，请使用以下验证码完成验证：</p>
      <div style="background:#f5f3ee;border-radius:12px;padding:24px;text-align:center;margin:0 0 24px">
        <span style="font-size:36px;font-weight:700;letter-spacing:8px;color:#1a1a2e">{code}</span>
      </div>
      <p style="color:#999;font-size:12px;margin:0">验证码 10 分钟内有效，请勿泄露给他人。</p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="color:#bbb;font-size:11px;margin:0">如非本人操作请忽略此邮件。<br>YueluDate · 岳麓山下的匹配实验</p>
    </div>
    """


def _send_via_qq_smtp(to_email: str, code: str) -> bool:
    """通过 QQ 邮箱 SMTP 发送验证码，作为 Resend 抑制时的回退。"""
    if not QQ_SMTP_EMAIL or not QQ_SMTP_AUTH_CODE:
        log.error("QQ SMTP 未配置，无法回退发送")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"YueluDate <{QQ_SMTP_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = "【YueluDate】邮箱验证码"
        msg.attach(MIMEText(_build_code_html(code), "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10) as s:
            s.login(QQ_SMTP_EMAIL, QQ_SMTP_AUTH_CODE)
            s.sendmail(QQ_SMTP_EMAIL, [to_email], msg.as_string())
        log.info("QQ SMTP 回退发送成功: %s", to_email)
        return True
    except Exception as e:
        log.error("QQ SMTP 发送失败: %s -> %s", to_email, e)
        return False


def generate_and_send(email: str):
    """生成验证码并通过 Resend 发送邮件；被抑制时自动回退到 QQ 邮箱。返回 (成功, 消息)。"""
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
            "subject": "【YueluDate】邮箱验证码",
            "html": _build_code_html(code),
        })

        # 检查邮件是否被 Resend 抑制（之前退信/投诉导致）
        email_id = r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
        if email_id:
            try:
                time.sleep(1)
                detail = resend.Emails.get(email_id)
                last_event = detail.get("last_event") if isinstance(detail, dict) else getattr(detail, "last_event", None)
                if last_event == "suppressed":
                    log.warning("Resend 抑制，回退 QQ SMTP: %s", email)
                    if _send_via_qq_smtp(email, code):
                        return True, "验证码已发送（备用通道）"
                    _store.pop(email, None)
                    return False, (
                        f"邮件发送失败：{email} 暂时无法送达，请稍后再试或联系管理员。"
                    )
                log.info("邮件已发送: %s (email_id=%s, status=%s)", email, email_id, last_event)
            except Exception as check_err:
                log.warning("检查邮件状态失败: %s", check_err)

        return True, "验证码已发送"
    except Exception as e:
        # Resend 完全失败时也尝试 QQ SMTP 回退
        log.warning("Resend 异常，回退 QQ SMTP: %s -> %s", email, e)
        if _send_via_qq_smtp(email, code):
            return True, "验证码已发送（备用通道）"
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
