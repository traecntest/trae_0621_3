"""借出管理对话框 - 借出登记和归还管理"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QDateEdit, QFormLayout,
    QMessageBox, QTabWidget, QWidget, QHeaderView, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush
from app.services.loan_service import LoanService
from app.services.item_service import ItemService
from datetime import datetime


class LoanDialog(QDialog):
    """借出管理对话框"""

    def __init__(self, parent=None, item_id=None):
        super().__init__(parent)
        self.loan_service = LoanService()
        self.item_service = ItemService()
        self.current_item_id = item_id

        self.setWindowTitle("借出管理")
        self.setMinimumSize(700, 500)
        self._init_ui()
        self._refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        self.active_tab = QWidget()
        self._init_active_tab()
        self.tabs.addTab(self.active_tab, "借出中")

        self.history_tab = QWidget()
        self._init_history_tab()
        self.tabs.addTab(self.history_tab, "历史记录")

        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def _init_active_tab(self):
        layout = QVBoxLayout(self.active_tab)

        toolbar = QHBoxLayout()
        self.add_loan_btn = QPushButton("新增借出")
        self.add_loan_btn.clicked.connect(self._add_loan)
        self.return_btn = QPushButton("登记归还")
        self.return_btn.clicked.connect(self._return_item)
        self.edit_loan_btn = QPushButton("编辑")
        self.edit_loan_btn.clicked.connect(self._edit_loan)

        toolbar.addWidget(self.add_loan_btn)
        toolbar.addWidget(self.return_btn)
        toolbar.addWidget(self.edit_loan_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        self.active_table = QTableWidget()
        self.active_table.setColumnCount(6)
        self.active_table.setHorizontalHeaderLabels(
            ["物品", "借用人", "联系方式", "借出日期", "预计归还", "状态"]
        )
        self.active_table.horizontalHeader().setStretchLastSection(True)
        self.active_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.active_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.active_table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.active_table)

    def _init_history_tab(self):
        layout = QVBoxLayout(self.history_tab)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索借用人或物品...")
        self.search_edit.textChanged.connect(self._refresh_history)
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.search_edit)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(
            ["物品", "借用人", "借出日期", "预计归还", "实际归还", "状态", "备注"]
        )
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.history_table)

    def _refresh_data(self):
        """刷新所有数据"""
        self._refresh_active()
        self._refresh_history()

    def _refresh_active(self):
        """刷新借出中列表"""
        loans = self.loan_service.get_active_loans()

        if self.current_item_id:
            loans = [l for l in loans if l["item_id"] == self.current_item_id]

        self.active_table.setRowCount(len(loans))

        today = datetime.now().date()

        for row, loan in enumerate(loans):
            self.active_table.setItem(row, 0, QTableWidgetItem(loan["item_name"]))
            self.active_table.setItem(row, 1, QTableWidgetItem(loan["borrower_name"]))
            self.active_table.setItem(row, 2, QTableWidgetItem(loan["borrower_contact"] or ""))
            self.active_table.setItem(row, 3, QTableWidgetItem(loan["loan_date"]))

            expected = loan["expected_return_date"] or ""
            self.active_table.setItem(row, 4, QTableWidgetItem(expected))

            status_text = "借出中"
            status_color = QColor("#2196F3")

            if expected:
                try:
                    exp_date = datetime.strptime(expected, "%Y-%m-%d").date()
                    days_left = (exp_date - today).days
                    if days_left < 0:
                        status_text = f"已逾期{abs(days_left)}天"
                        status_color = QColor("#F44336")
                    elif days_left <= 3:
                        status_text = f"即将到期({days_left}天)"
                        status_color = QColor("#FF9800")
                except:
                    pass

            item = QTableWidgetItem(status_text)
            item.setForeground(QBrush(status_color))
            self.active_table.setItem(row, 5, item)

            self.active_table.item(row, 0).setData(Qt.UserRole, loan["id"])

        self.active_table.resizeColumnsToContents()

    def _refresh_history(self):
        """刷新历史记录"""
        keyword = self.search_edit.text().strip()

        all_loans = self.loan_service.get_all_loans()
        if keyword:
            all_loans = [
                l for l in all_loans
                if keyword.lower() in l["item_name"].lower()
                or keyword.lower() in l["borrower_name"].lower()
            ]

        self.history_table.setRowCount(len(all_loans))

        for row, loan in enumerate(all_loans):
            self.history_table.setItem(row, 0, QTableWidgetItem(loan["item_name"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(loan["borrower_name"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(loan["loan_date"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(loan["expected_return_date"] or ""))
            self.history_table.setItem(row, 4, QTableWidgetItem(loan["actual_return_date"] or ""))
            self.history_table.setItem(row, 5, QTableWidgetItem(loan["status"]))
            self.history_table.setItem(row, 6, QTableWidgetItem(loan["notes"] or ""))
            self.history_table.item(row, 0).setData(Qt.UserRole, loan["id"])

        self.history_table.resizeColumnsToContents()

    def _get_selected_loan_id(self):
        """获取当前选中的借出记录ID"""
        current_tab = self.tabs.currentIndex()
        table = self.active_table if current_tab == 0 else self.history_table

        current_row = table.currentRow()
        if current_row < 0:
            return None

        item = table.item(current_row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_loan(self):
        """新增借出记录"""
        dialog = LoanEditDialog(self, item_id=self.current_item_id)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_data()

    def _return_item(self):
        """登记归还"""
        loan_id = self._get_selected_loan_id()
        if not loan_id:
            QMessageBox.information(self, "提示", "请先选择一条借出记录")
            return

        loan = self.loan_service.get_loan_by_id(loan_id)
        if not loan or loan["status"] != LoanService.STATUS_ACTIVE:
            QMessageBox.information(self, "提示", "该记录不是借出中状态")
            return

        reply = QMessageBox.question(
            self, "确认归还",
            f"确定「{loan['item_name']}」已归还吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                self.loan_service.return_item(loan_id)
                self._refresh_data()
                QMessageBox.information(self, "成功", "归还登记成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def _edit_loan(self):
        """编辑借出记录"""
        loan_id = self._get_selected_loan_id()
        if not loan_id:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return

        dialog = LoanEditDialog(self, loan_id=loan_id)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_data()


class LoanEditDialog(QDialog):
    """借出编辑对话框"""

    def __init__(self, parent=None, loan_id=None, item_id=None):
        super().__init__(parent)
        self.loan_id = loan_id
        self.initial_item_id = item_id
        self.loan_service = LoanService()
        self.item_service = ItemService()

        self.setWindowTitle("编辑借出" if loan_id else "新增借出")
        self.setMinimumWidth(400)
        self._init_ui()

        if loan_id:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.item_combo = QComboBox()
        items = self.item_service.get_all_items(status="在库")
        for item in items:
            self.item_combo.addItem(item["name"], item["id"])

        if self.loan_id:
            self.item_combo.setEnabled(False)

        if self.initial_item_id:
            idx = self.item_combo.findData(self.initial_item_id)
            if idx >= 0:
                self.item_combo.setCurrentIndex(idx)

        form_layout.addRow("物品*:", self.item_combo)

        self.borrower_edit = QLineEdit()
        self.borrower_edit.setPlaceholderText("借用人姓名")

        borrowers = self.loan_service.get_borrower_list()
        self.borrower_completer = None

        form_layout.addRow("借用人*:", self.borrower_edit)

        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("联系方式（可选）")
        form_layout.addRow("联系方式:", self.contact_edit)

        self.loan_date = QDateEdit()
        self.loan_date.setCalendarPopup(True)
        self.loan_date.setDate(QDate.currentDate())
        self.loan_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("借出日期:", self.loan_date)

        self.expected_date = QDateEdit()
        self.expected_date.setCalendarPopup(True)
        self.expected_date.setDate(QDate.currentDate().addDays(7))
        self.expected_date.setDisplayFormat("yyyy-MM-dd")
        self.expected_date.setSpecialValueText("（不限）")
        form_layout.addRow("预计归还:", self.expected_date)

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("备注（可选）")
        form_layout.addRow("备注:", self.notes_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """加载借出数据"""
        loan = self.loan_service.get_loan_by_id(self.loan_id)
        if not loan:
            return

        idx = self.item_combo.findData(loan["item_id"])
        if idx >= 0:
            self.item_combo.setCurrentIndex(idx)

        self.borrower_edit.setText(loan["borrower_name"])
        self.contact_edit.setText(loan["borrower_contact"] or "")

        if loan["loan_date"]:
            date = QDate.fromString(loan["loan_date"], "yyyy-MM-dd")
            self.loan_date.setDate(date)

        if loan["expected_return_date"]:
            date = QDate.fromString(loan["expected_return_date"], "yyyy-MM-dd")
            self.expected_date.setDate(date)

        self.notes_edit.setText(loan["notes"] or "")

    def _on_ok(self):
        """确认保存"""
        item_id = self.item_combo.currentData()
        borrower = self.borrower_edit.text().strip()

        if not item_id:
            QMessageBox.warning(self, "提示", "请选择物品")
            return
        if not borrower:
            QMessageBox.warning(self, "提示", "请输入借用人姓名")
            return

        try:
            if self.loan_id:
                self.loan_service.update_loan(
                    self.loan_id,
                    borrower_name=borrower,
                    borrower_contact=self.contact_edit.text().strip() or None,
                    expected_return_date=self.expected_date.date().toString("yyyy-MM-dd"),
                    notes=self.notes_edit.text().strip() or None
                )
            else:
                self.loan_service.create_loan(
                    item_id=item_id,
                    borrower_name=borrower,
                    borrower_contact=self.contact_edit.text().strip() or None,
                    loan_date=self.loan_date.date().toString("yyyy-MM-dd"),
                    expected_return_date=self.expected_date.date().toString("yyyy-MM-dd"),
                    notes=self.notes_edit.text().strip() or None
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
