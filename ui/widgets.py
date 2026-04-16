#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝科技风 — 自定义按钮 / 卡片 / 统计卡片组件
"""

from PyQt5.QtWidgets import (
    QPushButton, QGroupBox, QWidget, QVBoxLayout,
    QLabel, QHBoxLayout, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from ui.theme import Colors


# ===================== 按钮 =====================

def _make_btn(text: str, bg: str, hover: str, radius=8,
              padding="11px 22px", font_size=16, bold=False) -> QPushButton:
    btn = QPushButton(text)
    weight = "bold" if bold else "500"
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {Colors.TEXT_WHITE};
            border: none;
            border-radius: {radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: {weight};
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {bg};
        }}
        QPushButton:disabled {{
            background-color: {Colors.BTN_SECONDARY};
            color: {Colors.TEXT_MUTED};
        }}
    """)
    return btn


def primary_btn(text: str) -> QPushButton:
    return _make_btn(text, Colors.BTN_PRIMARY, "#5b7bf8")


def secondary_btn(text: str) -> QPushButton:
    return _make_btn(text, Colors.BTN_SECONDARY, "#3a4470")


def danger_btn(text: str) -> QPushButton:
    return _make_btn(text, Colors.BTN_DANGER, "#f87171", bold=True)


def success_btn(text: str) -> QPushButton:
    return _make_btn(text, Colors.BTN_SUCCESS, "#4ade80")


def warning_btn(text: str) -> QPushButton:
    return _make_btn(text, Colors.BTN_WARNING, "#fbbf24")


def gradient_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {Colors.ACCENT_BLUE}, stop:1 {Colors.ACCENT_PURPLE});
            color: {Colors.TEXT_WHITE};
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #5b7bf8, stop:1 #b86ef7);
        }}
        QPushButton:disabled {{
            background: {Colors.BTN_SECONDARY};
            color: {Colors.TEXT_MUTED};
        }}
    """)
    return btn


def sidebar_btn(text: str, icon_text: str = "", active: bool = False) -> QPushButton:
    """侧边栏导航按钮"""
    display = f"{icon_text}  {text}" if icon_text else text
    btn = QPushButton(display)
    bg = Colors.SIDEBAR_ACTIVE if active else "transparent"
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {Colors.TEXT_PRIMARY if active else Colors.TEXT_SECONDARY};
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 20px;
            font-weight: {'bold' if active else 'normal'};
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {Colors.SIDEBAR_HOVER};
            color: {Colors.TEXT_PRIMARY};
        }}
    """)
    return btn


# ===================== 卡片 =====================

def card(title: str) -> QGroupBox:
    """深色科技风卡片"""
    c = QGroupBox(title)
    return c


# ===================== 统计数字卡片 =====================

class StatCard(QWidget):
    """单个统计数字卡片（深色圆角 + 大号彩色数字）"""

    def __init__(self, icon: str, label: str, value: str, color: str,
                 parent=None):
        super().__init__(parent)
        self.color = color
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # 顶部图标 + 标签
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            color: {color};
            font-size: 18px;
            background: transparent;
        """)
        top.addWidget(icon_label)

        title_label = QLabel(label)
        title_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 16px;
            background: transparent;
        """)
        top.addWidget(title_label)
        top.addStretch()
        layout.addLayout(top)

        # 大号数值
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 36px;
            font-weight: bold;
            background: transparent;
            padding: 4px 0;
        """)
        layout.addWidget(self.value_label)

    def set_value(self, text: str):
        self.value_label.setText(text)

    def paintEvent(self, event):
        """绘制背景（确保 stylesheet 对自定义 QWidget 生效）"""
        from PyQt5.QtWidgets import QStyleOption, QStyle
        from PyQt5.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
