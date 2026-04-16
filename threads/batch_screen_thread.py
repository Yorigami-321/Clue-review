#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量筛查线程：关键词分类 + 可选 LLM 增强 + 去重"""

import logging

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal

from core.analyzer import TextAnalyzer
from core.cloud_api import call_cloud_api
from core.constants import STATUS_PENDING

logger = logging.getLogger("ClueScreener")


class BatchScreenThread(QThread):
    progress = pyqtSignal(int, int, str)   # current, total, message
    finished = pyqtSignal(list)            # list[dict]

    def __init__(self, df: pd.DataFrame, analyzer: TextAnalyzer,
                 use_llm=False, api_key="", api_url="", model="",
                 dup_threshold=0.6, existing_hashes=None):
        super().__init__()
        self.df = df
        self.analyzer = analyzer
        self.use_llm = use_llm
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.dup_threshold = dup_threshold
        self.existing_hashes = existing_hashes or set()

    def run(self):
        records = []
        total = len(self.df)
        seen_texts = []

        for i, (_, row) in enumerate(self.df.iterrows()):
            raw = str(row.get("原始内容", ""))
            masked = str(row.get("脱敏内容", ""))

            # ---- 去重 ----
            h = TextAnalyzer.text_hash(raw)
            is_dup = h in self.existing_hashes
            if not is_dup:
                for prev in seen_texts[-100:]:
                    if TextAnalyzer.jaccard_similarity(raw, prev) > self.dup_threshold:
                        is_dup = True
                        break
            if is_dup:
                self.progress.emit(i + 1, total, f"跳过重复 {i+1}/{total}")
                continue

            self.existing_hashes.add(h)
            seen_texts.append(raw)

            # ---- 分类 ----
            cat, conf = self.analyzer.classify(masked)
            grade, _, _ = TextAnalyzer.get_grade(conf)
            icon = TextAnalyzer.get_grade_icon(grade)
            summary = self.analyzer.summarize(masked)

            # ---- LLM 增强 ----
            llm_text = ""
            if self.use_llm and self.api_key and conf < 0.7:
                prompt = (
                    "你是检察院涉检线索分析助手。请分析以下12345投诉内容，"
                    "判断属于以下哪个类别：刑事犯罪、公益诉讼、民事支持起诉、"
                    "行政执法监督、行政争议、民生保障、营商环境、网络安全、"
                    "安全生产、其他。\n请给出：1)类别 2)理由(50字以内) "
                    f"3)建议处理方式\n\n投诉内容：{masked[:500]}"
                )
                llm_text = call_cloud_api(
                    prompt, self.api_key, self.api_url, self.model
                ) or ""
                if llm_text:
                    for c in self.analyzer.kw_config:
                        if c in llm_text[:50]:
                            cat = c
                            conf = max(conf, 0.6)
                            grade, _, _ = TextAnalyzer.get_grade(conf)
                            icon = TextAnalyzer.get_grade_icon(grade)
                            break

            # ---- 来源 ----
            source = ""
            for col in ["来源", "渠道", "source"]:
                if col in row.index and pd.notna(row.get(col)):
                    source = str(row[col])
                    break

            records.append(dict(
                raw_text=raw, masked_text=masked, category=cat,
                confidence=conf, grade=grade, grade_icon=icon,
                summary=summary, status=STATUS_PENDING, source=source,
                llm_analysis=llm_text, text_hash=h,
            ))
            self.progress.emit(i + 1, total, f"筛查中 {i+1}/{total}")

        self.finished.emit(records)
