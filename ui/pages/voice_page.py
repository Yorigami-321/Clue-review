from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QComboBox,
    QPushButton, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets import primary_btn, secondary_btn, danger_btn, card
from ui.theme import Colors


class VoicePage(QWidget):
    """语音识别页面 - 仅负责 UI 构建和事件转发"""
    
    # 信号定义
    load_model_clicked = pyqtSignal(str)  # 模型名称
    toggle_record_clicked = pyqtSignal()
    upload_audio_clicked = pyqtSignal()
    transcribe_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建语音识别页面UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # 模型加载
        mc = card("🎤  语音识别模型")
        mcl = QVBoxLayout(mc)
        row = QHBoxLayout()
        row.addWidget(self._lbl("Whisper 模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny","base","small","medium","large"])
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 9px 14px;
                background-color: {Colors.BG_INPUT};
                color: {Colors.TEXT_PRIMARY};
                font-size: 20px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border: 1px solid {Colors.BORDER_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid {Colors.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.BG_CARD};
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 18px;
                selection-background-color: {Colors.ACCENT_BLUE};
                selection-color: {Colors.TEXT_WHITE};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 8px 14px;
                min-height: 30px;
                border: none;
                background-color: transparent;
            }}
            QComboBox QAbstractItemView::item:selected {{
                color: {Colors.TEXT_WHITE};
                background-color: {Colors.ACCENT_BLUE};
            }}
        """)
        row.addWidget(self.model_combo)
        row.addStretch()
        mcl.addLayout(row)
        
        self.load_model_btn = primary_btn("加载语音模型")
        self.load_model_btn.clicked.connect(
            lambda: self.load_model_clicked.emit(self.model_combo.currentText())
        )
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
        self.record_btn.clicked.connect(self.toggle_record_clicked.emit)
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
        ub.clicked.connect(self.upload_audio_clicked.emit)
        rcl.addWidget(ub)
        
        self.transcribe_result = QTextEdit()
        self.transcribe_result.setPlaceholderText("转写结果将显示在这里...")
        self.transcribe_result.setMinimumHeight(150)
        rcl.addWidget(self.transcribe_result)
        
        self.transcribe_btn = primary_btn("▶  开始转写")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self.transcribe_clicked.emit)
        rcl.addWidget(self.transcribe_btn)
        
        layout.addWidget(rc)
        layout.addStretch()

        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
    
    def _lbl(self, text: str) -> QLabel:
        """创建带样式的标签"""
        lb = QLabel(text)
        lb.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 16px;")
        return lb
    
    def set_model_status(self, text: str, is_success: bool = False, is_error: bool = False):
        """更新模型状态"""
        self.model_status.setText(text)
        if is_error:
            self.model_status.setStyleSheet(f"""
                color: {Colors.ACCENT_RED};
                background: rgba(239,68,68,0.1);
                border: 1px solid rgba(239,68,68,0.3);
                padding: 10px; border-radius: 8px;
            """)
        elif is_success:
            self.model_status.setStyleSheet(f"""
                color: {Colors.ACCENT_GREEN};
                background: rgba(34,197,94,0.1);
                border: 1px solid rgba(34,197,94,0.3);
                padding: 10px; border-radius: 8px;
            """)
        else:
            self.model_status.setStyleSheet(f"""
                color: {Colors.ACCENT_ORANGE};
                background: rgba(245,158,11,0.1);
                border: 1px solid rgba(245,158,11,0.3);
                padding: 10px; border-radius: 8px;
            """)
    
    def set_model_combo_text(self, text: str):
        """设置模型下拉框文本"""
        self.model_combo.setCurrentText(text)
    
    def set_load_model_btn_enabled(self, enabled: bool):
        """设置加载模型按钮状态"""
        self.load_model_btn.setEnabled(enabled)
    
    def set_record_btn_text(self, text: str):
        """设置录音按钮文本"""
        self.record_btn.setText(text)
    
    def set_rec_status(self, text: str, is_recording: bool = False, is_success: bool = False):
        """更新录音状态"""
        self.rec_status.setText(text)
        if is_recording:
            self.rec_status.setStyleSheet(f"color: {Colors.ACCENT_RED}; font-weight: bold;")
        elif is_success:
            self.rec_status.setStyleSheet(f"color: {Colors.ACCENT_GREEN};")
        else:
            self.rec_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
    
    def set_volume_value(self, value: int):
        """设置音量值"""
        self.volume_bar.setValue(value)
    
    def set_transcribe_btn_enabled(self, enabled: bool):
        """设置转写按钮状态"""
        self.transcribe_btn.setEnabled(enabled)
    
    def set_transcribe_result(self, text: str):
        """设置转写结果"""
        self.transcribe_result.setText(text)
