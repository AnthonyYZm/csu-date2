
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None


SINGLE_LIKERT_FIELDS: Tuple[str, ...] = (
    "citylife",
    "marriage",
    "goodness",
    "idealism",
    "family_career",
    "process_result",
    "novelty",
    "conflict",
    "sleep",
    "tidy",
    "canteen",
    "spicy",
    "datespot",
    "together",
    "travel",
    "consume",
    "reply_anxiety",
    "ritual",
    "opposite_friend",
    "dominance",
    "caretaker",
    "intimacy_pace",
    "social_pda",
    "money_attitude",
    "conflict_response",
    "depend_comfort",
)

DUAL_TRACK_FIELDS: Tuple[str, ...] = (
    "hustle",
    "logic_feel",
    "introvert",
    "smoke",
    "drink",
    "appearance",
)

CATEGORICAL_FIELDS: Tuple[str, ...] = (
    "spending",
    "diet",
    "studyspot",
    "meet_freq",
)

ALL_SELF_FIELDS: Tuple[str, ...] = SINGLE_LIKERT_FIELDS + DUAL_TRACK_FIELDS

FIELD_LABELS: Dict[str, str] = {
    "citylife": "城市偏好",
    "marriage": "婚姻观",
    "goodness": "善良观",
    "idealism": "理想主义",
    "family_career": "家庭vs事业",
    "process_result": "过程vs结果",
    "novelty": "新鲜感",
    "conflict": "冲突处理",
    "sleep": "作息节律",
    "tidy": "整洁度",
    "canteen": "饮食习惯",
    "spicy": "辣度接受",
    "datespot": "约会地点",
    "together": "黏人程度",
    "travel": "旅行风格",
    "consume": "消费观",
    "reply_anxiety": "回复焦虑",
    "ritual": "仪式感",
    "opposite_friend": "异性好友",
    "dominance": "主导性",
    "caretaker": "照顾倾向",
    "intimacy_pace": "亲密节奏",
    "social_pda": "秀恩爱",
    "hustle": "上进心",
    "logic_feel": "理性vs感性",
    "introvert": "内向vs外向",
    "smoke": "吸烟态度",
    "drink": "饮酒态度",
    "appearance": "外貌气质",
    "money_attitude": "经济观",
    "conflict_response": "冲突回应",
    "depend_comfort": "依赖舒适度",
    "spending": "消费风格",
    "diet": "饮食要求",
    "studyspot": "自习偏好",
    "meet_freq": "见面频率",
    "traits": "核心特质",
    "interests": "兴趣爱好",
}

CRITICAL_ALIGNMENT_WEIGHTS: Dict[str, float] = {
    "marriage": 1.60,
    "smoke": 1.55,
    "intimacy_pace": 1.35,
    "drink": 1.30,
    "opposite_friend": 1.20,
    "consume": 1.15,          # elevated: #1 divorce predictor (Dew & Britt 2012)
    "conflict": 1.10,
    "family_career": 1.05,
    "conflict_response": 1.00,  # Gottman: defensiveness vs repair attempts
    "depend_comfort": 0.95,   # attachment avoidance (ECR-R; Candel & Turliuc 2019)
    "social_pda": 0.90,
    "reply_anxiety": 0.85,    # attachment anxiety proxy
}

WORLDVIEW_ALIGNMENT_WEIGHTS: Dict[str, float] = {
    "goodness": 1.05,         # self-transcendence (Van der Wal et al. 2023)
    "money_attitude": 0.90,   # financial philosophy alignment
    "ritual": 0.85,
    "idealism": 0.80,
}

LIFESTYLE_LIKERT_WEIGHTS: Dict[str, float] = {
    "sleep": 1.05,
    "tidy": 0.90,
    "canteen": 0.55,
    "spicy": 0.45,
    "datespot": 0.70,
    "together": 0.95,
    "travel": 0.70,
}

CHEMISTRY_SHARED_WEIGHTS: Dict[str, float] = {
    "novelty": 0.55,
    "citylife": 0.45,
    "process_result": 0.40,
}

SAFE_COMPLEMENT_FIELDS: Dict[str, float] = {
    "introvert": 1.00,
    "logic_feel": 0.85,
    "dominance": 0.70,        # complementarity evidence (Dijkstra & Barelds 2008)
    "caretaker": 0.65,        # care-give vs care-receive complementarity
}

PREFERENCE_DIM_WEIGHTS: Dict[str, float] = {
    "hustle": 1.00,
    "logic_feel": 0.95,
    "introvert": 0.95,
    "smoke": 1.35,
    "drink": 1.10,
    "appearance": 0.80,
}

SENSITIVITY_BY_DIM: Dict[str, float] = {
    "marriage": 0.72,
    "smoke": 0.72,
    "drink": 0.82,
    "intimacy_pace": 0.78,
    "opposite_friend": 0.82,
    "consume": 0.85,          # stricter: financial conflict evidence
    "money_attitude": 0.88,
    "conflict_response": 0.90,
    "social_pda": 0.95,
    "family_career": 0.95,
    "conflict": 0.95,
    "depend_comfort": 0.95,
    "hustle": 1.00,
    "reply_anxiety": 1.00,
    "sleep": 1.05,
    "tidy": 1.05,
    "ritual": 1.05,
    "logic_feel": 1.12,
    "introvert": 1.15,
    "appearance": 1.25,
}

DEFAULT_CATEGORICAL_COMPATIBILITY: Dict[str, Dict[str, Dict[str, float]]] = {
    "spending": {
        "aa": {"aa": 1.00, "flexible": 0.82, "one_side_more": 0.32},
        "flexible": {"aa": 0.82, "flexible": 1.00, "one_side_more": 0.72},
        "one_side_more": {"aa": 0.32, "flexible": 0.72, "one_side_more": 1.00},
    },
    "diet": {
        "no_restriction": {"no_restriction": 1.00, "halal": 0.88, "vegetarian": 0.80},
        "halal": {"no_restriction": 0.88, "halal": 1.00, "vegetarian": 0.62},
        "vegetarian": {"no_restriction": 0.80, "halal": 0.62, "vegetarian": 1.00},
    },
    "studyspot": {
        "library": {"library": 1.00, "cafe": 0.75, "dorm": 0.52, "anywhere": 0.84},
        "cafe": {"library": 0.75, "cafe": 1.00, "dorm": 0.60, "anywhere": 0.82},
        "dorm": {"library": 0.52, "cafe": 0.60, "dorm": 1.00, "anywhere": 0.68},
        "anywhere": {"library": 0.84, "cafe": 0.82, "dorm": 0.68, "anywhere": 1.00},
    },
    "meet_freq": {
        "low": {"low": 1.00, "medium": 0.68, "high": 0.26},
        "medium": {"low": 0.68, "medium": 1.00, "high": 0.70},
        "high": {"low": 0.26, "medium": 0.70, "high": 1.00},
    },
}


