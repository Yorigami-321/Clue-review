#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深蓝科技风主题 — 字体大小可在 FontSize 类中统一自定义
"""


# =====================================================================
#  ★★★ 字体大小控制中心 ★★★
#  只需修改这里的数值，即可全局生效
#  所有数值单位为 px
# =====================================================================
class FontSize:
    GLOBAL       = 14   # 全局默认字体
    LABEL        = 16   # 普通标签
    INPUT        = 20  # 输入框 / 下拉框 / 日期框
    BUTTON       = 16  # 普通按钮
    BUTTON_BIG   = 17  # 大号渐变按钮
    SIDEBAR      = 16 +2   # 侧边栏导航
    SIDEBAR_TITLE= 15 +2   # 侧边栏应用名
    CARD_TITLE   = 17 +2   # 卡片（QGroupBox）标题
    CHECKBOX     = 16 +2   # 复选框
    TAB          = 15    # 标签页 Tab
    TABLE_HEADER = 14 +2   # 表格表头
    TABLE_CELL   = 14 +2  # 表格内容
    MENUBAR      = 15 +2  # 菜单栏
    MENU_ITEM    = 15  +2  # 菜单项
    STATUSBAR    = 14 +2   # 状态栏
    TOOLTIP      = 14 +2   # 工具提示
    DIALOG       = 16 +2   # 对话框文字
    MSGBOX       = 16 +2   # 消息弹框
    MSGBOX_BTN   = 15  +2  # 消息弹框按钮
    STAT_LABEL   = 14  +2  # 统计卡片上方小标签
    STAT_ICON    = 18  +2  # 统计卡片图标
    STAT_VALUE   = 36  +2  # 统计卡片大号数字
    COMBO_ITEM   = 18  # 下拉菜单展开项
    CALENDAR     = 14  +2  # 日历弹窗


# =====================================================================
#  配色
# =====================================================================
class Colors:
    BG_DARKEST    = "#0a0e27"
    BG_DARK       = "#0d1233"
    BG_CARD       = "#111842"
    BG_CARD_HOVER = "#161d52"
    BG_INPUT      = "#0f1540"
    BG_HEADER     = "#080c22"

    BORDER        = "#1a2260"
    BORDER_LIGHT  = "#2a3480"
    BORDER_FOCUS  = "#4a6cf7"

    TEXT_PRIMARY   = "#e2e8f0"
    TEXT_SECONDARY = "#7a85a0"
    TEXT_MUTED     = "#4a5270"
    TEXT_WHITE     = "#ffffff"

    ACCENT_BLUE    = "#4a6cf7"
    ACCENT_CYAN    = "#22d3ee"
    ACCENT_GREEN   = "#22c55e"
    ACCENT_ORANGE  = "#f59e0b"
    ACCENT_RED     = "#ef4444"
    ACCENT_PURPLE  = "#a855f7"

    BTN_PRIMARY    = "#4a6cf7"
    BTN_SUCCESS    = "#22c55e"
    BTN_WARNING    = "#f59e0b"
    BTN_DANGER     = "#ef4444"
    BTN_SECONDARY  = "#2a3460"

    SIDEBAR_BG     = "#080c22"
    SIDEBAR_ACTIVE = "#4a6cf7"
    SIDEBAR_HOVER  = "#111842"


# =====================================================================
#  QSS 样式表（所有字号引用 FontSize）
# =====================================================================
F = FontSize
C = Colors

DARK_TECH_THEME = """

/* ========== 全局 ========== */
QWidget {
    color: #e2e8f0;
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 14px;
}
QMainWindow {
    background-color: #0d1233;
}

/* ========== 顶部标题栏 ========== */
QWidget#headerWidget {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #080c22, stop:1 #0a0e27);
    border-radius: 12px;
    border: 1px solid #1a2260;
}

