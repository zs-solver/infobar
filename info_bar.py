"""
单行信息条工具 - 可调整列宽的置顶窗口
"""
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLineEdit, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class EditableField(QLineEdit):
    def __init__(self, text):
        super().__init__(text)
        self.setReadOnly(True)
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if self.isReadOnly():
            event.ignore()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isReadOnly():
            event.ignore()
        else:
            super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.setReadOnly(False)
        self.setCursor(Qt.IBeamCursor)
        self.selectAll()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self.setReadOnly(True)
        self.setCursor(Qt.ArrowCursor)
        super().focusOutEvent(event)

class InfoBar(QWidget):
    def __init__(self, columns):
        super().__init__()
        self.columns = columns
        self.init_ui()

    def init_ui(self):
        # 窗口设置
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 添加列
        font = QFont("Microsoft YaHei", 10)
        for col_name, col_text in self.columns:
            edit = EditableField(f"{col_name}: {col_text}")
            edit.setFont(font)
            edit.setStyleSheet("padding: 5px; background: #2b2b2b; color: #ffffff; border: none;")
            splitter.addWidget(edit)

        # 布局
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

        # 窗口大小和位置
        self.resize(800, 35)
        self.move(100, 50)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

def main():
    app = QApplication(sys.argv)

    # 定义列：(列名, 内容)
    columns = [
        ("项目", "for_cc"),
        ("状态", "开发中"),
        ("分支", "main")
    ]

    bar = InfoBar(columns)
    bar.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