@dataclass
class PrecisionMatchConfig:
    # Group weights — rebalanced per evidence hierarchy
    # Values/lifestyle elevated (Schwartz 2023, Dew & Britt 2012);
    # traits reduced (Joel et al. 2017: weak predictive power)
    preference_group_weight: float = 0.35
    value_group_weight: float = 0.25
    lifestyle_group_weight: float = 0.20
    traits_group_weight: float = 0.08
    interest_group_weight: float = 0.06
    context_group_weight: float = 0.06

    mutual_weight: float = 0.78
    chemistry_weight: float = 0.22

    chemistry_interest_weight: float = 0.45
    chemistry_traits_weight: float = 0.35
    chemistry_complement_weight: float = 0.20

    # Reduced: stated preferences overfit actual importance
    # (Eastwick & Finkel 2008)
    important_multiplier: float = 1.55
    double_important_bonus: float = 1.12
    trait_important_multiplier: float = 1.25

    candidate_threshold: float = 0.50
    reveal_threshold: float = 0.62

    asymmetry_penalty_weight: float = 0.05
    repeat_penalty: float = 0.08

    severe_conflict_threshold: float = 0.22
    moderate_conflict_threshold: float = 0.35
    soft_conflict_threshold: float = 0.48

    severe_conflict_cap: float = 0.42
    moderate_conflict_cap: float = 0.75
    soft_conflict_cap: float = 0.90

    important_conflict_drop: float = 0.08

    coverage_floor: float = 0.85
    coverage_power: float = 0.90

    mutual_rank_bonus_max: float = 0.07
    exclusivity_bonus_max: float = 0.06

    target_match_rate: float = 0.50

    strict_same_college_filter: bool = True
    strict_diet_filter: bool = False

    categorical_compatibility: Dict[str, Dict[str, Dict[str, float]]] = field(
        default_factory=lambda: DEFAULT_CATEGORICAL_COMPATIBILITY
    )
    diet_hard_conflicts: Set[Tuple[str, str]] = field(default_factory=set)


@dataclass
class Participant:
    user_id: str
    gender: Optional[str] = None
    sexuality: Optional[str] = None
    acceptable_partner_genders: Optional[Set[str]] = None

    grade: Optional[int] = None
    campus: Optional[str] = None
    college: Optional[str] = None
    hometown: Optional[str] = None

    height: Optional[float] = None
    height_pref_min: Optional[float] = None
    height_pref_max: Optional[float] = None

    cross_campus: bool = True
    accept_same_college: bool = True

    status_verified: bool = True
    status_completed: bool = True
    status_paused: bool = False
    status_opt_in: bool = True

    self_likert: Dict[str, int] = field(default_factory=dict)
    partner_pref: Dict[str, int] = field(default_factory=dict)
    categorical: Dict[str, str] = field(default_factory=dict)

    interests: Set[str] = field(default_factory=set)
    interest_overlap_pref: str = "similar"

    self_traits: Set[str] = field(default_factory=set)
    partner_traits: Set[str] = field(default_factory=set)
    partner_traits_important: bool = False
    important_dimensions: Set[str] = field(default_factory=set)

    blocked_user_ids: Set[str] = field(default_factory=set)
    historical_match_user_ids: Set[str] = field(default_factory=set)

    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, item: Dict[str, Any]) -> "Participant":
        hard = item.get("hardFilters", {})
        features = item.get("features", {})
        preferences = item.get("preferences", {})
        display = item.get("displayFeatures", {})
        history = item.get("history", {})
        status = item.get("status", hard.get("status", {}))

        acceptable_partner_genders = None
        if hard.get("acceptablePartnerGenders"):
            acceptable_partner_genders = normalize_token_set(hard.get("acceptablePartnerGenders", []))

        self_likert = {}
        for field_name in ALL_SELF_FIELDS:
            value = _get_feature_value(features, field_name)
            if value is not None:
                self_likert[field_name] = int(value)

        partner_pref = {}
        for field_name in DUAL_TRACK_FIELDS:
            value = _get_preference_value(preferences, features, field_name)
            if value is not None:
                partner_pref[field_name] = int(value)

        categorical_source = features.get("categorical", {})
        categorical = {}
        for field_name in CATEGORICAL_FIELDS:
            value = features.get(field_name)
            if value is None:
                value = categorical_source.get(field_name)
            if value is None:
                value = hard.get(field_name)
            if value is not None:
                categorical[field_name] = normalize_token(value)

        return cls(
            user_id=str(item.get("userId")),
            gender=normalize_token(hard.get("gender")),
            sexuality=normalize_token(hard.get("sexuality")),
            acceptable_partner_genders=acceptable_partner_genders,
            grade=_maybe_int(hard.get("grade")),
            campus=normalize_token(hard.get("campus")),
            college=normalize_token(hard.get("college")),
            hometown=normalize_token(hard.get("hometown")),
            height=_maybe_float(hard.get("height")),
            height_pref_min=_maybe_float(hard.get("heightPrefMin")),
            height_pref_max=_maybe_float(hard.get("heightPrefMax")),
            cross_campus=_boolish(hard.get("crossCampus"), default=True),
            accept_same_college=_boolish(hard.get("sameCollege"), default=True),
            status_verified=_boolish(status.get("verified"), default=True),
            status_completed=_boolish(status.get("completedQuestionnaire"), default=True),
            status_paused=_boolish(status.get("paused"), default=False),
            status_opt_in=_boolish(status.get("optIn"), default=True),
            self_likert=self_likert,
            partner_pref=partner_pref,
            categorical=categorical,
            interests=normalize_token_set(features.get("interests", display.get("interests", []))),
            interest_overlap_pref=normalize_token(
                preferences.get(
                    "interestOverlap",
                    features.get("interest_overlap", display.get("interestOverlap", "similar")),
                )
            )
            or "similar",
            self_traits=normalize_token_set(features.get("selfTraits", display.get("selfTraits", []))),
            partner_traits=normalize_token_set(preferences.get("partnerTraits", display.get("partnerTraits", []))),
            partner_traits_important=_boolish(preferences.get("partnerTraitsImportant"), default=False),
            important_dimensions=normalize_token_set(preferences.get("importantDimensions", [])),
            blocked_user_ids=set(map(str, history.get("blockedUserIds", []))),
            historical_match_user_ids=set(map(str, history.get("matchedUserIds", []))),
            raw=item,
        )


@dataclass
class GroupScore:
    score: Optional[float]
    coverage: float
    detail: Dict[str, Any]


@dataclass
class MatchEdge:
    user_a: str
    user_b: str
    base_score: float
    total_score: float
    match_weight: float
    breakdown: Dict[str, float]
    evidence: Dict[str, Any]
    penalties: Dict[str, float]
    market_context: Dict[str, Any] = field(default_factory=dict)


def _maybe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def _maybe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y", "accept", "allow"}:
        return True
    if lowered in {"0", "false", "no", "n", "reject", "deny"}:
        return False
    return default


def normalize_token(value: Any) -> Optional[str]:
    if value is None:
        return None
    token = str(value).strip().lower()
    if not token:
        return None
    aliases = {
        "straight": "heterosexual",
        "hetero": "heterosexual",
        "gay": "homosexual",
        "bi": "bisexual",
        "pan": "pansexual",
        "same": "similar",
        "similarity": "similar",
        "complement": "complementary",
        "flex": "flexible",
    }
    return aliases.get(token, token)


def normalize_token_set(values: Iterable[Any]) -> Set[str]:
    result: Set[str] = set()
    for value in values or []:
        token = normalize_token(value)
        if token:
            result.add(token)
    return result


def _get_feature_value(features: Dict[str, Any], field_name: str) -> Optional[int]:
    value = features.get(field_name)
    if isinstance(value, dict):
        if "self" in value:
            return value["self"]
        if "value" in value:
            return value["value"]
    if value is not None and not isinstance(value, dict):
        return value

    self_map = features.get("selfLikert", {})
    if field_name in self_map:
        return self_map[field_name]

    dual_self_map = features.get("dualSelf", {})
    if field_name in dual_self_map:
        return dual_self_map[field_name]

    return None


