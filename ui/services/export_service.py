from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import os


class ExportService(QObject):
    """导出服务 - 封装所有导出相关逻辑"""
    
    # 信号定义
    export_success = pyqtSignal(str)  # 导出文件路径
    export_error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
    
    def export_csv(self, file_path: str):
        """导出为CSV"""
        try:
            df = self.db.get_all_clues()
            if df.empty:
                self.export_error.emit("无数据可导出")
                return
            
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            self.export_success.emit(file_path)
        except Exception as e:
            self.export_error.emit(f"CSV导出失败: {str(e)}")
    
    def export_excel(self, file_path: str):
        """导出为Excel"""
        try:
            df = self.db.get_all_clues()
            if df.empty:
                self.export_error.emit("无数据可导出")
                return
            
            df.to_excel(file_path, index=False, engine="openpyxl")
            self.export_success.emit(file_path)
        except Exception as e:
            self.export_error.emit(f"Excel导出失败: {str(e)}")
    
    def export_pdf(self, file_path: str):
        """导出为PDF"""
        try:
            # 尝试导入reportlab
            try:
                from reportlab.lib import colors as rlc
                from reportlab.lib.pagesizes import A4, landscape
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import mm
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
            except ImportError:
                self.export_error.emit("缺少依赖: reportlab")
                return
            
            df = self.db.get_all_clues()
            if df.empty:
                self.export_error.emit("无数据可导出")
                return
            
            # 注册中文字体
            bf = "Helvetica"
            for fp in ["C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont("CNFont", fp))
                    bf = "CNFont"
                    break
            
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
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
            
            elements.append(tbl)
            doc.build(elements)
            self.export_success.emit(file_path)
        except Exception as e:
            self.export_error.emit(f"PDF导出失败: {str(e)}")
