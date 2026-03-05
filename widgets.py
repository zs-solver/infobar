"""
自定义组件
"""
from PyQt5.QtWidgets import QPlainTextEdit, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QColor

class EditableField(QPlainTextEdit):
    """可编辑字段：支持多行文本，单击拖动，双击编辑"""
    contentChanged = pyqtSignal(str)

    def __init__(self, text, info_bar=None):
        super().__init__(text)
        self.info_bar = info_bar  # 保存 InfoBar 引用
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
            # 只读模式下，显示字段操作菜单
            from PyQt5.QtWidgets import QMenu

            if not self.info_bar:
                event.ignore()
                return

            menu = QMenu(self)

            # 编辑内容
            edit_action = menu.addAction("编辑内容")
            edit_action.triggered.connect(self.enter_edit_mode)

            menu.addSeparator()

            # 插入操作
            insert_left_action = menu.addAction("在左侧插入新格子")
            insert_left_action.triggered.connect(lambda: self.info_bar.insert_field_at(self, 'left'))

            insert_right_action = menu.addAction("在右侧插入新格子")
            insert_right_action.triggered.connect(lambda: self.info_bar.insert_field_at(self, 'right'))

            # 删除操作
            delete_action = menu.addAction("删除此格子")
            delete_action.triggered.connect(lambda: self.info_bar.delete_field(self))
            # 只有一个格子时不能删除
            if len(self.info_bar.fields) <= 1:
                delete_action.setEnabled(False)

            menu.addSeparator()

            # 移动操作子菜单
            move_menu = menu.addMenu("移动")
            move_first_action = move_menu.addAction("到最左")
            move_first_action.triggered.connect(lambda: self.info_bar.move_field(self, 'first'))

            move_left_action = move_menu.addAction("向左一位")
            move_left_action.triggered.connect(lambda: self.info_bar.move_field(self, 'left'))

            move_right_action = move_menu.addAction("向右一位")
            move_right_action.triggered.connect(lambda: self.info_bar.move_field(self, 'right'))

            move_last_action = move_menu.addAction("到最右")
            move_last_action.triggered.connect(lambda: self.info_bar.move_field(self, 'last'))

            menu.addSeparator()

            # 重置宽度
            reset_width_action = menu.addAction("重置所有宽度")
            reset_width_action.triggered.connect(self.info_bar.reset_all_widths)

            menu.addSeparator()

            # 主题和托盘
            theme_action = menu.addAction("主题设置")
            theme_action.triggered.connect(self.info_bar.open_theme_dialog)

            hide_action = menu.addAction("隐藏到托盘")
            hide_action.triggered.connect(self.info_bar.hide)

            menu.exec_(event.globalPos())
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

    def enter_edit_mode(self):
        """进入编辑模式"""
        self.setReadOnly(False)
        self.setCursor(Qt.IBeamCursor)
        self.selectAll()
        self.setFocus()


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
