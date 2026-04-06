"""
将 User/Profile 与问卷 raw JSON 适配为 precision_matching_engine 所需 payload，并落库 Match。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import Match, Profile, User

EDU_VERIFY_DAYS = 3


def _is_edu_blocked(user: User) -> bool:
    """非教育邮箱用户超过 3 天未验证教育邮箱则封锁。"""
    email = (user.email or "").strip().lower()
    if email.endswith("@csu.edu.cn"):
        return False
    if user.edu_email_verified_at:
        return False
    if not user.created_at:
        return False
    deadline = user.created_at + timedelta(days=EDU_VERIFY_DAYS)
    now = datetime.now(timezone.utc)
    deadline_aware = deadline.replace(tzinfo=timezone.utc) if deadline.tzinfo is None else deadline
    return now >= deadline_aware
from precision_matching_engine import PrecisionMatchConfig, solve_weekly_matches

logger = logging.getLogger(__name__)


def _safe_dict(obj: Any) -> Dict[str, Any]:
    return obj if isinstance(obj, dict) else {}


def _safe_list(obj: Any) -> List[Any]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    return []


def grade_to_int(grade_str: Optional[str], default: int = 3) -> int:
    if not grade_str:
        return default
    s = str(grade_str).strip()
    mapping = {
        "大一": 1,
        "大二": 2,
        "大三": 3,
        "大四": 4,
        "研究生": 5,
        "硕士": 5,
        "博士": 6,
    }
    return mapping.get(s, default)


def map_gender(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).strip().lower()
    table = {
        "男": "male",
        "女": "female",
        "非二元": "nonbinary",
        "male": "male",
        "female": "female",
        "nonbinary": "nonbinary",
    }
    return table.get(str(raw).strip(), table.get(s))


def map_sexuality(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    t = str(raw).strip()
    table = {
        "异性恋": "heterosexual",
        "同性恋": "homosexual",
        "双性恋": "bisexual",
        "其他": "bisexual",
        "heterosexual": "heterosexual",
        "homosexual": "homosexual",
        "bisexual": "bisexual",
    }
    return table.get(t, str(t).strip().lower() or None)


def map_spending(raw: Optional[str]) -> str:
    if not raw:
        return "flexible"
    t = str(raw).strip()
    m = {
        "接近aa制": "aa",
        "接近AA制": "aa",
        "收入高的一方多承担": "one_side_more",
        "男方多承担": "one_side_more",
        "看情况灵活处理": "flexible",
    }
    return m.get(t, "flexible")


def map_diet(raw: Optional[str]) -> str:
    if not raw:
        return "no_restriction"
    t = str(raw).strip()
    m = {
        "无特殊要求": "no_restriction",
        "清真（不吃猪肉）": "halal",
        "清真": "halal",
        "素食": "vegetarian",
        "其他": "no_restriction",
    }
    return m.get(t, "no_restriction")


def map_studyspot(raw: Optional[str]) -> str:
    if not raw:
        return "library"
    t = str(raw).strip()
    m = {
        "新校区图书馆": "library",
        "本部老图": "library",
        "铁道校区图书馆": "library",
        "后湖边长椅": "anywhere",
        "咖啡馆": "cafe",
        "不自习": "dorm",
    }
    return m.get(t, "library")


def map_meet_freq(raw: Optional[str]) -> str:
    if not raw:
        return "medium"
    t = str(raw).strip()
    m = {
        "每天": "high",
        "一周3-4次": "medium",
        "一周1-2次": "low",
        "看情况，不固定": "medium",
    }
    return m.get(t, "medium")


def same_college_to_bool(raw: Optional[Any], default: bool = True) -> bool:
    if raw is None:
        return default
    s = str(raw).strip()
    if "不接受" in s:
        return False
    return True


def interest_overlap_from_likert(raw: Dict[str, Any]) -> str:
    likert = _safe_dict(raw.get("likert"))
    block = likert.get("interest_overlap")
    if isinstance(block, dict) and block.get("self") is not None:
        try:
            v = int(block["self"])
            if v <= 3:
                return "complementary"
            if v >= 5:
                return "similar"
        except (TypeError, ValueError):
            pass
    return "similar"


def build_self_likert_and_prefs(
    raw: Dict[str, Any],
) -> Tuple[Dict[str, int], Dict[str, int], List[str]]:
    self_likert: Dict[str, int] = {}
    partner_pref: Dict[str, int] = {}
    important_dims: List[str] = []

    likert = _safe_dict(raw.get("likert"))
    for key, val in likert.items():
        if not isinstance(val, dict):
            continue
        if val.get("self") is not None:
            try:
                self_likert[str(key)] = int(val["self"])
            except (TypeError, ValueError):
                pass
        if val.get("partner") is not None:
            try:
                partner_pref[str(key)] = int(val["partner"])
            except (TypeError, ValueError):
                pass
        if val.get("important") is True:
            important_dims.append(str(key))

    return self_likert, partner_pref, important_dims


def historical_matched_user_ids(db: Session, user_id: int) -> List[str]:
    rows = (
        db.query(Match)
        .filter(
            or_(Match.user1_id == user_id, Match.user2_id == user_id),
            Match.week_number > 0,
        )
        .all()
    )
    out: Set[str] = set()
    for m in rows:
        oid = m.user2_id if m.user1_id == user_id else m.user1_id
        out.add(str(oid))
    return sorted(out)


def ordered_pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def user_profile_to_participant_item(
    user: User,
    profile: Profile,
    raw: Dict[str, Any],
    history_ids: List[str],
) -> Dict[str, Any]:
    cross = profile.cross_campus_ok
    if cross is None:
        cross = True

    height = raw.get("height")
    try:
        height_f = float(height) if height is not None else 170.0
    except (TypeError, ValueError):
        height_f = 170.0
    hmin = raw.get("heightPrefMin", 150)
    hmax = raw.get("heightPrefMax", 190)
    try:
        hmin_f = float(hmin)
    except (TypeError, ValueError):
        hmin_f = 150.0
    try:
        hmax_f = float(hmax)
    except (TypeError, ValueError):
        hmax_f = 190.0

    college = raw.get("college")
    college_s = str(college).strip().lower() if college else "other"
    if not college_s:
        college_s = "other"

    hometown = raw.get("hometown")
    hometown_s = str(hometown).strip().lower() if hometown else None

    self_likert, partner_pref, important_dims = build_self_likert_and_prefs(raw)

    interests = [str(x) for x in _safe_list(raw.get("interests"))]
    self_traits = [str(x) for x in _safe_list(raw.get("selfTraits"))]
    partner_traits = [str(x) for x in _safe_list(raw.get("partnerTraits"))]

    partner_traits_important = bool(raw.get("partnerTraitsImportant", False))

    spending = map_spending(raw.get("spending"))
    diet = map_diet(raw.get("diet"))
    studyspot = map_studyspot(raw.get("studyspot"))
    meet_freq = map_meet_freq(raw.get("meet_freq"))

    return {
        "userId": str(user.id),
        "hardFilters": {
            "gender": map_gender(profile.gender),
            "sexuality": map_sexuality(profile.sexuality),
            "grade": grade_to_int(user.grade, default=3),
            "campus": str(profile.campus or "").strip().lower() or None,
            "college": college_s,
            "hometown": hometown_s,
            "height": height_f,
            "heightPrefMin": hmin_f,
            "heightPrefMax": hmax_f,
            "crossCampus": bool(cross),
            "sameCollege": same_college_to_bool(raw.get("sameCollege"), default=True),
        },
        "status": {
            "verified": bool(user.is_verified),
            "completedQuestionnaire": bool(user.quiz_completed),
            "paused": bool(user.paused),
            "optIn": True,
        },
        "features": {
            "selfLikert": self_likert,
            "spending": spending,
            "diet": diet,
            "studyspot": studyspot,
            "meet_freq": meet_freq,
            "interests": interests,
            "selfTraits": self_traits,
        },
        "preferences": {
            "partnerPref": partner_pref,
            "partnerTraits": partner_traits,
            "interestOverlap": interest_overlap_from_likert(raw),
            "partnerTraitsImportant": partner_traits_important,
            "importantDimensions": important_dims,
        },
        "history": {
            "matchedUserIds": history_ids,
            "blockedUserIds": [],
        },
    }


def run_weekly_matching(db: Session, week_id: int) -> Dict[str, Any]:
    """
    查询可匹配用户，组装 payload，调用 solve_weekly_matches，将结果写入 Match 表。
    """
    all_rows = (
        db.query(User, Profile)
        .join(Profile, Profile.user_id == User.id)
        .filter(
            User.paused.is_(False),
            User.quiz_completed.is_(True),
        )
        .all()
    )

    # 过滤掉未验证教育邮箱且超过 3 天的非edu用户
    rows = [(u, p) for u, p in all_rows if not _is_edu_blocked(u)]
    edu_blocked_count = len(all_rows) - len(rows)
    if edu_blocked_count > 0:
        logger.info("edu_blocked: %d users excluded from matching", edu_blocked_count)

    if len(rows) < 2:
        return {
            "ok": True,
            "week_id": week_id,
            "participant_count": len(rows),
            "match_pair_count": 0,
            "message": "可匹配用户不足 2 人，未运行算法",
            "matches_created": [],
        }

    participants: List[Dict[str, Any]] = []
    for user, profile in rows:
        raw = _safe_dict(profile.raw_quiz_data)
        hist = historical_matched_user_ids(db, user.id)
        try:
            participants.append(user_profile_to_participant_item(user, profile, raw, hist))
        except Exception as exc:
            logger.warning("skip user %s: %s", user.id, exc)
            continue

    if len(participants) < 2:
        return {
            "ok": True,
            "week_id": week_id,
            "participant_count": len(participants),
            "match_pair_count": 0,
            "message": "有效问卷数据不足 2 人",
            "matches_created": [],
        }

    payload = {
        "cycleId": str(week_id),
        "algorithmVersion": "precision-v2.0.0",
        "participants": participants,
    }

    result = solve_weekly_matches(payload, PrecisionMatchConfig())
    matches_out = result.get("matches") or []

    created: List[Dict[str, Any]] = []
    for m in matches_out:
        try:
            ua = int(str(m.get("userA", "")))
            ub = int(str(m.get("userB", "")))
        except ValueError:
            continue
        u1, u2 = ordered_pair(ua, ub)
        exists = (
            db.query(Match)
            .filter(
                Match.user1_id == u1,
                Match.user2_id == u2,
                Match.week_number == week_id,
            )
            .first()
        )
        if exists:
            continue

        score_total = m.get("scoreTotal")
        try:
            sc = float(score_total) if score_total is not None else 0.0
        except (TypeError, ValueError):
            sc = 0.0
        score_db = round(sc * 100.0, 2)

        breakdown = m.get("scoreBreakdown") or {}
        report_data = {
            "kind": "algorithm",
            "breakdown": breakdown,
            "evidence": m.get("evidence"),
            "marketContext": m.get("marketContext"),
            "reportPayload": m.get("reportPayload"),
            "week_id": week_id,
        }

        db.add(
            Match(
                user1_id=u1,
                user2_id=u2,
                week_number=week_id,
                score=score_db,
                report_data=report_data,
            )
        )
        created.append({"user1_id": u1, "user2_id": u2, "score": score_db})

    db.commit()

    return {
        "ok": True,
        "week_id": week_id,
        "participant_count": len(participants),
        "match_pair_count": len(created),
        "matches_created": created,
        "unmatched_summary": {
            "count": len(result.get("unmatched") or []),
        },
    }


def default_week_id() -> int:
    iso = datetime.now(timezone.utc).isocalendar()
    return iso.year * 100 + iso.week
