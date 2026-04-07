"""
precision-v3.0.0 全流程测试
清空数据库 → 创建 100 账号+问卷 → 跑匹配 → 输出完整结果
直接操作 ORM，无需启动 API 服务器。
用法: python batch_test.py
"""

import json
import random
import sys
from collections import Counter

import bcrypt

from database import engine
from models import Base, Crush, Match, Profile, User
from sqlalchemy.orm import Session as SASession

from precision_matching_engine import PrecisionMatchConfig, solve_weekly_matches
from matcher_service import (
    _safe_dict,
    default_week_id,
    historical_matched_user_ids,
    ordered_pair,
    user_profile_to_participant_item,
)

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

PASSWORD = "test123456"
NUM_USERS = 100

# ═══════════════════════════════════════════════════════════
# 数据池
# ═══════════════════════════════════════════════════════════

GRADES = ["大一", "大二", "大三", "大四", "硕士", "博士"]
CAMPUSES = ["岳麓山", "潇湘", "南校区", "天心", "湘雅"]
COLLEGES = [
    "计算机学院", "数学与统计学院", "物理与电子学院", "商学院",
    "法学院", "自动化学院", "土木工程学院", "外国语学院",
    "湘雅公共卫生学院", "信息科学与工程学院",
]
PROVINCES = [
    "湖南", "广东", "北京", "四川", "浙江",
    "江苏", "河南", "湖北", "山东", "福建",
]
SPENDING = ["接近AA制", "收入高的一方多承担", "男方多承担", "看情况灵活处理"]
DIET = ["无特殊要求", "清真（不吃猪肉）", "素食", "其他"]
STUDYSPOT = ["新校区图书馆", "本部老图", "铁道校区图书馆", "后湖边长椅", "咖啡馆", "不自习"]
MEET_FREQ = ["每天", "一周3-4次", "一周1-2次", "看情况，不固定"]
SAME_COLLEGE = ["接受", "不接受", "无所谓"]
SEASONAL = ["爬岳麓山看日落", "后湖边散步聊天", "逛太平街吃吃喝喝", "图书馆一起自习", "橘子洲骑行"]

TRAITS = [
    "充满好奇心", "诚实正直", "聪明智慧", "温柔善良", "乐观开朗",
    "有勇气", "有创造力", "高度自律", "顾家", "独立",
    "忠诚", "有野心", "幽默风趣", "经世致用", "霸蛮坚韧",
]
INTERESTS_POOL = [
    "健身", "骑行", "球类运动", "跑步", "爬山/徒步", "游泳",
    "动漫/二次元", "电竞/PC游戏", "手游", "综艺影视", "桌游/剧本杀",
    "阅读", "音乐/乐器", "绘画/手工", "摄影", "历史/社科",
    "探店/美食", "旅行", "猫狗宠物", "烹饪/烘焙", "咖啡/茶道",
    "编程/算法", "硬件DIY/数码", "科学探索",
    "爬岳麓山", "后湖散步", "橘子洲骑行", "逛太平街",
]
MAJORS = [
    "计算机科学与技术", "软件工程", "数学", "物理学", "化学",
    "机械工程", "土木工程", "金融学", "法学", "英语",
    "临床医学", "自动化", "电子信息", "材料科学", "工商管理",
]
NAMES = [
    "张伟", "王芳", "李明", "赵丽", "刘洋", "陈晨", "杨帆", "黄蕾",
    "周杰", "吴敏", "徐磊", "孙静", "马超", "朱婷", "胡涛", "郭颖",
    "林峰", "何雨", "罗欣", "梁宇", "宋佳", "唐鑫", "韩雪", "冯旭",
    "曹芸", "邓超", "许晴", "彭博", "萧然", "田野", "董璇", "潘安",
]

