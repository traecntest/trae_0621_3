"""位置服务 - 管理层级位置结构"""

from app.database.db_manager import DatabaseManager


class LocationService:
    """位置管理服务"""

    def __init__(self):
        self.db = DatabaseManager()

    def get_all_locations(self):
        """获取所有位置，按层级排序"""
        return self.db.query(
            "SELECT * FROM locations ORDER BY sort_order, name"
        )

    def get_root_locations(self):
        """获取一级位置（根节点）"""
        return self.db.query(
            "SELECT * FROM locations WHERE parent_id IS NULL ORDER BY sort_order, name"
        )

    def get_child_locations(self, parent_id):
        """获取指定父节点的子位置"""
        return self.db.query(
            "SELECT * FROM locations WHERE parent_id = ? ORDER BY sort_order, name",
            (parent_id,)
        )

    def get_location_by_id(self, location_id):
        """根据ID获取位置"""
        return self.db.query_one(
            "SELECT * FROM locations WHERE id = ?",
            (location_id,)
        )

    def get_location_path(self, location_id):
        """获取位置的完整路径（如：客厅 / 01号柜 / 第3层）"""
        path = []
        current_id = location_id

        while current_id:
            loc = self.get_location_by_id(current_id)
            if loc:
                path.insert(0, loc["name"])
                current_id = loc["parent_id"]
            else:
                break

        return " / ".join(path)

    def add_location(self, name, code, parent_id=None, description=None):
        """添加新位置"""
        level = 1
        if parent_id:
            parent = self.get_location_by_id(parent_id)
            if parent:
                level = parent["level"] + 1

        cursor = self.db.execute(
            """INSERT INTO locations (name, code, parent_id, level, description)
               VALUES (?, ?, ?, ?, ?)""",
            (name, code, parent_id, level, description)
        )
        return cursor.lastrowid

    def update_location(self, location_id, name, code, description=None):
        """更新位置信息"""
        self.db.execute(
            """UPDATE locations SET name = ?, code = ?, description = ?,
               updated_at = datetime('now', 'localtime') WHERE id = ?""",
            (name, code, description, location_id)
        )

    def delete_location(self, location_id):
        """删除位置（级联删除子位置）"""
        self.db.execute("DELETE FROM locations WHERE id = ?", (location_id,))

    def get_location_tree(self):
        """获取位置树结构"""
        all_locations = self.get_all_locations()
        location_map = {}
        roots = []

        for loc in all_locations:
            loc["children"] = []
            location_map[loc["id"]] = loc

        for loc in all_locations:
            if loc["parent_id"] is None:
                roots.append(loc)
            else:
                parent = location_map.get(loc["parent_id"])
                if parent:
                    parent["children"].append(loc)

        return roots

    def search_locations(self, keyword):
        """搜索位置"""
        return self.db.query(
            "SELECT * FROM locations WHERE name LIKE ? OR code LIKE ? ORDER BY name",
            (f"%{keyword}%", f"%{keyword}%")
        )

    def code_exists(self, code, exclude_id=None):
        """检查位置编码是否已存在"""
        if exclude_id:
            result = self.db.query_one(
                "SELECT COUNT(*) as cnt FROM locations WHERE code = ? AND id != ?",
                (code, exclude_id)
            )
        else:
            result = self.db.query_one(
                "SELECT COUNT(*) as cnt FROM locations WHERE code = ?",
                (code,)
            )
        return result["cnt"] > 0
