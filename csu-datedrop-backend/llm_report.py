"""
调用 MiniMax 大模型，根据匹配引擎的结构化数据生成自然语言匹配报告。
使用 OpenAI 兼容接口：https://api.minimax.chat/v1
"""

from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

def _load_env():
    """从 .env 文件加载环境变量（如果 dotenv 可用则用它，否则手动解析）。"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.isfile(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

_load_env()

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5-highspeed")

FIELD_LABELS: Dict[str, str] = {
    "citylife": "城市偏好", "marriage": "婚姻观", "goodness": "善良观",
    "idealism": "理想主义", "family_career": "家庭vs事业",
    "process_result": "过程vs结果", "novelty": "新鲜感", "conflict": "冲突处理",
    "sleep": "作息节律", "tidy": "整洁度", "canteen": "饮食习惯",
    "spicy": "辣度接受", "datespot": "约会地点", "together": "黏人程度",
    "travel": "旅行风格", "consume": "消费观", "reply_anxiety": "回复焦虑",
    "ritual": "仪式感", "opposite_friend": "异性好友边界",
    "dominance": "主导性", "caretaker": "照顾倾向",
    "intimacy_pace": "亲密节奏", "social_pda": "秀恩爱态度",
    "hustle": "上进心", "logic_feel": "理性vs感性",
    "introvert": "内向vs外向", "smoke": "吸烟态度", "drink": "饮酒态度",
    "appearance": "外貌气质", "spending": "消费风格", "diet": "饮食要求",
    "studyspot": "自习偏好", "meet_freq": "见面频率",
    "traits": "核心特质", "interests": "兴趣爱好",
}


def _label(field: str) -> str:
    return FIELD_LABELS.get(field, field)


def _build_prompt(
    my_name: str,
    peer_name: str,
    score: int,
    breakdown: Dict[str, Any],
    report_payload: Dict[str, Any],
    peer_campus: str,
    peer_grade: str,
    peer_major: str,
) -> str:
    """将匹配引擎的结构化数据转换为 prompt。"""

    shared = report_payload.get("shared_points") or []
    complement = report_payload.get("complementary_points") or []
    risks = report_payload.get("risk_flags") or []

    # 构建共同点描述
    shared_lines = []
    for p in shared[:6]:
        label = _label(p.get("field", ""))
        items = p.get("items")
        sc = round((p.get("score") or 0) * 100)
        if items:
            shared_lines.append(f"- {label}：你们都选择了「{'、'.join(items)}」({sc}%)")
        else:
            shared_lines.append(f"- {label}：高度一致 ({sc}%)")
    shared_text = "\n".join(shared_lines) if shared_lines else "（暂无突出共同点）"

    # 构建互补描述
    comp_lines = []
    for p in complement[:4]:
        label = _label(p.get("field", ""))
        comp_lines.append(f"- {label}：{my_name}={p.get('a_value', '?')}，{peer_name}={p.get('b_value', '?')}")
    comp_text = "\n".join(comp_lines) if comp_lines else "（暂无显著互补差异）"

    # 构建风险点描述
    risk_lines = []
    for r in risks[:3]:
        label = _label(r.get("field", ""))
        risk_lines.append(f"- {label}：{r.get('reason', '潜在摩擦')}")
    risk_text = "\n".join(risk_lines) if risk_lines else "（无明显风险点）"

    # 维度分数
    dim_lines = []
    dim_map = {
        "directional_a_to_b": "A→B 适配度",
        "directional_b_to_a": "B→A 适配度",
        "chemistry": "化学反应",
        "mutual_harmonic": "双向调和均值",
    }
    for k, v in breakdown.items():
        if isinstance(v, (int, float)) and k in dim_map:
            dim_lines.append(f"- {dim_map[k]}：{round(v * 100)}%")
    dim_text = "\n".join(dim_lines) if dim_lines else ""

    return f"""# 角色

你是 YueluDate 校园匹配平台的灵魂匹配报告作者。
你的笔法介于骈文与现代散文之间——对仗工整但不迂腐，意象具体但不堆砌。你像一个洞察力极强的旁观者，用第二人称"你"凝视读者，笃定、温柔、不容置疑地替两个人的关系做一次翻译。

# 数据

- A（读者）：{my_name}
- B：{peer_name}，{peer_campus}，{peer_grade}，{peer_major}
- 契合度：{score}%

维度分数：
{dim_text}

共同点：
{shared_text}

互补差异：
{comp_text}

