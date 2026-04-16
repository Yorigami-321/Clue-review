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

DARK_TECH_THEME = f"""

/* ========== 全局 ========== */
QWidget {{
    color: {C.TEXT_PRIMARY};
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: {F.GLOBAL}px;
}}
QMainWindow {{
    background-color: {C.BG_DARK};
}}

/* ========== 顶部标题栏 ========== */
QWidget#headerWidget {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C.BG_HEADER}, stop:1 {C.BG_DARKEST});
    border-radius: 12px;
    border: 1px solid {C.BORDER};
}}

/* ========== 侧边栏 ========== */
QWidget#sidebarWidget {{
    background-color: {C.SIDEBAR_BG};
    border-right: 1px solid {C.BORDER};
    border-radius: 0px;
}}

/* ========== 卡片 ========== */
QGroupBox {{
    font-weight: bold;
    font-size: {F.CARD_TITLE}px;
    color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER};
    border-radius: 12px;
    margin-top: 18px;
    padding: 20px 14px 14px 14px;
    background-color: {C.BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 10px;
    color: {C.ACCENT_CYAN};
    font-size: {F.CARD_TITLE}px;
}}

/* ========== 标签 ========== */
QLabel {{
    color: {C.TEXT_PRIMARY};
    background: transparent;
    font-size: {F.LABEL}px;
}}

/* ========== 输入框 ========== */
QTextEdit {{
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_PRIMARY};
    font-size: {F.INPUT}px;
    selection-background-color: {C.ACCENT_BLUE};
}}
QLineEdit {{
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_PRIMARY};
    font-size: {F.INPUT}px;
    min-height: 24px;
    selection-background-color: {C.ACCENT_BLUE};
}}
QSpinBox, QDateEdit {{
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_PRIMARY};
    font-size: {F.INPUT}px;
    min-height: 24px;
}}
QTextEdit:focus, QLineEdit:focus {{
    border: 1px solid {C.BORDER_FOCUS};
}}

/* ========== 下拉框 ========== */
QComboBox {{
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_PRIMARY};
    font-size: {F.INPUT}px;
    min-height: 24px;
}}
QComboBox:hover {{
    border: 1px solid {C.BORDER_LIGHT};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid {C.TEXT_SECONDARY};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER_LIGHT};
    color: {C.TEXT_PRIMARY};
    font-size: {F.COMBO_ITEM}px;
    selection-background-color: {C.ACCENT_BLUE};
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    padding: 8px 14px;
    min-height: 30px;
}}

# QComboBox {{
#     border: 1px solid {C.BORDER};
#     border-radius: 8px;
#     padding: 9px 14px;
#     background-color: {C.BG_INPUT};
#     color: {C.TEXT_PRIMARY};
#     font-size: {F.INPUT}px;
#     min-height: 24px;
# }}

# QComboBox QAbstractItemView {{
#     background-color: {C.BG_CARD};
#     alternate-background-color: {C.BG_INPUT};
#     border: 1px solid {C.BORDER_LIGHT};
#     color: {C.TEXT_PRIMARY};
#     font-size: {F.COMBO_ITEM}px;
#     selection-background-color: {C.ACCENT_BLUE};
#     selection-color: {C.TEXT_WHITE};
#     outline: none;
#     padding: 4px;
# }}

# QComboBox QAbstractItemView::item {{
#     color: {C.TEXT_PRIMARY};
#     background: transparent;
#     padding: 8px 14px;
#     min-height: 30px;
# }}

# QComboBox QAbstractItemView::item:selected {{
#     color: {C.TEXT_WHITE};
#     background-color: {C.ACCENT_BLUE};
# }}

/* ========== 复选框 ========== */
QCheckBox {{
    spacing: 10px;
    color: {C.TEXT_PRIMARY};
    font-size: {F.CHECKBOX}px;
}}
QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 5px;
    border: 2px solid {C.BORDER_LIGHT};
    background: {C.BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {C.ACCENT_BLUE};
    border-color: {C.ACCENT_BLUE};
}}

/* ========== 标签页 ========== */
QTabWidget::pane {{
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    background-color: {C.BG_CARD};
    top: -1px;
}}
QTabBar::tab {{
    padding: 10px 22px;
    margin-right: 3px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_SECONDARY};
    border: 1px solid {C.BORDER};
    border-bottom: none;
    font-size: {F.TAB}px;
}}
QTabBar::tab:selected {{
    background-color: {C.ACCENT_BLUE};
    color: {C.TEXT_WHITE};
    border-color: {C.ACCENT_BLUE};
    font-size: {F.TAB}px;
}}
QTabBar::tab:hover:!selected {{
    background-color: {C.BG_CARD_HOVER};
    color: {C.TEXT_PRIMARY};
}}

/* ========== 表格 ========== */
QTableWidget {{
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    background-color: {C.BG_CARD};
    alternate-background-color: {C.BG_INPUT};
    gridline-color: {C.BORDER};
    color: {C.TEXT_PRIMARY};
    font-size: {F.TABLE_CELL}px;
    selection-background-color: {C.ACCENT_BLUE};
    selection-color: {C.TEXT_WHITE};
}}
QHeaderView::section {{
    background-color: {C.BG_DARKEST};
    color: {C.ACCENT_CYAN};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {C.ACCENT_BLUE};
    font-weight: bold;
    font-size: {F.TABLE_HEADER}px;
}}
QTableWidget::item {{
    padding: 7px 8px;
    border-bottom: 1px solid {C.BORDER};
}}
QTableWidget::item:selected {{
    background-color: rgba(74, 108, 247, 0.3);
    color: {C.TEXT_WHITE};
}}

/* ========== 进度条 ========== */
QProgressBar {{
    border: none;
    border-radius: 6px;
    text-align: center;
    background-color: {C.BG_INPUT};
    color: {C.TEXT_PRIMARY};
    font-size: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C.ACCENT_BLUE}, stop:1 {C.ACCENT_CYAN});
    border-radius: 6px;
}}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {{
    height: 4px; background: {C.BG_INPUT}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {C.ACCENT_BLUE}; width: 16px; height: 16px;
    margin: -6px 0; border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {C.ACCENT_BLUE}; border-radius: 2px;
}}

/* ========== 滚动条 ========== */
QScrollBar:vertical {{
    background: {C.BG_DARK}; width: 8px; border-radius: 4px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER_LIGHT}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C.ACCENT_BLUE}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QScrollBar:horizontal {{
    background: {C.BG_DARK}; height: 8px; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {C.BORDER_LIGHT}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C.ACCENT_BLUE}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

/* ========== 状态栏 ========== */
QStatusBar {{
    background-color: {C.BG_HEADER};
    color: {C.TEXT_SECONDARY};
    padding: 4px 12px;
    border-top: 1px solid {C.BORDER};
    font-size: {F.STATUSBAR}px;
}}

/* ========== 菜单栏 ========== */
QMenuBar {{
    background-color: {C.BG_DARKEST};
    color: {C.TEXT_PRIMARY};
    padding: 4px 8px;
    border-bottom: 1px solid {C.BORDER};
    font-size: {F.MENUBAR}px;
}}
QMenuBar::item {{
    padding: 8px 16px;
    border-radius: 6px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {C.ACCENT_BLUE};
    color: {C.TEXT_WHITE};
}}
QMenu {{
    background-color: {C.BG_CARD};
    border: 1px solid {C.BORDER_LIGHT};
    border-radius: 8px;
    padding: 6px;
    font-size: {F.MENU_ITEM}px;
}}
QMenu::item {{
    padding: 10px 32px;
    border-radius: 6px;
    color: {C.TEXT_PRIMARY};
}}
QMenu::item:selected {{
    background-color: {C.ACCENT_BLUE};
    color: {C.TEXT_WHITE};
}}
QMenu::separator {{
    height: 1px; background: {C.BORDER}; margin: 4px 12px;
}}

/* ========== 对话框 ========== */
QDialog {{
    background-color: {C.BG_DARK};
    color: {C.TEXT_PRIMARY};
    font-size: {F.DIALOG}px;
}}
QMessageBox {{
    background-color: {C.BG_DARK};
    font-size: {F.MSGBOX}px;
}}
QMessageBox QLabel {{
    color: {C.TEXT_PRIMARY};
    font-size: {F.MSGBOX}px;
}}
QMessageBox QPushButton {{
    min-width: 90px;
    min-height: 34px;
    font-size: {F.MSGBOX_BTN}px;
    border-radius: 6px;
    padding: 6px 16px;
    background-color: {C.BTN_PRIMARY};
    color: {C.TEXT_WHITE};
    border: none;
}}
QMessageBox QPushButton:hover {{
    background-color: #5b7bf8;
}}

/* ========== 工具提示 ========== */
QToolTip {{
    background-color: {C.BG_CARD};
    color: {C.TEXT_PRIMARY};
    border: 1px solid {C.BORDER_LIGHT};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: {F.TOOLTIP}px;
}}

/* ========== 滚动区域 ========== */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ========== 日历弹窗 ========== */
QCalendarWidget {{
    background-color: {C.BG_CARD};
    color: {C.TEXT_PRIMARY};
    font-size: {F.CALENDAR}px;
}}
QCalendarWidget QToolButton {{
    color: {C.TEXT_PRIMARY};
    background: {C.BG_INPUT};
    border-radius: 4px;
    padding: 6px;
    font-size: {F.CALENDAR}px;
}}
QCalendarWidget QMenu {{
    background-color: {C.BG_CARD};
    color: {C.TEXT_PRIMARY};
}}

/* ========== QDialogButtonBox ========== */
QDialogButtonBox QPushButton {{
    min-width: 100px;
    min-height: 36px;
    font-size: {F.BUTTON}px;
    border-radius: 6px;
    padding: 8px 18px;
}}
"""

LIGHT_THEME = DARK_TECH_THEME
