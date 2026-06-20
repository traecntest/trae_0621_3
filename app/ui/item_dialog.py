"""物品编辑对话框 - 物品录入和编辑界面"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QFileDialog, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from app.services.location_service import LocationService
from app.services.item_service import ItemService
import os


class ItemDialog(QDialog):
    """物品录入/编辑对话框"""

    def __init__(self, parent=None, item_id=None):
        super().__init__(parent)
        self.item_id = item_id
        self.location_service = LocationService()
        self.item_service = ItemService()
        self.photo_path = None

        self.setWindowTitle("编辑物品" if item_id else "新增物品")
        self.setMinimumSize(500, 600)
        self._init_ui()

        if item_id:
            self._load_item_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入物品名称")
        form_layout.addRow("物品名称*:", self.name_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("如：电子产品、书籍、衣物等")
        form_layout.addRow("类别:", self.category_edit)

        brand_model_layout = QHBoxLayout()
        self.brand_edit = QLineEdit()
        self.brand_edit.setPlaceholderText("品牌")
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("型号")
        brand_model_layout.addWidget(self.brand_edit)
        brand_model_layout.addWidget(self.model_edit)
        form_layout.addRow("品牌/型号:", brand_model_layout)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setValue(1)
        form_layout.addRow("数量:", self.quantity_spin)

        date_layout = QHBoxLayout()
        self.purchase_date = QDateEdit()
        self.purchase_date.setCalendarPopup(True)
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setDisplayFormat("yyyy-MM-dd")
        self.warranty_edit = QLineEdit()
        self.warranty_edit.setPlaceholderText("如：1年、2年")
        date_layout.addWidget(QLabel("购买日期:"))
        date_layout.addWidget(self.purchase_date)
        date_layout.addWidget(QLabel("保固:"))
        date_layout.addWidget(self.warranty_edit)
        form_layout.addRow("", date_layout)

        self.status_combo = QComboBox()
        for status in [ItemService.STATUS_IN_STOCK, ItemService.STATUS_LOANED,
                       ItemService.STATUS_TEMPORARY, ItemService.STATUS_LOST,
                       ItemService.STATUS_DISCARDED]:
            self.status_combo.addItem(status)
        form_layout.addRow("状态:", self.status_combo)

        self.location_combo = QComboBox()
        self._populate_locations()
        form_layout.addRow("存放位置:", self.location_combo)

        self.photo_label = QLabel("暂无照片")
        self.photo_label.setFixedSize(120, 120)
        self.photo_label.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_btn = QPushButton("选择照片")
        self.photo_btn.clicked.connect(self._select_photo)
        photo_layout = QHBoxLayout()
        photo_layout.addWidget(self.photo_label)
        photo_layout.addWidget(self.photo_btn)
        photo_layout.addStretch()
        form_layout.addRow("物品照片:", photo_layout)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("备注信息...")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("备注:", self.notes_edit)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    def _populate_locations(self):
        """填充位置下拉框"""
        self.location_combo.clear()
        self.location_combo.addItem("（未设置位置", None)

        locations = self.location_service.get_all_locations()
        for loc in locations:
            path = self.location_service.get_location_path(loc["id"])
            self.location_combo.addItem(path, loc["id"])

    def _select_photo(self):
        """选择物品照片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择照片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.photo_path = file_path
            pixmap = QPixmap(file_path)
            self.photo_label.setPixmap(pixmap.scaled(
                120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def _load_item_data(self):
        """加载物品数据"""
        item = self.item_service.get_item_by_id(self.item_id)
        if not item:
            return

        self.name_edit.setText(item["name"] or "")
        self.category_edit.setText(item["category"] or "")
        self.brand_edit.setText(item["brand"] or "")
        self.model_edit.setText(item["model"] or "")
        self.quantity_spin.setValue(item["quantity"] or 1)

        if item["purchase_date"]:
            date = QDate.fromString(item["purchase_date"], "yyyy-MM-dd")
            self.purchase_date.setDate(date)

        self.warranty_edit.setText(item["warranty_period"] or "")

        status = item["status"] or ItemService.STATUS_IN_STOCK
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        if item["location_id"]:
            idx = self.location_combo.findData(item["location_id"])
            if idx >= 0:
                self.location_combo.setCurrentIndex(idx)

        if item["photo_path"] and os.path.exists(item["photo_path"]):
            self.photo_path = item["photo_path"]
            pixmap = QPixmap(item["photo_path"])
            self.photo_label.setPixmap(pixmap.scaled(
                120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

        self.notes_edit.setPlainText(item["notes"] or "")

    def _on_save(self):
        """保存物品"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入物品名称")
            return

        location_id = self.location_combo.currentData()

        data = {
            "name": name,
            "category": self.category_edit.text().strip() or None,
            "brand": self.brand_edit.text().strip() or None,
            "model": self.model_edit.text().strip() or None,
            "quantity": self.quantity_spin.value(),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "warranty_period": self.warranty_edit.text().strip() or None,
            "status": self.status_combo.currentText(),
            "location_id": location_id,
            "photo_path": self.photo_path,
            "notes": self.notes_edit.toPlainText().strip() or None
        }

        try:
            if self.item_id:
                self.item_service.update_item(self.item_id, **data)
            else:
                self.item_service.add_item(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
