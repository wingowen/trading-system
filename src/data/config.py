"""
StockExpert 全局配置
所有模块统一从此处导入配置，禁止硬编码路径。
"""
import os
from pathlib import Path

# 数据库路径：环境变量 STOCKEXPERT_DB 或相对于 src/ 的 data/ 目录
DB_PATH = os.environ.get(
    "STOCKEXPERT_DB",
    str(Path(__file__).parent.parent.parent / "data" / "stockexpert.db")
)
