from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QLineEdit,
    QCheckBox, QPushButton
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets import primary_btn, secondary_btn, card
from ui.theme import Colors


class LLMPage(QWidget):
    """LLM设置页面 - 仅负责 UI 构建和事件转发"""
    
    # 信号定义
    save_config_clicked = pyqtSignal(str, str, str, bool)  # api_key, api_url, model, use_llm
    test_cloud_clicked = pyqtSignal(str, str, str)  # api_key, api_url, model
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """构建LLM设置页面UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
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
        lcl.addWidget(self.api_key_input)

        lcl.addWidget(self._lbl("API 地址:"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://open.bigmodel.cn/api/paas/v4")
        lcl.addWidget(self.api_url_input)

        lcl.addWidget(self._lbl("模型名称:"))
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("glm-4-flash / deepseek-chat / qwen-turbo")
        lcl.addWidget(self.model_name_input)

        lcl.addSpacing(10)
        br = QHBoxLayout()
        sb = primary_btn("💾  保存配置")
        sb.clicked.connect(self._on_save)
        br.addWidget(sb)
        tb = secondary_btn("🔗  测试连接")
        tb.clicked.connect(self._on_test)
        br.addWidget(tb)
        br.addStretch()
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
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0,0,0,0)
        pl.addWidget(scroll)
    
    def _lbl(self, text: str) -> QLabel:
        """创建带样式的标签"""
        lb = QLabel(text)
        lb.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 16px;")
        return lb
    
    def _on_save(self):
        """保存配置"""
        api_key = self.api_key_input.text()
        api_url = self.api_url_input.text()
        model = self.model_name_input.text()
        use_llm = self.use_llm_cb.isChecked()
        self.save_config_clicked.emit(api_key, api_url, model, use_llm)
    
    def _on_test(self):
        """测试连接"""
        api_key = self.api_key_input.text()
        api_url = self.api_url_input.text()
        model = self.model_name_input.text()
        self.test_cloud_clicked.emit(api_key, api_url, model)
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key_input.setText(api_key)
    
    def set_api_url(self, api_url: str):
        """设置API地址"""
        self.api_url_input.setText(api_url)
    
    def set_model_name(self, model_name: str):
        """设置模型名称"""
        self.model_name_input.setText(model_name)
    
    def set_use_llm(self, use_llm: bool):
        """设置是否启用LLM"""
        self.use_llm_cb.setChecked(use_llm)
