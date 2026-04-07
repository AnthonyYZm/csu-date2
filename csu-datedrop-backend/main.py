import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
import resend
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from config import (
    ACCESS_TOKEN_EXPIRE_DAYS,
    ADMIN_TOKEN,
    ALGORITHM,
    EDU_DOMAIN,
    EDU_VERIFY_DAYS,
    NARRATIVE_WORKERS,
    QUIZ_LOCK_HOUR_END,
    QUIZ_LOCK_HOUR_START,
    QUIZ_LOCK_WEEKDAY,
    SECRET_KEY,
    is_edu_email,
)
from database import engine, get_db
from models import Base, Crush, Match, PageView, Profile, User
from matcher_service import default_week_id, run_weekly_matching
from llm_report import generate_narrative  # 提前 import，确保 .env 已加载
from schemas import (
    EduEmailSendCodeRequest,
    EduEmailVerifyRequest,
    GreetRequest,
    LoginRequest,
    PausedRequest,
    ProfileUpdateRequest,
    QuizSubmit,
    RegisterRequest,
    ResetPasswordRequest,
    RunMatchBody,
    SendCodeRequest,
    ShootRequest,
    VerifyCodeRequest,
    WechatUpdateRequest,
)
import email_service
from email_service import FROM_EMAIL

logger = logging.getLogger(__name__)

# --- Security ---

if SECRET_KEY == "dev-csu-date-change-me":
    logger.warning("CSU_DATE_SECRET 使用默认值，请在生产环境设置安全的密钥！")

security = HTTPBearer(auto_error=False)

app = FastAPI(title="CSU Date API")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest


# ── 页面访问量记录中间件 ──
TRACKED_PAGES = {
    "/", "/index.html", "/login.html", "/dashboard.html",
    "/report.html", "/greet.html", "/inbox.html", "/profile.html",
    "/about.html", "/admin-dashboard.html",
}


class PageViewMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        # 记录页面访问和 API 调用
        if path in TRACKED_PAGES or path.startswith("/api/"):
            try:
                db = next(get_db())
                db.add(PageView(
                    path=path,
                    timestamp=datetime.now(timezone.utc),
                    ip=request.client.host if request.client else None,
                    user_agent=(request.headers.get("user-agent") or "")[:256],
                ))
                db.commit()
                db.close()
            except Exception:
                logger.exception("Failed to record page view for %s", path)
        return response


app.add_middleware(PageViewMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """将 Pydantic 422 错误转换为用户友好的中文提示。"""
    messages = []
    for err in exc.errors():
        field = err.get("loc", [])[-1] if err.get("loc") else ""
        etype = err.get("type", "")
        field_names = {
            "email": "邮箱", "password": "密码", "code": "验证码",
            "name": "昵称", "campus": "校区", "grade": "年级", "major": "专业",
        }
        fname = field_names.get(field, field)
        if "missing" in etype:
            messages.append(f"请填写{fname}")
        elif "too_short" in etype:
            messages.append(f"{fname}长度不足")
        elif "too_long" in etype:
            messages.append(f"{fname}过长")
        else:
            messages.append(f"{fname}格式有误")
    detail = "；".join(messages) if messages else "请求参数有误，请检查后重试"
    return JSONResponse(status_code=422, content={"detail": detail})


# --- Helpers ---


def normalize_csu_email(raw: str, no_edu: bool = False) -> str:
    s = raw.strip().lower()
    if no_edu:
        if "@" not in s:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请输入完整的邮箱地址",
            )
        return s
    if "@" not in s:
        s = f"{s}{EDU_DOMAIN}"
    if not s.endswith(EDU_DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"必须使用 {EDU_DOMAIN} 邮箱",
        )
    return s


def edu_verify_deadline(user: User) -> Optional[datetime]:
    """返回该用户的教育邮箱验证截止时间，教育邮箱用户返回 None。"""
    if is_edu_email(user.email):
        return None
    if user.edu_email_verified_at:
        return None
    if not user.created_at:
        return None
    return user.created_at + timedelta(days=EDU_VERIFY_DAYS)


def is_edu_blocked(user: User) -> bool:
    """非教育邮箱用户超过验证期限未验证，则封锁匹配功能。"""
    if is_edu_email(user.email):
        return False
    if user.edu_email_verified_at:
        return False
    deadline = edu_verify_deadline(user)
    if deadline is None:
        return False
    return datetime.now(timezone.utc) >= deadline.replace(tzinfo=timezone.utc) if deadline.tzinfo is None else datetime.now(timezone.utc) >= deadline


def _password_bytes(plain: str) -> bytes:
    """bcrypt 仅使用前 72 字节。"""
    return plain.encode("utf-8")[:72]


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_password_bytes(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_password_bytes(plain), bcrypt.gensalt()).decode("ascii")


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> int:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = data.get("sub")
        if sub is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的凭证")
        return int(sub)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的凭证或已过期")


