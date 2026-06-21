"""物品服务 - 物品的增删改查及业务逻辑"""

from app.database.db_manager import DatabaseManager
from app.services.location_service import LocationService
from datetime import datetime


class ItemService:
    """物品管理服务"""

    STATUS_IN_STOCK = "在库"
    STATUS_LOANED = "借出中"
    STATUS_TEMPORARY = "临时取出"
    STATUS_LOST = "丢失"
    STATUS_DISCARDED = "报废"

    def __init__(self):
        self.db = DatabaseManager()
        self.location_service = LocationService()

    def get_all_items(self, status=None, category=None, location_id=None):
        """获取物品列表，支持筛选"""
        sql = "SELECT i.*, l.name as location_name FROM items i LEFT JOIN locations l ON i.location_id = l.id WHERE 1=1"
        params = []

        if status:
            sql += " AND i.status = ?"
            params.append(status)
        if category:
            sql += " AND i.category = ?"
            params.append(category)
        if location_id:
            sql += " AND i.location_id = ?"
            params.append(location_id)

        sql += " ORDER BY i.updated_at DESC"
        return self.db.query(sql, params)

    def get_item_by_id(self, item_id):
        """根据ID获取物品详情"""
        item = self.db.query_one(
            """SELECT i.*, l.name as location_name FROM items i
               LEFT JOIN locations l ON i.location_id = l.id WHERE i.id = ?""",
            (item_id,)
        )
        if item:
            item["location_path"] = self.location_service.get_location_path(item["location_id"]) if item["location_id"] else ""
        return item

    def add_item(self, name, category=None, brand=None, model=None,
                 quantity=1, purchase_date=None, warranty_period=None,
                 status=None, location_id=None, photo_path=None, notes=None):
        """添加新物品"""
        if status is None:
            status = self.STATUS_IN_STOCK

        cursor = self.db.execute(
            """INSERT INTO items (name, category, brand, model, quantity,
               purchase_date, warranty_period, status, location_id, photo_path, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, category, brand, model, quantity, purchase_date,
             warranty_period, status, location_id, photo_path, notes)
        )
        item_id = cursor.lastrowid

        if location_id:
            self._record_location_change(item_id, None, location_id, "新增")

        return item_id

    def update_item(self, item_id, **kwargs):
        """更新物品信息"""
        old_item = self.get_item_by_id(item_id)
        if not old_item:
            return False

        allowed_fields = ["name", "category", "brand", "model", "quantity",
                          "purchase_date", "warranty_period", "status",
                          "location_id", "photo_path", "notes"]

        update_fields = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                update_fields.append(f"{field} = ?")
                params.append(kwargs[field])

        if not update_fields:
            return False

        update_fields.append("updated_at = datetime('now', 'localtime')")
        params.append(item_id)

        sql = f"UPDATE items SET {', '.join(update_fields)} WHERE id = ?"
        self.db.execute(sql, params)

        new_location_id = kwargs.get("location_id")
        if new_location_id is not None and new_location_id != old_item["location_id"]:
            self._record_location_change(item_id, old_item["location_id"], new_location_id, "移动")

        return True

    def delete_item(self, item_id):
        """删除物品"""
        self.db.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return True

    def search_items(self, keyword, status=None, category=None, location_id=None, limit=100):
        """模糊搜索物品"""
        self._record_search(keyword)

        sql = """SELECT i.*, l.name as location_name
                 FROM items i LEFT JOIN locations l ON i.location_id = l.id
                 WHERE (i.name LIKE ? OR i.category LIKE ? OR i.brand LIKE ?
                        OR i.model LIKE ? OR i.notes LIKE ?)"""
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%",
                  f"%{keyword}%", f"%{keyword}%"]

        if status:
            sql += " AND i.status = ?"
            params.append(status)
        if category:
            sql += " AND i.category = ?"
            params.append(category)
        if location_id:
            sql += " AND i.location_id = ?"
            params.append(location_id)

        sql += " ORDER BY i.last_viewed DESC NULLS LAST, i.updated_at DESC LIMIT ?"
        params.append(limit)

        results = self.db.query(sql, params)
        for item in results:
            item["location_path"] = self.location_service.get_location_path(item["location_id"]) if item["location_id"] else ""
        return results

    def update_last_viewed(self, item_id):
        """更新物品最后查看时间"""
        self.db.execute(
            "UPDATE items SET last_viewed = datetime('now', 'localtime') WHERE id = ?",
            (item_id,)
        )

    def get_categories(self):
        """获取所有物品类别"""
        result = self.db.query(
            "SELECT DISTINCT category FROM items WHERE category IS NOT NULL AND category != '' ORDER BY category"
        )
        return [row["category"] for row in result]

    def get_items_by_status(self, status):
        """按状态获取物品"""
        return self.get_all_items(status=status)

    def get_loaned_items(self):
        """获取借出中的物品，包含借出信息"""
        return self.db.query("""
            SELECT i.*, l.borrower_name, l.borrower_contact, l.loan_date,
                   l.expected_return_date, l.id as loan_id
            FROM items i
            JOIN loans l ON i.id = l.item_id
            WHERE l.status = '借出中'
            ORDER BY l.expected_return_date ASC
        """)

    def get_location_history(self, item_id):
        """获取物品的位置变更历史"""
        return self.db.query("""
            SELECT lh.*, f.name as from_location_name, t.name as to_location_name
            FROM location_history lh
            LEFT JOIN locations f ON lh.from_location_id = f.id
            LEFT JOIN locations t ON lh.to_location_id = t.id
            WHERE lh.item_id = ?
            ORDER BY lh.changed_at DESC
        """, (item_id,))

    def _record_location_change(self, item_id, from_loc_id, to_loc_id, change_type, notes=None):
        """记录位置变更"""
        self.db.execute("""
            INSERT INTO location_history (item_id, from_location_id, to_location_id, change_type, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, from_loc_id, to_loc_id, change_type, notes))

    def _record_search(self, keyword):
        """记录搜索历史"""
        existing = self.db.query_one(
            "SELECT * FROM search_history WHERE keyword = ?",
            (keyword,)
        )
        if existing:
            self.db.execute(
                """UPDATE search_history SET search_count = search_count + 1,
                   last_searched = datetime('now', 'localtime') WHERE keyword = ?""",
                (keyword,)
            )
        else:
            self.db.execute(
                "INSERT INTO search_history (keyword) VALUES (?)",
                (keyword,)
            )

    def get_search_history(self, limit=20):
        """获取搜索历史"""
        return self.db.query(
            "SELECT * FROM search_history ORDER BY last_searched DESC LIMIT ?",
            (limit,)
        )

    def get_long_unviewed_items(self, days=30, limit=10, status=None):
        """获取长期未查看的物品（整理建议）"""
        sql = """
            SELECT i.*, l.name as location_name
            FROM items i LEFT JOIN locations l ON i.location_id = l.id
            WHERE (i.last_viewed IS NULL
                   OR julianday('now') - julianday(i.last_viewed) > ?)
        """
        params = [days]

        if status:
            sql += " AND i.status = ?"
            params.append(status)

        sql += " ORDER BY COALESCE(i.last_viewed, i.created_at) ASC LIMIT ?"
        params.append(limit)

        return self.db.query(sql, params)

    def get_statistics(self):
        """获取统计信息"""
        total = self.db.query_one("SELECT COUNT(*) as cnt FROM items")["cnt"]
        in_stock = self.db.query_one("SELECT COUNT(*) as cnt FROM items WHERE status = '在库'")["cnt"]
        loaned = self.db.query_one("SELECT COUNT(*) as cnt FROM items WHERE status = '借出中'")["cnt"]
        temporary = self.db.query_one("SELECT COUNT(*) as cnt FROM items WHERE status = '临时取出'")["cnt"]
        categories = self.db.query_one("SELECT COUNT(DISTINCT category) as cnt FROM items WHERE category IS NOT NULL")["cnt"]

        return {
            "total": total,
            "in_stock": in_stock,
            "loaned": loaned,
            "temporary": temporary,
            "categories": categories
        }