def _get_preference_value(
    preferences: Dict[str, Any],
    features: Dict[str, Any],
    field_name: str,
) -> Optional[int]:
    value = preferences.get(field_name)
    if isinstance(value, dict):
        if "partner" in value:
            return value["partner"]
        if "value" in value:
            return value["value"]

    partner_map = preferences.get("partnerPref", {})
    if field_name in partner_map:
        return partner_map[field_name]

    feature_value = features.get(field_name)
    if isinstance(feature_value, dict) and "partner" in feature_value:
        return feature_value["partner"]

    return None


def is_active_for_cycle(p: Participant) -> bool:
    return p.status_verified and p.status_completed and (not p.status_paused) and p.status_opt_in


def infer_acceptable_partner_genders(p: Participant) -> Optional[Set[str]]:
    if p.acceptable_partner_genders:
        return p.acceptable_partner_genders

    sexuality = normalize_token(p.sexuality)
    gender = normalize_token(p.gender)

    if sexuality in {"bisexual", "pansexual"}:
        return None
    if sexuality == "heterosexual" and gender is not None:
        if gender == "male":
            return {"female"}
        if gender == "female":
            return {"male"}
    if sexuality == "homosexual" and gender is not None:
        return {gender}
    return None


def gender_compatible(a: Participant, b: Participant) -> bool:
    a_target = infer_acceptable_partner_genders(a)
    b_target = infer_acceptable_partner_genders(b)

    if a_target is not None and normalize_token(b.gender) not in a_target:
        return False
    if b_target is not None and normalize_token(a.gender) not in b_target:
        return False
    return True


def height_compatible(a: Participant, b: Participant) -> bool:
    if a.height is not None:
        if b.height_pref_min is not None and a.height < b.height_pref_min:
            return False
        if b.height_pref_max is not None and a.height > b.height_pref_max:
            return False
    if b.height is not None:
        if a.height_pref_min is not None and b.height < a.height_pref_min:
            return False
        if a.height_pref_max is not None and b.height > a.height_pref_max:
            return False
    return True


def campus_compatible(a: Participant, b: Participant) -> bool:
    if a.campus and b.campus and a.campus != b.campus:
        if not a.cross_campus or not b.cross_campus:
            return False
    return True


def same_college_compatible(a: Participant, b: Participant, config: PrecisionMatchConfig) -> bool:
    if not config.strict_same_college_filter:
        return True
    if a.college and b.college and a.college == b.college:
        if not a.accept_same_college or not b.accept_same_college:
            return False
    return True


def diet_compatible(a: Participant, b: Participant, config: PrecisionMatchConfig) -> bool:
    if not config.strict_diet_filter:
        return True
    da = a.categorical.get("diet")
    db = b.categorical.get("diet")
    if not da or not db:
        return True
    return ((da, db) not in config.diet_hard_conflicts) and ((db, da) not in config.diet_hard_conflicts)


def hard_filter_pair(a: Participant, b: Participant, config: PrecisionMatchConfig) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    if not is_active_for_cycle(a):
        reasons.append("user_a_inactive")
    if not is_active_for_cycle(b):
        reasons.append("user_b_inactive")
    if reasons:
        return False, reasons

    if b.user_id in a.blocked_user_ids or a.user_id in b.blocked_user_ids:
        reasons.append("blocked")
    if not gender_compatible(a, b):
        reasons.append("gender_or_sexuality_incompatible")
    if not height_compatible(a, b):
        reasons.append("height_preference_incompatible")
    if not campus_compatible(a, b):
        reasons.append("cross_campus_incompatible")
    if not same_college_compatible(a, b, config):
        reasons.append("same_college_incompatible")
    if not diet_compatible(a, b, config):
        reasons.append("diet_incompatible")

    return len(reasons) == 0, reasons


def shaped_similarity(a_value: Optional[int], b_value: Optional[int], sensitivity: float = 1.0) -> Optional[float]:
    if a_value is None or b_value is None:
        return None
    distance = abs(float(a_value) - float(b_value)) / 6.0
    return max(0.0, 1.0 - (distance ** sensitivity))


def bell_similarity(diff: float, ideal: float, width: float, floor: float = 0.0) -> float:
    score = max(0.0, 1.0 - abs(diff - ideal) / width)
    return max(floor, min(1.0, score))


def harmonic_mean(a: float, b: float, eps: float = 1e-9) -> float:
    return 2.0 * a * b / (a + b + eps)


def safe_jaccard(a_items: Set[str], b_items: Set[str]) -> float:
    union = a_items | b_items
    if not union:
        return 0.55
    return len(a_items & b_items) / len(union)


def coverage_score(need_items: Set[str], have_items: Set[str]) -> float:
    if not need_items:
        return 0.58
    return len(need_items & have_items) / len(need_items)


def categorical_pair_score(
    field_name: str,
    a_value: Optional[str],
    b_value: Optional[str],
    config: PrecisionMatchConfig,
) -> Optional[float]:
    if a_value is None and b_value is None:
        return None
    if a_value is None or b_value is None:
        return 0.56
    matrix = config.categorical_compatibility.get(field_name, {})
    if a_value in matrix and b_value in matrix[a_value]:
        return matrix[a_value][b_value]
    if b_value in matrix and a_value in matrix[b_value]:
        return matrix[b_value][a_value]
    if a_value == b_value:
        return 1.00
    return 0.58


def _owner_importance_multiplier(owner: Participant, other: Participant, dim: str, config: PrecisionMatchConfig) -> float:
    weight = 1.0
    if dim in owner.important_dimensions:
        weight *= config.important_multiplier
    if (dim in owner.important_dimensions) and (dim in other.important_dimensions):
        weight *= config.double_important_bonus
    return weight


def _group_weighted_average(items: List[Tuple[Optional[float], float]], total_possible_weight: float) -> GroupScore:
    numerator = 0.0
    answered_weight = 0.0
    detail: Dict[str, Any] = {}
    for score, weight in items:
        if score is None or weight <= 0:
            continue
        numerator += score * weight
        answered_weight += weight
    coverage = (answered_weight / total_possible_weight) if total_possible_weight > 0 else 1.0
    if answered_weight == 0:
        return GroupScore(score=None, coverage=coverage, detail=detail)
    return GroupScore(score=numerator / answered_weight, coverage=coverage, detail=detail)


def directional_preference_fit(owner: Participant, other: Participant, config: PrecisionMatchConfig) -> GroupScore:
    items: List[Tuple[Optional[float], float]] = []
    per_dim: Dict[str, float] = {}
    total_possible_weight = 0.0

    for dim, dim_weight in PREFERENCE_DIM_WEIGHTS.items():
        base_weight = dim_weight * _owner_importance_multiplier(owner, other, dim, config)
        total_possible_weight += base_weight
        sensitivity = SENSITIVITY_BY_DIM.get(dim, 1.0)
        score = shaped_similarity(owner.partner_pref.get(dim), other.self_likert.get(dim), sensitivity=sensitivity)
        if score is not None:
            per_dim[dim] = score
        items.append((score, base_weight))

    group = _group_weighted_average(items, total_possible_weight)
    group.detail = {
        "per_dim": per_dim,
        "answered": sorted(per_dim.keys()),
        "group": "preference_fit",
    }
    return group


