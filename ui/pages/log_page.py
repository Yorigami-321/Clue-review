from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QPushButton, QHeaderView, QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets import secondary_btn
from ui.theme import Colors


class LogPage(QWidget):
    """操作日志页面 - 仅负责 UI 构建和事件转发"""
    
    # 信号定义
    refresh_logs_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建操作日志页面UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["时间", "操作", "详情"])
        # 设置列宽模式：时间和操作列自适应内容，详情列拉伸填充
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                background-color: {Colors.BG_CARD};
                alternate-background-color: {Colors.BG_INPUT};
                gridline-color: {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
                font-size: 16px;
                selection-background-color: {Colors.ACCENT_BLUE};
                selection-color: {Colors.TEXT_WHITE};
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_DARKEST};
                color: {Colors.ACCENT_CYAN};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {Colors.ACCENT_BLUE};
                font-weight: bold;
                font-size: 16px;
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                min-height: 35px;
                border-bottom: 1px solid {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(74, 108, 247, 0.3);
                color: {Colors.TEXT_WHITE};
            }}
        """)
        layout.addWidget(self.log_table)

        refresh_btn = secondary_btn("🔄  刷新日志")
        refresh_btn.clicked.connect(self.refresh_logs_clicked.emit)
        layout.addWidget(refresh_btn)
    
    def update_logs(self, logs: list):
        """更新日志表格"""
        self.log_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.log_table.setItem(i, 0, QTableWidgetItem(log.get("timestamp","")))
            self.log_table.setItem(i, 1, QTableWidgetItem(log.get("action","")))
            self.log_table.setItem(i, 2, QTableWidgetItem(log.get("detail","")))
