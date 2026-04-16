#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 数据库管理器 — 线索持久化 + 操作日志
"""

import sqlite3
import logging
from typing import Optional, List
from datetime import datetime

import pandas as pd

from core.constants import DB_PATH

logger = logging.getLogger("ClueScreener")


class DatabaseManager:
    """线索数据库：增删改查 + 统计 + 操作日志"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    #  连接
    # ------------------------------------------------------------------
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ------------------------------------------------------------------
    #  建表
    # ------------------------------------------------------------------
    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS clues (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_text     TEXT,
                    masked_text  TEXT,
                    category     TEXT    DEFAULT '',
                    confidence   REAL    DEFAULT 0.0,
                    grade        TEXT    DEFAULT '',
                    grade_icon   TEXT    DEFAULT '',
                    summary      TEXT    DEFAULT '',
                    status       TEXT    DEFAULT '待处理',
                    source       TEXT    DEFAULT '',
                    llm_analysis TEXT    DEFAULT '',
                    text_hash    TEXT    DEFAULT '',
                    created_at   TEXT    DEFAULT (datetime('now','localtime')),
                    updated_at   TEXT    DEFAULT (datetime('now','localtime')),
                    note         TEXT    DEFAULT ''
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    action    TEXT,
                    detail    TEXT,
                    timestamp TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_cat   ON clues(category)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_grade ON clues(grade)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_stat  ON clues(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_hash  ON clues(text_hash)")
            c.commit()
        logger.info("数据库初始化完成")

    # ------------------------------------------------------------------
    #  插入
    # ------------------------------------------------------------------
    def insert_clue(self, **kw) -> int:
        cols = ", ".join(kw.keys())
        phs = ", ".join(["?"] * len(kw))
        with self._conn() as c:
            cur = c.execute(
                f"INSERT INTO clues ({cols}) VALUES ({phs})",
                list(kw.values()),
            )
            c.commit()
            return cur.lastrowid

    def insert_clues_batch(self, records: List[dict]):
        if not records:
            return
        cols = list(records[0].keys())
        col_str = ", ".join(cols)
        phs = ", ".join(["?"] * len(cols))
        rows = [tuple(r[c] for c in cols) for r in records]
        with self._conn() as c:
            c.executemany(f"INSERT INTO clues ({col_str}) VALUES ({phs})", rows)
            c.commit()

    # ------------------------------------------------------------------
    #  更新 / 删除
    # ------------------------------------------------------------------
    def update_clue(self, clue_id: int, **kw):
        kw["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clause = ", ".join(f"{k}=?" for k in kw)
        vals = list(kw.values()) + [clue_id]
        with self._conn() as c:
            c.execute(f"UPDATE clues SET {clause} WHERE id=?", vals)
            c.commit()

    def delete_clue(self, clue_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM clues WHERE id=?", (clue_id,))
            c.commit()

    def clear_all(self):
        with self._conn() as c:
            c.execute("DELETE FROM clues")
            c.commit()

    # ------------------------------------------------------------------
    #  查询
    # ------------------------------------------------------------------
    def get_all_clues(self) -> pd.DataFrame:
        with self._conn() as c:
            return pd.read_sql_query("SELECT * FROM clues ORDER BY id DESC", c)

    def get_clues_filtered(self, category=None, grade=None, status=None,
                           keyword=None, date_from=None, date_to=None) -> pd.DataFrame:
        sql = "SELECT * FROM clues WHERE 1=1"
        params = []
        if category:
            sql += " AND category=?"; params.append(category)
        if grade:
            sql += " AND grade=?"; params.append(grade)
        if status:
            sql += " AND status=?"; params.append(status)
        if keyword:
            sql += " AND (raw_text LIKE ? OR masked_text LIKE ? OR summary LIKE ?)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])
        if date_from:
            sql += " AND created_at>=?"; params.append(date_from)
        if date_to:
            sql += " AND created_at<=?"; params.append(date_to + " 23:59:59")
        sql += " ORDER BY id DESC"
        with self._conn() as c:
            return pd.read_sql_query(sql, c, params=params)

    def get_clue_by_id(self, clue_id: int) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM clues WHERE id=?", (clue_id,)).fetchone()
            return dict(row) if row else None

    def check_duplicate(self, text_hash: str) -> bool:
        with self._conn() as c:
            r = c.execute(
                "SELECT COUNT(*) AS cnt FROM clues WHERE text_hash=?",
                (text_hash,),
            ).fetchone()
            return r["cnt"] > 0

    # ------------------------------------------------------------------
    #  统计
    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) AS n FROM clues").fetchone()["n"]
            avg_c = c.execute("SELECT AVG(confidence) AS a FROM clues").fetchone()["a"] or 0
            high = c.execute("SELECT COUNT(*) AS n FROM clues WHERE confidence>=0.8").fetchone()["n"]
            low = c.execute("SELECT COUNT(*) AS n FROM clues WHERE confidence<0.5").fetchone()["n"]
            cats = {r["category"]: r["cnt"] for r in
                    c.execute("SELECT category, COUNT(*) AS cnt FROM clues GROUP BY category")}
            grades = {r["grade"]: r["cnt"] for r in
                      c.execute("SELECT grade, COUNT(*) AS cnt FROM clues GROUP BY grade")}
            statuses = {r["status"]: r["cnt"] for r in
                        c.execute("SELECT status, COUNT(*) AS cnt FROM clues GROUP BY status")}
        return dict(total=total, avg_confidence=avg_c, high_confidence=high,
                    low_confidence=low, categories=cats, grades=grades, statuses=statuses)

    # ------------------------------------------------------------------
    #  操作日志
    # ------------------------------------------------------------------
    def log_operation(self, action: str, detail: str = ""):
        with self._conn() as c:
            c.execute("INSERT INTO operation_logs(action,detail) VALUES(?,?)",
                      (action, detail))
            c.commit()

    def get_recent_logs(self, limit: int = 300) -> List[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
