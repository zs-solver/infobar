"""
单行信息条工具 - 可调整列宽的置顶窗口
"""
import sys
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from widgets import EditableField
from storage import Storage
from theme import ThemeManager

class InfoBar(QWidget):
    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.config = self.storage.load()
        self.theme = ThemeManager(self.config["theme"])
        self.fields = []
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.splitter = QSplitter(Qt.Horizontal)
        font = QFont("Microsoft YaHei", 10)

        for col in self.config["columns"]:
            field = EditableField(f"{col['name']}: {col['content']}")
            field.setFont(font)
            field.setStyleSheet(self.theme.get_stylesheet())
            field.contentChanged.connect(self.save_config)
            self.fields.append(field)
            self.splitter.addWidget(field)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        win = self.config["window"]
        self.resize(win["width"], win["height"])
        self.move(win["x"], win["y"])

    def save_config(self):
        for i, field in enumerate(self.fields):
            text = field.text()
            if ": " in text:
                name, content = text.split(": ", 1)
                self.config["columns"][i] = {"name": name, "content": content}

        pos = self.pos()
        self.config["window"] = {
            "x": pos.x(), "y": pos.y(),
            "width": self.width(), "height": self.height()
        }
        self.config["theme"] = self.theme.to_dict()
        self.storage.save(self.config)

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
