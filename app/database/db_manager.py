"""SQLite数据库管理器 - 桌面物品管理系统数据层核心"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """单例模式的数据库管理器"""

    _instance = None
    _db_path = None

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path=None):
        if self._initialized:
            return
        self._initialized = True

        if db_path:
            self.db_path = db_path
        else:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            self.db_path = str(data_dir / "inventory.db")

        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _create_tables(self):
        """创建所有数据表"""
        cursor = self.conn.cursor()

        cursor.executescript("""
            -- 位置表（层级结构）
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                level INTEGER NOT NULL DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE CASCADE
            );

            -- 物品表
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                brand TEXT,
                model TEXT,
                quantity INTEGER NOT NULL DEFAULT 1,
                purchase_date TEXT,
                warranty_period TEXT,
                status TEXT NOT NULL DEFAULT '在库',
                location_id INTEGER,
                photo_path TEXT,
                notes TEXT,
                last_viewed TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL
            );

            -- 借出记录表
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                borrower_name TEXT NOT NULL,
                borrower_contact TEXT,
                loan_date TEXT NOT NULL,
                expected_return_date TEXT,
                actual_return_date TEXT,
                status TEXT NOT NULL DEFAULT '借出中',
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            );

            -- 位置变更历史表
            CREATE TABLE IF NOT EXISTS location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                from_location_id INTEGER,
                to_location_id INTEGER,
                change_type TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            );

            -- 搜索历史表
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                search_count INTEGER NOT NULL DEFAULT 1,
                last_searched TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            -- 索引
            CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
            CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
            CREATE INDEX IF NOT EXISTS idx_items_location ON items(location_id);
            CREATE INDEX IF NOT EXISTS idx_loans_item ON loans(item_id);
            CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
            CREATE INDEX IF NOT EXISTS idx_locations_parent ON locations(parent_id);
        """)

        self.conn.commit()
        self._initialize_default_locations()

    def _initialize_default_locations(self):
        """初始化默认位置数据"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM locations")
        count = cursor.fetchone()["cnt"]
        if count == 0:
            default_locations = [
                ("客厅", "LIVING", None, 1, 1),
                ("卧室", "BED", None, 1, 2),
                ("厨房", "KITCHEN", None, 1, 3),
                ("书房", "STUDY", None, 1, 4),
                ("卫生间", "BATH", None, 1, 5),
                ("阳台", "BALCONY", None, 1, 6),
                ("储物间", "STORAGE", None, 1, 7),
            ]
            for name, code, parent_id, level, sort_order in default_locations:
                cursor.execute(
                    "INSERT INTO locations (name, code, parent_id, level, sort_order) VALUES (?, ?, ?, ?, ?)",
                    (name, code, parent_id, level, sort_order)
                )
            self.conn.commit()

    def execute(self, sql, params=None):
        """执行SQL语句"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        self.conn.commit()
        return cursor

    def query(self, sql, params=None):
        """查询数据，返回所有行"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def query_one(self, sql, params=None):
        """查询单行数据"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def get_db_path(self):
        """获取数据库文件路径"""
        return self.db_path