def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "需要登录")
    uid = decode_token(creds.credentials)
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def local_id_from_email(email: str) -> str:
    return email.split("@", 1)[0] if "@" in email else str(email)


def current_week_id() -> int:
    iso = datetime.now(timezone.utc).isocalendar()
    return iso.year * 100 + iso.week


def ordered_user_pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _cross_campus_to_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    if value == "可以接受":
        return True
    if value == "不接受":
        return False
    return None


def compute_match_stats(db: Session, user_id: int) -> dict:
    rows = (
        db.query(Match)
        .filter(or_(Match.user1_id == user_id, Match.user2_id == user_id))
        .all()
    )
    if not rows:
        return {"matches": 0, "bestScore": 0, "weeks": 0}
    best = 0
    weeks_set = set()
    for m in rows:
        sc = m.score
        if sc is not None and sc >= 0:
            best = max(best, int(round(sc)))
        if m.week_number and m.week_number > 0:
            weeks_set.add(m.week_number)
    return {
        "matches": len(rows),
        "bestScore": best,
        "weeks": len(weeks_set),
    }


def has_weekly_match(db: Session, user_id: int, week_id: int) -> bool:
    return (
        db.query(Match)
        .filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id),
            Match.week_number == week_id,
        )
        .first()
        is not None
    )


def serialize_user(db: Session, user: User, login_time_ms: Optional[int] = None) -> dict:
    stats = compute_match_stats(db, user.id)
    weekly = has_weekly_match(db, user.id, current_week_id())
    values = user.values_json if isinstance(user.values_json, list) else []
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # 教育邮箱验证状态
    edu_verified = is_edu_email(user.email) or bool(user.edu_email_verified_at)
    deadline = edu_verify_deadline(user)
    deadline_ms = int(deadline.replace(tzinfo=timezone.utc).timestamp() * 1000) if deadline and deadline.tzinfo is None else (int(deadline.timestamp() * 1000) if deadline else None)

    return {
        "id": local_id_from_email(user.email),
        "email": user.email,
        "name": user.name or "",
        "campus": user.campus or "",
        "grade": user.grade or "",
        "major": user.major or "",
        "bio": user.bio or "",
        "values": values,
        "wechat": user.wechat or "",
        "stats": stats,
        "loggedIn": True,
        "loginTime": login_time_ms if login_time_ms is not None else now_ms,
        "quizCompleted": bool(user.quiz_completed),
        "weeklyMatch": weekly,
        "paused": bool(user.paused),
        "eduEmailVerified": edu_verified,
        "eduEmail": user.edu_email or "",
        "eduVerifyDeadline": deadline_ms,
        "eduBlocked": is_edu_blocked(user),
    }


def peer_from_match(db: Session, m: Match, me_id: int) -> Optional[User]:
    pid = m.user2_id if m.user1_id == me_id else m.user1_id
    return db.query(User).filter(User.id == pid).first()


def messages_for_user(rd: dict, me_id: int, peer_id: int) -> Tuple[Optional[str], Optional[str]]:
    if not rd:
        return None, None
    by_uid = rd.get("messagesByUserId") or {}
    if isinstance(by_uid, dict) and by_uid:
        your = by_uid.get(str(me_id)) or by_uid.get(me_id)
        their = by_uid.get(str(peer_id)) or by_uid.get(peer_id)
        return their, your
    their = rd.get("theirMessage") or rd.get("their_message")
    your = rd.get("yourMessage") or rd.get("your_message")
    return their, your


# --- Routes ---


@app.get("/")
def read_root():
    return {"message": "CSU Date API 已启动"}


@app.get("/api/stats")
def public_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    quiz_done = db.query(User).filter(User.quiz_completed == True).count()
    total_matches = db.query(Match).count()
    return {"totalUsers": total_users, "quizCompleted": quiz_done, "totalMatches": total_matches}


