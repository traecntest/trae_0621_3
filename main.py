"""桌面物品管理系统 - 主入口"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("桌面物品管理系统")
    app.setOrganizationName("InventoryManager")

    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QToolBar {
            background-color: white;
            border: none;
            padding: 4px;
            spacing: 4px;
        }
        QToolBar QToolButton {
            padding: 6px 12px;
            border-radius: 4px;
        }
        QToolBar QToolButton:hover {
            background-color: #e3f2fd;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            gridline-color: #f0f0f0;
        }
        QTableWidget::item {
            padding: 4px;
        }
        QTableWidget::item:selected {
            background-color: #2196F3;
            color: white;
        }
        QHeaderView::section {
            background-color: #fafafa;
            padding: 6px;
            border: none;
            border-bottom: 2px solid #e0e0e0;
            font-weight: bold;
        }
        QTreeWidget {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
        QTreeWidget::item {
            padding: 4px;
        }
        QTreeWidget::item:selected {
            background-color: #2196F3;
            color: white;
        }
        QTabWidget::pane {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            top: -1px;
        }
        QTabBar::tab {
            background-color: #f5f5f5;
            padding: 8px 16px;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
        }
        QTabBar::tab:selected {
            background-color: white;
            color: #2196F3;
        }
        QPushButton {
            padding: 6px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
        QPushButton:hover {
            background-color: #f5f5f5;
        }
        QPushButton:pressed {
            background-color: #e0e0e0;
        }
        QPushButton:default {
            background-color: #2196F3;
            color: white;
            border: 1px solid #2196F3;
        }
        QPushButton:default:hover {
            background-color: #1976D2;
        }
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit {
            padding: 6px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QTextEdit:focus {
            border-color: #2196F3;
        }
        QStatusBar {
            background-color: white;
            border-top: 1px solid #e0e0e0;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
