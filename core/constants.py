#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局常量定义
"""

APP_NAME = "涉检线索智能筛查工具"
APP_VERSION = "6.0"
DB_PATH = "./clue_database.db"
CONFIG_FILE = "./config.json"
LOG_DIR = "./logs"

# 线索处理状态
STATUS_PENDING = "待处理"
STATUS_PROCESSING = "处理中"
STATUS_DONE = "已处理"
STATUS_ARCHIVED = "已归档"
STATUS_TRANSFERRED = "已移交"

ALL_STATUSES = [
    STATUS_PENDING,
    STATUS_PROCESSING,
    STATUS_DONE,
    STATUS_ARCHIVED,
    STATUS_TRANSFERRED,
]
