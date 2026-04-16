#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音频转写线程"""

import os
import time
import tempfile

from PyQt5.QtCore import QThread, pyqtSignal

from core.analyzer import TextAnalyzer


class AudioTranscribeThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(tuple)  # (raw_text, masked_text, success_bool)

    def __init__(self, audio_data: bytes, whisper_model):
        super().__init__()
        self.audio_data = audio_data
        self.whisper_model = whisper_model

    def run(self):
        tmp = None
        try:
            self.progress.emit("正在转写音频...")
            tmp = os.path.join(tempfile.gettempdir(), f"tr_{int(time.time())}.wav")
            with open(tmp, "wb") as f:
                f.write(self.audio_data)

            result = self.whisper_model.transcribe(
                tmp, language="zh", task="transcribe", verbose=False
            )
            raw = result["text"]
            analyzer = TextAnalyzer()
            masked = analyzer.desensitize(raw)
            self.progress.emit("转写完成")
            self.finished.emit((raw, masked, True))
        except Exception as e:
            self.finished.emit(("", f"转写失败: {e}", False))
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
