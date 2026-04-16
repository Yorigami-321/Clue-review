#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Whisper 模型加载线程"""

import os
from PyQt5.QtCore import QThread, pyqtSignal


class WhisperLoadThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, model_size: str = "base"):
        super().__init__()
        self.model_size = model_size

    def run(self):
        try:
            import whisper
            self.progress.emit(f"正在加载 Whisper {self.model_size} 模型...")
            model_dir = "./whisper_models"
            os.makedirs(model_dir, exist_ok=True)
            model = whisper.load_model(self.model_size, download_root=model_dir)
            self.progress.emit(f"Whisper {self.model_size} 模型加载完成")
            self.finished.emit(model)
        except Exception as e:
            self.error.emit(str(e))