def directional_value_alignment(owner: Participant, other: Participant, config: PrecisionMatchConfig) -> GroupScore:
    items: List[Tuple[Optional[float], float]] = []
    per_dim: Dict[str, float] = {}
    total_possible_weight = 0.0

    for dim, dim_weight in {**CRITICAL_ALIGNMENT_WEIGHTS, **WORLDVIEW_ALIGNMENT_WEIGHTS}.items():
        base_weight = dim_weight * _owner_importance_multiplier(owner, other, dim, config)
        total_possible_weight += base_weight
        sensitivity = SENSITIVITY_BY_DIM.get(dim, 0.95)
        score = shaped_similarity(owner.self_likert.get(dim), other.self_likert.get(dim), sensitivity=sensitivity)
        if score is not None:
            per_dim[dim] = score
        items.append((score, base_weight))

    group = _group_weighted_average(items, total_possible_weight)
    group.detail = {
        "per_dim": per_dim,
        "answered": sorted(per_dim.keys()),
        "group": "value_alignment",
    }
    return group


def directional_lifestyle_fit(owner: Participant, other: Participant, config: PrecisionMatchConfig) -> GroupScore:
    items: List[Tuple[Optional[float], float]] = []
    per_dim: Dict[str, float] = {}
    total_possible_weight = 0.0

    for dim, dim_weight in LIFESTYLE_LIKERT_WEIGHTS.items():
        base_weight = dim_weight * _owner_importance_multiplier(owner, other, dim, config)
        total_possible_weight += base_weight
        sensitivity = SENSITIVITY_BY_DIM.get(dim, 1.05)
        score = shaped_similarity(owner.self_likert.get(dim), other.self_likert.get(dim), sensitivity=sensitivity)
        if score is not None:
            per_dim[dim] = score
        items.append((score, base_weight))

    for dim in CATEGORICAL_FIELDS:
        dim_weight = 0.85 if dim in {"diet", "meet_freq"} else 0.70
        base_weight = dim_weight * _owner_importance_multiplier(owner, other, dim, config)
        total_possible_weight += base_weight
        score = categorical_pair_score(dim, owner.categorical.get(dim), other.categorical.get(dim), config)
        if score is not None:
            per_dim[dim] = score
        items.append((score, base_weight))

    group = _group_weighted_average(items, total_possible_weight)
    group.detail = {
        "per_dim": per_dim,
        "answered": sorted(per_dim.keys()),
        "group": "lifestyle_fit",
    }
    return group


def directional_trait_fit(owner: Participant, other: Participant, config: PrecisionMatchConfig) -> GroupScore:
    base_weight = config.trait_important_multiplier if owner.partner_traits_important else 1.0
    total_possible_weight = 1.0 * base_weight

    pref_fit = coverage_score(owner.partner_traits, other.self_traits)
    overlap = safe_jaccard(owner.self_traits, other.self_traits)
    combined = 0.80 * pref_fit + 0.20 * overlap

    coverage = 1.0
    if not owner.partner_traits and not owner.self_traits:
        coverage = 0.0
        combined = None

    detail = {
        "pref_fit": pref_fit,
        "self_overlap": overlap,
        "wanted_traits_hit": sorted(owner.partner_traits & other.self_traits),
        "shared_traits": sorted(owner.self_traits & other.self_traits),
        "group": "trait_fit",
    }
    if combined is None:
        return GroupScore(score=None, coverage=coverage, detail=detail)
    return GroupScore(score=combined, coverage=coverage, detail=detail)


def directional_interest_fit(owner: Participant, other: Participant) -> GroupScore:
    if not owner.interests and not other.interests:
        return GroupScore(score=None, coverage=0.0, detail={"group": "interest_fit"})

    jaccard = safe_jaccard(owner.interests, other.interests)
    pref = normalize_token(owner.interest_overlap_pref) or "similar"

    if pref == "similar":
        score = 0.15 + 0.85 * jaccard
    elif pref == "complementary":
        score = 0.55 + 0.45 * bell_similarity(jaccard, ideal=0.35, width=0.35, floor=0.0)
    else:
        score = 0.40 + 0.60 * jaccard

    detail = {
        "jaccard": jaccard,
        "preference": pref,
        "shared": sorted(owner.interests & other.interests),
        "only_owner": sorted(owner.interests - other.interests),
        "only_other": sorted(other.interests - owner.interests),
        "group": "interest_fit",
    }
    return GroupScore(score=score, coverage=1.0, detail=detail)


def directional_context_fit(owner: Participant, other: Participant) -> GroupScore:
    score = 0.52
    detail: Dict[str, Any] = {"group": "context_fit", "signals": {}}

    if owner.campus and other.campus and owner.campus == other.campus:
        score += 0.16
        detail["signals"]["same_campus"] = True
    if owner.grade is not None and other.grade is not None:
        gap = abs(owner.grade - other.grade)
        if gap <= 1:
            score += 0.12
            detail["signals"]["grade_gap"] = gap
        elif gap == 2:
            score += 0.06
            detail["signals"]["grade_gap"] = gap
    if owner.hometown and other.hometown and owner.hometown == other.hometown:
        score += 0.08
        detail["signals"]["same_hometown"] = True
    if owner.college and other.college and owner.college == other.college:
        score += 0.04
        detail["signals"]["same_college"] = True

    return GroupScore(score=min(score, 1.0), coverage=1.0, detail=detail)


def compute_directional_utility(owner: Participant, other: Participant, config: PrecisionMatchConfig) -> Dict[str, Any]:
    pref = directional_preference_fit(owner, other, config)
    value = directional_value_alignment(owner, other, config)
    lifestyle = directional_lifestyle_fit(owner, other, config)
    traits = directional_trait_fit(owner, other, config)
    interests = directional_interest_fit(owner, other)
    context = directional_context_fit(owner, other)

    group_weights = {
        "preference_fit": config.preference_group_weight,
        "value_alignment": config.value_group_weight,
        "lifestyle_fit": config.lifestyle_group_weight,
        "trait_fit": config.traits_group_weight * (config.trait_important_multiplier if owner.partner_traits_important else 1.0),
        "interest_fit": config.interest_group_weight,
        "context_fit": config.context_group_weight,
    }

    groups = {
        "preference_fit": pref,
        "value_alignment": value,
        "lifestyle_fit": lifestyle,
        "trait_fit": traits,
        "interest_fit": interests,
        "context_fit": context,
    }

    numerator = 0.0
    answered_weight = 0.0
    possible_weight = sum(group_weights.values())

    for group_name, group in groups.items():
        group_weight = group_weights[group_name]
        if group.score is not None:
            numerator += group.score * group_weight
            answered_weight += group_weight
        # coverage is tracked separately so missing data still reduces confidence

    coverage_numerator = 0.0
    for group_name, group in groups.items():
        coverage_numerator += group_weights[group_name] * group.coverage
    coverage = coverage_numerator / possible_weight if possible_weight else 1.0

    utility = numerator / answered_weight if answered_weight else 0.0

    return {
        "score": utility,
        "coverage": coverage,
        "groups": {
            "preference_fit": pref,
            "value_alignment": value,
            "lifestyle_fit": lifestyle,
            "trait_fit": traits,
            "interest_fit": interests,
            "context_fit": context,
        },
    }


