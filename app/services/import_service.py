"""导入服务 - CSV批量导入和测试数据生成"""

import csv
import os
from datetime import datetime, timedelta
import random
from app.database.db_manager import DatabaseManager
from app.services.item_service import ItemService
from app.services.location_service import LocationService
from app.services.loan_service import LoanService


class ImportService:
    """数据导入服务"""

    def __init__(self):
        self.db = DatabaseManager()
        self.item_service = ItemService()
        self.location_service = LocationService()
        self.loan_service = LoanService()

    def import_from_csv(self, file_path, has_header=True):
        """从CSV文件批量导入物品"""
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)

        start_idx = 1 if has_header else 0

        for i, row in enumerate(rows[start_idx:], start=start_idx + 1):
            try:
                if len(row) < 1 or not row[0].strip():
                    continue

                name = row[0].strip() if len(row) > 0 else ""
                category = row[1].strip() if len(row) > 1 and row[1].strip() else None
                brand = row[2].strip() if len(row) > 2 and row[2].strip() else None
                model = row[3].strip() if len(row) > 3 and row[3].strip() else None
                quantity = int(row[4]) if len(row) > 4 and row[4].strip() else 1
                purchase_date = row[5].strip() if len(row) > 5 and row[5].strip() else None
                warranty_period = row[6].strip() if len(row) > 6 and row[6].strip() else None
                location_name = row[7].strip() if len(row) > 7 and row[7].strip() else None
                notes = row[8].strip() if len(row) > 8 and row[8].strip() else None

                location_id = None
                if location_name:
                    location_id = self._find_or_create_location(location_name)

                self.item_service.add_item(
                    name=name,
                    category=category,
                    brand=brand,
                    model=model,
                    quantity=quantity,
                    purchase_date=purchase_date,
                    warranty_period=warranty_period,
                    location_id=location_id,
                    notes=notes
                )
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"第{i}行: {str(e)}")

        return results

    def _find_or_create_location(self, location_path):
        """根据位置路径查找或创建位置"""
        parts = [p.strip() for p in location_path.replace('\\', '/').split('/') if p.strip()]
        if not parts:
            return None

        parent_id = None
        for idx, part in enumerate(parts):
            existing = self.db.query_one(
                "SELECT * FROM locations WHERE name = ? AND parent_id IS ?",
                (part, parent_id)
            )
            if existing:
                parent_id = existing["id"]
            else:
                code = f"{part.upper()}_{random.randint(100, 999)}"
                cursor = self.db.execute(
                    "INSERT INTO locations (name, code, parent_id, level) VALUES (?, ?, ?, ?)",
                    (part, code, parent_id, idx + 1)
                )
                parent_id = cursor.lastrowid

        return parent_id

    def generate_test_data(self):
        """生成测试数据"""
        locations = self._generate_test_locations()
        items = self._generate_test_items(locations)
        loans = self._generate_test_loans(items)

        return {
            "locations": len(locations),
            "items": items,
            "loans": loans
        }

    def _generate_test_locations(self):
        """生成测试位置数据"""
        all_locations = self.location_service.get_all_locations()
        has_children = any(loc["level"] > 1 for loc in all_locations)

        if has_children:
            return [loc["id"] for loc in all_locations]

        name_to_id = {loc["name"]: loc["id"] for loc in all_locations}

        child_locations = [
            ("01号柜", "LIVING-01", "客厅", 2),
            ("第1层", "LIVING-01-1", "01号柜", 3),
            ("第2层", "LIVING-01-2", "01号柜", 3),
            ("第3层", "LIVING-01-3", "01号柜", 3),
            ("电视柜", "LIVING-TV", "客厅", 2),
            ("沙发旁", "LIVING-SOFA", "客厅", 2),
            ("衣柜", "BED-CLOSET", "卧室", 2),
            ("上层", "BED-CLOSET-TOP", "衣柜", 3),
            ("中层", "BED-CLOSET-MID", "衣柜", 3),
            ("下层", "BED-CLOSET-BOT", "衣柜", 3),
            ("床头柜", "BED-TABLE", "卧室", 2),
            ("书架", "STUDY-BOOK", "书房", 2),
            ("A区", "STUDY-BOOK-A", "书架", 3),
            ("B区", "STUDY-BOOK-B", "书架", 3),
            ("书桌", "STUDY-DESK", "书房", 2),
            ("储物架A", "STORAGE-A", "储物间", 2),
            ("储物架B", "STORAGE-B", "储物间", 2),
            ("橱柜", "KITCHEN-CAB", "厨房", 2),
            ("冰箱", "KITCHEN-FRIDGE", "厨房", 2),
        ]

        for name, code, parent_name, level in child_locations:
            parent_id = name_to_id.get(parent_name)
            loc_id = self.location_service.add_location(
                name=name, code=code, parent_id=parent_id
            )
            name_to_id[name] = loc_id

        return list(name_to_id.values())

    def _generate_test_items(self, location_ids):
        """生成测试物品数据"""
        item_templates = [
            ("无线耳机", "电子产品", "索尼", "WH-1000XM5", 1),
            ("笔记本电脑", "电子产品", "联想", "ThinkPad X1", 1),
            ("机械键盘", "电子产品", "樱桃", "MX 3.0S", 1),
            ("鼠标", "电子产品", "罗技", "MX Master 3", 2),
            ("移动硬盘", "电子产品", "西部数据", "2TB", 3),
            ("U盘", "电子产品", "金士顿", "64GB", 5),
            ("充电器", "电子产品", "小米", "65W GaN", 4),
            ("数据线", "电子产品", "品胜", "Type-C 1m", 10),
            ("蓝牙音箱", "电子产品", "JBL", "Flip 5", 1),
            ("智能手表", "电子产品", "华为", "Watch GT3", 1),

            ("《Python编程从入门到实践》", "书籍", "人民邮电", "", 1),
            ("《深入理解计算机系统》", "书籍", "机械工业", "", 1),
            ("《设计模式》", "书籍", "机械工业", "", 1),
            ("《代码整洁之道》", "书籍", "人民邮电", "", 1),
            ("笔记本", "文具", "得力", "A5", 8),
            ("签字笔", "文具", "晨光", "0.5mm黑色", 20),
            ("文件夹", "文具", "得力", "A4蓝色", 15),
            ("便签纸", "文具", "3M", "便利贴", 6),

            ("T恤", "衣物", "优衣库", "L码", 5),
            ("牛仔裤", "衣物", "Levis", "32/32", 3),
            ("外套", "衣物", "北面", "M码", 2),
            ("运动鞋", "衣物", "耐克", "Air Max", 2),
            ("拖鞋", "衣物", "回力", "42码", 2),

            ("感冒药", "药品", "999", "感冒灵颗粒", 2),
            ("创可贴", "药品", "云南白药", "防水型", 1),
            ("维生素C", "药品", "汤臣倍健", "100片", 1),

            ("马克杯", "生活用品", "无印良品", "", 3),
            ("雨伞", "生活用品", "天堂伞", "自动折叠", 2),
            ("钥匙扣", "生活用品", "", "", 4),
            ("剪刀", "生活用品", "张小泉", "", 2),
            ("胶带", "生活用品", "3M", "透明胶带", 3),
            ("手电筒", "生活用品", "神火", "LED强光", 1),
            ("工具套装", "生活用品", "博世", "12件套", 1),

            ("绿茶", "食品", "西湖龙井", "明前茶", 2),
            ("咖啡豆", "食品", "星巴克", "深度烘焙", 1),
            ("巧克力", "食品", "德芙", "黑巧70%", 3),
        ]

        location_names = self.location_service.get_all_locations()
        leaf_locations = [loc for loc in location_names if loc["level"] >= 2]

        count = 0
        for name, category, brand, model, qty in item_templates:
            location = random.choice(leaf_locations) if leaf_locations else None
            loc_id = location["id"] if location else None

            purchase_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            warranty = f"{random.choice([1, 2, 3])}年" if category == "电子产品" else None

            self.item_service.add_item(
                name=name,
                category=category,
                brand=brand,
                model=model,
                quantity=qty,
                purchase_date=purchase_date,
                warranty_period=warranty,
                location_id=loc_id,
                notes=f"测试物品 - {category}"
            )
            count += 1

        return count

    def _generate_test_loans(self, item_count):
        """生成测试借出记录"""
        items = self.item_service.get_all_items(status="在库")
        if not items:
            return 0

        borrowers = ["张三", "李四", "王五", "赵六", "同事小王"]
        contacts = ["13800138001", "13900139002", "13700137003", "13600136004", "13500135005"]

        loan_count = min(5, len(items))
        selected_items = random.sample(items, loan_count)

        for i, item in enumerate(selected_items):
            loan_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
            expected_date = (datetime.now() + timedelta(days=random.randint(-10, 30))).strftime("%Y-%m-%d")

            self.loan_service.create_loan(
                item_id=item["id"],
                borrower_name=borrowers[i % len(borrowers)],
                borrower_contact=contacts[i % len(contacts)],
                loan_date=loan_date,
                expected_return_date=expected_date,
                notes="测试借出记录"
            )

        return loan_count

    def export_to_csv(self, file_path):
        """导出物品数据到CSV"""
        items = self.item_service.get_all_items()

        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "名称", "类别", "品牌", "型号", "数量", "购买日期",
                "保固期限", "状态", "位置", "备注"
            ])

            for item in items:
                location_path = self.location_service.get_location_path(item["location_id"]) if item["location_id"] else ""
                writer.writerow([
                    item["name"],
                    item["category"] or "",
                    item["brand"] or "",
                    item["model"] or "",
                    item["quantity"],
                    item["purchase_date"] or "",
                    item["warranty_period"] or "",
                    item["status"],
                    location_path,
                    item["notes"] or ""
                ])

        return len(items)
