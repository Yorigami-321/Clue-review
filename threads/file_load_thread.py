#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件加载线程（CSV / Excel）"""

import logging

import pandas as pd
import chardet
from PyQt5.QtCore import QThread, pyqtSignal

from core.analyzer import TextAnalyzer

logger = logging.getLogger("ClueScreener")


class FileLoadThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, chunk_size: int = 50000):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size

    def run(self):
        try:
            self.progress.emit("正在读取文件...")
            if self.file_path.lower().endswith(".csv"):
                with open(self.file_path, "rb") as f:
                    enc = chardet.detect(f.read(10000)).get("encoding", "utf-8") or "utf-8"
                chunks = list(pd.read_csv(
                    self.file_path, encoding=enc, chunksize=self.chunk_size
                ))
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_excel(self.file_path)

            # 自动识别文本列
            text_col = None
            for c in df.columns:
                if any(x in c for x in
                       ["内容", "投诉", "描述", "诉求", "text", "content", "问题"]):
                    text_col = c
                    break
            if text_col is None:
                text_col = df.columns[0]

            df.rename(columns={text_col: "原始内容"}, inplace=True)

            analyzer = TextAnalyzer()
            df["脱敏内容"] = df["原始内容"].apply(
                lambda x: analyzer.desensitize(str(x)) if pd.notna(x) else ""
            )

            self.progress.emit(f"加载完成，共 {len(df)} 条数据")
            self.finished.emit(df)
        except Exception as e:
            logger.error(f"文件加载失败: {e}")
            self.error.emit(str(e))
