"""
自定义组件
"""
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt, pyqtSignal, QSize

class EditableField(QPlainTextEdit):
    """可编辑字段：支持多行文本，单击拖动，双击编辑"""
    contentChanged = pyqtSignal(str)

    def __init__(self, text):
        super().__init__(text)
        self.setReadOnly(True)
        self.setCursor(Qt.ArrowCursor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 设置边距确保文字显示完整
        self.setContentsMargins(2, 2, 2, 2)
        self.document().setDocumentMargin(2)
        self.textChanged.connect(self._on_text_changed)

    def setFont(self, font):
        """设置字体后重新计算高度"""
        super().setFont(font)
        self.adjust_height()

    def setStyleSheet(self, stylesheet):
        """设置样式后重新计算高度"""
        super().setStyleSheet(stylesheet)
        self.adjust_height()

    def _on_text_changed(self):
        self.adjust_height()
        self.contentChanged.emit(self.toPlainText())

    def adjust_height(self):
        self.setFixedHeight(self.get_content_height())

    def get_content_height(self):
        """根据文本行数计算所需高度"""
        line_count = self.document().blockCount()
        line_height = self.fontMetrics().height()
        doc_margin = self.document().documentMargin()
        margins = self.contentsMargins()
        # 包含行高、文档边距、内容边距和额外空间，确保字母下伸部分完整显示
        return int(line_count * line_height + doc_margin * 2 + margins.top() + margins.bottom() + 4)


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