def _build_growth_series(db: Session):
    """构建用户增长时间序列，按小时聚合。"""
    from sqlalchemy import func as fn
    rows = (
        db.query(User.created_at)
        .filter(User.created_at.isnot(None))
        .order_by(User.created_at)
        .all()
    )
    if not rows:
        return {"timestamps": [], "cumUsers": [], "hourlyNew": [], "cumQuiz": []}

    # 累计注册
    timestamps = []
    cum_users = []
    for i, (ts,) in enumerate(rows, 1):
        timestamps.append(ts.strftime("%Y-%m-%d %H:%M:%S"))
        cum_users.append(i)

    # 每小时新增
    from collections import OrderedDict
    hourly = OrderedDict()
    for (ts,) in rows:
        h = ts.strftime("%Y-%m-%d %H:00")
        hourly[h] = hourly.get(h, 0) + 1

    # 问卷完成累计（按 user id 顺序近似）
    quiz_ids = (
        db.query(User.created_at)
        .filter(User.created_at.isnot(None), User.quiz_completed == True)
        .order_by(User.created_at)
        .all()
    )
    quiz_ts = []
    cum_quiz = []
    for i, (ts,) in enumerate(quiz_ids, 1):
        quiz_ts.append(ts.strftime("%Y-%m-%d %H:%M:%S"))
        cum_quiz.append(i)

    return {
        "timestamps": timestamps,
        "cumUsers": cum_users,
        "hourlyLabels": list(hourly.keys()),
        "hourlyNew": list(hourly.values()),
        "quizTimestamps": quiz_ts,
        "cumQuiz": cum_quiz,
    }


@app.get("/api/admin/dashboard-stats")
def admin_dashboard_stats(db: Session = Depends(get_db)):
    """管理看板数据：用户统计、分布、匹配概览。"""
    from sqlalchemy import func, case

    total = db.query(User).count()
    verified = db.query(User).filter(User.is_verified == True).count()
    quiz_done = db.query(User).filter(User.quiz_completed == True).count()
    paused = db.query(User).filter(User.paused == True).count()
    total_matches = db.query(Match).count()

    # 校区分布
    campus_rows = (
        db.query(User.campus, func.count())
        .filter(User.campus != "")
        .group_by(User.campus)
        .order_by(func.count().desc())
        .all()
    )
    campus_dist = [{"name": r[0], "value": r[1]} for r in campus_rows]

    # 年级分布
    grade_rows = (
        db.query(User.grade, func.count())
        .filter(User.grade != "")
        .group_by(User.grade)
        .order_by(func.count().desc())
        .all()
    )
    grade_dist = [{"name": r[0], "value": r[1]} for r in grade_rows]

    # 性别分布
    gender_rows = (
        db.query(Profile.gender, func.count())
        .filter(Profile.gender.isnot(None))
        .group_by(Profile.gender)
        .order_by(func.count().desc())
        .all()
    )
    gender_dist = [{"name": r[0], "value": r[1]} for r in gender_rows]

    # 性取向分布
    sexuality_rows = (
        db.query(Profile.sexuality, func.count())
        .filter(Profile.sexuality.isnot(None))
        .group_by(Profile.sexuality)
        .order_by(func.count().desc())
        .all()
    )
    sexuality_dist = [{"name": r[0], "value": r[1]} for r in sexuality_rows]

    # 专业 Top 10
    major_rows = (
        db.query(User.major, func.count())
        .filter(User.major != "")
        .group_by(User.major)
        .order_by(func.count().desc())
        .limit(10)
        .all()
    )
    major_dist = [{"name": r[0], "value": r[1]} for r in major_rows]

    # 匹配分数分布
    match_rows = db.query(Match.score).all()
    score_brackets = {"85+": 0, "80-85": 0, "75-80": 0, "70-75": 0, "<70": 0}
    for (s,) in match_rows:
        if s is None:
            continue
        if s >= 85:
            score_brackets["85+"] += 1
        elif s >= 80:
            score_brackets["80-85"] += 1
        elif s >= 75:
            score_brackets["75-80"] += 1
        elif s >= 70:
            score_brackets["70-75"] += 1
        else:
            score_brackets["<70"] += 1
    score_dist = [{"name": k, "value": v} for k, v in score_brackets.items()]

    # 跨校区意愿
    cross_yes = db.query(Profile).filter(Profile.cross_campus_ok == True).count()
    cross_no = db.query(Profile).filter(Profile.cross_campus_ok == False).count()

    return {
        "overview": {
            "totalUsers": total,
            "verified": verified,
            "quizCompleted": quiz_done,
            "paused": paused,
            "totalMatches": total_matches,
            "matchedUsers": total_matches * 2,
            "unmatchedUsers": quiz_done - paused - total_matches * 2 if quiz_done - paused > total_matches * 2 else 0,
        },
        "campusDist": campus_dist,
        "gradeDist": grade_dist,
        "genderDist": gender_dist,
        "sexualityDist": sexuality_dist,
        "majorDist": major_dist,
        "scoreDist": score_dist,
        "crossCampus": {"yes": cross_yes, "no": cross_no},
        "growth": _build_growth_series(db),
        "pageViews": _build_page_view_stats(db),
    }


