"""
自定义组件
"""
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

class EditableField(QLineEdit):
    """可编辑字段：单击拖动，双击编辑"""
    contentChanged = pyqtSignal(str)

    def __init__(self, text):
        super().__init__(text)
        self.setReadOnly(True)
        self.setCursor(Qt.ArrowCursor)
        self.textChanged.connect(lambda: self.contentChanged.emit(self.text()))

    def contextMenuEvent(self, event):
        if self.isReadOnly():
            # 只读模式下，传递给父窗口
            event.ignore()
        else:
            # 编辑模式下，显示默认菜单
            super().contextMenuEvent(event)

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
