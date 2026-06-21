"""主窗口 - 桌面物品管理系统主界面"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QLabel, QSplitter, QToolBar, QStatusBar, QMessageBox, QAbstractItemView,
    QHeaderView, QMenu, QInputDialog, QFileDialog, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QBrush
from app.services.item_service import ItemService
from app.services.location_service import LocationService
from app.services.loan_service import LoanService
from app.services.import_service import ImportService
from app.ui.item_dialog import ItemDialog
from app.ui.location_dialog import LocationDialog
from app.ui.loan_dialog import LoanDialog
from datetime import datetime
import os


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.item_service = ItemService()
        self.location_service = LocationService()
        self.loan_service = LoanService()
        self.import_service = ImportService()

        self.current_search_keyword = ""
        self.current_filter_status = None
        self.current_location_id = None

        self.setWindowTitle("桌面物品管理系统")
        self.setMinimumSize(1100, 700)
        self._init_ui()
        self._refresh_all()

        QTimer.singleShot(1000, self._check_loan_reminders)

    def _init_ui(self):
        """初始化界面"""
        self._create_toolbar()
        self._create_central_widget()
        self._create_statusbar()

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        add_action = QAction("新增物品", self)
        add_action.triggered.connect(self._add_item)
        toolbar.addAction(add_action)

        edit_action = QAction("编辑物品", self)
        edit_action.triggered.connect(self._edit_item)
        toolbar.addAction(edit_action)

        delete_action = QAction("删除物品", self)
        delete_action.triggered.connect(self._delete_item)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        loan_action = QAction("借出管理", self)
        loan_action.triggered.connect(self._open_loan_manager)
        toolbar.addAction(loan_action)

        toolbar.addSeparator()

        loc_action = QAction("位置管理", self)
        loc_action.triggered.connect(self._open_location_manager)
        toolbar.addAction(loc_action)

        toolbar.addSeparator()

        import_action = QAction("导入CSV", self)
        import_action.triggered.connect(self._import_csv)
        toolbar.addAction(import_action)

        export_action = QAction("导出CSV", self)
        export_action.triggered.connect(self._export_csv)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        test_action = QAction("生成测试数据", self)
        test_action.triggered.connect(self._generate_test_data)
        toolbar.addAction(test_action)

    def _create_central_widget(self):
        """创建中心部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索物品名称、类别、品牌、型号、备注...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit, 1)

        self.status_filter = QPushButton("全部状态")
        self.status_filter.setFixedWidth(100)
        self.status_filter.setMenu(self._create_status_menu())
        search_layout.addWidget(self.status_filter)

        main_layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("位置导航:"))

        self.location_tree = QTreeWidget()
        self.location_tree.setHeaderLabels(["位置"])
        self.location_tree.setHeaderHidden(True)
        self.location_tree.itemClicked.connect(self._on_location_clicked)
        left_layout.addWidget(self.location_tree)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        self.items_tab = QWidget()
        self._init_items_tab()
        self.tabs.addTab(self.items_tab, "物品列表")

        self.tips_tab = QWidget()
        self._init_tips_tab()
        self.tabs.addTab(self.tips_tab, "整理建议")

        right_layout.addWidget(self.tabs)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def _init_items_tab(self):
        """初始化物品列表标签页"""
        layout = QVBoxLayout(self.items_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            ["名称", "类别", "品牌型号", "数量", "状态", "位置", "最后查看"]
        )
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.doubleClicked.connect(self._edit_item)
        self.items_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self._show_item_context_menu)
        layout.addWidget(self.items_table)

    def _init_tips_tab(self):
        """初始化整理建议标签页"""
        layout = QVBoxLayout(self.tips_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        tip_label = QLabel("以下物品长时间未被查看，建议检查或整理：")
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("color: #666; padding: 8px 0;")
        layout.addWidget(tip_label)

        self.tips_table = QTableWidget()
        self.tips_table.setColumnCount(4)
        self.tips_table.setHorizontalHeaderLabels(
            ["物品名称", "类别", "存放位置", "状态"]
        )
        self.tips_table.horizontalHeader().setStretchLastSection(True)
        self.tips_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tips_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tips_table)

    def _create_status_menu(self):
        """创建状态筛选菜单"""
        menu = QMenu(self)

        all_action = menu.addAction("全部状态")
        all_action.triggered.connect(lambda checked=False: self._set_status_filter(None, "全部状态"))

        menu.addSeparator()

        for status in [ItemService.STATUS_IN_STOCK, ItemService.STATUS_LOANED,
                       ItemService.STATUS_TEMPORARY, ItemService.STATUS_LOST,
                       ItemService.STATUS_DISCARDED]:
            action = menu.addAction(status)
            action.triggered.connect(
                lambda checked, s=status: self._set_status_filter(s, s)
            )

        return menu

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _set_status_filter(self, status, text):
        """设置状态筛选"""
        self.current_filter_status = status
        self.status_filter.setText(text)
        self._refresh_items()
        self._refresh_tips()

    def _refresh_all(self):
        """刷新所有数据"""
        self._refresh_location_tree()
        self._refresh_items()
        self._refresh_tips()
        self._update_status_bar()

    def _refresh_location_tree(self):
        """刷新位置树"""
        self.location_tree.clear()

        all_item = QTreeWidgetItem(["全部物品"])
        all_item.setData(0, Qt.UserRole, None)
        self.location_tree.addTopLevelItem(all_item)

        tree_data = self.location_service.get_location_tree()
        self._add_location_tree_items(self.location_tree.invisibleRootItem(), tree_data)

        self.location_tree.expandAll()

    def _add_location_tree_items(self, parent_item, locations):
        """递归添加位置树节点"""
        for loc in locations:
            item = QTreeWidgetItem([loc["name"]])
            item.setData(0, Qt.UserRole, loc["id"])
            parent_item.addChild(item)

            if loc.get("children"):
                self._add_location_tree_items(item, loc["children"])

    def _refresh_items(self):
        """刷新物品列表"""
        if self.current_search_keyword:
            items = self.item_service.search_items(
                self.current_search_keyword,
                status=self.current_filter_status,
                location_id=self.current_location_id
            )
        else:
            items = self.item_service.get_all_items(
                status=self.current_filter_status,
                location_id=self.current_location_id
            )

        self.items_table.setRowCount(len(items))

        status_colors = {
            ItemService.STATUS_IN_STOCK: QColor("#4CAF50"),
            ItemService.STATUS_LOANED: QColor("#F44336"),
            ItemService.STATUS_TEMPORARY: QColor("#FF9800"),
            ItemService.STATUS_LOST: QColor("#9E9E9E"),
            ItemService.STATUS_DISCARDED: QColor("#9E9E9E"),
        }

        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(item["category"] or ""))
            brand_model = f"{item['brand'] or ''} {item['model'] or ''}".strip()
            self.items_table.setItem(row, 2, QTableWidgetItem(brand_model))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item["quantity"])))

            status_item = QTableWidgetItem(item["status"])
            color = status_colors.get(item["status"], QColor("#666"))
            status_item.setForeground(QBrush(color))
            self.items_table.setItem(row, 4, status_item)

            location_path = self.location_service.get_location_path(item["location_id"]) if item["location_id"] else "—"
            self.items_table.setItem(row, 5, QTableWidgetItem(location_path))

            last_viewed = item["last_viewed"] or "—"
            if last_viewed != "—":
                try:
                    dt = datetime.strptime(last_viewed, "%Y-%m-%d %H:%M:%S")
                    last_viewed = dt.strftime("%m-%d %H:%M")
                except:
                    pass
            self.items_table.setItem(row, 6, QTableWidgetItem(last_viewed))

            self.items_table.item(row, 0).setData(Qt.UserRole, item["id"])

        self.items_table.resizeColumnsToContents()

    def _refresh_tips(self):
        """刷新整理建议"""
        items = self.item_service.get_long_unviewed_items(
            days=30, limit=20, status=self.current_filter_status
        )
        self.tips_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.tips_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.tips_table.setItem(row, 1, QTableWidgetItem(item["category"] or ""))
            location_path = self.location_service.get_location_path(item["location_id"]) if item["location_id"] else "—"
            self.tips_table.setItem(row, 2, QTableWidgetItem(location_path))
            self.tips_table.setItem(row, 3, QTableWidgetItem(item["status"]))
            self.tips_table.item(row, 0).setData(Qt.UserRole, item["id"])

        self.tips_table.resizeColumnsToContents()

    def _update_status_bar(self):
        """更新状态栏"""
        stats = self.item_service.get_statistics()
        msg = f"物品总数: {stats['total']}  |  在库: {stats['in_stock']}  |  借出中: {stats['loaned']}  |  临时取出: {stats['temporary']}  |  类别: {stats['categories']}种"
        self.status_bar.showMessage(msg)

    def _on_search(self, keyword):
        """搜索物品"""
        self.current_search_keyword = keyword.strip()
        self._refresh_items()

    def _on_location_clicked(self, item, column):
        """点击位置树"""
        location_id = item.data(0, Qt.UserRole)
        self.current_location_id = location_id
        self._refresh_items()

    def _get_selected_item_id(self):
        """获取当前选中的物品ID"""
        current_row = self.items_table.currentRow()
        if current_row < 0:
            return None
        item = self.items_table.item(current_row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_item(self):
        """新增物品"""
        dialog = ItemDialog(self)
        if dialog.exec() == ItemDialog.Accepted:
            self._refresh_all()

    def _edit_item(self):
        """编辑物品"""
        item_id = self._get_selected_item_id()
        if not item_id:
            QMessageBox.information(self, "提示", "请先选择一个物品")
            return

        self.item_service.update_last_viewed(item_id)

        dialog = ItemDialog(self, item_id=item_id)
        if dialog.exec() == ItemDialog.Accepted:
            self._refresh_all()

    def _delete_item(self):
        """删除物品"""
        item_id = self._get_selected_item_id()
        if not item_id:
            QMessageBox.information(self, "提示", "请先选择一个物品")
            return

        item = self.item_service.get_item_by_id(item_id)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除物品「{item['name']}」吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.item_service.delete_item(item_id)
            self._refresh_all()

    def _show_item_context_menu(self, pos):
        """显示物品右键菜单"""
        item_id = self._get_selected_item_id()
        if not item_id:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(self._edit_item)

        loan_action = menu.addAction("借出登记")
        loan_action.triggered.connect(lambda: self._loan_item(item_id))

        return_action = menu.addAction("归还登记")
        return_action.triggered.connect(lambda: self._return_item(item_id))

        menu.addSeparator()

        temp_action = menu.addAction("标记为临时取出")
        temp_action.triggered.connect(lambda: self._mark_temporary(item_id))

        menu.addSeparator()

        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(self._delete_item)

        menu.exec(self.items_table.mapToGlobal(pos))

    def _loan_item(self, item_id):
        """借出物品"""
        item = self.item_service.get_item_by_id(item_id)
        if item["status"] == ItemService.STATUS_LOANED:
            QMessageBox.information(self, "提示", "该物品已借出")
            return

        dialog = LoanDialog(self, item_id=item_id)
        dialog.exec()
        self._refresh_all()

    def _return_item(self, item_id):
        """归还物品"""
        loans = self.loan_service.get_all_loans(status="借出中", item_id=item_id)
        if not loans:
            QMessageBox.information(self, "提示", "该物品没有借出记录")
            return

        loan = loans[0]
        reply = QMessageBox.question(
            self, "确认归还",
            f"确定「{loan['item_name']}」已归还吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.loan_service.return_item(loan["id"])
            self._refresh_all()

    def _mark_temporary(self, item_id):
        """标记为临时取出"""
        item = self.item_service.get_item_by_id(item_id)
        new_status = ItemService.STATUS_TEMPORARY
        if item["status"] == ItemService.STATUS_TEMPORARY:
            new_status = ItemService.STATUS_IN_STOCK

        self.item_service.update_item(item_id, status=new_status)
        self._refresh_all()

    def _open_loan_manager(self):
        """打开借出管理"""
        dialog = LoanDialog(self)
        dialog.exec()
        self._refresh_all()

    def _open_location_manager(self):
        """打开位置管理"""
        dialog = LocationDialog(self)
        dialog.exec()
        self._refresh_location_tree()

    def _import_csv(self):
        """导入CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv)"
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self, "确认导入",
            "确定要从CSV文件导入物品吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            try:
                result = self.import_service.import_from_csv(file_path)
                msg = f"导入完成！\n成功: {result['success']} 条\n失败: {result['failed']} 条"
                if result["errors"]:
                    msg += "\n\n错误详情:\n" + "\n".join(result["errors"][:5])
                QMessageBox.information(self, "导入结果", msg)
                self._refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def _export_csv(self):
        """导出CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "items.csv", "CSV文件 (*.csv)"
        )
        if not file_path:
            return

        try:
            count = self.import_service.export_to_csv(file_path)
            QMessageBox.information(self, "导出成功", f"成功导出 {count} 条物品记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _generate_test_data(self):
        """生成测试数据"""
        reply = QMessageBox.question(
            self, "生成测试数据",
            "确定要生成测试数据吗？\n这会添加一些示例物品和位置。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            result = self.import_service.generate_test_data()
            msg = f"测试数据生成完成！\n\n位置: {result['locations']} 个\n物品: {result['items']} 个\n借出记录: {result['loans']} 条"
            QMessageBox.information(self, "完成", msg)
            self._refresh_all()

    def _check_loan_reminders(self):
        """检查借出到期提醒"""
        overdue = self.loan_service.get_overdue_loans()
        due_soon = self.loan_service.get_loans_due_soon(days=3)

        if overdue or due_soon:
            messages = []

            if overdue:
                messages.append(f"有 {len(overdue)} 个物品已逾期：")
                for loan in overdue[:3]:
                    messages.append(f"  • {loan['item_name']} - {loan['borrower_name']}")
                if len(overdue) > 3:
                    messages.append(f"  ... 还有 {len(overdue) - 3} 个")

            if due_soon:
                if messages:
                    messages.append("")
                messages.append(f"有 {len(due_soon)} 个物品即将到期：")
                for loan in due_soon[:3]:
                    messages.append(f"  • {loan['item_name']} - {loan['expected_return_date']}")
                if len(due_soon) > 3:
                    messages.append(f"  ... 还有 {len(due_soon) - 3} 个")

            QMessageBox.information(self, "借出提醒", "\n".join(messages))
