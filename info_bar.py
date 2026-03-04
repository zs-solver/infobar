"""
单行信息条工具 - 可调整列宽的置顶窗口
"""
import sys
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from widgets import EditableField
from storage import Storage
from theme import ThemeManager
from theme_dialog import ThemeDialog
from tray_manager import TrayManager

class InfoBar(QWidget):
    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.config = self.storage.load()
        self.theme = ThemeManager(self.config["theme"])
        self.fields = []
        self.init_ui()
        self.tray = TrayManager(self)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.splitter = QSplitter(Qt.Horizontal)
        font = QFont("Microsoft YaHei", 10)

        for col in self.config["columns"]:
            field = EditableField(col)
            field.setFont(font)
            field.setStyleSheet(self.theme.get_stylesheet())
            field.contentChanged.connect(self.save_config)
            field.contentChanged.connect(self.sync_heights)
            self.fields.append(field)
            self.splitter.addWidget(field)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        win = self.config["window"]
        self.resize(win["width"], win["height"])
        self.move(win["x"], win["y"])
        self.sync_heights()

    def sync_heights(self):
        """统一所有字段高度为最高字段的高度，避免透明穿透"""
        max_height = max(field.get_content_height() for field in self.fields)
        for field in self.fields:
            field.setFixedHeight(max_height)

    def save_config(self):
        for i, field in enumerate(self.fields):
            self.config["columns"][i] = field.toPlainText()

        pos = self.pos()
        self.config["window"] = {
            "x": pos.x(), "y": pos.y(),
            "width": self.width(), "height": self.height()
        }
        self.config["theme"] = self.theme.to_dict()
        self.storage.save(self.config)

    def closeEvent(self, event):
        self.save_config()
        self.hide()
        event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        theme_action = menu.addAction("主题设置")
        theme_action.triggered.connect(self.open_theme_dialog)
        hide_action = menu.addAction("隐藏到托盘")
        hide_action.triggered.connect(self.hide)
        menu.exec_(event.globalPos())

    def open_theme_dialog(self):
        dialog = ThemeDialog(self.theme, self)
        if dialog.exec_():
            self.config["theme"] = dialog.get_theme_config()
            self.apply_theme()
            self.save_config()

    def apply_theme(self):
        stylesheet = self.theme.get_stylesheet()
        for field in self.fields:
            field.setStyleSheet(stylesheet)
