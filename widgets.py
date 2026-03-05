"""
自定义组件
"""
from PyQt5.QtWidgets import QPlainTextEdit, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QColor

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


class EdgeHandle(QWidget):
    """边缘拖动手柄 - 拖动时按比例缩放窗口宽度"""

    def __init__(self, side, parent_bar):
        """
        side: 'left' 或 'right'
        parent_bar: InfoBar 实例
        """
        super().__init__(parent_bar)
        self.side = side
        self.parent_bar = parent_bar
        self.dragging = False
        self.setCursor(Qt.SizeHorCursor)
        self.setFixedWidth(5)
        self._bg_color = QColor(128, 128, 128, 80)

    def set_handle_color(self, color):
        """设置手柄背景色"""
        self._bg_color = color
        self.update()

    def paintEvent(self, event):
        """绘制与 QSplitter handle 一致的外观"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._bg_color)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_x = event.globalPos().x()
            self.drag_start_width = self.parent_bar.width()
            self.drag_start_pos = self.parent_bar.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPos().x() - self.drag_start_x
            if self.side == 'left':
                new_width = self.drag_start_width - delta
                if new_width >= 100:
                    # 保存旧的 splitter 比例
                    old_sizes = self.parent_bar.splitter.sizes()
                    old_total = sum(old_sizes)

                    new_x = self.drag_start_pos.x() + delta
                    self.parent_bar.move(new_x, self.drag_start_pos.y())
                    self.parent_bar.resize(new_width, self.parent_bar.height())

                    # 按比例恢复 splitter 大小
                    if old_total > 0:
                        new_total = self.parent_bar.splitter.width()
                        new_sizes = [int(s / old_total * new_total) for s in old_sizes]
                        self.parent_bar.splitter.setSizes(new_sizes)
            else:  # right
                new_width = self.drag_start_width + delta
                if new_width >= 100:
                    old_sizes = self.parent_bar.splitter.sizes()
                    old_total = sum(old_sizes)

                    self.parent_bar.resize(new_width, self.parent_bar.height())

                    if old_total > 0:
                        new_total = self.parent_bar.splitter.width()
                        new_sizes = [int(s / old_total * new_total) for s in old_sizes]
                        self.parent_bar.splitter.setSizes(new_sizes)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.parent_bar.save_config()
            event.accept()
