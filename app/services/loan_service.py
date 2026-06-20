"""借出服务 - 管理物品借出和归还"""

from app.database.db_manager import DatabaseManager
from app.services.item_service import ItemService
from datetime import datetime, timedelta


class LoanService:
    """借出管理服务"""

    STATUS_ACTIVE = "借出中"
    STATUS_RETURNED = "已归还"
    STATUS_OVERDUE = "已逾期"

    def __init__(self):
        self.db = DatabaseManager()
        self.item_service = ItemService()

    def get_all_loans(self, status=None, item_id=None):
        """获取借出记录"""
        sql = """SELECT l.*, i.name as item_name, i.photo_path as item_photo
                 FROM loans l JOIN items i ON l.item_id = i.id WHERE 1=1"""
        params = []

        if status:
            sql += " AND l.status = ?"
            params.append(status)
        if item_id:
            sql += " AND l.item_id = ?"
            params.append(item_id)

        sql += " ORDER BY l.loan_date DESC"
        return self.db.query(sql, params)

    def get_active_loans(self):
        """获取所有借出中的记录"""
        return self.get_all_loans(status=self.STATUS_ACTIVE)

    def get_loan_by_id(self, loan_id):
        """根据ID获取借出记录"""
        return self.db.query_one("""
            SELECT l.*, i.name as item_name, i.photo_path as item_photo
            FROM loans l JOIN items i ON l.item_id = i.id
            WHERE l.id = ?
        """, (loan_id,))

    def create_loan(self, item_id, borrower_name, borrower_contact=None,
                    loan_date=None, expected_return_date=None, notes=None):
        """创建借出记录"""
        if loan_date is None:
            loan_date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.db.execute("""
            INSERT INTO loans (item_id, borrower_name, borrower_contact,
                               loan_date, expected_return_date, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, borrower_name, borrower_contact, loan_date,
              expected_return_date, self.STATUS_ACTIVE, notes))

        loan_id = cursor.lastrowid

        self.item_service.update_item(item_id, status=ItemService.STATUS_LOANED)

        return loan_id

    def return_item(self, loan_id, return_date=None, notes=None):
        """归还物品"""
        if return_date is None:
            return_date = datetime.now().strftime("%Y-%m-%d")

        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return False

        self.db.execute("""
            UPDATE loans SET actual_return_date = ?, status = ?, notes = ?,
                   updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (return_date, self.STATUS_RETURNED, notes, loan_id))

        self.item_service.update_item(loan["item_id"], status=ItemService.STATUS_IN_STOCK)

        return True

    def update_loan(self, loan_id, **kwargs):
        """更新借出记录"""
        allowed_fields = ["borrower_name", "borrower_contact",
                          "expected_return_date", "notes"]

        update_fields = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                update_fields.append(f"{field} = ?")
                params.append(kwargs[field])

        if not update_fields:
            return False

        update_fields.append("updated_at = datetime('now', 'localtime')")
        params.append(loan_id)

        sql = f"UPDATE loans SET {', '.join(update_fields)} WHERE id = ?"
        self.db.execute(sql, params)
        return True

    def delete_loan(self, loan_id):
        """删除借出记录"""
        loan = self.get_loan_by_id(loan_id)
        if not loan:
            return False

        self.db.execute("DELETE FROM loans WHERE id = ?", (loan_id,))

        if loan["status"] == self.STATUS_ACTIVE:
            self.item_service.update_item(loan["item_id"], status=ItemService.STATUS_IN_STOCK)

        return True

    def get_overdue_loans(self):
        """获取逾期借出记录"""
        return self.db.query("""
            SELECT l.*, i.name as item_name, i.photo_path as item_photo
            FROM loans l JOIN items i ON l.item_id = i.id
            WHERE l.status = '借出中'
              AND l.expected_return_date IS NOT NULL
              AND date(l.expected_return_date) < date('now', 'localtime')
            ORDER BY l.expected_return_date ASC
        """)

    def get_loans_due_soon(self, days=3):
        """获取即将到期的借出记录"""
        return self.db.query("""
            SELECT l.*, i.name as item_name, i.photo_path as item_photo
            FROM loans l JOIN items i ON l.item_id = i.id
            WHERE l.status = '借出中'
              AND l.expected_return_date IS NOT NULL
              AND date(l.expected_return_date) >= date('now', 'localtime')
              AND date(l.expected_return_date) <= date('now', ? || ' days', 'localtime')
            ORDER BY l.expected_return_date ASC
        """, (days,))

    def get_loan_history_by_item(self, item_id):
        """获取物品的借出历史"""
        return self.db.query("""
            SELECT * FROM loans WHERE item_id = ? ORDER BY loan_date DESC
        """, (item_id,))

    def get_borrower_list(self):
        """获取借用人列表（去重）"""
        result = self.db.query("""
            SELECT DISTINCT borrower_name FROM loans
            WHERE borrower_name IS NOT NULL AND borrower_name != ''
            ORDER BY borrower_name
        """)
        return [row["borrower_name"] for row in result]
