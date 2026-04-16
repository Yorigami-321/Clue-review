#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本分析引擎：TF-IDF 加权分类 / 脱敏 / 摘要 / 去重
"""

import re
import math
import hashlib
from typing import Dict, Tuple

from core.keywords import DEFAULT_KEYWORDS


class TextAnalyzer:
    """关键词 + TF-IDF 加权分类引擎"""

    MOBILE_RE = re.compile(r"1[3-9]\d{9}")
    ID_RE = re.compile(r"\d{17}[\dXx]")
    BANK_RE = re.compile(r"\d{16,19}")

    def __init__(self, kw_config: dict = None):
        self.kw_config = kw_config or DEFAULT_KEYWORDS
        self._build_idf()

    # ---------- IDF ----------
    def _build_idf(self):
        cat_count = max(
            sum(1 for i in self.kw_config.values() if i.get("enabled", True)), 1
        )
        kw_cats: Dict[str, set] = {}
        for cat, info in self.kw_config.items():
            if not info.get("enabled", True):
                continue
            for kw in info.get("keywords", []):
                kw_cats.setdefault(kw, set()).add(cat)

        self.kw_idf = {kw: math.log(cat_count / len(cats)) + 1.0
                       for kw, cats in kw_cats.items()}

    # ---------- 脱敏 ----------
    def desensitize(self, text: str) -> str:
        if not isinstance(text, str):
            return str(text) if text else ""
        text = self.MOBILE_RE.sub(
            lambda m: m.group()[:3] + "****" + m.group()[7:], text)
        text = self.ID_RE.sub(
            lambda m: m.group()[:4] + "**********" + m.group()[-4:], text)
        text = self.BANK_RE.sub(
            lambda m: m.group()[:4] + "****" + m.group()[-4:], text)
        return text

    # ---------- 分类 ----------
    def classify(self, text: str) -> Tuple[str, float]:
        if not isinstance(text, str) or not text.strip():
            return "其他", 0.0

        scores = {}
        for cat, info in self.kw_config.items():
            if not info.get("enabled", True):
                continue
            w = info.get("weight", 1.0)
            s = 0.0
            for kw in info.get("keywords", []):
                cnt = text.count(kw)
                if cnt > 0:
                    tf = 1 + math.log(cnt)
                    s += tf * self.kw_idf.get(kw, 1.0) * w
            scores[cat] = s

        if not scores or max(scores.values()) == 0:
            return "其他", 0.0

        best = max(scores, key=scores.get)
        total = sum(scores.values())
        conf = scores[best] / total if total > 0 else 0.0

        matched = sum(1 for kw in self.kw_config[best].get("keywords", [])
                      if kw in text)
        bonus = min(matched * 0.05, 0.2)
        conf = round(min(max(conf + bonus, 0.0), 1.0), 3)
        return best, conf

    # ---------- 等级 ----------
    @staticmethod
    def get_grade(confidence: float) -> Tuple[str, str, str]:
        if confidence >= 0.85:
            return "A", "#2ecc71", "高价值线索，可直接采纳"
        if confidence >= 0.70:
            return "B", "#3498db", "较有价值，建议优先处理"
        if confidence >= 0.55:
            return "C", "#f1c40f", "中等价值，正常处理"
        if confidence >= 0.35:
            return "D", "#e67e22", "低价值，需人工复核"
        return "E", "#e74c3c", "待定，重点复核"

    @staticmethod
    def get_grade_icon(grade: str) -> str:
        return {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🟠", "E": "🔴"}.get(grade, "⚪")

    # ---------- 摘要 ----------
    def summarize(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        found = []
        for info in self.kw_config.values():
            if not info.get("enabled", True):
                continue
            for kw in info.get("keywords", []):
                if kw in text and kw not in found:
                    found.append(kw)

        phones = self.MOBILE_RE.findall(text)
        parts = []
        if phones:
            p = phones[0]
            parts.append(f"电话{p[:3]}****{p[7:]}")
        if found:
            parts.append(f"涉及{'、'.join(found[:5])}")
        return "；".join(parts) if parts else (text[:120] + ("..." if len(text) > 120 else ""))

    # ---------- 哈希 / 去重 ----------
    @staticmethod
    def text_hash(text: str) -> str:
        cleaned = re.sub(r"\s+", "", str(text))
        return hashlib.md5(cleaned.encode("utf-8")).hexdigest()

    @staticmethod
    def jaccard_similarity(a: str, b: str) -> float:
        sa, sb = set(a), set(b)
        union = sa | sb
        return len(sa & sb) / len(union) if union else 0.0