def compute_chemistry(a: Participant, b: Participant, config: PrecisionMatchConfig) -> Dict[str, Any]:
    interest_jaccard = safe_jaccard(a.interests, b.interests)
    shared_trait_jaccard = safe_jaccard(a.self_traits, b.self_traits)

    shared_self_scores: List[Tuple[float, float]] = []
    for dim, dim_weight in CHEMISTRY_SHARED_WEIGHTS.items():
        score = shaped_similarity(a.self_likert.get(dim), b.self_likert.get(dim), sensitivity=1.15)
        if score is not None:
            shared_self_scores.append((score, dim_weight))

    shared_self_score = (
        sum(score * weight for score, weight in shared_self_scores) / sum(weight for _, weight in shared_self_scores)
        if shared_self_scores
        else 0.58
    )

    complement_scores: List[Tuple[float, float]] = []
    complement_detail: Dict[str, float] = {}
    for dim, dim_weight in SAFE_COMPLEMENT_FIELDS.items():
        av = a.self_likert.get(dim)
        bv = b.self_likert.get(dim)
        if av is None or bv is None:
            continue
        diff = abs(av - bv)
        score = bell_similarity(diff, ideal=2.0, width=2.2, floor=0.35)
        complement_scores.append((score, dim_weight))
        complement_detail[dim] = score

    complement_score = (
        sum(score * weight for score, weight in complement_scores) / sum(weight for _, weight in complement_scores)
        if complement_scores
        else 0.55
    )

    interests_component = 0.55 + 0.45 * interest_jaccard
    traits_component = 0.45 + 0.55 * shared_trait_jaccard
    shared_self_component = shared_self_score

    chemistry = (
        config.chemistry_interest_weight * interests_component
        + config.chemistry_traits_weight * ((traits_component + shared_self_component) / 2.0)
        + config.chemistry_complement_weight * complement_score
    )

    return {
        "score": chemistry,
        "shared_interest_jaccard": interest_jaccard,
        "shared_trait_jaccard": shared_trait_jaccard,
        "shared_self_score": shared_self_score,
        "safe_complement_score": complement_score,
        "complement_detail": complement_detail,
    }


def _cap_after_conflict(base_cap: float, config: PrecisionMatchConfig, severity: str, important: bool = False) -> float:
    if severity == "severe":
        cap = config.severe_conflict_cap
    elif severity == "moderate":
        cap = config.moderate_conflict_cap
    else:
        cap = config.soft_conflict_cap
    if important:
        cap = max(0.20, cap - config.important_conflict_drop)
    return min(base_cap, cap)


def compute_conflict_profile(a: Participant, b: Participant, config: PrecisionMatchConfig) -> Dict[str, Any]:
    cap = 1.0
    flags: List[Dict[str, Any]] = []

    for dim, dim_weight in CRITICAL_ALIGNMENT_WEIGHTS.items():
        score = shaped_similarity(a.self_likert.get(dim), b.self_likert.get(dim), sensitivity=SENSITIVITY_BY_DIM.get(dim, 0.8))
        if score is None:
            continue
        important = (dim in a.important_dimensions) or (dim in b.important_dimensions)
        severity = None
        if score <= config.severe_conflict_threshold:
            severity = "severe"
        elif score <= config.moderate_conflict_threshold:
            severity = "moderate"
        elif score <= config.soft_conflict_threshold:
            severity = "soft"

        if severity:
            cap = _cap_after_conflict(cap, config, severity, important=important)
            flags.append(
                {
                    "type": "critical_value_conflict",
                    "field": dim,
                    "label": FIELD_LABELS.get(dim, dim),
                    "score": round(score, 4),
                    "severity": severity,
                    "important": important,
                    "a_value": a.self_likert.get(dim),
                    "b_value": b.self_likert.get(dim),
                }
            )

    for owner, other, direction in ((a, b, "a_pref_to_b"), (b, a, "b_pref_to_a")):
        for dim in ("smoke", "drink", "appearance", "hustle"):
            pref = owner.partner_pref.get(dim)
            actual = other.self_likert.get(dim)
            if pref is None or actual is None:
                continue
            score = shaped_similarity(pref, actual, sensitivity=SENSITIVITY_BY_DIM.get(dim, 0.9))
            if score is None:
                continue
            important = dim in owner.important_dimensions
            severity = None
            if score <= config.severe_conflict_threshold and (important or dim in {"smoke", "drink"}):
                severity = "severe"
            elif score <= config.moderate_conflict_threshold and (important or dim in {"smoke", "drink"}):
                severity = "moderate"
            elif score <= config.soft_conflict_threshold and important:
                severity = "soft"
            if severity:
                cap = _cap_after_conflict(cap, config, severity, important=important)
                flags.append(
                    {
                        "type": "preference_conflict",
                        "field": dim,
                        "label": FIELD_LABELS.get(dim, dim),
                        "score": round(score, 4),
                        "severity": severity,
                        "important": important,
                        "direction": direction,
                        "wanted": pref,
                        "actual": actual,
                    }
                )

    for dim in ("diet", "meet_freq", "spending"):
        cat_score = categorical_pair_score(dim, a.categorical.get(dim), b.categorical.get(dim), config)
        if cat_score is None:
            continue
        if cat_score <= 0.35:
            cap = _cap_after_conflict(cap, config, "soft", important=False)
            flags.append(
                {
                    "type": "categorical_friction",
                    "field": dim,
                    "label": FIELD_LABELS.get(dim, dim),
                    "score": round(cat_score, 4),
                    "severity": "soft",
                    "a_value": a.categorical.get(dim),
                    "b_value": b.categorical.get(dim),
                }
            )

    # Composite: anxious-avoidant attachment mismatch detection
    # Pursue-withdraw dynamics are among the strongest dissolution predictors
    # (Candel & Turliuc 2019; Li & Chan 2012 TARA model)
    _ANX_DIMS = ("reply_anxiety", "together")
    _AVO_DIMS = ("intimacy_pace",)       # high = needs long trust-building
    _AVO_INV = ("depend_comfort",)       # low = hard to depend on partner

    for p_anx, p_avo, tag in ((a, b, "A_anx_B_avo"), (b, a, "B_anx_A_avo")):
        anx_vals = [p_anx.self_likert[d] for d in _ANX_DIMS if d in p_anx.self_likert]
        avo_vals = [p_avo.self_likert[d] for d in _AVO_DIMS if d in p_avo.self_likert]
        avo_vals += [8 - p_avo.self_likert[d] for d in _AVO_INV if d in p_avo.self_likert]
        if anx_vals and avo_vals:
            anx_m = sum(anx_vals) / len(anx_vals) / 7.0
            avo_m = sum(avo_vals) / len(avo_vals) / 7.0
            if anx_m >= 0.65 and avo_m >= 0.65:
                sev = "moderate" if (anx_m >= 0.78 and avo_m >= 0.78) else "soft"
                cap = _cap_after_conflict(cap, config, sev)
                flags.append({
                    "type": "attachment_mismatch",
                    "field": "attachment",
                    "label": "依恋模式冲突",
                    "score": round(1.0 - anx_m * avo_m, 4),
                    "severity": sev,
                    "detail": tag,
                })

    return {
        "cap": cap,
        "risk_flags": flags[:8],
    }


def compute_confidence(a_to_b: Dict[str, Any], b_to_a: Dict[str, Any], config: PrecisionMatchConfig) -> float:
    coverage = (a_to_b["coverage"] + b_to_a["coverage"]) / 2.0
    confidence = config.coverage_floor + (1.0 - config.coverage_floor) * (coverage ** config.coverage_power)
    return min(1.0, max(config.coverage_floor, confidence))


