"""
全局配置文件
"""
import os
from pathlib import Path

# ============ 路径配置 ============
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CACHE_DIR = DATA_DIR / "cache"
THUMBNAIL_DIR = DATA_DIR / "thumbnails"
EXPORT_DIR = DATA_DIR / "exports"

for d in [DATA_DIR, UPLOAD_DIR, CACHE_DIR, THUMBNAIL_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============ 模型配置 ============
# 多模态大模型 - Qwen2.5-VL
VLM_MODEL_PATH = os.getenv("VLM_MODEL_PATH", "Qwen/Qwen2.5-VL-7B-Instruct")
VLM_DEVICE = "cuda"  # "cuda" or "cpu"
VLM_MAX_TOKENS = 4096

# YOLOv8 OBB 检测模型
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n-obb.pt")
YOLO_CONF_THRESHOLD = 0.35
YOLO_IOU_THRESHOLD = 0.45

# 文本嵌入模型
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "BAAI/bge-large-zh-v1.5")
EMBEDDING_DIM = 1024

# ============ 数据库配置 ============
# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Milvus
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION = "engineering_drawings"

# ============ OCR 配置 ============
OCR_LANG = "ch"
OCR_USE_GPU = True

# ============ 图纸区域检测类别 ============
DRAWING_REGION_CLASSES = [
    "title_block",        # 标题栏
    "bom_table",          # 明细表
    "dimension",          # 尺寸标注
    "tech_requirement",   # 技术要求
    "view_area",          # 视图区域
    "gdt_symbol",         # GD&T符号
    "surface_roughness",  # 表面粗糙度
    "tolerance",          # 公差标注
    "note",               # 注释
]

# ============ 审查规则 ============
REVIEW_RULES = {
    "title_block_completeness": {
        "required_fields": ["part_name", "part_number", "material", "designer", "date", "scale"],
        "weight": 20
    },
    "dimension_check": {
        "description": "检查尺寸标注完整性",
        "weight": 30
    },
    "material_validity": {
        "valid_materials": [
            "45#钢", "Q235", "Q345", "304不锈钢", "316不锈钢",
            "6061铝合金", "7075铝合金", "HT200", "HT250", "QT500",
            "H62黄铜", "T2紫铜", "40Cr", "20CrMnTi", "GCr15",
            "尼龙", "PTFE", "POM"
        ],
        "weight": 15
    },
    "tolerance_reasonableness": {
        "description": "公差合理性检查",
        "weight": 20
    },
    "standard_compliance": {
        "description": "标准引用正确性",
        "weight": 15
    }
}