# 单轨 Likert（含 v3 新增字段）
SINGLE_LIKERT = [
    "citylife", "marriage", "goodness", "idealism", "family_career",
    "process_result", "novelty", "conflict", "sleep", "tidy",
    "canteen", "spicy", "datespot", "together", "travel", "consume",
    "reply_anxiety", "ritual", "opposite_friend", "dominance",
    "caretaker", "intimacy_pace", "social_pda",
    "money_attitude", "conflict_response", "depend_comfort",  # v3 新增
    "interest_overlap", "grooming", "appearance_weight",
]

# 双轨 Likert（self + partner）
DUAL_TRACK = ["hustle", "logic_feel", "introvert", "smoke", "drink", "appearance"]

# 可标记"重要"的维度
IMPORTANT_CANDIDATES = [
    "marriage", "smoke", "consume", "intimacy_pace", "sleep",
    "conflict_response", "depend_comfort", "money_attitude",
    "opposite_friend", "together", "hustle",
]

# ── 5 种人格原型，用于生成更真实的数据 ──
# 每种原型定义偏好中心值，实际值 = center ± noise
ARCHETYPES = {
    "浪漫理想型": {
        "marriage": 6, "ritual": 6, "together": 6, "intimacy_pace": 5,
        "reply_anxiety": 5, "social_pda": 5, "idealism": 5, "goodness": 6,
        "depend_comfort": 6, "conflict_response": 6, "novelty": 5,
    },
    "理性务实型": {
        "marriage": 5, "hustle": 6, "logic_feel": 6, "consume": 5,
        "money_attitude": 5, "process_result": 2, "ritual": 3,
        "together": 3, "novelty": 4, "conflict_response": 5,
    },
    "自由探索型": {
        "novelty": 6, "travel": 6, "introvert": 2, "marriage": 3,
        "together": 3, "idealism": 6, "datespot": 6, "sleep": 2,
        "money_attitude": 5, "social_pda": 4,
    },
    "传统稳重型": {
        "marriage": 7, "family_career": 6, "tidy": 6, "sleep": 6,
        "consume": 3, "conflict": 5, "money_attitude": 3, "together": 5,
        "conflict_response": 5, "depend_comfort": 5,
    },
    "社交达人型": {
        "introvert": 1, "social_pda": 6, "together": 6, "datespot": 6,
        "reply_anxiety": 3, "drink": 4, "canteen": 5, "dominance": 5,
        "novelty": 5, "conflict_response": 5,
    },
}

ARCHETYPE_NAMES = list(ARCHETYPES.keys())


def clamp_likert(v: float) -> int:
    return max(1, min(7, round(v)))


def random_likert_with_archetype(key: str, archetype: dict) -> int:
    if key in archetype:
        center = archetype[key]
        noise = random.gauss(0, 1.2)
        return clamp_likert(center + noise)
    return random.randint(1, 7)


# ═══════════════════════════════════════════════════════════
# 问卷生成
# ═══════════════════════════════════════════════════════════

