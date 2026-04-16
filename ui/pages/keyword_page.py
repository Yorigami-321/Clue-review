from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QCheckBox,
    QPushButton, QTabWidget, QVBoxLayout as QVBoxLayout2
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QColor

from ui.widgets import success_btn, secondary_btn, card
from ui.theme import Colors, FontSize
from core.keywords import DEFAULT_KEYWORDS


class KeywordPage(QWidget):
    """关键词库页面 - 仅负责 UI 构建和事件转发"""
    
    # 信号定义
    save_keywords_clicked = pyqtSignal(str, list, bool)  # category, keywords, enabled
    reset_keywords_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._kw_inputs = {}
        self._build_ui()
    
    def _build_ui(self):
        """构建关键词库页面UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        kc = card("📚  关键词库管理")
        kcl = QVBoxLayout(kc)
        self.kw_tabs = QTabWidget()
        
        # 让标签页在空间不足时可滚动，不强行压缩
        self.kw_tabs.tabBar().setExpanding(False)
        self.kw_tabs.tabBar().setUsesScrollButtons(True)
        self.kw_tabs.tabBar().setElideMode(Qt.ElideRight)
        
        # 仅覆盖"关键词页"tab样式，避免受全局大字号挤压
        self.kw_tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 14px;
                min-width: 96px;
                font-size: 16px;
            }
            QTabBar::tab:selected {
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #1a2260;
                border-radius: 10px;
                top: -1px;
            }
        """)
        # 使用 QPalette 设置 QTabWidget 背景色（更可靠）
        palette = self.kw_tabs.palette()
        palette.setColor(QPalette.Window, QColor(Colors.BG_CARD))
        palette.setColor(QPalette.Base, QColor(Colors.BG_CARD))
        self.kw_tabs.setPalette(palette)
        self.kw_tabs.setAutoFillBackground(True)
        
        for cat, info in DEFAULT_KEYWORDS.items():
            tab = QWidget()
            # 使用 QPalette 设置 tab 页面背景色（比 stylesheet 更可靠）
            tab_palette = tab.palette()
            tab_palette.setColor(QPalette.Window, QColor(Colors.BG_CARD))
            tab.setPalette(tab_palette)
            tab.setAutoFillBackground(True)
            tl = QVBoxLayout2(tab)
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
            # 直接设置样式属性，不要包含控件名称选择器
            kw_edit.setStyleSheet(f"""
                background-color: {Colors.BG_INPUT};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: {FontSize.INPUT}px;
            """)
            # 设置 viewport 的背景色（QTextEdit 内部的可滚动区域）
            kw_edit.viewport().setStyleSheet(f"background-color: {Colors.BG_INPUT};")
            tl.addWidget(kw_edit)
            en_cb = QCheckBox("启用此分类")
            en_cb.setChecked(info["enabled"])
            tl.addWidget(en_cb)
            self._kw_inputs[cat] = (kw_edit, en_cb)
            sv = success_btn("保存")
            sv.clicked.connect(lambda _, c=cat: self._on_save(c))
            tl.addWidget(sv)
            self.kw_tabs.addTab(tab, cat)
        
        kcl.addWidget(self.kw_tabs)
        rk = secondary_btn("🔄  重置所有关键词")
        rk.clicked.connect(self.reset_keywords_clicked.emit)
        kcl.addWidget(rk)
        layout.addWidget(kc)
        layout.addStretch()

        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
    
    def _on_save(self, category: str):
        """保存关键词"""
        edit, cb = self._kw_inputs[category]
        # 处理中英文逗号
        import re
        kws = [k.strip() for k in re.split(r"[,，]", edit.toPlainText()) if k.strip()]
        enabled = cb.isChecked()
        self.save_keywords_clicked.emit(category, kws, enabled)
    
    def reset_keywords(self):
        """重置所有关键词"""
        for cat, (edit, cb) in self._kw_inputs.items():
            edit.setText("，".join(DEFAULT_KEYWORDS[cat]["keywords"]))
            cb.setChecked(True)
