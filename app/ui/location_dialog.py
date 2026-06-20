"""位置管理对话框 - 层级位置管理界面"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QFormLayout, QMessageBox,
    QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt
from app.services.location_service import LocationService


class LocationDialog(QDialog):
    """位置管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.location_service = LocationService()
        self.setWindowTitle("位置管理")
        self.setMinimumSize(600, 500)
        self._init_ui()
        self._refresh_tree()

    def _init_ui(self):
        layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("位置结构:"))

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "编码", "层级"])
        self.tree_widget.setColumnWidth(0, 200)
        self.tree_widget.setColumnWidth(1, 100)
        left_layout.addWidget(self.tree_widget)

        btn_layout = QHBoxLayout()
        self.add_root_btn = QPushButton("添加根位置")
        self.add_root_btn.clicked.connect(self._add_root_location)
        self.add_child_btn = QPushButton("添加子位置")
        self.add_child_btn.clicked.connect(self._add_child_location)
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_location)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete_location)

        btn_layout.addWidget(self.add_root_btn)
        btn_layout.addWidget(self.add_child_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        left_layout.addLayout(btn_layout)

        layout.addLayout(left_layout, 2)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("位置详情:"))

        form_layout = QFormLayout()
        self.name_label = QLabel("—")
        self.code_label = QLabel("—")
        self.level_label = QLabel("—")
        self.parent_label = QLabel("—")
        self.desc_label = QLabel("—")
        self.desc_label.setWordWrap(True)

        form_layout.addRow("名称:", self.name_label)
        form_layout.addRow("编码:", self.code_label)
        form_layout.addRow("层级:", self.level_label)
        form_layout.addRow("父级位置:", self.parent_label)
        form_layout.addRow("描述:", self.desc_label)

        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        right_layout.addWidget(self.close_btn)

        layout.addLayout(right_layout, 1)

        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _refresh_tree(self):
        """刷新位置树"""
        self.tree_widget.clear()
        tree_data = self.location_service.get_location_tree()
        self._add_tree_items(None, tree_data)
        self.tree_widget.expandAll()

    def _add_tree_items(self, parent_item, locations):
        """递归添加树节点"""
        for loc in locations:
            item = QTreeWidgetItem()
            item.setText(0, loc["name"])
            item.setText(1, loc["code"])
            item.setText(2, str(loc["level"]))
            item.setData(0, Qt.UserRole, loc["id"])

            if parent_item is None:
                self.tree_widget.addTopLevelItem(item)
            else:
                parent_item.addChild(item)

            if loc.get("children"):
                self._add_tree_items(item, loc["children"])

    def _on_selection_changed(self):
        """选中项变化时更新详情"""
        items = self.tree_widget.selectedItems()
        if not items:
            self.name_label.setText("—")
            self.code_label.setText("—")
            self.level_label.setText("—")
            self.parent_label.setText("—")
            self.desc_label.setText("—")
            return

        item = items[0]
        loc_id = item.data(0, Qt.UserRole)
        loc = self.location_service.get_location_by_id(loc_id)

        if loc:
            self.name_label.setText(loc["name"])
            self.code_label.setText(loc["code"])
            self.level_label.setText(f"第{loc['level']}层")

            if loc["parent_id"]:
                parent = self.location_service.get_location_by_id(loc["parent_id"])
                self.parent_label.setText(parent["name"] if parent else "—")
            else:
                self.parent_label.setText("（根位置）")

            self.desc_label.setText(loc["description"] or "—")

    def _get_selected_location_id(self):
        """获取当前选中的位置ID"""
        items = self.tree_widget.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _add_root_location(self):
        """添加根位置"""
        self._show_location_dialog()

    def _add_child_location(self):
        """添加子位置"""
        parent_id = self._get_selected_location_id()
        if not parent_id:
            QMessageBox.information(self, "提示", "请先选择一个父位置")
            return
        self._show_location_dialog(parent_id=parent_id)

    def _edit_location(self):
        """编辑位置"""
        loc_id = self._get_selected_location_id()
        if not loc_id:
            QMessageBox.information(self, "提示", "请先选择要编辑的位置")
            return
        self._show_location_dialog(loc_id=loc_id)

    def _delete_location(self):
        """删除位置"""
        loc_id = self._get_selected_location_id()
        if not loc_id:
            QMessageBox.information(self, "提示", "请先选择要删除的位置")
            return

        loc = self.location_service.get_location_by_id(loc_id)
        children = self.location_service.get_child_locations(loc_id)

        msg = f"确定要删除位置「{loc['name']}」吗？"
        if children:
            msg += f"\n\n注意：该位置下有 {len(children)} 个子位置，删除后将一并删除。"

        reply = QMessageBox.question(
            self, "确认删除", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.location_service.delete_location(loc_id)
                self._refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def _show_location_dialog(self, loc_id=None, parent_id=None):
        """显示位置编辑对话框"""
        dialog = LocationEditDialog(self, loc_id, parent_id)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_tree()


class LocationEditDialog(QDialog):
    """位置编辑对话框"""

    def __init__(self, parent=None, loc_id=None, parent_id=None):
        super().__init__(parent)
        self.loc_id = loc_id
        self.parent_id = parent_id
        self.location_service = LocationService()

        if loc_id:
            self.setWindowTitle("编辑位置")
        else:
            self.setWindowTitle("添加位置")

        self.setMinimumWidth(350)
        self._init_ui()

        if loc_id:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("名称*:", self.name_edit)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("如：LIVING-01")
        form_layout.addRow("编码*:", self.code_edit)

        self.desc_edit = QLineEdit()
        form_layout.addRow("描述:", self.desc_edit)

        if self.parent_id:
            parent = self.location_service.get_location_by_id(self.parent_id)
            parent_label = QLabel(parent["name"] if parent else "—")
            form_layout.addRow("父级位置:", parent_label)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """加载位置数据"""
        loc = self.location_service.get_location_by_id(self.loc_id)
        if loc:
            self.name_edit.setText(loc["name"])
            self.code_edit.setText(loc["code"])
            self.desc_edit.setText(loc["description"] or "")
            self.parent_id = loc["parent_id"]

    def _on_ok(self):
        """确认保存"""
        name = self.name_edit.text().strip()
        code = self.code_edit.text().strip()
        desc = self.desc_edit.text().strip() or None

        if not name:
            QMessageBox.warning(self, "提示", "请输入名称")
            return
        if not code:
            QMessageBox.warning(self, "提示", "请输入编码")
            return

        if self.location_service.code_exists(code, self.loc_id):
            QMessageBox.warning(self, "提示", "编码已存在，请使用其他编码")
            return

        try:
            if self.loc_id:
                self.location_service.update_location(self.loc_id, name, code, desc)
            else:
                self.location_service.add_location(name, code, self.parent_id, desc)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