def _build_page_view_stats(db: Session):
    """构建页面访问量统计。"""
    from sqlalchemy import func as fn
    from collections import OrderedDict

    total_views = db.query(PageView).count()

    # 今日访问量
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_views = db.query(PageView).filter(PageView.timestamp >= today_start).count()

    # 独立 IP 数
    unique_ips = db.query(fn.count(fn.distinct(PageView.ip))).scalar() or 0
    today_unique_ips = (
        db.query(fn.count(fn.distinct(PageView.ip)))
        .filter(PageView.timestamp >= today_start)
        .scalar() or 0
    )

    # 各页面访问量（仅页面，不含 API）
    page_rows = (
        db.query(PageView.path, fn.count())
        .filter(~PageView.path.startswith("/api/"))
        .group_by(PageView.path)
        .order_by(fn.count().desc())
        .all()
    )
    page_dist = [{"name": r[0], "value": r[1]} for r in page_rows]

    # API 调用量 Top 10
    api_rows = (
        db.query(PageView.path, fn.count())
        .filter(PageView.path.startswith("/api/"))
        .group_by(PageView.path)
        .order_by(fn.count().desc())
        .limit(10)
        .all()
    )
    api_dist = [{"name": r[0], "value": r[1]} for r in api_rows]

    # 每小时访问量趋势
    hourly_rows = (
        db.query(PageView.timestamp)
        .filter(PageView.timestamp.isnot(None))
        .order_by(PageView.timestamp)
        .all()
    )
    hourly = OrderedDict()
    for (ts,) in hourly_rows:
        h = ts.strftime("%Y-%m-%d %H:00")
        hourly[h] = hourly.get(h, 0) + 1

    return {
        "totalViews": total_views,
        "todayViews": today_views,
        "uniqueIPs": unique_ips,
        "todayUniqueIPs": today_unique_ips,
        "pageDist": page_dist,
        "apiDist": api_dist,
        "hourlyLabels": list(hourly.keys()),
        "hourlyViews": list(hourly.values()),
    }


@app.post("/api/auth/send-code")
def auth_send_code(body: SendCodeRequest):
    """发送邮箱验证码（注册前调用）。"""
    email = normalize_csu_email(body.email, no_edu=body.no_edu)
    ok, msg = email_service.generate_and_send(email)
    if not ok:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, msg)
    return {"ok": True, "message": msg}


@app.post("/api/auth/register")
def auth_register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = normalize_csu_email(body.email, no_edu=body.no_edu)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该邮箱已注册")

    # 验证邮箱验证码
    ok, msg = email_service.verify_code(email, body.code)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, msg)

    user = User(
        email=email,
        hashed_password=hash_password(body.password),
        name=body.name,
        campus=body.campus,
        grade=body.grade,
        major=body.major,
        quiz_completed=False,
        paused=False,
        is_verified=True,
        bio="",
        values_json=[],
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "注册失败")
    db.refresh(user)
    token = create_access_token(user.id)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(db, user, login_time_ms=now_ms),
    }


@app.post("/api/auth/login")
def auth_login(body: LoginRequest, db: Session = Depends(get_db)):
    # 登录时宽松匹配：同时尝试教育邮箱和原始邮箱，兼容老的非教育邮箱用户
    raw = body.email.strip().lower()
    candidates = []
    if "@" in raw:
        candidates.append(raw)
        # 如果不是教育邮箱，也尝试学号格式（以防用户输入了完整教育邮箱）
        if not raw.endswith(EDU_DOMAIN):
            candidates.append(f"{raw.split('@')[0]}{EDU_DOMAIN}")
    else:
        # 没有@，按学号处理，拼上教育邮箱后缀
        candidates.append(f"{raw}{EDU_DOMAIN}")
    user = None
    for email in candidates:
        user = db.query(User).filter(User.email == email).first()
        if user:
            break
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "邮箱或密码错误")
    token = create_access_token(user.id)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(db, user, login_time_ms=now_ms),
    }


@app.post("/api/auth/reset-password")
def auth_reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """通过邮箱验证码重置密码。"""
    # 宽松匹配，兼容非教育邮箱用户
    raw = body.email.strip().lower()
    candidates = []
    if "@" in raw:
        candidates.append(raw)
        if not raw.endswith(EDU_DOMAIN):
            candidates.append(f"{raw.split('@')[0]}{EDU_DOMAIN}")
    else:
        candidates.append(f"{raw}{EDU_DOMAIN}")
    user = None
    email = candidates[0]
    for e in candidates:
        user = db.query(User).filter(User.email == e).first()
        if user:
            email = e
            break
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该邮箱未注册")

    ok, msg = email_service.verify_code(email, body.code)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, msg)

    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"ok": True, "message": "密码已重置，请重新登录"}


@app.get("/api/user/me")
def get_me(user: CurrentUser, db: Session = Depends(get_db)):
    return serialize_user(db, user)


