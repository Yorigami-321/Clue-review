#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 — 涉检线索智能筛查工具 v6.0
深蓝科技风侧边栏布局
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox,
    QComboBox, QCheckBox, QLineEdit, QTabWidget, QStatusBar,
    QHeaderView, QFrame, QGridLayout, QDialog,
    QScrollArea, QAbstractItemView, QSystemTrayIcon,
    QMenu, QAction, QDateEdit, QDialogButtonBox,
    QStackedWidget, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QColor

from core.constants import (
    APP_NAME, APP_VERSION, ALL_STATUSES,
    STATUS_PENDING, STATUS_DONE, STATUS_ARCHIVED, STATUS_TRANSFERRED,
)
from core.keywords import DEFAULT_KEYWORDS
from core.database import DatabaseManager
from core.analyzer import TextAnalyzer
from core.cloud_api import load_config, save_config, call_cloud_api

from threads.whisper_thread import WhisperLoadThread
from threads.recorder_thread import AudioRecorderThread
from threads.transcribe_thread import AudioTranscribeThread
from threads.file_load_thread import FileLoadThread
from threads.batch_screen_thread import BatchScreenThread

from ui.theme import DARK_TECH_THEME, Colors
from ui.widgets import (
    primary_btn, secondary_btn, danger_btn,
    success_btn, warning_btn, gradient_btn,
    sidebar_btn, card, StatCard,
)
from ui.dialogs import ClueDetailDialog, LogDialog, StatisticsDialog
from PyQt5.QtWidgets import QApplication


