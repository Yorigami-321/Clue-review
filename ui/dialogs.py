#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框：线索详情 / 操作日志 / 统计图表（深蓝科技风）
"""

import os
import logging

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QTextEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget, QScrollArea, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.constants import ALL_STATUSES, STATUS_PENDING
from core.database import DatabaseManager
from ui.theme import Colors

logger = logging.getLogger("ClueScreener")

# 图表深色配色
CHART_BG = "#0d1233"
CHART_FACE = "#111842"
CHART_TEXT = "#e2e8f0"
CHART_GRID = "#1a2260"


def _dark_ax(ax):
    """将 matplotlib axes 设为深色风格"""
    ax.set_facecolor(CHART_FACE)
    ax.tick_params(colors=CHART_TEXT, labelsize=9)
    ax.xaxis.label.set_color(CHART_TEXT)
    ax.yaxis.label.set_color(CHART_TEXT)
    ax.title.set_color(CHART_TEXT)
    for spine in ax.spines.values():
        spine.set_color(CHART_GRID)


def _dark_fig(fig):
    fig.set_facecolor(CHART_BG)


# ===================== 线索详情 =====================
class ClueDetailDialog(QDialog):
    status_changed = pyqtSignal(int, str)

    def __init__(self, clue: dict, parent=None):
        super().__init__(parent)
        self.clue = clue
        self.setWindowTitle(f"线索详情 — #{clue.get('id', 'N/A')}")
        self.setMinimumSize(720, 620)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Colors.BG_DARK}; }}
            QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
            QTextEdit {{ background: {Colors.BG_INPUT}; color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: 8px; padding: 8px; }}
            QComboBox {{ background: {Colors.BG_INPUT}; color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: 8px; padding: 6px; }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        inner = QWidget(); inner.setStyleSheet("background: transparent;")
        form = QFormLayout(inner); form.setSpacing(12)

        form.addRow("ID:", QLabel(str(self.clue.get("id", ""))))
        form.addRow("创建时间:", QLabel(str(self.clue.get("created_at", ""))))

        grade = self.clue.get("grade", "")
        icon = self.clue.get("grade_icon", "")
        conf = self.clue.get("confidence", 0)
        gl = QLabel(f"{icon} {grade}级  (置信度 {conf:.1%})")
        gl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.ACCENT_CYAN};")
        form.addRow("线索等级:", gl)

        cl = QLabel(self.clue.get("category", ""))
        cl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.ACCENT_BLUE};")
        form.addRow("线索类别:", cl)

        form.addRow("来源:", QLabel(self.clue.get("source", "") or "未知"))

        self.status_combo = QComboBox()
        self.status_combo.addItems(ALL_STATUSES)
        cur = self.clue.get("status", STATUS_PENDING)
        if cur in ALL_STATUSES: self.status_combo.setCurrentText(cur)
        form.addRow("处理状态:", self.status_combo)

        for label_text, key, h in [("精简摘要:", "summary", 70),
                                    ("原始内容:", "raw_text", 130),
                                    ("脱敏内容:", "masked_text", 130)]:
            te = QTextEdit(); te.setPlainText(self.clue.get(key, ""))
            te.setReadOnly(True); te.setMaximumHeight(h)
            form.addRow(label_text, te)

        if self.clue.get("llm_analysis"):
            le = QTextEdit(); le.setPlainText(self.clue["llm_analysis"])
            le.setReadOnly(True); le.setMaximumHeight(100)
            form.addRow("LLM 分析:", le)

        self.note_edit = QTextEdit()
        self.note_edit.setPlainText(self.clue.get("note", ""))
        self.note_edit.setMaximumHeight(90)
        self.note_edit.setPlaceholderText("请输入处理备注...")
        form.addRow("处理备注:", self.note_edit)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        bb = QDialogButtonBox()
        save = bb.addButton("保存修改", QDialogButtonBox.AcceptRole)
        save.setStyleSheet(f"background:{Colors.ACCENT_BLUE}; color:white; border:none; border-radius:6px; padding:8px 20px;")
        cancel = bb.addButton("关闭", QDialogButtonBox.RejectRole)
        cancel.setStyleSheet(f"background:{Colors.BTN_SECONDARY}; color:white; border:none; border-radius:6px; padding:8px 20px;")
        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        layout.addWidget(bb)

    def _save(self):
        self.clue["status"] = self.status_combo.currentText()
        self.clue["note"] = self.note_edit.toPlainText()
        cid = self.clue.get("id")
        if cid: self.status_changed.emit(cid, self.clue["status"])
        self.accept()


# ===================== 操作日志 =====================
class LogDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("操作日志")
        self.setMinimumSize(750, 520)
        self.setStyleSheet(f"QDialog {{ background: {Colors.BG_DARK}; }}")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["时间", "操作", "详情"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        logs = db.get_recent_logs(500)
        self.table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.table.setItem(i, 0, QTableWidgetItem(log.get("timestamp","")))
            self.table.setItem(i, 1, QTableWidgetItem(log.get("action","")))
            self.table.setItem(i, 2, QTableWidgetItem(log.get("detail","")))
        btn = QPushButton("关闭")
        btn.setStyleSheet(f"background:{Colors.BTN_SECONDARY}; color:white; border:none; border-radius:6px; padding:8px 20px;")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)


# ===================== 统计图表 =====================
class StatisticsDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("📊 线索分布统计")
        self.setMinimumSize(1100, 850)
        self.setStyleSheet(f"QDialog {{ background: {Colors.BG_DARK}; }}")
        self._build(); self._draw()

    def _build(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        names = ["类别分布","等级分布","置信度分布","处理状态","时间趋势","关键词云"]
        self.canvases = {}
        for name in names:
            tab = QWidget()
            tab.setStyleSheet(f"background: {Colors.BG_DARK};")
            tl = QVBoxLayout(tab)
            canvas = FigureCanvas(Figure(figsize=(9,6)))
            tl.addWidget(canvas)
            self.tabs.addTab(tab, name)
            self.canvases[name] = canvas
        btn = QPushButton("关闭")
        btn.setStyleSheet(f"background:{Colors.BTN_SECONDARY}; color:white; border:none; border-radius:6px; padding:8px 20px;")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)

    def _draw(self):
        df = self.db.get_all_clues()
        if df.empty: return

        chart_colors = ["#4a6cf7","#22c55e","#22d3ee","#f59e0b","#a855f7",
                        "#ef4444","#ec4899","#06b6d4","#84cc16","#6b7280"]

        # 1 类别
        fig = self.canvases["类别分布"].figure; fig.clear(); _dark_fig(fig)
        ax = fig.add_subplot(111); _dark_ax(ax)
        vc = df["category"].value_counts()
        bars = ax.bar(range(len(vc)), vc.values, color=chart_colors[:len(vc)])
        ax.set_xticks(range(len(vc)))
        ax.set_xticklabels(vc.index, rotation=45, ha="right")
        ax.set_title("线索类别分布"); ax.set_ylabel("数量")
        for b,v in zip(bars, vc.values):
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                    str(v), ha="center", color=CHART_TEXT, fontweight="bold")
        fig.tight_layout(); self.canvases["类别分布"].draw()

        # 2 等级
        fig2 = self.canvases["等级分布"].figure; fig2.clear(); _dark_fig(fig2)
        ax2 = fig2.add_subplot(111); _dark_ax(ax2)
        gc = df["grade"].value_counts().sort_index()
        gcm = {"A":"#22c55e","B":"#4a6cf7","C":"#f59e0b","D":"#f97316","E":"#ef4444"}
        bc = [gcm.get(g,"#6b7280") for g in gc.index]
        bars2 = ax2.bar(range(len(gc)), gc.values, color=bc)
        ax2.set_xticks(range(len(gc)))
        ax2.set_xticklabels([f"{g}级" for g in gc.index])
        ax2.set_title("线索等级分布"); ax2.set_ylabel("数量")
        for b,v in zip(bars2, gc.values):
            ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                    str(v), ha="center", color=CHART_TEXT, fontweight="bold")
        fig2.tight_layout(); self.canvases["等级分布"].draw()

        # 3 置信度
        fig3 = self.canvases["置信度分布"].figure; fig3.clear(); _dark_fig(fig3)
        ax3 = fig3.add_subplot(111); _dark_ax(ax3)
        bins = [0,0.2,0.35,0.55,0.7,0.85,1.0]
        labels = ["0-20%","20-35%","35-55%","55-70%","70-85%","85-100%"]
        h, _ = np.histogram(df["confidence"], bins=bins)
        bc3 = ["#ef4444","#f97316","#f59e0b","#f59e0b","#4a6cf7","#22c55e"]
        bars3 = ax3.bar(range(len(labels)), h, color=bc3)
        ax3.set_xticks(range(len(labels))); ax3.set_xticklabels(labels)
        ax3.set_title("置信度分布"); ax3.set_ylabel("数量")
        for b,v in zip(bars3, h):
            if v > 0: ax3.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                               str(v), ha="center", color=CHART_TEXT)
        fig3.tight_layout(); self.canvases["置信度分布"].draw()

        # 4 状态饼图
        fig4 = self.canvases["处理状态"].figure; fig4.clear(); _dark_fig(fig4)
        ax4 = fig4.add_subplot(111); _dark_ax(ax4)
        sc = df["status"].value_counts()
        smap = {"待处理":"#ef4444","处理中":"#f59e0b","已处理":"#22c55e",
                "已归档":"#6b7280","已移交":"#4a6cf7"}
        pc = [smap.get(s,"#6b7280") for s in sc.index]
        wedges, texts, autotexts = ax4.pie(sc.values, labels=sc.index,
            autopct="%1.1f%%", colors=pc, startangle=90,
            textprops={"color": CHART_TEXT})
        for t in autotexts: t.set_color(CHART_TEXT)
        ax4.set_title("处理状态分布")
        fig4.tight_layout(); self.canvases["处理状态"].draw()

        # 5 时间趋势
        fig5 = self.canvases["时间趋势"].figure; fig5.clear(); _dark_fig(fig5)
        ax5 = fig5.add_subplot(111); _dark_ax(ax5)
        if "created_at" in df.columns:
            df["_date"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date
            daily = df.groupby("_date").size()
            if len(daily) > 1:
                ax5.plot(daily.index, daily.values, marker="o",
                         color="#4a6cf7", linewidth=2, markersize=4)
                ax5.fill_between(daily.index, daily.values, alpha=0.15, color="#4a6cf7")
                ax5.set_title("线索录入趋势"); ax5.set_ylabel("新增数")
                for t in ax5.get_xticklabels(): t.set_rotation(45)
            else:
                ax5.text(0.5,0.5,"数据不足",ha="center",va="center",
                         transform=ax5.transAxes, color=CHART_TEXT)
        fig5.tight_layout(); self.canvases["时间趋势"].draw()

        # 6 词云
        fig6 = self.canvases["关键词云"].figure; fig6.clear(); _dark_fig(fig6)
        ax6 = fig6.add_subplot(111); _dark_ax(ax6)
        try:
            from wordcloud import WordCloud
            all_text = " ".join(df["masked_text"].dropna().tolist())
            if all_text.strip():
                font = None
                for fp in ["C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
                    if os.path.exists(fp): font=fp; break
                wc = WordCloud(font_path=font, width=900, height=600,
                    background_color=CHART_BG, max_words=150,
                    colormap="cool").generate(all_text)
                ax6.imshow(wc, interpolation="bilinear")
                ax6.axis("off"); ax6.set_title("关键词云")
            else:
                ax6.text(0.5,0.5,"无文本",ha="center",va="center",
                         transform=ax6.transAxes, color=CHART_TEXT)
        except ImportError:
            ax6.text(0.5,0.5,"需安装 wordcloud",ha="center",va="center",
                     transform=ax6.transAxes, color=CHART_TEXT)
        fig6.tight_layout(); self.canvases["关键词云"].draw()