/* ========== 侧边栏 ========== */
QWidget#sidebarWidget {
    background-color: #080c22;
    border-right: 1px solid #1a2260;
    border-radius: 0px;
}

/* ========== 卡片 ========== */
QGroupBox {
    font-weight: bold;
    font-size: 19px;
    color: #e2e8f0;
    border: 1px solid #1a2260;
    border-radius: 12px;
    margin-top: 18px;
    padding: 20px 14px 14px 14px;
    background-color: transparent;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
    color: #22d3ee;
    font-size: 19px;
}

/* ========== 标签 ========== */
QLabel {
    color: #e2e8f0;
    background: transparent;
    font-size: 16px;
}

/* ========== 输入框 ========== */
QTextEdit {
    border: 1px solid #1a2260;
    border-radius: 8px;
    padding: 10px 14px;
    background-color: #0f1540;
    color: #e2e8f0;
    font-size: 20px;
    selection-background-color: #4a6cf7;
}
QLineEdit {
    border: 1px solid #1a2260;
    border-radius: 8px;
    padding: 9px 14px;
    background-color: #0f1540;
    color: #e2e8f0;
    font-size: 20px;
    min-height: 24px;
    selection-background-color: #4a6cf7;
}
QSpinBox, QDateEdit {
    border: 1px solid #1a2260;
    border-radius: 8px;
    padding: 9px 14px;
    background-color: #0f1540;
    color: #e2e8f0;
    font-size: 20px;
    min-height: 24px;
}
QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #4a6cf7;
}

/* ========== 下拉框 ========== */
QComboBox {
    border: 1px solid #1a2260;
    border-radius: 8px;
    padding: 9px 14px;
    background-color: #0f1540;
    color: #e2e8f0;
    font-size: 20px;
    min-height: 24px;
}
QComboBox:hover {
    border: 1px solid #2a3480;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #7a85a0;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #111842;
    border: 1px solid #2a3480;
    color: #e2e8f0;
    font-size: 18px;
    selection-background-color: #4a6cf7;
    outline: none;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    padding: 8px 14px;
    min-height: 30px;
}

# QComboBox {
#     border: 1px solid #1a2260;
#     border-radius: 8px;
#     padding: 9px 14px;
#     background-color: #0f1540;
#     color: #e2e8f0;
#     font-size: 20px;
#     min-height: 24px;
# }

# QComboBox QAbstractItemView {
#     background-color: #111842;
#     alternate-background-color: #0f1540;
#     border: 1px solid #2a3480;
#     color: #e2e8f0;
#     font-size: 18px;
#     selection-background-color: #4a6cf7;
#     selection-color: #ffffff;
#     outline: none;
#     padding: 4px;
# }

# QComboBox QAbstractItemView::item {
#     color: #e2e8f0;
#     background: transparent;
#     padding: 8px 14px;
#     min-height: 30px;
# }

# QComboBox QAbstractItemView::item:selected {
#     color: #ffffff;
#     background-color: #4a6cf7;
# }

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 10px;
    color: #e2e8f0;
    font-size: 18px;
}
QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 5px;
    border: 2px solid #2a3480;
    background: #0f1540;
}
QCheckBox::indicator:checked {
    background-color: #4a6cf7;
    border-color: #4a6cf7;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    border: 1px solid #1a2260;
    border-radius: 10px;
    background-color: transparent;
    top: -1px;
}
QTabBar::tab {
    padding: 10px 22px;
    margin-right: 3px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    background-color: #0f1540;
    color: #7a85a0;
    border: 1px solid #1a2260;
    border-bottom: none;
    font-size: 15px;
}
QTabBar::tab:selected {
    background-color: #4a6cf7;
    color: #ffffff;
    border-color: #4a6cf7;
    font-size: 15px;
}
QTabBar::tab:hover:!selected {
    background-color: #161d52;
    color: #e2e8f0;
}