def compute_penalties(a: Participant, b: Participant, config: PrecisionMatchConfig) -> Dict[str, float]:
    penalties: Dict[str, float] = {}
    if (b.user_id in a.historical_match_user_ids) or (a.user_id in b.historical_match_user_ids):
        penalties["repeat_penalty"] = config.repeat_penalty
    return penalties


def build_evidence(
    a: Participant,
    b: Participant,
    a_to_b: Dict[str, Any],
    b_to_a: Dict[str, Any],
    chemistry: Dict[str, Any],
    conflict: Dict[str, Any],
) -> Dict[str, Any]:
    shared_points: List[Dict[str, Any]] = []
    complementary_points: List[Dict[str, Any]] = []

    def add_positive_points(owner_prefix: str, directional: Dict[str, Any]) -> None:
        pref_scores = directional["groups"]["preference_fit"].detail.get("per_dim", {})
        value_scores = directional["groups"]["value_alignment"].detail.get("per_dim", {})
        lifestyle_scores = directional["groups"]["lifestyle_fit"].detail.get("per_dim", {})
        for dim, score in sorted(pref_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 0.84:
                shared_points.append(
                    {
                        "type": "preference_hit",
                        "from": owner_prefix,
                        "field": dim,
                        "label": FIELD_LABELS.get(dim, dim),
                        "score": round(score, 4),
                    }
                )
        for dim, score in sorted(value_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 0.86:
                shared_points.append(
                    {
                        "type": "value_alignment",
                        "from": owner_prefix,
                        "field": dim,
                        "label": FIELD_LABELS.get(dim, dim),
                        "score": round(score, 4),
                    }
                )
        for dim, score in sorted(lifestyle_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 0.84 and dim in {"sleep", "tidy", "diet", "meet_freq", "spending"}:
                shared_points.append(
                    {
                        "type": "lifestyle_alignment",
                        "from": owner_prefix,
                        "field": dim,
                        "label": FIELD_LABELS.get(dim, dim),
                        "score": round(score, 4),
                    }
                )

    add_positive_points("A", a_to_b)
    add_positive_points("B", b_to_a)

    shared_interest_items = sorted(a.interests & b.interests)
    if shared_interest_items:
        shared_points.append(
            {
                "type": "shared_interests",
                "field": "interests",
                "label": FIELD_LABELS.get("interests", "interests"),
                "score": round(chemistry["shared_interest_jaccard"], 4),
                "items": shared_interest_items[:5],
            }
        )

    shared_trait_items = sorted(a.self_traits & b.self_traits)
    if shared_trait_items:
        shared_points.append(
            {
                "type": "shared_traits",
                "field": "traits",
                "label": FIELD_LABELS.get("traits", "traits"),
                "score": round(chemistry["shared_trait_jaccard"], 4),
                "items": shared_trait_items[:5],
            }
        )

    a_wanted_hit = sorted(a.partner_traits & b.self_traits)
    b_wanted_hit = sorted(b.partner_traits & a.self_traits)
    if a_wanted_hit:
        shared_points.append(
            {
                "type": "partner_trait_hit",
                "field": "traits",
                "label": "你期望的特质对方都有",
                "score": round(a_to_b["groups"]["trait_fit"].detail.get("pref_fit", 0.0), 4),
                "items": a_wanted_hit[:5],
            }
        )
    if b_wanted_hit:
        shared_points.append(
            {
                "type": "partner_trait_hit",
                "field": "traits",
                "label": "对方期望的特质你都有",
                "score": round(b_to_a["groups"]["trait_fit"].detail.get("pref_fit", 0.0), 4),
                "items": b_wanted_hit[:5],
            }
        )

    for dim, score in chemistry["complement_detail"].items():
        av = a.self_likert.get(dim)
        bv = b.self_likert.get(dim)
        if av is None or bv is None:
            continue
        if score >= 0.72 and abs(av - bv) >= 1:
            complementary_points.append(
                {
                    "type": "safe_complement",
                    "field": dim,
                    "label": FIELD_LABELS.get(dim, dim),
                    "score": round(score, 4),
                    "a_value": av,
                    "b_value": bv,
                }
            )

    shared_points = sorted(shared_points, key=lambda x: x.get("score", 0.0), reverse=True)
    complementary_points = sorted(complementary_points, key=lambda x: x.get("score", 0.0), reverse=True)

    return {
        "shared_points": shared_points[:8],
        "complementary_points": complementary_points[:5],
        "risk_flags": conflict["risk_flags"][:5],
        "directional_reasons": {
            "forA": top_directional_reasons(a_to_b),
            "forB": top_directional_reasons(b_to_a),
        },
        "chemistry_detail": chemistry,
    }


def top_directional_reasons(directional: Dict[str, Any], top_n: int = 4) -> List[Dict[str, Any]]:
    reasons: List[Dict[str, Any]] = []
    for group_name in ("preference_fit", "value_alignment", "lifestyle_fit"):
        per_dim = directional["groups"][group_name].detail.get("per_dim", {})
        for dim, score in per_dim.items():
            reasons.append(
                {
                    "group": group_name,
                    "field": dim,
                    "label": FIELD_LABELS.get(dim, dim),
                    "score": round(score, 4),
                }
            )
    reasons.sort(key=lambda x: x["score"], reverse=True)
    return reasons[:top_n]


def rescale_display_score(raw: float) -> float:
    """Nonlinear score calibration (Finkel et al. 2012).

    Pairs passing hard filters already have baseline compatibility.
    Power curve boosts mid-range scores to reflect this, preserving ordering.
    0.60 raw → 0.65 display, 0.70 → 0.74, 0.80 → 0.82.
    """
    if raw <= 0.0:
        return 0.0
    return min(1.0, raw ** 0.82)


def score_pair(a: Participant, b: Participant, config: PrecisionMatchConfig) -> Optional[MatchEdge]:
    passed, hard_filter_reasons = hard_filter_pair(a, b, config)
    if not passed:
        return None

    a_to_b = compute_directional_utility(a, b, config)
    b_to_a = compute_directional_utility(b, a, config)
    chemistry = compute_chemistry(a, b, config)
    conflict = compute_conflict_profile(a, b, config)
    confidence = compute_confidence(a_to_b, b_to_a, config)
    penalties = compute_penalties(a, b, config)

    mutual = harmonic_mean(a_to_b["score"], b_to_a["score"])
    asymmetry_penalty = config.asymmetry_penalty_weight * abs(a_to_b["score"] - b_to_a["score"])

    raw_score = config.mutual_weight * mutual + config.chemistry_weight * chemistry["score"]
    raw_score = max(0.0, raw_score - asymmetry_penalty)
    base_score = raw_score * conflict["cap"] * confidence
    total_score = rescale_display_score(max(0.0, min(1.0, base_score - sum(penalties.values()))))

    evidence = build_evidence(
        a=a,
        b=b,
        a_to_b=a_to_b,
        b_to_a=b_to_a,
        chemistry=chemistry,
        conflict=conflict,
    )
    evidence["hard_filter_reasons"] = hard_filter_reasons
    evidence["mutual_profile"] = {
        "a_to_b": round(a_to_b["score"], 6),
        "b_to_a": round(b_to_a["score"], 6),
        "mutual_harmonic_mean": round(mutual, 6),
        "a_coverage": round(a_to_b["coverage"], 6),
        "b_coverage": round(b_to_a["coverage"], 6),
        "confidence": round(confidence, 6),
        "conflict_cap": round(conflict["cap"], 6),
    }

    # Per-group averaged scores (harmonic mean of both directions) for frontend display
    group_names = ("preference_fit", "value_alignment", "lifestyle_fit", "trait_fit", "interest_fit")
    per_group: Dict[str, float] = {}
    for gn in group_names:
        sa = a_to_b["groups"][gn].score
        sb = b_to_a["groups"][gn].score
        if sa is not None and sb is not None:
            per_group[gn] = round(harmonic_mean(sa, sb), 6)
        elif sa is not None:
            per_group[gn] = round(sa, 6)
        elif sb is not None:
            per_group[gn] = round(sb, 6)

    breakdown = {
        "directional_a_to_b": round(a_to_b["score"], 6),
        "directional_b_to_a": round(b_to_a["score"], 6),
        "mutual_harmonic": round(mutual, 6),
        "chemistry": round(chemistry["score"], 6),
        "conflict_cap": round(conflict["cap"], 6),
        "confidence": round(confidence, 6),
        "asymmetry_penalty": round(asymmetry_penalty, 6),
        "repeat_penalty": round(penalties.get("repeat_penalty", 0.0), 6),
        "base_score": round(base_score, 6),
        "rank_bonus": 0.0,
        "exclusivity_bonus": 0.0,
        "preference_fit": per_group.get("preference_fit", 0.0),
        "value_alignment": per_group.get("value_alignment", 0.0),
        "lifestyle_fit": per_group.get("lifestyle_fit", 0.0),
        "trait_fit": per_group.get("trait_fit", 0.0),
        "interest_fit": per_group.get("interest_fit", 0.0),
    }

    return MatchEdge(
        user_a=a.user_id,
        user_b=b.user_id,
        base_score=round(base_score, 6),
        total_score=round(total_score, 6),
        match_weight=0.0,
        breakdown=breakdown,
        evidence=evidence,
        penalties=penalties,
    )


def build_candidate_edges(participants: Sequence[Participant], config: PrecisionMatchConfig) -> List[MatchEdge]:
    edges: List[MatchEdge] = []
    for a, b in combinations(participants, 2):
        edge = score_pair(a, b, config)
        if edge is None:
            continue
        if edge.total_score >= config.candidate_threshold:
            edges.append(edge)
    return edges


def _rank_score(rank: int) -> float:
    if rank == 1:
        return 1.00
    if rank == 2:
        return 0.70
    if rank == 3:
        return 0.45
    if rank <= 5:
        return 0.20
    return 0.0


def apply_market_recalibration(edges: Sequence[MatchEdge], config: PrecisionMatchConfig) -> None:
    if not edges:
        return

    by_user: Dict[str, List[Tuple[str, float]]] = {}
    for edge in edges:
        by_user.setdefault(edge.user_a, []).append((edge.user_b, edge.base_score))
        by_user.setdefault(edge.user_b, []).append((edge.user_a, edge.base_score))

    sorted_scores: Dict[str, List[Tuple[str, float]]] = {
        user: sorted(items, key=lambda x: x[1], reverse=True) for user, items in by_user.items()
    }
    rank_map: Dict[Tuple[str, str], int] = {}
    score_gap_map: Dict[str, float] = {}
    for user, items in sorted_scores.items():
        for idx, (other, _) in enumerate(items, start=1):
            rank_map[(user, other)] = idx
        if len(items) == 1:
            score_gap_map[user] = max(0.0, items[0][1] - config.candidate_threshold)
        else:
            score_gap_map[user] = max(0.0, items[0][1] - items[1][1])

    for edge in edges:
        rank_a = rank_map.get((edge.user_a, edge.user_b), 99)
        rank_b = rank_map.get((edge.user_b, edge.user_a), 99)
        quality_factor = max(
            0.0,
            min(1.0, (edge.base_score - config.candidate_threshold) / max(1e-9, 1.0 - config.candidate_threshold)),
        )

        rank_bonus = config.mutual_rank_bonus_max * ((_rank_score(rank_a) + _rank_score(rank_b)) / 2.0) * quality_factor

        uniqueness_a = min(1.0, score_gap_map.get(edge.user_a, 0.0) / 0.12) if rank_a == 1 else 0.0
        uniqueness_b = min(1.0, score_gap_map.get(edge.user_b, 0.0) / 0.12) if rank_b == 1 else 0.0
        exclusivity_bonus = config.exclusivity_bonus_max * ((uniqueness_a + uniqueness_b) / 2.0) * quality_factor

        edge.market_context = {
            "rankA": rank_a,
            "rankB": rank_b,
            "rankBonus": round(rank_bonus, 6),
            "exclusivityBonus": round(exclusivity_bonus, 6),
            "qualityFactor": round(quality_factor, 6),
            "topGapA": round(score_gap_map.get(edge.user_a, 0.0), 6),
            "topGapB": round(score_gap_map.get(edge.user_b, 0.0), 6),
        }

        edge.breakdown["rank_bonus"] = round(rank_bonus, 6)
        edge.breakdown["exclusivity_bonus"] = round(exclusivity_bonus, 6)

        edge.total_score = round(min(1.0, edge.total_score + rank_bonus + exclusivity_bonus), 6)
        edge.match_weight = round(max(0.0, edge.total_score - config.reveal_threshold + 0.01) ** 2 * 1000.0 + edge.total_score, 6)


def maximum_weight_matching(edges: Sequence[MatchEdge], participants: Sequence[Participant]) -> List[Tuple[str, str]]:
    if not edges:
        return []

    if nx is None:
        return greedy_matching(edges)

    graph = nx.Graph()
    graph.add_nodes_from([p.user_id for p in participants])

    for edge in edges:
        w = edge.match_weight
        graph.add_edge(edge.user_a, edge.user_b, weight=w)

    matching = nx.algorithms.matching.max_weight_matching(
        graph,
        maxcardinality=False,
        weight="weight",
    )

    result = []
    for a, b in matching:
        result.append(tuple(sorted((str(a), str(b)))))
    result.sort()
    return result


def greedy_matching(edges: Sequence[MatchEdge]) -> List[Tuple[str, str]]:
    used: Set[str] = set()
    chosen: List[Tuple[str, str]] = []
    for edge in sorted(edges, key=lambda e: e.match_weight, reverse=True):
        if edge.user_a in used or edge.user_b in used:
            continue
        used.add(edge.user_a)
        used.add(edge.user_b)
        chosen.append(tuple(sorted((edge.user_a, edge.user_b))))
    return chosen


def index_edges(edges: Sequence[MatchEdge]) -> Dict[Tuple[str, str], MatchEdge]:
    lookup: Dict[Tuple[str, str], MatchEdge] = {}
    for edge in edges:
        key = tuple(sorted((edge.user_a, edge.user_b)))
        lookup[key] = edge
    return lookup


def solve_weekly_matches(
    payload: Dict[str, Any],
    config: Optional[PrecisionMatchConfig] = None,
) -> Dict[str, Any]:
    config = config or PrecisionMatchConfig()
    participants = [Participant.from_payload(x) for x in payload.get("participants", [])]
    active_participants = [p for p in participants if is_active_for_cycle(p)]

    candidate_edges = build_candidate_edges(active_participants, config)
    apply_market_recalibration(candidate_edges, config)

    matched_pairs = maximum_weight_matching(candidate_edges, active_participants)
    edge_lookup = index_edges(candidate_edges)

    matched_users: Set[str] = set()
    matches: List[Dict[str, Any]] = []

    for user_a, user_b in matched_pairs:
        edge = edge_lookup[(user_a, user_b)]
        if edge.total_score < config.reveal_threshold:
            continue

        matched_users.add(user_a)
        matched_users.add(user_b)
        matches.append(
            {
                "userA": user_a,
                "userB": user_b,
                "scoreTotal": edge.total_score,
                "scoreBreakdown": edge.breakdown,
                "marketContext": edge.market_context,
                "evidence": edge.evidence,
                "reportPayload": {
                    "shared_points": edge.evidence["shared_points"],
                    "complementary_points": edge.evidence["complementary_points"],
                    "risk_flags": edge.evidence["risk_flags"],
                    "directional_reasons": edge.evidence["directional_reasons"],
                    "mutual_profile": edge.evidence["mutual_profile"],
                    "chemistry_detail": edge.evidence["chemistry_detail"],
                },
            }
        )

    # Dynamic match rate control — cap at target_match_rate
    if config.target_match_rate < 1.0:
        max_matched_users = max(2, round(len(active_participants) * config.target_match_rate))
        target_pairs = max(1, max_matched_users // 2)
        if len(matches) > target_pairs:
            matches.sort(key=lambda m: m["scoreTotal"], reverse=True)
            for excess in matches[target_pairs:]:
                matched_users.discard(excess["userA"])
                matched_users.discard(excess["userB"])
            matches = matches[:target_pairs]

    candidate_count_by_user: Dict[str, int] = {p.user_id: 0 for p in participants}
    best_score_by_user: Dict[str, float] = {p.user_id: 0.0 for p in participants}
    for edge in candidate_edges:
        candidate_count_by_user[edge.user_a] = candidate_count_by_user.get(edge.user_a, 0) + 1
        candidate_count_by_user[edge.user_b] = candidate_count_by_user.get(edge.user_b, 0) + 1
        best_score_by_user[edge.user_a] = max(best_score_by_user.get(edge.user_a, 0.0), edge.total_score)
        best_score_by_user[edge.user_b] = max(best_score_by_user.get(edge.user_b, 0.0), edge.total_score)

    unmatched: List[Dict[str, Any]] = []
    for p in participants:
        if not is_active_for_cycle(p):
            reason = "inactive_for_cycle"
        elif p.user_id in matched_users:
            continue
        elif candidate_count_by_user.get(p.user_id, 0) == 0:
            reason = "no_candidate_after_precision_filter"
        elif best_score_by_user.get(p.user_id, 0.0) < config.reveal_threshold:
            reason = "below_reveal_threshold"
        else:
            reason = "not_selected_in_global_optimization"

        unmatched.append(
            {
                "userId": p.user_id,
                "reason": reason,
                "candidateCount": candidate_count_by_user.get(p.user_id, 0),
                "bestScore": round(best_score_by_user.get(p.user_id, 0.0), 6),
            }
        )

    return {
        "cycleId": payload.get("cycleId"),
        "algorithmVersion": payload.get("algorithmVersion", "precision-v3.0.0"),
        "matches": matches,
        "unmatched": unmatched,
        "debug": {
            "participantCount": len(participants),
            "activeParticipantCount": len(active_participants),
            "candidateEdgeCount": len(candidate_edges),
            "candidateEdges": [
                {
                    "userA": e.user_a,
                    "userB": e.user_b,
                    "baseScore": e.base_score,
                    "scoreTotal": e.total_score,
                    "matchWeight": e.match_weight,
                    "scoreBreakdown": e.breakdown,
                    "marketContext": e.market_context,
                    "penalties": e.penalties,
                }
                for e in sorted(candidate_edges, key=lambda x: x.total_score, reverse=True)
            ],
        },
    }


if __name__ == "__main__":
    demo_payload = {
        "cycleId": "2026w14",
        "algorithmVersion": "precision-v2.0.0",
        "participants": [
            {
                "userId": "u_1",
                "hardFilters": {
                    "gender": "female",
                    "sexuality": "heterosexual",
                    "grade": 2,
                    "campus": "main",
                    "college": "business",
                    "height": 165,
                    "heightPrefMin": 170,
                    "heightPrefMax": 190,
                    "crossCampus": True,
                    "sameCollege": True,
                },
                "status": {"verified": True, "completedQuestionnaire": True, "paused": False, "optIn": True},
                "features": {
                    "selfLikert": {
                        "marriage": 6,
                        "sleep": 5,
                        "ritual": 6,
                        "introvert": 4,
                        "logic_feel": 5,
                        "hustle": 6,
                        "drink": 2,
                        "smoke": 1,
                        "family_career": 5,
                        "conflict": 5,
                        "intimacy_pace": 4,
                        "opposite_friend": 3,
                        "reply_anxiety": 4,
                        "consume": 4,
                        "together": 5,
                        "travel": 5,
                    },
                    "spending": "flexible",
                    "diet": "no_restriction",
                    "studyspot": "library",
                    "meet_freq": "medium",
                    "interests": ["movie", "travel", "coffee"],
                    "selfTraits": ["warm", "stable", "honest"],
                },
                "preferences": {
                    "partnerPref": {
                        "hustle": 5,
                        "logic_feel": 4,
                        "introvert": 3,
                        "smoke": 1,
                        "drink": 2,
                        "appearance": 5,
                    },
                    "partnerTraits": ["honest", "stable"],
                    "interestOverlap": "similar",
                    "importantDimensions": ["marriage", "smoke", "drink", "hustle"],
                    "partnerTraitsImportant": True,
                },
            },
            {
                "userId": "u_2",
                "hardFilters": {
                    "gender": "male",
                    "sexuality": "heterosexual",
                    "grade": 3,
                    "campus": "main",
                    "college": "engineering",
                    "height": 178,
                    "heightPrefMin": 155,
                    "heightPrefMax": 170,
                    "crossCampus": True,
                    "sameCollege": True,
                },
                "status": {"verified": True, "completedQuestionnaire": True, "paused": False, "optIn": True},
                "features": {
                    "selfLikert": {
                        "marriage": 6,
                        "sleep": 4,
                        "ritual": 5,
                        "introvert": 3,
                        "logic_feel": 4,
                        "hustle": 6,
                        "drink": 2,
                        "smoke": 1,
                        "family_career": 5,
                        "conflict": 4,
                        "intimacy_pace": 4,
                        "opposite_friend": 4,
                        "reply_anxiety": 4,
                        "consume": 4,
                        "together": 4,
                        "travel": 5,
                    },
                    "spending": "flexible",
                    "diet": "no_restriction",
                    "studyspot": "library",
                    "meet_freq": "medium",
                    "interests": ["movie", "basketball", "coffee"],
                    "selfTraits": ["stable", "honest", "active"],
                },
                "preferences": {
                    "partnerPref": {
                        "hustle": 5,
                        "logic_feel": 5,
                        "introvert": 4,
                        "smoke": 1,
                        "drink": 2,
                        "appearance": 4,
                    },
                    "partnerTraits": ["warm", "honest"],
                    "interestOverlap": "similar",
                    "importantDimensions": ["marriage", "smoke", "drink"],
                    "partnerTraitsImportant": True,
                },
            },
        ],
    }

    import json

    print(json.dumps(solve_weekly_matches(demo_payload), indent=2))