风险：
{risk_text}

# 输出格式

三段正文 + 标题区，共 250-350 字。直接输出，不加任何元说明。

## 标题区
- 一个诗意标题，格式："XX里的XX"（如"麓山脚下的温差方程"）
- 一句对仗箴言作为副标题（如"你用逻辑丈量世界，某某用直觉触摸真相"）
- 三个二到四字的关系标签，用 ｜ 分隔（如：智识共振 ｜ 节奏互补 ｜ 静水深流）

## 正文

- **第一段 · 你们为什么被放到一起**：从契合度数字切入，将共同点翻译为具象场景。不说"你们兴趣一致"，要说"你们都会在周末把相机塞进书包、往岳麓山后山走——一个拍光影，一个拍路人，但回来的时候大概会在同一个路口停下来"。数据嵌在叙述里，不裸露。
- **第二段 · 互补与风险**：先写互补差异，用"冷面→热心"的反转笔法——先描述差异造成的表面张力，再翻转写这种张力为什么反而有用。风险点不回避，但用一个安静的转折收住："不过"或"值得留意的是"，一句话，不放大。
- **第三段 · 破冰建议**：给一个具体的、落在岳麓山大学城里的第一步（岳麓山、后湖、橘子洲、桃子湖、爱晚亭、图书馆、食堂……选一个），用一个具象画面收束全文。

# 文风铁律

## 骈文式现代句法
- 核心节奏：对仗并列。"在……中……，于……里……"、"既能……，也能……"、"不是……，而是……"。
- 每段至少一组对仗长句，但不超过两组——多了就成八股。
- 短句和长句交替，制造呼吸感。

## 具象隐喻替代一切直白描述
- 禁止直接输出心理学标签或数据结论的白话翻译。
- "内向 vs 外向"→"你习惯在人群散去后才开口说真话，某某却能在满桌陌生人中间先替你把气氛撑起来"。
- "婚姻观一致 92%"→"你们对'以后'这个词的理解，重合到几乎可以共用同一张时间表"。
- 每个数据点都必须找到一个生活场景或物件来承载。

## 冷热反转公式
- 写互补差异时必须使用：先写"冷/克制/表面张力"的一面，再急转写"暖/契合/恰好需要"的一面。
- 这个反转是全文的情绪引擎，放在第二段。

## 第二人称凝视
- 全文用"你"指代读者 A，用姓指代 B。
- 语气像塔罗师：我比你更早看见这件事的全貌，现在平静地讲给你听。

## 关键词加粗
- 对学校、专业、年级、兴趣标签、关键行为习惯加粗，作为人设锚点和视觉节奏点。

## 绝对禁止
- 缘分、奇妙、惊人、碰撞、火花、宝藏、旅程、灵魂共鸣、冥冥之中、想象一下、值得被爱
- 感叹号
- 空洞鸡汤、抒情升华、说教语气
- 裸露的百分比罗列（数据必须化入叙述）
- 网络流行语、emoji"""


def generate_narrative(
    my_name: str,
    peer_name: str,
    score: int,
    breakdown: Dict[str, Any],
    report_payload: Dict[str, Any],
    peer_campus: str = "",
    peer_grade: str = "",
    peer_major: str = "",
) -> Optional[str]:
    """调用 MiniMax 生成匹配叙事，失败返回 None。"""
    api_key = os.getenv("MINIMAX_API_KEY", "") or MINIMAX_API_KEY
    if not api_key:
        logger.warning("MINIMAX_API_KEY 未设置，跳过 LLM 生成")
        return None

    prompt = _build_prompt(
        my_name, peer_name, score, breakdown,
        report_payload, peer_campus, peer_grade, peer_major,
    )

    base_url = os.getenv("MINIMAX_BASE_URL", "") or MINIMAX_BASE_URL
    model = os.getenv("MINIMAX_MODEL", "") or MINIMAX_MODEL

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是YueluDate校园匹配平台的灵魂匹配报告作者。笔法介于骈文与现代散文之间——对仗工整但不迂腐，意象具体但不堆砌。像一个洞察力极强的旁观者，用第二人称凝视读者，笃定、温柔、不容置疑地替两个人的关系做一次翻译。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
            temperature=0.8,
        )
        text = resp.choices[0].message.content or ""
        # 去掉模型可能输出的 <think>...</think> 推理过程
        import re
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        return text if text else None
    except Exception as e:
        logger.error("MiniMax API 调用失败: %s: %s", type(e).__name__, e)
        return None
