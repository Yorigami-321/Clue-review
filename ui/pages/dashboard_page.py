from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ui.widgets import primary_btn, secondary_btn, danger_btn, success_btn, warning_btn, gradient_btn, card, StatCard
from ui.theme import Colors
from core.constants import ALL_STATUSES
from core.keywords import DEFAULT_KEYWORDS


class DashboardPage(QWidget):
    """仪表盘页面 - 仅负责 UI 构建和事件转发"""
    
    # 信号定义
    load_file_clicked = pyqtSignal()
    screen_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    show_stats_clicked = pyqtSignal()
    batch_status_clicked = pyqtSignal()
    delete_selected_clicked = pyqtSignal()
    clear_db_clicked = pyqtSignal()
    table_double_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建仪表盘页面UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # ---- 操作栏 ----
        op_row = QHBoxLayout()
        self.load_file_btn = primary_btn("📂  导入文件 (CSV/Excel)")
        self.load_file_btn.clicked.connect(self.load_file_clicked.emit)
        op_row.addWidget(self.load_file_btn)

        self.file_info = QLabel("未加载文件")
        self.file_info.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 16px;")
        op_row.addWidget(self.file_info)
        op_row.addStretch()

        self.screen_btn = gradient_btn("🚀  开始智能筛查")
        self.screen_btn.setEnabled(False)
        self.screen_btn.clicked.connect(self.screen_clicked.emit)
        op_row.addWidget(self.screen_btn)
        layout.addLayout(op_row)

        self.screen_progress = QWidget()  # 占位，由MainWindow控制
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
        fl.addWidget(self.search_input, 2)

        fl.addWidget(self._lbl("类别:"))
        self.f_cat = QComboBox(); self.f_cat.addItem("全部")
        for c in DEFAULT_KEYWORDS: self.f_cat.addItem(c)
        self.f_cat.addItem("其他")
        fl.addWidget(self.f_cat)

        fl.addWidget(self._lbl("等级:"))
        self.f_grade = QComboBox()
        self.f_grade.addItems(["全部","A","B","C","D","E"])
        fl.addWidget(self.f_grade)

        fl.addWidget(self._lbl("状态:"))
        self.f_status = QComboBox(); self.f_status.addItem("全部")
        self.f_status.addItems(ALL_STATUSES)
        fl.addWidget(self.f_status)

        fl.addWidget(self._lbl("从:"))
        self.d_from = QDateEdit(); self.d_from.setCalendarPopup(True)
        fl.addWidget(self.d_from)

        fl.addWidget(self._lbl("到:"))
        self.d_to = QDateEdit(); self.d_to.setCalendarPopup(True)
        fl.addWidget(self.d_to)

        sbtn = primary_btn("🔍 搜索")
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
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
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
        self.export_btn.clicked.connect(self.export_clicked.emit)
        action_row.addWidget(self.export_btn)

        cb = primary_btn("📊  统计图表")
        cb.clicked.connect(self.show_stats_clicked.emit)
        action_row.addWidget(cb)

        bsb = warning_btn("📝  批量改状态")
        bsb.clicked.connect(self.batch_status_clicked.emit)
        action_row.addWidget(bsb)

        db_ = danger_btn("🗑  删除选中")
        db_.clicked.connect(self.delete_selected_clicked.emit)
        action_row.addWidget(db_)

        action_row.addStretch()

        clb = secondary_btn("清空数据库")
        clb.clicked.connect(self.clear_db_clicked.emit)
        action_row.addWidget(clb)

        layout.addLayout(action_row)

        scroll.setWidget(inner)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0,0,0,0)
        page_layout.addWidget(scroll)
    
    def _lbl(self, text: str) -> QLabel:
        """创建带样式的标签"""
        lb = QLabel(text)
        lb.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 16px;")
        return lb
    
    def set_file_info(self, text: str, is_success: bool = False):
        """更新文件信息"""
        self.file_info.setText(text)
        if is_success:
            self.file_info.setStyleSheet(f"color: {Colors.ACCENT_GREEN}; font-size: 12px;")
        else:
            self.file_info.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 16px;")
    
    def set_screen_btn_enabled(self, enabled: bool):
        """设置筛查按钮状态"""
        self.screen_btn.setEnabled(enabled)
    
    def set_screen_progress_visible(self, visible: bool):
        """设置进度条可见性"""
        if hasattr(self, 'screen_progress'):
            self.screen_progress.setVisible(visible)
        self.progress_label.setVisible(visible)
    
    def set_progress_text(self, text: str):
        """设置进度文本"""
        self.progress_label.setText(text)
    
    def update_stats(self, stats: dict):
        """更新统计卡片"""
        if stats.get('total') is not None:
            self.stat_cards["total"].set_value(str(stats['total']))
        if stats.get('avg_confidence') is not None:
            self.stat_cards["avg"].set_value(f"{stats['avg_confidence']:.1%}")
        if stats.get('high_confidence') is not None:
            self.stat_cards["high"].set_value(str(stats['high_confidence']))
        if stats.get('low_confidence') is not None:
            self.stat_cards["low"].set_value(str(stats['low_confidence']))
        if stats.get('statuses'):
            statuses = stats['statuses']
            self.stat_cards["pending"].set_value(str(statuses.get('待处理', 0)))
            self.stat_cards["done"].set_value(str(statuses.get('已处理', 0)))
            self.stat_cards["archived"].set_value(str(statuses.get('已归档', 0)))
            self.stat_cards["transferred"].set_value(str(statuses.get('已移交', 0)))