def make_quiz(gender_cn: str, archetype_name: str):
    """生成一份随机问卷（raw_quiz_data 格式，不含 gender/sexuality/campus/crossCampus）。"""
    arch = ARCHETYPES[archetype_name]

    is_male = gender_cn == "男"
    height = random.randint(165, 188) if is_male else random.randint(152, 172)

    q = {
        "school": "csu",
        "grade": random.choice(GRADES),
        "college": random.choice(COLLEGES),
        "height": height,
        "heightPrefMin": random.randint(150, 158) if is_male else random.randint(165, 172),
        "heightPrefMax": random.randint(170, 180) if is_male else random.randint(180, 200),
        "hometown": random.choice(PROVINCES),
        "sameCollege": random.choice(SAME_COLLEGE),
        "spending": random.choice(SPENDING),
        "diet": random.choice(DIET),
        "studyspot": random.choice(STUDYSPOT),
        "meet_freq": random.choice(MEET_FREQ),
        "seasonal": random.choice(SEASONAL),
        "interests": random.sample(INTERESTS_POOL, random.randint(2, 5)),
        "selfTraits": random.sample(TRAITS, random.randint(3, 5)),
        "partnerTraits": random.sample(TRAITS, random.randint(3, 5)),
        "partnerTraitsImportant": random.choice([True, False]),
        "likert": {},
    }

    # 单轨 Likert
    for k in SINGLE_LIKERT:
        val = random_likert_with_archetype(k, arch)
        q["likert"][k] = {"self": val}

    # 双轨 Likert (self + partner)
    for k in DUAL_TRACK:
        self_val = random_likert_with_archetype(k, arch)
        # partner preference: similar to self with some variation
        partner_val = clamp_likert(self_val + random.gauss(0, 1.0))
        q["likert"][k] = {"self": self_val, "partner": partner_val}

    # 随机标记 1-3 个维度为"重要"
    for dim in random.sample(IMPORTANT_CANDIDATES, random.randint(1, 3)):
        if dim in q["likert"]:
            q["likert"][dim]["important"] = True

    return q


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    random.seed(42)  # 可复现
    hashed_pw = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

    # ── 0. 清空数据库 ──
    Base.metadata.create_all(bind=engine)
    with SASession(engine) as s:
        for tbl in [Match, Crush, Profile, User]:
            s.query(tbl).delete()
        s.commit()
    print("✓ 已清空数据库全部表\n")

    # ── 1. 创建 100 个用户 + Profile + 问卷 ──
    print(f"=== 创建 {NUM_USERS} 个测试账号 ===\n")
    accounts = []
    arch_counter = Counter()

    with SASession(engine) as s:
        for i in range(1, NUM_USERS + 1):
            gender_cn = "男" if i % 2 == 1 else "女"
            campus = random.choice(CAMPUSES)
            grade = random.choice(GRADES)
            major = random.choice(MAJORS)
            name = random.choice(NAMES) + str(random.randint(10, 99))
            arch_name = random.choice(ARCHETYPE_NAMES)
            arch_counter[arch_name] += 1

            user = User(
                email=f"testuser{i:03d}@csu.edu.cn",
                hashed_password=hashed_pw,
                is_verified=True,
                name=name,
                campus=campus,
                grade=grade,
                major=major,
                quiz_completed=True,
                paused=False,
            )
            s.add(user)
            s.flush()

            quiz = make_quiz(gender_cn, arch_name)

            profile = Profile(
                user_id=user.id,
                gender=gender_cn,
                sexuality="异性恋",
                campus=campus,
                cross_campus_ok=True,
                raw_quiz_data=quiz,
            )
            s.add(profile)

            accounts.append({
                "no": i,
                "user_id": user.id,
                "email": user.email,
                "name": name,
                "gender": gender_cn,
                "campus": campus,
                "grade": grade,
                "archetype": arch_name,
            })

            if i % 10 == 0:
                print(f"  已创建 {i}/{NUM_USERS} ...")

        s.commit()

    print(f"\n✓ {NUM_USERS} 个账号创建完成")
    print(f"  人格分布: {dict(arch_counter)}")
    print(f"  统一密码: {PASSWORD}\n")

    # ── 2. 运行 precision-v3.0.0 匹配 ──
    print("=== 运行 precision-v3.0.0 匹配算法 ===\n")

    week_id = default_week_id()
    config = PrecisionMatchConfig()

    with SASession(engine) as session:
        rows = (
            session.query(User, Profile)
            .join(Profile, Profile.user_id == User.id)
            .filter(User.paused.is_(False), User.quiz_completed.is_(True))
            .all()
        )

        part_items = []
        for u, p in rows:
            raw = _safe_dict(p.raw_quiz_data)
            hist = historical_matched_user_ids(session, u.id)
            part_items.append(user_profile_to_participant_item(u, p, raw, hist))

        payload = {
            "cycleId": str(week_id),
            "algorithmVersion": "precision-v3.0.0",
            "participants": part_items,
        }
        result = solve_weekly_matches(payload, config)
        matches_out = result.get("matches") or []

        # 写入 Match 表
        created = []
        for m in matches_out:
            ua, ub = int(m["userA"]), int(m["userB"])
            u1, u2 = ordered_pair(ua, ub)
            sc = round(float(m.get("scoreTotal", 0)) * 100, 2)
            report_data = {
                "kind": "algorithm",
                "breakdown": m.get("scoreBreakdown") or {},
                "evidence": m.get("evidence"),
                "marketContext": m.get("marketContext"),
                "reportPayload": m.get("reportPayload"),
                "week_id": week_id,
            }
            session.add(Match(
                user1_id=u1, user2_id=u2, week_number=week_id,
                score=sc, report_data=report_data,
            ))
            created.append({
                "user1_id": u1, "user2_id": u2, "score": sc,
                "breakdown": m.get("scoreBreakdown"),
                "evidence": m.get("evidence"),
                "market": m.get("marketContext"),
            })
        session.commit()

    # ── 3. 分析结果 ──
    debug = result.get("debug", {})
    unmatched = result.get("unmatched") or []
    all_edges = debug.get("candidateEdges", [])

    print(f"  参与人数:     {debug.get('activeParticipantCount', '?')}")
    print(f"  候选配对数:   {debug.get('candidateEdgeCount', '?')}")
    print(f"  最终匹配:     {len(created)} 对 ({len(created) * 2} 人)")
    print(f"  未匹配:       {len(unmatched)} 人")
    match_rate = len(created) * 2 / NUM_USERS * 100 if NUM_USERS else 0
    print(f"  匹配率:       {match_rate:.0f}%")

    # ── 4. 分数分布 ──
    scores = [c["score"] for c in created]
    if scores:
        print(f"\n=== 匹配分数分布 ===\n")
        print(f"  最高: {max(scores):.1f}%  最低: {min(scores):.1f}%  平均: {sum(scores)/len(scores):.1f}%  中位: {sorted(scores)[len(scores)//2]:.1f}%")

        # 直方图
        buckets = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "50-59": 0, "<50": 0}
        for sc in scores:
            if sc >= 90: buckets["90-100"] += 1
            elif sc >= 80: buckets["80-89"] += 1
            elif sc >= 70: buckets["70-79"] += 1
            elif sc >= 60: buckets["60-69"] += 1
            elif sc >= 50: buckets["50-59"] += 1
            else: buckets["<50"] += 1

        for label, count in buckets.items():
            bar = "█" * count
            print(f"  {label:>7}: {count:>3} {bar}")

    # 候选配对分数分布
    if all_edges:
        edge_scores = [e["scoreTotal"] * 100 for e in all_edges]
        print(f"\n  候选配对分数: 最高={max(edge_scores):.1f}%  最低={min(edge_scores):.1f}%  平均={sum(edge_scores)/len(edge_scores):.1f}%")

    # ── 5. 未匹配原因 ──
    if unmatched:
        reasons = Counter(u["reason"] for u in unmatched)
        print(f"\n=== 未匹配原因分布 ===\n")
        for reason, cnt in reasons.most_common():
            print(f"  {reason}: {cnt}")

    # ── 6. 匹配明细 ──
    # 构建 user_id -> account 映射
    uid_to_account = {a["user_id"]: a for a in accounts}
    match_peer = {}
    for c in created:
        match_peer[c["user1_id"]] = (c["user2_id"], c["score"])
        match_peer[c["user2_id"]] = (c["user1_id"], c["score"])

    print(f"\n=== 匹配明细 (按分数降序) ===\n")
    print(f"{'分数':>6}  {'用户A':<24} {'人格A':<10} {'用户B':<24} {'人格B':<10} {'亮点'}")
    print("-" * 120)

    for c in sorted(created, key=lambda x: x["score"], reverse=True):
        a1 = uid_to_account.get(c["user1_id"], {})
        a2 = uid_to_account.get(c["user2_id"], {})
        evidence = c.get("evidence") or {}
        shared = evidence.get("shared_points") or []
        top_shared = ", ".join(p.get("label", "?") for p in shared[:3])
        risks = evidence.get("risk_flags") or []
        risk_str = ""
        if risks:
            risk_str = " | 风险: " + ", ".join(f'{r.get("label","?")}({r.get("severity","?")})'
                                                for r in risks[:2])

        name_a = f'{a1.get("name","?")}({a1.get("gender","?")})'
        name_b = f'{a2.get("name","?")}({a2.get("gender","?")})'
        arch_a = a1.get("archetype", "?")
        arch_b = a2.get("archetype", "?")

        print(f"{c['score']:>5.1f}%  {name_a:<24} {arch_a:<10} {name_b:<24} {arch_b:<10} {top_shared}{risk_str}")

    # ── 7. 人格原型配对统计 ──
    print(f"\n=== 人格原型配对矩阵 ===\n")
    pair_matrix = Counter()
    for c in created:
        a1 = uid_to_account.get(c["user1_id"], {})
        a2 = uid_to_account.get(c["user2_id"], {})
        pair = tuple(sorted([a1.get("archetype", "?"), a2.get("archetype", "?")]))
        pair_matrix[pair] += 1

    for pair, cnt in pair_matrix.most_common():
        print(f"  {pair[0]} × {pair[1]}: {cnt} 对")

    # ── 8. 样本详细报告 (Top 3) ──
    print(f"\n=== Top 3 匹配详细报告 ===\n")
    top3 = sorted(created, key=lambda x: x["score"], reverse=True)[:3]
    for rank, c in enumerate(top3, 1):
        bd = c.get("breakdown") or {}
        ev = c.get("evidence") or {}
        mk = c.get("market") or {}
        a1 = uid_to_account.get(c["user1_id"], {})
        a2 = uid_to_account.get(c["user2_id"], {})
        print(f"  #{rank}  {a1.get('name','')} × {a2.get('name','')} = {c['score']:.1f}%")
        print(f"       偏好匹配={bd.get('preference_fit',0):.3f}  价值观={bd.get('value_alignment',0):.3f}  "
              f"生活方式={bd.get('lifestyle_fit',0):.3f}  化学反应={bd.get('chemistry',0):.3f}")
        print(f"       冲突上限={bd.get('conflict_cap',0):.3f}  置信度={bd.get('confidence',0):.3f}  "
              f"排名奖励={bd.get('rank_bonus',0):.4f}  排他奖励={bd.get('exclusivity_bonus',0):.4f}")
        shared = ev.get("shared_points") or []
        if shared:
            print(f"       共鸣: {', '.join(p.get('label','?') + '(' + str(round(p.get('score',0)*100)) + '%)' for p in shared[:5])}")
        risks = ev.get("risk_flags") or []
        if risks:
            print(f"       风险: {', '.join(r.get('label','?') + '(' + r.get('severity','?') + ')' for r in risks[:3])}")
        comps = ev.get("complementary_points") or []
        if comps:
            print(f"       互补: {', '.join(p.get('label','?') for p in comps[:3])}")
        print()

    # ── 9. 保存账号清单 ──
    for a in accounts:
        uid = a["user_id"]
        if uid in match_peer:
            peer_id, sc = match_peer[uid]
            peer = uid_to_account.get(peer_id, {})
            a["matched_with"] = peer.get("email", "?")
            a["match_score"] = sc
        else:
            a["matched_with"] = None
            a["match_score"] = None
        a["password"] = PASSWORD

    with open("accounts.json", "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    print(f"✓ 账号清单已保存到 accounts.json")

    # ── 10. 总结 ──
    matched_count = sum(1 for a in accounts if a.get("matched_with"))
    print(f"\n{'='*60}")
    print(f"  算法版本:   precision-v3.0.0")
    print(f"  总账号数:   {NUM_USERS}")
    print(f"  匹配成功:   {matched_count} 人 ({len(created)} 对)")
    print(f"  匹配率:     {match_rate:.0f}%")
    if scores:
        print(f"  平均分数:   {sum(scores)/len(scores):.1f}%")
    print(f"  统一密码:   {PASSWORD}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