/* ========== 表格 ========== */
QTableWidget {
    border: 1px solid #1a2260;
    border-radius: 10px;
    background-color: #111842;
    alternate-background-color: #0f1540;
    gridline-color: #1a2260;
    color: #e2e8f0;
    font-size: 16px;
    selection-background-color: #4a6cf7;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #0a0e27;
    color: #22d3ee;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #4a6cf7;
    font-weight: bold;
    font-size: 16px;
}
QTableWidget::item {
    padding: 7px 8px;
    border-bottom: 1px solid #1a2260;
}
QTableWidget::item:selected {
    background-color: rgba(74, 108, 247, 0.3);
    color: #ffffff;
}

/* ========== 进度条 ========== */
QProgressBar {
    border: none;
    border-radius: 6px;
    text-align: center;
    background-color: #0f1540;
    color: #e2e8f0;
    font-size: 12px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #4a6cf7, stop:1 #22d3ee);
    border-radius: 6px;
}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {
    height: 4px; background: #0f1540; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #4a6cf7; width: 16px; height: 16px;
    margin: -6px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #4a6cf7; border-radius: 2px;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: #0d1233; width: 8px; border-radius: 4px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a3480; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #4a6cf7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal {
    background: #0d1233; height: 8px; border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2a3480; border-radius: 4px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #4a6cf7; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #080c22;
    color: #7a85a0;
    padding: 4px 12px;
    border-top: 1px solid #1a2260;
    font-size: 16px;
}

/* ========== 菜单栏 ========== */
QMenuBar {
    background-color: #0a0e27;
    color: #e2e8f0;
    padding: 4px 8px;
    border-bottom: 1px solid #1a2260;
    font-size: 17px;
}
QMenuBar::item {
    padding: 8px 16px;
    border-radius: 6px;
    background: transparent;
}
QMenuBar::item:selected {
    background-color: #4a6cf7;
    color: #ffffff;
}
QMenu {
    background-color: #111842;
    border: 1px solid #2a3480;
    border-radius: 8px;
    padding: 6px;
    font-size: 17px;
}
QMenu::item {
    padding: 10px 32px;
    border-radius: 6px;
    color: #e2e8f0;
}
QMenu::item:selected {
    background-color: #4a6cf7;
    color: #ffffff;
}
QMenu::separator {
    height: 1px; background: #1a2260; margin: 4px 12px;
}

/* ========== 对话框 ========== */
QDialog {
    background-color: #0d1233;
    color: #e2e8f0;
    font-size: 18px;
}
QMessageBox {
    background-color: #0d1233;
    font-size: 18px;
}
QMessageBox QLabel {
    color: #e2e8f0;
    font-size: 18px;
}
QMessageBox QPushButton {
    min-width: 90px;
    min-height: 34px;
    font-size: 17px;
    border-radius: 6px;
    padding: 6px 16px;
    background-color: #4a6cf7;
    color: #ffffff;
    border: none;
}
QMessageBox QPushButton:hover {
    background-color: #5b7bf8;
}

/* ========== 工具提示 ========== */
QToolTip {
    background-color: #111842;
    color: #e2e8f0;
    border: 1px solid #2a3480;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 16px;
}

/* ========== 滚动区域 ========== */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* ========== 日历弹窗 ========== */
QCalendarWidget {
    background-color: #111842;
    color: #e2e8f0;
    font-size: 16px;
}
QCalendarWidget QToolButton {
    color: #e2e8f0;
    background: #0f1540;
    border-radius: 4px;
    padding: 6px;
    font-size: 16px;
}
QCalendarWidget QMenu {
    background-color: #111842;
    color: #e2e8f0;
}

/* ========== QDialogButtonBox ========== */
QDialogButtonBox QPushButton {
    min-width: 100px;
    min-height: 36px;
    font-size: 16px;
    border-radius: 6px;
    padding: 8px 18px;
}
"""

LIGHT_THEME = DARK_TECH_THEME