@app.put("/api/user/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """更新用户个人资料（昵称、简介、校区、年级、专业）。"""
    if body.name is not None:
        user.name = body.name.strip()[:32]
    if body.bio is not None:
        user.bio = body.bio.strip()[:200]
    if body.campus is not None:
        user.campus = body.campus.strip()[:32]
    if body.grade is not None:
        user.grade = body.grade.strip()[:16]
    if body.major is not None:
        user.major = body.major.strip()[:64]
    db.commit()
    db.refresh(user)
    return {"ok": True, "user": serialize_user(db, user)}


@app.get("/api/user/quiz")
def get_quiz(user: CurrentUser, db: Session = Depends(get_db)):
    """返回用户已保存的问卷数据，用于前端回填。"""
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile or not profile.raw_quiz_data:
        return {"saved": False}
    raw = profile.raw_quiz_data if isinstance(profile.raw_quiz_data, dict) else {}
    # 把 Profile 表的硬性字段也合并回去
    raw["gender"] = profile.gender
    raw["sexuality"] = profile.sexuality
    raw["campus"] = profile.campus
    cross = profile.cross_campus_ok
    if cross is True:
        raw["crossCampus"] = "可以接受"
    elif cross is False:
        raw["crossCampus"] = "不接受"
    return {"saved": True, "quiz": raw}


@app.post("/api/user/wechat")
def update_wechat(
    body: WechatUpdateRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    user.wechat = (body.wechat or "").strip()[:64]
    db.commit()
    db.refresh(user)
    return {"ok": True, "user": serialize_user(db, user)}


@app.post("/api/user/paused")
def set_paused(
    body: PausedRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    user.paused = body.paused
    db.commit()
    db.refresh(user)
    return {"ok": True, "user": serialize_user(db, user)}


@app.post("/api/user/edu-email/send-code")
def edu_email_send_code(
    body: EduEmailSendCodeRequest,
    user: CurrentUser,
):
    """非教育邮箱用户发送教育邮箱验证码。"""
    if is_edu_email(user.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "你已使用教育邮箱注册，无需验证")
    if user.edu_email_verified_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "你已验证过教育邮箱")

    edu_email = body.edu_email.strip().lower()
    if not edu_email.endswith(EDU_DOMAIN):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"必须使用 {EDU_DOMAIN} 教育邮箱")

    ok, msg = email_service.generate_and_send(edu_email)
    if not ok:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, msg)
    return {"ok": True, "message": msg}


@app.post("/api/user/edu-email/verify")
def edu_email_verify(
    body: EduEmailVerifyRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """验证教育邮箱验证码，完成绑定。"""
    if is_edu_email(user.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "你已使用教育邮箱注册，无需验证")
    if user.edu_email_verified_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "你已验证过教育邮箱")

    edu_email = body.edu_email.strip().lower()
    if not edu_email.endswith(EDU_DOMAIN):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"必须使用 {EDU_DOMAIN} 教育邮箱")

    # 检查该教育邮箱是否已被其他账号使用或绑定
    existing = db.query(User).filter(
        (User.email == edu_email) | (User.edu_email == edu_email)
    ).first()
    if existing and existing.id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该教育邮箱已被其他账号使用")

    ok, msg = email_service.verify_code(edu_email, body.code)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, msg)

    user.edu_email = edu_email
    user.edu_email_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return {"ok": True, "message": "教育邮箱验证成功", "user": serialize_user(db, user)}


@app.post("/api/crush/shoot")
def crush_shoot(
    body: ShootRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if is_edu_blocked(user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"你尚未验证教育邮箱，注册已超过 {EDU_VERIFY_DAYS} 天，无法参与匹配。请先绑定 {EDU_DOMAIN} 教育邮箱。",
        )

    target_email = normalize_csu_email(body.target_email, no_edu=("@" in body.target_email and not body.target_email.strip().endswith(EDU_DOMAIN)))
    if target_email == user.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能对自己发射")

    target = db.query(User).filter(User.email == target_email).first()

    existing = (
        db.query(Crush)
        .filter(Crush.sender_id == user.id, Crush.target_email == target_email)
        .order_by(Crush.id.desc())
        .first()
    )
    if existing and existing.is_mutual:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "已与该用户双向匹配")

    if not existing:
        crush = Crush(
            sender_id=user.id,
            target_email=target_email,
            message=(body.message or "")[:2000],
            is_mutual=False,
        )
        db.add(crush)
    else:
        crush = existing
        crush.message = (body.message or "")[:2000]

    mutual = False
    if target:
        inverse = (
            db.query(Crush)
            .filter(
                Crush.sender_id == target.id,
                Crush.target_email == user.email,
            )
            .order_by(Crush.id.desc())
            .first()
        )
        if inverse:
            mutual = True
            crush.is_mutual = True
            inverse.is_mutual = True
            u1, u2 = ordered_user_pair(user.id, target.id)
            dup = (
                db.query(Match)
                .filter(
                    Match.user1_id == u1,
                    Match.user2_id == u2,
                    Match.week_number == 0,
                )
                .first()
            )
            if not dup:
                rd = {
                    "kind": "mutual_shot",
                    "messagesByUserId": {
                        str(user.id): crush.message or "",
                        str(target.id): inverse.message or "",
                    },
                }
                m = Match(
                    user1_id=u1,
                    user2_id=u2,
                    week_number=0,
                    score=100.0,
                    report_data=rd,
                )
                db.add(m)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "匹配记录已存在或数据冲突",
        )

    return {
        "ok": True,
        "mutual": mutual,
        "message": "双向匹配成功" if mutual else "已保存，等待对方也向你发射",
        "user": serialize_user(db, user),
    }


@app.get("/api/inbox")
def get_inbox(user: CurrentUser, db: Session = Depends(get_db)):
    items = []

    matches = (
        db.query(Match)
        .filter(or_(Match.user1_id == user.id, Match.user2_id == user.id))
        .order_by(Match.week_number.desc(), Match.id.desc())
        .all()
    )
    for m in matches:
        peer = peer_from_match(db, m, user.id)
        if not peer:
            continue
        rd = m.report_data if isinstance(m.report_data, dict) else {}
        kind = rd.get("kind", "algorithm")
        their_msg, your_msg = messages_for_user(rd, user.id, peer.id)
        preview = their_msg or your_msg or "匹配记录"
        items.append(
            {
                "id": m.id,
                "type": "mutual",
                "status": "mutual",
                "weekNumber": m.week_number,
                "score": int(round(m.score)) if m.score is not None else None,
                "peerName": peer.name or "CSU 用户",
                "peerEmail": peer.email,
                "peerCampus": peer.campus or "",
                "peerGrade": peer.grade or "",
                "peerMajor": peer.major or "",
                "peerInitial": (peer.name or "?")[:1],
                "peerWechat": peer.wechat or "",
                "theirMessage": their_msg,
                "yourMessage": your_msg,
                "preview": preview,
                "kind": kind,
            }
        )

    pending = (
        db.query(Crush)
        .filter(Crush.sender_id == user.id, Crush.is_mutual.is_(False))
        .order_by(Crush.id.desc())
        .all()
    )
    for c in pending:
        items.append(
            {
                "id": f"crush-{c.id}",
                "type": "waiting",
                "status": "waiting",
                "weekNumber": None,
                "targetEmail": c.target_email,
                "preview": c.message or "已发送 Shoot Your Shot，等待对方也向你发射…",
                "message": c.message or "",
            }
        )

    return {"threads": items}


@app.get("/api/match/{match_id}")
def get_match_report(match_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    """返回单条匹配的详细报告数据。叙事在 run-match 阶段已批量预生成。"""
    m = (
        db.query(Match)
        .filter(
            Match.id == match_id,
            or_(Match.user1_id == user.id, Match.user2_id == user.id),
        )
        .first()
    )
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "匹配记录不存在")

    peer = peer_from_match(db, m, user.id)
    rd = m.report_data if isinstance(m.report_data, dict) else {}
    their_msg, your_msg = messages_for_user(rd, user.id, peer.id if peer else 0)

    return {
        "id": m.id,
        "weekNumber": m.week_number,
        "score": int(round(m.score)) if m.score is not None else 0,
        "kind": rd.get("kind", "algorithm"),
        "peerName": peer.name if peer else "CSU 用户",
        "peerEmail": peer.email if peer else "",
        "peerCampus": (peer.campus or "") if peer else "",
        "peerGrade": (peer.grade or "") if peer else "",
        "peerMajor": (peer.major or "") if peer else "",
        "peerInitial": (peer.name or "?")[:1] if peer else "?",
        "theirMessage": their_msg,
        "yourMessage": your_msg,
        "breakdown": rd.get("breakdown") or {},
        "evidence": rd.get("evidence") or {},
        "reportPayload": rd.get("reportPayload") or {},
        "narrative": rd.get("narrative"),
    }


@app.post("/api/match/{match_id}/greet")
def send_match_greeting(
    match_id: int,
    body: GreetRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """给匹配对象发送一条留言（每人仅限一条）。"""
    m = (
        db.query(Match)
        .filter(
            Match.id == match_id,
            or_(Match.user1_id == user.id, Match.user2_id == user.id),
        )
        .first()
    )
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "匹配记录不存在")

    msg = (body.message or "").strip()[:200]
    if not msg:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "消息不能为空")

    rd = m.report_data if isinstance(m.report_data, dict) else {}
    by_uid = rd.get("messagesByUserId") or {}
    uid_key = str(user.id)

    if by_uid.get(uid_key):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "你已经发送过消息了")

    by_uid[uid_key] = msg
    rd["messagesByUserId"] = by_uid
    m.report_data = rd
    flag_modified(m, "report_data")
    db.commit()

    return {"ok": True, "message": "发送成功"}


def is_quiz_locked() -> bool:
    """匹配计算窗口期间锁定问卷提交（默认周四 16:00~21:00 UTC+8）。"""
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    except Exception:
        tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    if now.weekday() == QUIZ_LOCK_WEEKDAY:
        if QUIZ_LOCK_HOUR_START <= now.hour < QUIZ_LOCK_HOUR_END:
            return True
    return False


@app.post("/api/quiz/submit")
def submit_quiz(
    payload: QuizSubmit,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if is_quiz_locked():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"问卷提交已锁定（匹配计算窗口 {QUIZ_LOCK_HOUR_START}:00-{QUIZ_LOCK_HOUR_END}:00），请 {QUIZ_LOCK_HOUR_END}:00 后再修改",
        )

    if is_edu_blocked(user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"你尚未验证教育邮箱，注册已超过 {EDU_VERIFY_DAYS} 天，无法提交问卷。请先绑定 {EDU_DOMAIN} 教育邮箱。",
        )

    cross_ok = _cross_campus_to_bool(payload.crossCampus)

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    profile.gender = payload.gender
    profile.sexuality = payload.sexuality
    profile.campus = payload.campus
    profile.cross_campus_ok = cross_ok
    profile.raw_quiz_data = payload.raw_quiz_data

    user.quiz_completed = True
    db.commit()
    db.refresh(profile)
    db.refresh(user)

    return {
        "status": "success",
        "message": "问卷已保存",
        "profile_id": profile.id,
        "user_id": user.id,
        "user": serialize_user(db, user),
    }




def _bg_generate_narratives(week_id: int):
    """后台线程：并发生成叙事并写入 DB。"""
    import traceback
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from database import SessionLocal
    from llm_report import _load_env
    _load_env()

    print(f"[narrative_bg] started for week {week_id}, workers={NARRATIVE_WORKERS}", flush=True)

    # 先用一个 session 读出所有待生成的任务参数
    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.week_number == week_id).all()
        tasks = []
        for m in matches:
            rd = m.report_data if isinstance(m.report_data, dict) else {}
            if rd.get("narrative") or rd.get("kind") != "algorithm":
                continue
            u1 = db.query(User).filter(User.id == m.user1_id).first()
            u2 = db.query(User).filter(User.id == m.user2_id).first()
            if not u1 or not u2:
                continue
            tasks.append({
                "match_id": m.id,
                "score": int(round(m.score)) if m.score is not None else 0,
                "u1_name": u1.name or "用户A",
                "u2_name": u2.name or "用户B",
                "u2_campus": u2.campus or "",
                "u2_grade": u2.grade or "",
                "u2_major": u2.major or "",
                "breakdown": rd.get("breakdown") or {},
                "report_payload": rd.get("reportPayload") or {},
            })
    finally:
        db.close()

    print(f"[narrative_bg] {len(tasks)} narratives to generate", flush=True)
    if not tasks:
        print("[narrative_bg] nothing to do", flush=True)
        return

    # 并发调用 LLM（纯 API 调用，无 DB 操作）
    def call_llm(t):
        text = generate_narrative(
            my_name=t["u1_name"],
            peer_name=t["u2_name"],
            score=t["score"],
            breakdown=t["breakdown"],
            report_payload=t["report_payload"],
            peer_campus=t["u2_campus"],
            peer_grade=t["u2_grade"],
            peer_major=t["u2_major"],
        )
        return t["match_id"], text

    results = {}
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=NARRATIVE_WORKERS) as pool:
        futures = {pool.submit(call_llm, t): t["match_id"] for t in tasks}
        for future in as_completed(futures):
            mid = futures[future]
            try:
                match_id, text = future.result()
                if text:
                    results[match_id] = text
                    ok += 1
                else:
                    fail += 1
                print(f"[narrative_bg] {ok+fail}/{len(tasks)} {'ok' if text else 'FAIL'} (match {mid})", flush=True)
            except Exception as e:
                fail += 1
                print(f"[narrative_bg] {ok+fail}/{len(tasks)} ERROR match {mid}: {e}", flush=True)

    # 单线程写回 DB
    from sqlalchemy.orm.attributes import flag_modified
    db = SessionLocal()
    try:
        for match_id, text in results.items():
            m = db.query(Match).filter(Match.id == match_id).first()
            if m:
                rd = m.report_data if isinstance(m.report_data, dict) else {}
                rd["narrative"] = text
                m.report_data = rd
                flag_modified(m, "report_data")
        db.commit()
        print(f"[narrative_bg] done: ok={ok} fail={fail} saved={len(results)}", flush=True)
    except Exception as e:
        print(f"[narrative_bg] DB write error: {e}", flush=True)
        traceback.print_exc()
    finally:
        db.close()


def verify_admin_token(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
):
    """校验管理员 token。需在 .env 中设置 CSU_DATE_ADMIN_TOKEN。"""
    if not ADMIN_TOKEN:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "管理员令牌未配置（请设置 CSU_DATE_ADMIN_TOKEN 环境变量）")
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "需要管理员令牌")
    if creds.credentials != ADMIN_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "管理员令牌无效")


@app.post("/api/admin/run-match")
def admin_run_match(
    body: Optional[RunMatchBody] = None,
    db: Session = Depends(get_db),
    _admin: None = Depends(verify_admin_token),
):
    """MVP：无鉴权。先跑匹配，然后后台线程批量生成 LLM 叙事（不阻塞响应）。"""
    import threading

    week_id = default_week_id()
    if body is not None and body.week_id is not None:
        week_id = body.week_id

    result = run_weekly_matching(db, week_id)

    # 后台线程生成叙事，不阻塞返回
    t = threading.Thread(target=_bg_generate_narratives, args=(week_id,), daemon=True)
    t.start()
    result["narrative_status"] = "generating_in_background"

    return result


@app.get("/api/admin/narrative-progress")
def narrative_progress(
    db: Session = Depends(get_db),
    _admin: None = Depends(verify_admin_token),
):
    """查看当前周叙事生成进度。"""
    week_id = default_week_id()
    matches = db.query(Match).filter(Match.week_number == week_id).all()
    total = len(matches)
    done = sum(
        1 for m in matches
        if isinstance(m.report_data, dict) and m.report_data.get("narrative")
    )
    return {"week_id": week_id, "total": total, "done": done, "pending": total - done}


@app.post("/api/admin/check-email-status")
def admin_check_email_status(
    body: dict,
    _admin: None = Depends(verify_admin_token),
):
    """检查某邮箱在 Resend 的投递状态（是否被抑制）。"""
    email_addr = body.get("email", "").strip()
    if not email_addr:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请提供 email 参数")

    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [email_addr],
            "subject": "【CSU Date】邮件投递测试",
            "html": "<p>这是一封测试邮件，用于检查邮件投递状态。如收到请忽略。</p>",
        })
        email_id = r.get("id") if isinstance(r, dict) else getattr(r, "id", None)
        if not email_id:
            return {"email": email_addr, "status": "unknown", "detail": "未获取到邮件 ID"}

        import time as _time
        _time.sleep(2)
        detail = resend.Emails.get(email_id)
        last_event = detail.get("last_event") if isinstance(detail, dict) else getattr(detail, "last_event", None)
        return {
            "email": email_addr,
            "status": last_event,
            "email_id": email_id,
            "suppressed": last_event == "suppressed",
            "message": "该邮箱已被抑制，请在 Resend 控制台移除抑制" if last_event == "suppressed" else "邮件正常发送",
        }
    except Exception as e:
        return {"email": email_addr, "status": "error", "detail": str(e)}


@app.get("/api/admin/user-lookup")
def admin_user_lookup(
    q: str,
    db: Session = Depends(get_db),
    _admin: None = Depends(verify_admin_token),
):
    """按邮箱/学号/昵称模糊查找用户。"""
    q = q.strip()
    if not q:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请提供查询参数 q")
    users = db.query(User).filter(
        or_(
            User.email.contains(q),
            User.name.contains(q),
            User.edu_email.contains(q),
        )
    ).limit(20).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "campus": u.campus,
            "grade": u.grade,
            "major": u.major,
            "edu_email": u.edu_email,
            "edu_email_verified_at": str(u.edu_email_verified_at) if u.edu_email_verified_at else None,
            "created_at": str(u.created_at) if u.created_at else None,
        }
        for u in users
    ]


@app.post("/api/admin/verify-edu-email")
def admin_verify_edu_email(
    body: dict,
    db: Session = Depends(get_db),
    _admin: None = Depends(verify_admin_token),
):
    """管理员手动为用户通过教育邮箱验证。"""
    user_id = body.get("user_id")
    edu_email = body.get("edu_email", "").strip().lower()
    if not user_id or not edu_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "需要 user_id 和 edu_email")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    user.edu_email = edu_email
    user.edu_email_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return {
        "ok": True,
        "message": f"已为 {user.name}({user.email}) 绑定教育邮箱 {edu_email}",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "edu_email": user.edu_email,
            "edu_email_verified_at": str(user.edu_email_verified_at),
        },
    }
