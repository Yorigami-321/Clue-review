#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涉检线索智能筛查工具 v6.0 — 程序入口
"""

import sys
import os

# 设置 FFmpeg 路径（Whisper 依赖）
FFMPEG_DIR = r"D:\APP\ffmpeg\bin"
if os.path.isdir(FFMPEG_DIR):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QApplication


def main():
    # 高分屏支持：必须在 QApplication 实例化之前设置
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("涉检线索智能筛查工具")
    app.setApplicationVersion("6.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()