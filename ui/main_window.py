#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口 — 涉检线索智能筛查工具 v6.0
深蓝科技风侧边栏布局
"""

import os
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle, QSystemTrayIcon, QMenu, QAction, QDialog, QDialogButtonBox, QComboBox, QLabel
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QStatusBar,
    QHeaderView, QFrame, QApplication, QStackedWidget,
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

from ui.theme import DARK_TECH_THEME, Colors
from ui.dialogs import ClueDetailDialog, LogDialog, StatisticsDialog
from ui.widgets import sidebar_btn

# 导入页面模块
from ui.pages import DashboardPage, VoicePage, LLMPage, KeywordPage, LogPage
# 导入服务模块
from ui.services import ClueService, ExportService


logger = logging.getLogger("ClueScreener")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_data: Optional[bytes] = None
        self.is_recording = False

        self.db = DatabaseManager()
        self.analyzer = TextAnalyzer()
        self.config = load_config()

        # 初始化服务
        self.clue_service = ClueService(self.db, self.analyzer)
        self.export_service = ExportService(self.db)

        # 初始化页面
        self._init_pages()
        
        self._build_ui()
        self._build_menu()
        self.setStyleSheet(DARK_TECH_THEME)
        self._refresh_table()
        self._refresh_stats()
        self._setup_tray()

        logger.info("应用启动")
        self.db.log_operation("启动", "应用启动")

    def _init_pages(self):
        """初始化所有页面"""
        # 初始化仪表盘页面
        self.dashboard_page = DashboardPage()
        self.dashboard_page.load_file_clicked.connect(self._load_file)
        self.dashboard_page.screen_clicked.connect(self._start_screen)
        self.dashboard_page.export_clicked.connect(self._export)
        self.dashboard_page.show_stats_clicked.connect(self._show_stats)
        self.dashboard_page.batch_status_clicked.connect(self._batch_status)
        self.dashboard_page.delete_selected_clicked.connect(self._delete_sel)
        self.dashboard_page.clear_db_clicked.connect(self._clear_db)
        
        # 初始化语音识别页面
        self.voice_page = VoicePage()
        self.voice_page.load_model_clicked.connect(self._load_whisper)
        self.voice_page.toggle_record_clicked.connect(self._toggle_rec)
        self.voice_page.upload_audio_clicked.connect(self._upload_audio)
        self.voice_page.transcribe_clicked.connect(self._transcribe)
        
        # 初始化LLM设置页面
        self.llm_page = LLMPage()
        self.llm_page.save_config_clicked.connect(self._save_llm)
        self.llm_page.test_cloud_clicked.connect(self._test_cloud)
        
        # 初始化关键词库页面
        self.keyword_page = KeywordPage()
        self.keyword_page.save_keywords_clicked.connect(self._save_kw)
        self.keyword_page.reset_keywords_clicked.connect(self._reset_kw)
        
        # 初始化操作日志页面
        self.log_page = LogPage()
        self.log_page.refresh_logs_clicked.connect(self._refresh_log_table)
        
        # 连接服务信号
        self.clue_service.file_loaded.connect(self._file_ok)
        self.clue_service.file_load_error.connect(self._file_err)
        self.clue_service.progress_updated.connect(lambda m: self.sbar.showMessage(m))
        
        # 设置初始值
        self.voice_page.set_model_combo_text(self.config.get("whisper_model", "base"))
        self.llm_page.set_api_key(self.config.get("cloud_api_key", ""))
        self.llm_page.set_api_url(self.config.get("cloud_api_url", "https://open.bigmodel.cn/api/paas/v4"))
        self.llm_page.set_model_name(self.config.get("cloud_model", "glm-4-flash"))

    # ==================================================================
    #  整体布局
    # ==================================================================
    def _build_ui(self):
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
        self.stacked.addWidget(self.dashboard_page)
        # 页面1: 语音识别
        self.stacked.addWidget(self.voice_page)
        # 页面2: LLM设置
        self.stacked.addWidget(self.llm_page)
        # 页面3: 关键词库
        self.stacked.addWidget(self.keyword_page)
        # 页面4: 操作日志
        self.stacked.addWidget(self.log_page)

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
    def _load_whisper(self, model_size):
        """加载Whisper模型"""
        self.voice_page.set_load_model_btn_enabled(False)
        self.voice_page.set_model_status("⏳ 正在加载模型...")
        
        self.config["whisper_model"] = model_size
        save_config(self.config)
        
        # 连接服务信号
        self.clue_service.whisper_loaded.connect(self._whisper_ok)
        self.clue_service.whisper_error.connect(self._whisper_err)
        self.clue_service.progress_updated.connect(lambda m: self.sbar.showMessage(m))
        
        self.clue_service.load_whisper(model_size)

    def _whisper_ok(self, model):
        """Whisper模型加载成功"""
        self.voice_page.set_model_status("✅ 语音识别模型已就绪", is_success=True)
        self.voice_page.set_load_model_btn_enabled(True)
        self.voice_page.set_transcribe_btn_enabled(True)
        self.db.log_operation("加载模型", f"Whisper {self.voice_page.model_combo.currentText()}")

    def _whisper_err(self, err):
        """Whisper模型加载失败"""
        self.voice_page.set_model_status(f"❌ 加载失败: {err[:50]}", is_error=True)
        self.voice_page.set_load_model_btn_enabled(True)
        QMessageBox.warning(self, "失败", f"模型加载失败：{err}")

    # ==================================================================
    #  录音 / 转写
    # ==================================================================
    def _toggle_rec(self):
        """切换录音状态"""
        if not self.is_recording:
            try:
                import pyaudio  # noqa
            except ImportError:
                QMessageBox.warning(self, "缺少依赖", "需要 pyaudio: pip install pyaudio"); return
            self.is_recording = True
            self.voice_page.set_record_btn_text("⏹️  停止录音")
            self.voice_page.set_rec_status("🔴 正在录音...", is_recording=True)
            
            # 连接服务信号
            self.clue_service.recording_progress.connect(lambda s: self.voice_page.set_rec_status(s, is_recording=True))
            self.clue_service.recording_finished.connect(self._rec_done)
            
            self.clue_service.start_recording()
        else:
            self.clue_service.stop_recording()
            self.is_recording = False
            self.voice_page.set_record_btn_text("🎙️  开始录音")
            self.voice_page.set_rec_status("⚪ 就绪")
            self.voice_page.set_volume_value(0)

    def _rec_done(self, data):
        """录音完成"""
        self.audio_data = data
        self.voice_page.set_rec_status(f"✅ 录音完成 ({len(data)/(16000*2):.1f}s)", is_success=True)
        self.voice_page.set_transcribe_btn_enabled(True)
        self._transcribe()

    def _upload_audio(self):
        """上传音频文件"""
        p, _ = QFileDialog.getOpenFileName(self, "选择音频", "",
            "音频 (*.wav *.mp3 *.m4a *.flac *.ogg)")
        if p:
            with open(p, "rb") as f: self.audio_data = f.read()
            self.voice_page.set_transcribe_result(f"已加载: {os.path.basename(p)}")
            self.voice_page.set_transcribe_btn_enabled(True)

    def _transcribe(self):
        """转写音频"""
        if not self.audio_data:
            QMessageBox.warning(self, "提示", "请先录音或选择音频"); return
        
        self.voice_page.set_transcribe_btn_enabled(False)
        
        # 连接服务信号
        self.clue_service.transcribe_finished.connect(self._tr_done)
        self.clue_service.progress_updated.connect(lambda m: self.sbar.showMessage(m))
        
        self.clue_service.transcribe(self.audio_data)

    def _tr_done(self, raw, masked, ok):
        """转写完成"""
        if ok:
            cat, conf = self.analyzer.classify(masked)
            grade, _, desc = TextAnalyzer.get_grade(conf)
            icon = TextAnalyzer.get_grade_icon(grade)
            summary = self.analyzer.summarize(masked)
            self.voice_page.set_transcribe_result(
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
            self.voice_page.set_transcribe_result(masked)
        self.voice_page.set_transcribe_btn_enabled(True)

    # ==================================================================
    #  LLM
    # ==================================================================
    def _save_llm(self, api_key, api_url, model, use_llm):
        """保存LLM配置"""
        self.config["cloud_api_key"] = api_key
        self.config["cloud_api_url"] = api_url
        self.config["cloud_model"] = model
        save_config(self.config)
        QMessageBox.information(self, "保存成功", "云端配置已保存")

    def _test_cloud(self, api_key, api_url, model):
        """测试云端连接"""
        if not api_key: QMessageBox.warning(self, "提示", "请输入 API 密钥"); return
        self.sbar.showMessage("正在测试连接...")
        r = call_cloud_api("你好，回复'连接成功'", api_key, api_url, model)
        if r:
            QMessageBox.information(self, "连接成功", f"云端回复: {r[:100]}")
        else:
            QMessageBox.warning(self, "连接失败", "请检查配置")

    # ==================================================================
    #  文件导入 & 批量筛查
    # ==================================================================
    def _load_file(self):
        """加载文件"""
        p, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "数据 (*.csv *.xlsx *.xls)")
        if not p: return
        
        self.dashboard_page.load_file_btn.setEnabled(False)
        self.clue_service.load_file(p)

    def _file_ok(self, df):
        """文件加载成功"""
        self.dashboard_page.set_file_info(f"✅ 已加载 {len(df)} 条数据", is_success=True)
        self.dashboard_page.load_file_btn.setEnabled(True)
        self.dashboard_page.set_screen_btn_enabled(True)
        self.db.log_operation("导入文件", f"{len(df)} 条")
        
        # 将加载的数据插入到数据库中
        if df is not None and not df.empty:
            # 将DataFrame转换为字典列表
            records = []
            for _, row in df.iterrows():
                raw_text = str(row.get('原始内容', '')) if pd.notna(row.get('原始内容')) else ''
                masked_text = str(row.get('脱敏内容', '')) if pd.notna(row.get('脱敏内容')) else ''
                
                # 使用analyzer进行分类和分级
                category, confidence = self.analyzer.classify(masked_text)
                grade, _, desc = TextAnalyzer.get_grade(confidence)
                grade_icon = TextAnalyzer.get_grade_icon(grade)
                summary = self.analyzer.summarize(masked_text)
                text_hash = TextAnalyzer.text_hash(raw_text)
                
                # 检查是否重复
                if not self.db.check_duplicate(text_hash):
                    record = {
                        'raw_text': raw_text,
                        'masked_text': masked_text,
                        'category': category,
                        'confidence': confidence,
                        'grade': grade,
                        'grade_icon': grade_icon,
                        'summary': summary,
                        'status': '待处理',
                        'source': '文件导入',
                        'text_hash': text_hash
                    }
                    records.append(record)
            
            # 批量插入数据库
            if records:
                self.db.insert_clues_batch(records)
                self.db.log_operation("文件数据入库", f"{len(records)} 条")
                
                # 刷新表格和统计数据
                self._refresh_table()
                self._refresh_stats()
                
                QMessageBox.information(self, "导入成功", f"已导入 {len(records)} 条数据到台账")
            else:
                QMessageBox.information(self, "提示", "所有数据已存在，无需重复导入")

    def _file_err(self, err):
        """文件加载失败"""
        self.dashboard_page.load_file_btn.setEnabled(True)
        QMessageBox.critical(self, "失败", f"加载失败：{err}")

    def _start_screen(self):
        """开始批量筛查"""
        # 连接服务信号
        self.clue_service.screen_progress.connect(self._scr_prog)
        self.clue_service.screen_finished.connect(self._scr_done)
        
        self.dashboard_page.set_screen_btn_enabled(False)
        self.dashboard_page.set_screen_progress_visible(True)
        
        # 获取LLM配置
        use_llm = True  # 默认启用
        api_key = self.config.get("cloud_api_key", "")
        api_url = self.config.get("cloud_api_url", "https://open.bigmodel.cn/api/paas/v4")
        model = self.config.get("cloud_model", "glm-4-flash")
        
        self.clue_service.start_screen(use_llm, api_key, api_url, model)

    def _scr_prog(self, cur, tot, msg):
        """筛查进度更新"""
        # 这里可以添加进度条更新逻辑
        self.sbar.showMessage(msg)

    def _scr_done(self, records):
        """筛查完成"""
        self.dashboard_page.set_screen_progress_visible(False)
        self.dashboard_page.set_screen_btn_enabled(True)

        total_in = len(self.clue_service.get_pending_df()) if self.clue_service.get_pending_df() is not None else 0
        if records:
            self.db.insert_clues_batch(records)
            self.db.log_operation("批量筛查", f"新增{len(records)}条")

        skipped = total_in - len(records)
        self._refresh_table(); self._refresh_stats()
        QMessageBox.information(self, "筛查完成",
            f"✅ 新增: {len(records)} 条" +
            (f"\n跳过重复: {skipped} 条" if skipped > 0 else ""))

    # ==================================================================
    #  表格 & 统计
    # ==================================================================
    def _refresh_table(self):
        """刷新表格"""
        # 获取筛选条件
        cat = self.dashboard_page.f_cat.currentText() if hasattr(self.dashboard_page, "f_cat") else "全部"
        grade = self.dashboard_page.f_grade.currentText() if hasattr(self.dashboard_page, "f_grade") else "全部"
        status = self.dashboard_page.f_status.currentText() if hasattr(self.dashboard_page, "f_status") else "全部"
        kw = self.dashboard_page.search_input.text().strip() if hasattr(self.dashboard_page, "search_input") else ""
        df_from = self.dashboard_page.d_from.date().toString("yyyy-MM-dd") if hasattr(self.dashboard_page, "d_from") else None
        df_to = self.dashboard_page.d_to.date().toString("yyyy-MM-dd") if hasattr(self.dashboard_page, "d_to") else None

        df = self.db.get_clues_filtered(
            category=cat if cat != "全部" else None,
            grade=grade if grade != "全部" else None,
            status=status if status != "全部" else None,
            keyword=kw or None, date_from=df_from, date_to=df_to)

        # 表格更新逻辑
        table = self.dashboard_page.table
        cols = ["id","grade_icon","grade","category","confidence",
                "status","masked_text","summary","source","created_at"]
        hdrs = ["ID","图标","等级","类别","置信度",
                "状态","脱敏内容","摘要","来源","创建时间"]

        table.setSortingEnabled(False)
        table.setColumnCount(len(hdrs))
        table.setHorizontalHeaderLabels(hdrs)

        mx = 2000; n = min(len(df), mx)
        table.setRowCount(n)

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
                table.setItem(i, j, item)

        hh = table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)

        # 文本长的两列继续自适应撑满
        hh.setSectionResizeMode(6, QHeaderView.Stretch)   # 脱敏内容
        hh.setSectionResizeMode(7, QHeaderView.Stretch)   # 摘要

        # 其余列给足宽度
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
            table.setColumnWidth(ci, w)
        table.setSortingEnabled(True)
        self.sbar.showMessage(f"共 {len(df)} 条线索" +
                              (f"（显示前{mx}条）" if n<len(df) else ""))

    def _refresh_stats(self):
        """刷新统计数据"""
        s = self.db.get_stats()
        self.dashboard_page.update_stats(s)

    def _on_dbl_click(self, index):
        """双击表格行"""
        table = self.dashboard_page.table
        item = table.item(index.row(), 0)
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
        """批量修改状态"""
        table = self.dashboard_page.table
        sel = table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self, "提示", "请先选择行"); return
        ids = []
        for idx in sel:
            item = table.item(idx.row(), 0)
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
        """删除选中"""
        table = self.dashboard_page.table
        sel = table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self, "提示", "请先选择行"); return
        ids = []
        for idx in sel:
            item = table.item(idx.row(), 0)
            if item:
                cid = item.data(Qt.UserRole)
                if cid: ids.append(cid)
        if QMessageBox.question(self, "确认", f"删除 {len(ids)} 条？",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            for cid in ids: self.db.delete_clue(cid)
            self.db.log_operation("删除", f"{len(ids)}条")
            self._refresh_table(); self._refresh_stats()

    def _clear_db(self):
        """清空数据库"""
        if QMessageBox.question(self, "确认", "⚠️ 清空所有数据？",
                QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_all()
            self.db.log_operation("清空数据库", "")
            self._refresh_table(); self._refresh_stats()

    # ==================================================================
    #  导出
    # ==================================================================
    def _export(self):
        """导出数据"""
        df = self.db.get_all_clues()
        if df.empty: QMessageBox.warning(self, "提示", "无数据"); return
        fmt = self.dashboard_page.export_fmt.currentText()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 连接服务信号
        self.export_service.export_success.connect(lambda p: QMessageBox.information(self, "成功", f"已导出: {p}"))
        self.export_service.export_error.connect(lambda e: QMessageBox.warning(self, "失败", e))
        
        if fmt == "CSV":
            p, _ = QFileDialog.getSaveFileName(self,"导出",f"涉检线索_{ts}.csv","CSV (*.csv)")
            if p:
                self.export_service.export_csv(p)
                self.db.log_operation("导出CSV", p)
        elif fmt == "Excel":
            p, _ = QFileDialog.getSaveFileName(self,"导出",f"涉检线索_{ts}.xlsx","Excel (*.xlsx)")
            if p:
                self.export_service.export_excel(p)
                self.db.log_operation("导出Excel", p)
        elif fmt == "PDF":
            p, _ = QFileDialog.getSaveFileName(self, "导出PDF",
                f"涉检线索_{ts}.pdf", "PDF (*.pdf)")
            if p:
                self.export_service.export_pdf(p)
                self.db.log_operation("导出PDF", p)

    # ==================================================================
    #  其他
    # ==================================================================
    def _show_stats(self):
        """显示统计图表"""
        if self.db.get_all_clues().empty:
            QMessageBox.warning(self, "提示", "暂无数据"); return
        StatisticsDialog(self.db, self).show()

    def _show_logs(self):
        """显示操作日志"""
        LogDialog(self.db, self).exec_()

    def _save_kw(self, category, keywords, enabled):
        """保存关键词"""
        DEFAULT_KEYWORDS[category]["keywords"] = keywords
        DEFAULT_KEYWORDS[category]["enabled"] = enabled
        self.analyzer = TextAnalyzer(DEFAULT_KEYWORDS)
        self.db.log_operation("更新关键词", f"{category}:{len(keywords)}个")
        QMessageBox.information(self, "成功", f'"{category}"已更新({len(keywords)}个)')

    def _reset_kw(self):
        """重置关键词"""
        if QMessageBox.question(self, "确认", "重置所有关键词？",
                QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        self.keyword_page.reset_keywords()
        self.analyzer = TextAnalyzer(DEFAULT_KEYWORDS)

    def _about(self):
        """关于"""
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

    def _refresh_log_table(self):
        """刷新日志表格"""
        logs = self.db.get_recent_logs(500)
        self.log_page.update_logs(logs)
