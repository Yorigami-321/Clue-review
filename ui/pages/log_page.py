from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QPushButton, QHeaderView, QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets import secondary_btn


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
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setAlternatingRowColors(True)
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