logger = logging.getLogger("ClueScreener")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.whisper_model = None
        self.audio_data: Optional[bytes] = None
        self.recorder_thread: Optional[AudioRecorderThread] = None
        self.is_recording = False
        self._pending_df: Optional[pd.DataFrame] = None

        self.db = DatabaseManager()
        self.analyzer = TextAnalyzer()
        self.config = load_config()

        self._build_ui()
        self._build_menu()
        self.setStyleSheet(DARK_TECH_THEME)
        self._refresh_table()
        self._refresh_stats()
        self._setup_tray()

        logger.info("应用启动")
        self.db.log_operation("启动", "应用启动")

    # ==================================================================
    #  整体布局
    # ==================================================================
    def _build_ui(self):
        # self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        # self.setGeometry(60, 40, 1600, 960)
        # self.setMinimumSize(1200, 700)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        screen = QApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.9)
        h = int(screen.height() * 0.9)
        # 给一个上限，避免在大屏上过大
        w = min(w, 1500)
        h = min(h, 900)
        self.resize(w, h)
        # 最小尺寸也适当下调，避免小屏挤爆
        self.setMinimumSize(980, 620)
        central = QWidget()
        central.setStyleSheet(f"background-color: {Colors.BG_DARK};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ========== 左侧边栏 ==========
        sidebar = QWidget()
        sidebar.setObjectName("sidebarWidget")
        # sidebar.setFixedWidth(200)
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"""
            QWidget#sidebarWidget {{
                background-color: {Colors.SIDEBAR_BG};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(6)

        # Logo
        logo_label = QLabel("⚖️")
        logo_label.setFont(QFont("Segoe UI", 32))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        sb_layout.addWidget(logo_label)

        app_title = QLabel("涉检线索\n智能筛查")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setFont(QFont("Microsoft YaHei", 19, QFont.Bold))
        app_title.setStyleSheet(f"color: {Colors.TEXT_WHITE}; background: transparent; margin-bottom: 8px;")
        sb_layout.addWidget(app_title)

        sub_label = QLabel("Clue Screener AI")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px; background: transparent; margin-bottom: 20px;")
        sb_layout.addWidget(sub_label)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {Colors.BORDER}; max-height: 1px;")
        sb_layout.addWidget(sep)
        sb_layout.addSpacing(10)

        # 导航按钮
        self.nav_btns = {}
        nav_items = [
            ("dashboard",  "📊", "仪 表 盘"),
            ("voice",      "🎤", "语音识别"),
            ("llm",        "🤖", "LLM 设置"),
            ("keywords",   "📚", "关键词库"),
            ("logs",       "📋", "操作日志"),
        ]
        for key, icon, text in nav_items:
            btn = sidebar_btn(text, icon, active=(key == "dashboard"))
            btn.clicked.connect(lambda _, k=key: self._switch_page(k))
            sb_layout.addWidget(btn)
            self.nav_btns[key] = btn

        sb_layout.addStretch()

        # 版本号
        ver = QLabel(f"v{APP_VERSION}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px; background: transparent;")
        sb_layout.addWidget(ver)

        root.addWidget(sidebar)

        # ========== 右侧主内容区 ==========
        main_area = QWidget()
        main_area.setStyleSheet(f"background-color: {Colors.BG_DARK};")
        ma_layout = QVBoxLayout(main_area)
        ma_layout.setContentsMargins(0, 0, 0, 0)
        ma_layout.setSpacing(0)

        # 顶部栏
        header = QWidget()
        header.setObjectName("headerWidget")
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QWidget#headerWidget {{
                background-color: {Colors.BG_HEADER};
                border-bottom: 1px solid {Colors.BORDER};
                border-radius: 0px;
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        page_title = QLabel("仪表盘")
        page_title.setFont(QFont("Microsoft YaHei", 21, QFont.Bold))
        page_title.setStyleSheet(f"color: {Colors.TEXT_WHITE}; background: transparent;")
        self.page_title_label = page_title
        h_layout.addWidget(page_title)
        h_layout.addStretch()

        self.status_indicator = QLabel("● 系统就绪")
        self.status_indicator.setStyleSheet(f"""
            color: {Colors.ACCENT_GREEN};
            font-size: 16px;
            padding: 10px 18px;
            background: rgba(34,197,94,0.15);
            border: 1px solid rgba(34,197,94,0.3);
            border-radius: 16px;
        """)
        h_layout.addWidget(self.status_indicator)

        ma_layout.addWidget(header)

        # 堆叠页面
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background: transparent;")
        ma_layout.addWidget(self.stacked)

        # 页面0: 仪表盘（主操作界面）
        self.stacked.addWidget(self._build_dashboard_page())
        # 页面1: 语音识别
        self.stacked.addWidget(self._build_voice_page())
        # 页面2: LLM设置
        self.stacked.addWidget(self._build_llm_page())
        # 页面3: 关键词库
        self.stacked.addWidget(self._build_keyword_page())
        # 页面4: 操作日志
        self.stacked.addWidget(self._build_log_page())

        root.addWidget(main_area)

        # 状态栏
        self.sbar = QStatusBar()
        self.setStatusBar(self.sbar)
        self.sbar.showMessage("系统就绪")

    # ------------------------------------------------------------------
    #  侧边栏切换
    # ------------------------------------------------------------------
    def _switch_page(self, key: str):
        pages = {"dashboard": 0, "voice": 1, "llm": 2, "keywords": 3, "logs": 4}
        titles = {"dashboard": "仪表盘", "voice": "语音识别", "llm": "LLM 设置",
                  "keywords": "关键词库", "logs": "操作日志"}
        idx = pages.get(key, 0)
        self.stacked.setCurrentIndex(idx)
        self.page_title_label.setText(titles.get(key, ""))

        for k, btn in self.nav_btns.items():
            is_active = (k == key)
            bg = Colors.SIDEBAR_ACTIVE if is_active else "transparent"
            clr = Colors.TEXT_PRIMARY if is_active else Colors.TEXT_SECONDARY
            fw = "bold" if is_active else "normal"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {clr};
                    border: none; border-radius: 8px;
                    padding: 12px 16px; font-size: 20px;
                    font-weight: {fw}; text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SIDEBAR_HOVER};
                    color: {Colors.TEXT_PRIMARY};
                }}
            """)

        # 刷新日志页
        if key == "logs":
            self._refresh_log_table()

    # ==================================================================
    #  页面构建
    # ==================================================================

    def _build_dashboard_page(self) -> QWidget:
        """仪表盘：统计 + 导入筛查 + 搜索 + 表格 + 操作"""
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        # layout.setContentsMargins(24, 20, 24, 20)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # ---- 操作栏 ----
        op_row = QHBoxLayout()
        self.load_file_btn = primary_btn("📂  导入文件 (CSV/Excel)")
        self.load_file_btn.clicked.connect(self._load_file)
        op_row.addWidget(self.load_file_btn)

        self.file_info = QLabel("未加载文件")
        self.file_info.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 16px;")
        op_row.addWidget(self.file_info)
        op_row.addStretch()

        self.screen_btn = gradient_btn("🚀  开始智能筛查")
        self.screen_btn.setEnabled(False)
        self.screen_btn.clicked.connect(self._start_screen)
        op_row.addWidget(self.screen_btn)
        layout.addLayout(op_row)

        self.screen_progress = QProgressBar()
        self.screen_progress.setVisible(False)
        self.screen_progress.setFixedHeight(6)
        layout.addWidget(self.screen_progress)
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 15px;")
        layout.addWidget(self.progress_label)

        # ---- 统计卡片 ----
        title_label = QLabel("系统概览")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Colors.TEXT_WHITE};")
        layout.addWidget(title_label)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        self.stat_cards = {}

        card_defs = [
            ("total",       "📋", "总线索数",        "0", Colors.ACCENT_BLUE,   0, 0),
            ("avg",         "📈", "平均置信度",      "0%", Colors.ACCENT_CYAN,   0, 1),
            ("high",        "✅", "高置信度(≥80%)",  "0", Colors.ACCENT_GREEN,  0, 2),
            ("low",         "⚠️", "低置信度(<50%)",  "0", Colors.ACCENT_ORANGE, 0, 3),
            ("pending",     "🕐", "待处理",          "0", Colors.ACCENT_RED,    1, 0),
            ("done",        "✔",  "已处理",          "0", Colors.ACCENT_GREEN,  1, 1),
            ("archived",    "📦", "已归档",          "0", Colors.TEXT_SECONDARY, 1, 2),
            ("transferred", "↗",  "已移交",          "0", Colors.ACCENT_BLUE,   1, 3),
        ]
        for key, icon, label, val, color, r, c in card_defs:
            sc = StatCard(icon, label, val, color)
            stats_grid.addWidget(sc, r, c)
            self.stat_cards[key] = sc
        layout.addLayout(stats_grid)

        # ---- 搜索与筛选 ----
        filter_card = card("🔍  搜索与筛选")
        fl = QHBoxLayout(filter_card)
        fl.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索关键词...")
        self.search_input.returnPressed.connect(self._refresh_table)
        fl.addWidget(self.search_input, 2)

        fl.addWidget(self._lbl("类别:"))
        self.f_cat = QComboBox(); self.f_cat.addItem("全部")
        for c in DEFAULT_KEYWORDS: self.f_cat.addItem(c)
        self.f_cat.addItem("其他")
        self.f_cat.currentIndexChanged.connect(self._refresh_table)
        fl.addWidget(self.f_cat)

        fl.addWidget(self._lbl("等级:"))
        self.f_grade = QComboBox()
        self.f_grade.addItems(["全部","A","B","C","D","E"])
        self.f_grade.currentIndexChanged.connect(self._refresh_table)
        fl.addWidget(self.f_grade)

        fl.addWidget(self._lbl("状态:"))
        self.f_status = QComboBox(); self.f_status.addItem("全部")
        self.f_status.addItems(ALL_STATUSES)
        self.f_status.currentIndexChanged.connect(self._refresh_table)
        fl.addWidget(self.f_status)

        fl.addWidget(self._lbl("从:"))
        self.d_from = QDateEdit(); self.d_from.setCalendarPopup(True)
        self.d_from.setDate(QDate.currentDate().addMonths(-12))
        fl.addWidget(self.d_from)

        fl.addWidget(self._lbl("到:"))
        self.d_to = QDateEdit(); self.d_to.setCalendarPopup(True)
        self.d_to.setDate(QDate.currentDate())
        fl.addWidget(self.d_to)

        sbtn = primary_btn("🔍 搜索")
        sbtn.clicked.connect(self._refresh_table)
        fl.addWidget(sbtn)

        layout.addWidget(filter_card)

        # ---- 表格 ----
        table_title = QLabel("线索台账")
        table_title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        table_title.setStyleSheet(f"color: {Colors.TEXT_WHITE};")
        layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_dbl_click)
        self.table.setMinimumHeight(300)
        layout.addWidget(self.table, 1)

        # ---- 底部操作 ----
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        # 导出格式选择
        action_row.addWidget(self._lbl("导出格式:"))
        self.export_fmt = QComboBox()
        self.export_fmt.addItems(["CSV", "Excel", "PDF"])
        self.export_fmt.setFixedWidth(110)
        action_row.addWidget(self.export_fmt)

        self.export_btn = success_btn("💾  导出台账")
        self.export_btn.clicked.connect(self._export)
        action_row.addWidget(self.export_btn)

        cb = primary_btn("📊  统计图表")
        cb.clicked.connect(self._show_stats)
        action_row.addWidget(cb)

        bsb = warning_btn("📝  批量改状态")
        bsb.clicked.connect(self._batch_status)
        action_row.addWidget(bsb)

        db_ = danger_btn("🗑  删除选中")
        db_.clicked.connect(self._delete_sel)
        action_row.addWidget(db_)

        action_row.addStretch()

        clb = secondary_btn("清空数据库")
        clb.clicked.connect(self._clear_db)
        action_row.addWidget(clb)

        layout.addLayout(action_row)

        scroll.setWidget(inner)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0,0,0,0)
        page_layout.addWidget(scroll)
        return page

    def _build_voice_page(self) -> QWidget:
        """语音识别页面"""
        page = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        inner = QWidget(); inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        # layout.setSpacing(16)
        layout.setSpacing(10)


        # 模型加载
        mc = card("🎤  语音识别模型")
        mcl = QVBoxLayout(mc)
        row = QHBoxLayout()
        row.addWidget(self._lbl("Whisper 模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny","base","small","medium","large"])
        self.model_combo.setCurrentText(self.config.get("whisper_model","base"))
        row.addWidget(self.model_combo); row.addStretch()
        mcl.addLayout(row)
        self.load_model_btn = primary_btn("加载语音模型")
        self.load_model_btn.clicked.connect(self._load_whisper)
        mcl.addWidget(self.load_model_btn)
        self.model_status = QLabel("⏳ 模型未加载")
        self.model_status.setAlignment(Qt.AlignCenter)
        self.model_status.setStyleSheet(f"""
            color: {Colors.ACCENT_ORANGE};
            background: rgba(245,158,11,0.1);
            border: 1px solid rgba(245,158,11,0.3);
            padding: 10px; border-radius: 8px;
        """)
        mcl.addWidget(self.model_status)
        layout.addWidget(mc)

        # 录音
        rc = card("🎙️  录音与转写")
        rcl = QVBoxLayout(rc)
        self.record_btn = danger_btn("🎙️  开始录音")
        self.record_btn.clicked.connect(self._toggle_rec)
        rcl.addWidget(self.record_btn)
        self.rec_status = QLabel("⚪ 就绪")
        self.rec_status.setAlignment(Qt.AlignCenter)
        self.rec_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        rcl.addWidget(self.rec_status)
        self.volume_bar = QProgressBar()
        self.volume_bar.setMaximum(100); self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(False); self.volume_bar.setFixedHeight(6)
        rcl.addWidget(self.volume_bar)
        ub = secondary_btn("📁  选择音频文件")
        ub.clicked.connect(self._upload_audio)
        rcl.addWidget(ub)
        self.transcribe_result = QTextEdit()
        self.transcribe_result.setPlaceholderText("转写结果将显示在这里...")
        self.transcribe_result.setMinimumHeight(150)
        rcl.addWidget(self.transcribe_result)
        self.transcribe_btn = primary_btn("▶  开始转写")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self._transcribe)
        rcl.addWidget(self.transcribe_btn)
        layout.addWidget(rc)
        layout.addStretch()

        scroll.setWidget(inner)
        pl = QVBoxLayout(page); pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
        return page

    def _build_llm_page(self) -> QWidget:
        """LLM 配置页面"""
        page = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        inner = QWidget(); inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        lc = card("🤖  云端 LLM 增强分析设置")
        lcl = QVBoxLayout(lc)

        self.use_llm_cb = QCheckBox("启用 LLM 增强分析（对低置信度线索自动调用云端分析）")
        lcl.addWidget(self.use_llm_cb)
        lcl.addSpacing(10)

        lcl.addWidget(self._lbl("API 密钥:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入云端 API 密钥")
        self.api_key_input.setText(self.config.get("cloud_api_key",""))
        lcl.addWidget(self.api_key_input)

        lcl.addWidget(self._lbl("API 地址:"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://open.bigmodel.cn/api/paas/v4")
        self.api_url_input.setText(
            self.config.get("cloud_api_url","https://open.bigmodel.cn/api/paas/v4"))
        lcl.addWidget(self.api_url_input)

        lcl.addWidget(self._lbl("模型名称:"))
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("glm-4-flash / deepseek-chat / qwen-turbo")
        self.model_name_input.setText(self.config.get("cloud_model","glm-4-flash"))
        lcl.addWidget(self.model_name_input)

        lcl.addSpacing(10)
        br = QHBoxLayout()
        sb = primary_btn("💾  保存配置"); sb.clicked.connect(self._save_llm)
        br.addWidget(sb)
        tb = secondary_btn("🔗  测试连接"); tb.clicked.connect(self._test_cloud)
        br.addWidget(tb); br.addStretch()
        lcl.addLayout(br)

        layout.addWidget(lc)

        # 说明
        note = card("💡  使用说明")
        nl = QVBoxLayout(note)
        note_text = QLabel(
            "• 支持所有兼容 OpenAI 格式的 API（智谱GLM、DeepSeek、通义千问等）\n"
            "• 启用后，批量筛查时会对置信度<70%的线索自动调用 LLM 进行二次分析\n"
            "• LLM 返回的类别判断可修正关键词分类结果，提升准确率\n"
            "• API 密钥仅保存在本地 config.json，不会上传到任何服务器"
        )
        note_text.setWordWrap(True)
        note_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; line-height: 1.6;")
        nl.addWidget(note_text)
        layout.addWidget(note)

        layout.addStretch()
        scroll.setWidget(inner)
        pl = QVBoxLayout(page); pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
        return page

    def _build_keyword_page(self) -> QWidget:

        self.kw_tabs = QTabWidget()

        # 让标签页在空间不足时可滚动，不强行压缩
        self.kw_tabs.tabBar().setExpanding(False)
        self.kw_tabs.tabBar().setUsesScrollButtons(True)
        self.kw_tabs.tabBar().setElideMode(Qt.ElideRight)

        # 仅覆盖“关键词页”tab样式，避免受全局大字号挤压
        self.kw_tabs.setStyleSheet(f"""
            QTabBar::tab {{
                padding: 8px 14px;
                min-width: 96px;
                font-size: 16px;
            }}
            QTabBar::tab:selected {{
                font-size: 14px;
            }}
        """)

        """关键词库管理页面"""
        page = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        inner = QWidget(); inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        kc = card("📚  关键词库管理")
        kcl = QVBoxLayout(kc)
        self.kw_tabs = QTabWidget()
        self._kw_inputs = {}
        for cat, info in DEFAULT_KEYWORDS.items():
            tab = QWidget(); tl = QVBoxLayout(tab)
            desc = QLabel(f"📝 {info['description']}")
            desc.setWordWrap(True)
            desc.setStyleSheet(f"""
                color: {info['color']};
                padding: 8px;
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                border-left: 3px solid {info['color']};
            """)
            tl.addWidget(desc)
            kw_edit = QTextEdit()
            kw_edit.setText("，".join(info["keywords"]))
            kw_edit.setMinimumHeight(100)
            tl.addWidget(kw_edit)
            en_cb = QCheckBox("启用此分类")
            en_cb.setChecked(info["enabled"])
            tl.addWidget(en_cb)
            self._kw_inputs[cat] = (kw_edit, en_cb)
            sv = success_btn("保存")
            sv.clicked.connect(lambda _, c=cat: self._save_kw(c))
            tl.addWidget(sv)
            self.kw_tabs.addTab(tab, cat)
        kcl.addWidget(self.kw_tabs)
        rk = secondary_btn("🔄  重置所有关键词")
        rk.clicked.connect(self._reset_kw)
        kcl.addWidget(rk)
        layout.addWidget(kc)
        layout.addStretch()

        scroll.setWidget(inner)
        pl = QVBoxLayout(page); pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
        return page

    def _build_log_page(self) -> QWidget:
        """操作日志页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["时间", "操作", "详情"])
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setAlternatingRowColors(True)
        layout.addWidget(self.log_table)

        refresh_btn = secondary_btn("🔄  刷新日志")
        refresh_btn.clicked.connect(self._refresh_log_table)
        layout.addWidget(refresh_btn)
        return page

    def _refresh_log_table(self):
        logs = self.db.get_recent_logs(500)
        self.log_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.log_table.setItem(i, 0, QTableWidgetItem(log.get("timestamp","")))
            self.log_table.setItem(i, 1, QTableWidgetItem(log.get("action","")))
            self.log_table.setItem(i, 2, QTableWidgetItem(log.get("detail","")))

    # ------------------------------------------------------------------
    #  辅助
    # ------------------------------------------------------------------
    def _lbl(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 16px;")
        return lb

    # ==================================================================
    #  菜单
    # ==================================================================
    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("文件")
        a = QAction("打开文件", self); a.setShortcut("Ctrl+O")
        a.triggered.connect(self._load_file); fm.addAction(a)
        a2 = QAction("导出台账", self); a2.setShortcut("Ctrl+S")
        a2.triggered.connect(self._export); fm.addAction(a2)
        fm.addSeparator()
        a3 = QAction("退出", self); a3.setShortcut("Ctrl+Q")
        a3.triggered.connect(self.close); fm.addAction(a3)

        vm = mb.addMenu("查看")
        a4 = QAction("统计图表", self); a4.triggered.connect(self._show_stats); vm.addAction(a4)
        a5 = QAction("操作日志", self)
        a5.triggered.connect(lambda: self._switch_page("logs")); vm.addAction(a5)
        a6 = QAction("刷新", self); a6.setShortcut("F5")
        a6.triggered.connect(self._refresh_table); vm.addAction(a6)

        hm = mb.addMenu("帮助")
        a9 = QAction("关于", self); a9.triggered.connect(self._about); hm.addAction(a9)

    # ==================================================================
    #  系统托盘
    # ==================================================================
    # def _setup_tray(self):
    #     if QSystemTrayIcon.isSystemTrayAvailable():
    #         self.tray = QSystemTrayIcon(self)
    #         self.tray.setToolTip(APP_NAME)
    #         m = QMenu()
    #         m.addAction("显示").triggered.connect(self.showNormal)
    #         m.addAction("退出").triggered.connect(lambda: __import__("sys").exit())
    #         self.tray.setContextMenu(m)
    #         self.tray.activated.connect(
    #             lambda r: (self.showNormal(), self.activateWindow())
    #             if r == QSystemTrayIcon.DoubleClick else None)
    #         self.tray.show()

    # def changeEvent(self, e):
    #     if e.type() == e.Type.WindowStateChange and self.isMinimized():
    #         if hasattr(self, "tray"):
    #             self.hide()
    #             self.tray.showMessage(APP_NAME, "已最小化到托盘",
    #                                   QSystemTrayIcon.Information, 2000)
    #     super().changeEvent(e)
    
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QStyle

    def _setup_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        tray = QSystemTrayIcon(self)

        # 先用系统标准图标兜底，避免 No Icon set
        icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        if icon.isNull():
            return  # 没有图标就不启用托盘，避免最小化后“消失”

        tray.setIcon(icon)
        tray.setToolTip(APP_NAME)

        m = QMenu()
        m.addAction("显示").triggered.connect(self.showNormal)
        m.addAction("退出").triggered.connect(lambda: __import__("sys").exit())
        tray.setContextMenu(m)
        tray.activated.connect(
            lambda r: (self.showNormal(), self.activateWindow())
            if r == QSystemTrayIcon.DoubleClick else None
        )
        tray.show()
        self.tray = tray

    def changeEvent(self, e):
        if e.type() == e.Type.WindowStateChange and self.isMinimized():
            # 只有托盘已正确创建才隐藏到托盘
            if getattr(self, "tray", None) is not None:
                self.hide()
                self.tray.showMessage(APP_NAME, "已最小化到托盘", QSystemTrayIcon.Information, 2000)
        super().changeEvent(e)

    # ==================================================================
    #  Whisper
    # ==================================================================
    def _load_whisper(self):
        self.load_model_btn.setEnabled(False)
        self.model_status.setText("⏳ 正在加载模型...")
        self.model_status.setStyleSheet(f"""
            color: {Colors.ACCENT_ORANGE};
            background: rgba(245,158,11,0.1);
            border: 1px solid rgba(245,158,11,0.3);
            padding: 10px; border-radius: 8px;
        """)
        size = self.model_combo.currentText()
        self.config["whisper_model"] = size; save_config(self.config)
        self._wt = WhisperLoadThread(size)
        self._wt.progress.connect(lambda m: self.sbar.showMessage(m))
        self._wt.finished.connect(self._whisper_ok)
        self._wt.error.connect(self._whisper_err)
        self._wt.start()

    def _whisper_ok(self, model):
        self.whisper_model = model
        self.model_status.setText("✅ 语音识别模型已就绪")
        self.model_status.setStyleSheet(f"""
            color: {Colors.ACCENT_GREEN};
            background: rgba(34,197,94,0.1);
            border: 1px solid rgba(34,197,94,0.3);
            padding: 10px; border-radius: 8px;
        """)
        self.load_model_btn.setEnabled(True)
        self.transcribe_btn.setEnabled(True)
        self.db.log_operation("加载模型", f"Whisper {self.model_combo.currentText()}")

    def _whisper_err(self, err):
        self.model_status.setText(f"❌ 加载失败: {err[:50]}")
        self.model_status.setStyleSheet(f"""
            color: {Colors.ACCENT_RED};
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            padding: 10px; border-radius: 8px;
        """)
        self.load_model_btn.setEnabled(True)
        QMessageBox.warning(self, "失败", f"模型加载失败：{err}")

    # ==================================================================
    #  录音 / 转写
    # ==================================================================
    def _toggle_rec(self):
        if not self.is_recording:
            try:
                import pyaudio  # noqa
            except ImportError:
                QMessageBox.warning(self, "缺少依赖", "需要 pyaudio: pip install pyaudio"); return
            self.is_recording = True
            self.record_btn.setText("⏹️  停止录音")
            self.rec_status.setText("🔴 正在录音...")
            self.rec_status.setStyleSheet(f"color: {Colors.ACCENT_RED}; font-weight: bold;")
            self.recorder_thread = AudioRecorderThread()
            self.recorder_thread.recording_progress.connect(lambda s: self.rec_status.setText(s))
            self.recorder_thread.amplitude_update.connect(
                lambda a: self.volume_bar.setValue(int(min(a*500, 100))))
            self.recorder_thread.recording_finished.connect(self._rec_done)
            self.recorder_thread.start_recording()
        else:
            if self.recorder_thread: self.recorder_thread.stop_recording()
            self.is_recording = False
            self.record_btn.setText("🎙️  开始录音")
            self.rec_status.setText("⚪ 就绪")
            self.rec_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            self.volume_bar.setValue(0)

    def _rec_done(self, data):
        self.audio_data = data
        self.rec_status.setText(f"✅ 录音完成 ({len(data)/(16000*2):.1f}s)")
        self.rec_status.setStyleSheet(f"color: {Colors.ACCENT_GREEN};")
        self.transcribe_btn.setEnabled(True)
        self._transcribe()

    def _upload_audio(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择音频", "",
            "音频 (*.wav *.mp3 *.m4a *.flac *.ogg)")
        if p:
            with open(p, "rb") as f: self.audio_data = f.read()
            self.transcribe_result.setText(f"已加载: {os.path.basename(p)}")
            self.transcribe_btn.setEnabled(True)

    def _transcribe(self):
        if not self.audio_data:
            QMessageBox.warning(self, "提示", "请先录音或选择音频"); return
        if not self.whisper_model:
            QMessageBox.warning(self, "提示", "请先加载语音模型"); return
        self.transcribe_btn.setEnabled(False)
        self._tt = AudioTranscribeThread(self.audio_data, self.whisper_model)
        self._tt.progress.connect(lambda m: self.sbar.showMessage(m))
        self._tt.finished.connect(self._tr_done)
        self._tt.start()

    def _tr_done(self, result):
        raw, masked, ok = result
        if ok:
            cat, conf = self.analyzer.classify(masked)
            grade, _, desc = TextAnalyzer.get_grade(conf)
            icon = TextAnalyzer.get_grade_icon(grade)
            summary = self.analyzer.summarize(masked)
            self.transcribe_result.setText(
                f"【转写结果】{masked}\n\n"
                f"【分类】{cat} ({conf:.1%})\n"
                f"【等级】{icon}{grade}级 — {desc}\n"
                f"【摘要】{summary}")
            reply = QMessageBox.question(self, "添加到台账",
                f"分类: {cat}\n等级: {grade}级\n摘要: {summary}\n\n添加到台账？",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                h = TextAnalyzer.text_hash(raw)
                if self.db.check_duplicate(h):
                    QMessageBox.information(self, "提示", "已存在相同内容")
                else:
                    self.db.insert_clue(
                        raw_text=raw, masked_text=masked, category=cat,
                        confidence=conf, grade=grade, grade_icon=icon,
                        summary=summary, source="语音录入", text_hash=h)
                    self.db.log_operation("语音录入", f"{cat}/{grade}")
                    self._refresh_table(); self._refresh_stats()
                    QMessageBox.information(self, "成功", "已添加到台账")
        else:
            self.transcribe_result.setText(masked)
        self.transcribe_btn.setEnabled(True)

    # ==================================================================
    #  LLM
    # ==================================================================
    def _save_llm(self):
        self.config["cloud_api_key"] = self.api_key_input.text()
        self.config["cloud_api_url"] = self.api_url_input.text()
        self.config["cloud_model"] = self.model_name_input.text()
        save_config(self.config)
        QMessageBox.information(self, "保存成功", "云端配置已保存")

    def _test_cloud(self):
        k = self.api_key_input.text()
        if not k: QMessageBox.warning(self, "提示", "请输入 API 密钥"); return
        self.sbar.showMessage("正在测试连接...")
        r = call_cloud_api("你好，回复'连接成功'", k,
                           self.api_url_input.text(), self.model_name_input.text())
        if r:
            QMessageBox.information(self, "连接成功", f"云端回复: {r[:100]}")
        else:
            QMessageBox.warning(self, "连接失败", "请检查配置")

    # ==================================================================
    #  文件导入 & 批量筛查
    # ==================================================================
    def _load_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "数据 (*.csv *.xlsx *.xls)")
        if not p: return
        self.load_file_btn.setEnabled(False)
        self._flt = FileLoadThread(p)
        self._flt.progress.connect(lambda m: self.sbar.showMessage(m))
        self._flt.finished.connect(self._file_ok)
        self._flt.error.connect(self._file_err)
        self._flt.start()

    def _file_ok(self, df):
        self._pending_df = df
        self.file_info.setText(f"✅ 已加载 {len(df)} 条数据")
        self.file_info.setStyleSheet(f"color: {Colors.ACCENT_GREEN}; font-size: 12px;")
        self.load_file_btn.setEnabled(True)
        self.screen_btn.setEnabled(True)
        self.db.log_operation("导入文件", f"{len(df)} 条")

    def _file_err(self, err):
        self.load_file_btn.setEnabled(True)
        QMessageBox.critical(self, "失败", f"加载失败：{err}")

    def _start_screen(self):
        if self._pending_df is None:
            QMessageBox.warning(self, "提示", "请先导入文件"); return
        self.screen_btn.setEnabled(False)
        self.screen_progress.setVisible(True); self.screen_progress.setValue(0)
        self.progress_label.setVisible(True)

        existing = self.db.get_all_clues()
        eh = set(existing["text_hash"].dropna().tolist()) if not existing.empty else set()

        self._bst = BatchScreenThread(
            self._pending_df, self.analyzer,
            use_llm=self.use_llm_cb.isChecked(),
            api_key=self.api_key_input.text(),
            api_url=self.api_url_input.text(),
            model=self.model_name_input.text(),
            dup_threshold=self.config.get("duplicate_threshold", 0.6),
            existing_hashes=eh)
        self._bst.progress.connect(self._scr_prog)
        self._bst.finished.connect(self._scr_done)
        self._bst.start()

    def _scr_prog(self, cur, tot, msg):
        self.screen_progress.setValue(int(cur/max(tot,1)*100))
        self.progress_label.setText(msg)
        self.sbar.showMessage(msg)

    def _scr_done(self, records):
        self.screen_progress.setVisible(False)
        self.progress_label.setVisible(False)
        self.screen_btn.setEnabled(True)

        total_in = len(self._pending_df) if self._pending_df is not None else 0
        if records:
            self.db.insert_clues_batch(records)
            self.db.log_operation("批量筛查", f"新增{len(records)}条")

        skipped = total_in - len(records)
        self._pending_df = None
        self._refresh_table(); self._refresh_stats()
        QMessageBox.information(self, "筛查完成",
            f"✅ 新增: {len(records)} 条" +
            (f"\n跳过重复: {skipped} 条" if skipped > 0 else ""))

    # ==================================================================
    #  表格 & 统计
    # ==================================================================
    def _refresh_table(self):
        cat = self.f_cat.currentText() if hasattr(self,"f_cat") else "全部"
        grade = self.f_grade.currentText() if hasattr(self,"f_grade") else "全部"
        status = self.f_status.currentText() if hasattr(self,"f_status") else "全部"
        kw = self.search_input.text().strip() if hasattr(self,"search_input") else ""
        df_from = self.d_from.date().toString("yyyy-MM-dd") if hasattr(self,"d_from") else None
        df_to = self.d_to.date().toString("yyyy-MM-dd") if hasattr(self,"d_to") else None

        df = self.db.get_clues_filtered(
            category=cat if cat != "全部" else None,
            grade=grade if grade != "全部" else None,
            status=status if status != "全部" else None,
            keyword=kw or None, date_from=df_from, date_to=df_to)

        cols = ["id","grade_icon","grade","category","confidence",
                "status","masked_text","summary","source","created_at"]
        hdrs = ["ID","图标","等级","类别","置信度",
                "状态","脱敏内容","摘要","来源","创建时间"]

        self.table.setSortingEnabled(False)
        self.table.setColumnCount(len(hdrs))
        self.table.setHorizontalHeaderLabels(hdrs)

        mx = 2000; n = min(len(df), mx)
        self.table.setRowCount(n)

        gc = {"A":Colors.ACCENT_GREEN,"B":Colors.ACCENT_BLUE,
              "C":Colors.ACCENT_ORANGE,"D":"#f97316","E":Colors.ACCENT_RED}
        stc = {STATUS_PENDING:Colors.ACCENT_RED,"处理中":Colors.ACCENT_ORANGE,
               STATUS_DONE:Colors.ACCENT_GREEN,STATUS_ARCHIVED:Colors.TEXT_SECONDARY,
               STATUS_TRANSFERRED:Colors.ACCENT_BLUE}

        for i in range(n):
            row = df.iloc[i]
            for j, col in enumerate(cols):
                v = row.get(col, "")
                if col == "confidence":
                    d = f"{float(v):.1%}" if v else "0%"
                elif col == "masked_text":
                    s = str(v) if pd.notna(v) else ""
                    d = s[:80] + ("..." if len(s)>80 else "")
                else:
                    d = str(v) if pd.notna(v) else ""
                item = QTableWidgetItem(d)
                if col == "grade" and str(v) in gc:
                    item.setForeground(QColor(gc[str(v)]))
                if col == "status" and str(v) in stc:
                    item.setForeground(QColor(stc[str(v)]))
                if col == "id":
                    item.setData(Qt.UserRole, int(v) if v else 0)
                self.table.setItem(i, j, item)

        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        # self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        # for ci, w in [(0,50),(1,40),(2,45),(3,100),(4,70),(5,70)]:
        #     self.table.setColumnWidth(ci, w)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)

        # 文本长的两列继续自适应撑满
        hh.setSectionResizeMode(6, QHeaderView.Stretch)   # 脱敏内容
        hh.setSectionResizeMode(7, QHeaderView.Stretch)   # 摘要

        # 其余列给足宽度（按你现在的大字号）
        for ci, w in [
            (0, 70),   # ID
            (1, 60),   # 图标
            (2, 70),   # 等级
            (3, 130),  # 类别
            (4, 110),  # 置信度
            (5, 110),  # 状态
            (8, 120),  # 来源
            (9, 170),  # 创建时间
        ]:
            self.table.setColumnWidth(ci, w)
        self.table.setSortingEnabled(True)
        self.sbar.showMessage(f"共 {len(df)} 条线索" +
                              (f"（显示前{mx}条）" if n<len(df) else ""))

    def _refresh_stats(self):
        s = self.db.get_stats()
        self.stat_cards["total"].set_value(str(s["total"]))
        self.stat_cards["avg"].set_value(f"{s['avg_confidence']:.1%}")
        self.stat_cards["high"].set_value(str(s["high_confidence"]))
        self.stat_cards["low"].set_value(str(s["low_confidence"]))
        self.stat_cards["pending"].set_value(str(s["statuses"].get(STATUS_PENDING, 0)))
        self.stat_cards["done"].set_value(str(s["statuses"].get(STATUS_DONE, 0)))
        self.stat_cards["archived"].set_value(str(s["statuses"].get(STATUS_ARCHIVED, 0)))
        self.stat_cards["transferred"].set_value(str(s["statuses"].get(STATUS_TRANSFERRED, 0)))

    def _on_dbl_click(self, index):
        item = self.table.item(index.row(), 0)
        if not item: return
        cid = item.data(Qt.UserRole)
        if not cid: return
        clue = self.db.get_clue_by_id(cid)
        if not clue: return
        dlg = ClueDetailDialog(clue, self)
        dlg.status_changed.connect(lambda i,s: self.db.update_clue(i, status=s))
        if dlg.exec_() == QDialog.Accepted:
            self.db.update_clue(cid, status=dlg.clue["status"],
                                note=dlg.clue.get("note",""))
            self.db.log_operation("更新", f"ID={cid}")
            self._refresh_table(); self._refresh_stats()

    # ==================================================================
    #  操作
    # ==================================================================
    def _batch_status(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self, "提示", "请先选择行"); return
        ids = []
        for idx in sel:
            item = self.table.item(idx.row(), 0)
            if item:
                cid = item.data(Qt.UserRole)
                if cid: ids.append(cid)
        if not ids: return
        dlg = QDialog(self); dlg.setWindowTitle(f"批量修改 ({len(ids)} 条)")
        lo = QVBoxLayout(dlg)
        lo.addWidget(QLabel(f"将 {len(ids)} 条线索状态改为:"))
        combo = QComboBox(); combo.addItems(ALL_STATUSES)
        lo.addWidget(combo)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        lo.addWidget(bb)
        if dlg.exec_() == QDialog.Accepted:
            ns = combo.currentText()
            for cid in ids: self.db.update_clue(cid, status=ns)
            self.db.log_operation("批量改状态", f"{len(ids)}条->{ns}")
            self._refresh_table(); self._refresh_stats()

    def _delete_sel(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self, "提示", "请先选择行"); return
        ids = []
        for idx in sel:
            item = self.table.item(idx.row(), 0)
            if item:
                cid = item.data(Qt.UserRole)
                if cid: ids.append(cid)
        if QMessageBox.question(self, "确认", f"删除 {len(ids)} 条？",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            for cid in ids: self.db.delete_clue(cid)
            self.db.log_operation("删除", f"{len(ids)}条")
            self._refresh_table(); self._refresh_stats()

    def _clear_db(self):
        if QMessageBox.question(self, "确认", "⚠️ 清空所有数据？",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_all()
            self.db.log_operation("清空数据库", "")
            self._refresh_table(); self._refresh_stats()

    # ==================================================================
    #  导出
    # ==================================================================
    def _export(self):
        df = self.db.get_all_clues()
        if df.empty: QMessageBox.warning(self, "提示", "无数据"); return
        fmt = self.export_fmt.currentText()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt == "CSV":
            p, _ = QFileDialog.getSaveFileName(self,"导出",f"涉检线索_{ts}.csv","CSV (*.csv)")
            if p:
                df.to_csv(p, index=False, encoding="utf-8-sig")
                self.db.log_operation("导出CSV", p)
                QMessageBox.information(self, "成功", f"已导出: {p}")
        elif fmt == "Excel":
            p, _ = QFileDialog.getSaveFileName(self,"导出",f"涉检线索_{ts}.xlsx","Excel (*.xlsx)")
            if p:
                df.to_excel(p, index=False, engine="openpyxl")
                self.db.log_operation("导出Excel", p)
                QMessageBox.information(self, "成功", f"已导出: {p}")
        elif fmt == "PDF":
            self._export_pdf(df)

    def _export_pdf(self, df):
        try:
            from reportlab.lib import colors as rlc
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            QMessageBox.warning(self, "缺少依赖", "需要 reportlab: pip install reportlab"); return

        p, _ = QFileDialog.getSaveFileName(self, "导出PDF",
            f"涉检线索_{datetime.now():%Y%m%d_%H%M%S}.pdf", "PDF (*.pdf)")
        if not p: return
        try:
            bf = "Helvetica"
            for fp in ["C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont("CNFont", fp)); bf = "CNFont"; break
            doc = SimpleDocTemplate(p, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            ts_ = ParagraphStyle("T", parent=styles["Title"], fontName=bf, fontSize=18)
            ns = ParagraphStyle("N", parent=styles["Normal"], fontName=bf, fontSize=8)
            elements = [Paragraph("涉检线索智能筛查台账", ts_), Spacer(1, 8*mm)]
            stats = self.db.get_stats()
            elements.append(Paragraph(
                f"总数:{stats['total']} | 平均置信度:{stats['avg_confidence']:.1%} "
                f"| 导出:{datetime.now():%Y-%m-%d %H:%M}", ns))
            elements.append(Spacer(1, 5*mm))
            header = ["ID","等级","类别","置信度","状态","摘要","时间"]
            data = [header]
            for _, row in df.head(500).iterrows():
                data.append([
                    str(row.get("id","")), str(row.get("grade","")),
                    str(row.get("category","")),
                    f"{float(row.get('confidence',0)):.1%}",
                    str(row.get("status","")),
                    Paragraph(str(row.get("summary",""))[:60], ns),
                    str(row.get("created_at",""))[:16]])
            tbl = Table(data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0), rlc.HexColor("#2c7da0")),
                ("TEXTCOLOR",(0,0),(-1,0), rlc.white),
                ("FONTNAME",(0,0),(-1,-1), bf),
                ("FONTSIZE",(0,0),(-1,-1), 7),
                ("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("GRID",(0,0),(-1,-1), 0.5, rlc.grey),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),
                 [rlc.white, rlc.HexColor("#f8f9fa")])]))
            elements.append(tbl); doc.build(elements)
            self.db.log_operation("导出PDF", p)
            QMessageBox.information(self, "成功", f"已导出: {p}")
        except Exception as e:
            QMessageBox.critical(self, "失败", f"PDF导出失败: {e}")

    # ==================================================================
    #  其他
    # ==================================================================
    def _show_stats(self):
        if self.db.get_all_clues().empty:
            QMessageBox.warning(self, "提示", "暂无数据"); return
        StatisticsDialog(self.db, self).show()

    def _show_logs(self):
        LogDialog(self.db, self).exec_()

    def _save_kw(self, cat):
        edit, cb = self._kw_inputs[cat]
        kws = [k.strip() for k in re.split(r"[,，]", edit.toPlainText()) if k.strip()]
        DEFAULT_KEYWORDS[cat]["keywords"] = kws
        DEFAULT_KEYWORDS[cat]["enabled"] = cb.isChecked()
        self.analyzer = TextAnalyzer(DEFAULT_KEYWORDS)
        self.db.log_operation("更新关键词", f"{cat}:{len(kws)}个")
        QMessageBox.information(self, "成功", f'"{cat}"已更新({len(kws)}个)')

    def _reset_kw(self):
        if QMessageBox.question(self, "确认", "重置所有关键词？",
                QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        for cat, (edit, cb) in self._kw_inputs.items():
            edit.setText("，".join(DEFAULT_KEYWORDS[cat]["keywords"]))
            cb.setChecked(True); DEFAULT_KEYWORDS[cat]["enabled"] = True
        self.analyzer = TextAnalyzer(DEFAULT_KEYWORDS)

    def _about(self):
        QMessageBox.about(self, "关于",
            f"{APP_NAME}\n版本 {APP_VERSION}\n\n"
            "• Whisper 语音转文字 + 实时录音\n"
            "• 9大类关键词 + TF-IDF 加权分类\n"
            "• 五级线索分级 (A/B/C/D/E)\n"
            "• 云端 LLM 增强分析\n"
            "• SQLite 持久化 + 全局搜索\n"
            "• 重复检测 + 状态跟踪\n"
            "• 统计图表 + 词云\n"
            "• CSV / Excel / PDF 导出\n\n"
            "数据安全 · 完全本地部署")
