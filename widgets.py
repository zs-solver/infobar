"""
自定义组件
"""
from PyQt5.QtWidgets import QPlainTextEdit, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect, QTimer
from PyQt5.QtGui import QPainter, QColor, QCursor

# EdgeHandle 常量
EDGE_HANDLE_DEFAULT_WIDTH = 5      # 默认宽度
EDGE_HANDLE_EXPANDED_WIDTH = 24    # 悬停展开宽度
EDGE_ZONE_HEIGHT = 44              # 上下区域高度（从文本区域外"长出来"）
SPLIT_FACTOR = 2.0                 # 裂变阈值：边缘格子宽度 >= 标准宽度 * SPLIT_FACTOR 时裂变
MIN_FIELD_WIDTH = 30               # 格子最小宽度


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

            # 隐藏到托盘
            hide_action = menu.addAction("隐藏到托盘")
            hide_action.triggered.connect(self.info_bar.hide)

            menu.addSeparator()

            # 编辑内容
            edit_action = menu.addAction("编辑内容")
            edit_action.triggered.connect(self.enter_edit_mode)

            menu.addSeparator()

            # 插入操作
            insert_left_action = menu.addAction("在左侧插入新格子")
            insert_left_action.triggered.connect(lambda: self.info_bar.insert_field_at(self, 'left'))

            insert_right_action = menu.addAction("在右侧插入新格子")
            insert_right_action.triggered.connect(lambda: self.info_bar.insert_field_at(self, 'right'))

            # 删除操作 - 拆分为两个选项
            delete_shrink_action = menu.addAction("删除此格子（窗口缩小）")
            delete_shrink_action.triggered.connect(lambda: self.info_bar.delete_field_shrink(self))

            delete_keep_action = menu.addAction("删除此格子（宽度不变）")
            delete_keep_action.triggered.connect(lambda: self.info_bar.delete_field_keep_width(self))

            # 只有一个格子时不能删除
            if len(self.info_bar.fields) <= 1:
                delete_shrink_action.setEnabled(False)
                delete_keep_action.setEnabled(False)

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

            # 主题设置
            theme_action = menu.addAction("主题设置")
            theme_action.triggered.connect(self.info_bar.open_theme_dialog)

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
    """边缘拖动手柄 - 三区域设计：上(插入)、中(调宽)、下(裂变/删除)

    悬停时上下区域从中区域的两端「长出来」，窗口只向下扩展，不跳动：
      - 默认：高度 = 文本高度（_base_height），全部是中区域
      - 悬停：高度 = _base_height + 2 * EDGE_ZONE_HEIGHT
              插入按钮 [0, EDGE_ZONE_HEIGHT)
              中区域   [EDGE_ZONE_HEIGHT, EDGE_ZONE_HEIGHT + _base_height)
              裂变按钮 [EDGE_ZONE_HEIGHT + _base_height, 末尾)
    """

    # 区域枚举
    ZONE_INSERT = 'insert'
    ZONE_MIDDLE = 'middle'
    ZONE_SPLIT = 'split'

    def __init__(self, side, parent_bar):
        """
        side: 'left' 或 'right'
        parent_bar: InfoBar 实例
        """
        super().__init__(parent_bar)
        self.side = side
        self.parent_bar = parent_bar
        self.dragging = False
        self._drag_zone = None  # 当前拖拽区域
        self._expanded = False
        self._base_height = 0   # 文本区域高度 = 中区域高度（由 sync_heights 设置）
        self._bg_color = QColor(128, 128, 128, 80)
        self._top_color = QColor(100, 200, 100, 120)     # 插入按钮 - 绿色调
        self._bottom_color = QColor(100, 100, 200, 120)  # 裂变按钮 - 蓝色调

        self.setFixedWidth(EDGE_HANDLE_DEFAULT_WIDTH)
        self.setCursor(Qt.SizeHorCursor)
        self.setMouseTracking(True)

        # 防闪烁定时器：leaveEvent 延迟收回
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(80)
        self._leave_timer.timeout.connect(self._do_collapse)

    def set_base_height(self, h):
        """设置基础高度（文本高度），由 InfoBar.sync_heights 调用"""
        self._base_height = h
        if not self._expanded:
            self.setFixedHeight(h)

    def set_handle_color(self, color):
        """设置手柄背景色"""
        self._bg_color = color
        # 基于背景色调整上下区域颜色（加亮、偏色，更易区分）
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        self._top_color = QColor(min(r + 40, 255), min(g + 60, 255), b, min(a + 60, 255))
        self._bottom_color = QColor(r, min(g + 40, 255), min(b + 60, 255), min(a + 60, 255))
        self.update()

    def _zone_rects(self):
        """计算三个区域的矩形。

        展开时布局（上-中-下）：
          [0, 0]                      → insert_rect  (高 EDGE_ZONE_HEIGHT，插入按钮)
          [0, EDGE_ZONE_HEIGHT]       → middle_rect  (高 _base_height，调宽拖拽)
          [0, EDGE_ZONE_HEIGHT + bh]  → split_rect   (高 EDGE_ZONE_HEIGHT，裂变按钮)
        """
        w = self.width()
        bh = self._base_height
        insert_rect = QRect(0, 0, w, EDGE_ZONE_HEIGHT)
        middle_rect = QRect(0, EDGE_ZONE_HEIGHT, w, bh)
        split_rect = QRect(0, EDGE_ZONE_HEIGHT + bh, w, EDGE_ZONE_HEIGHT)
        return insert_rect, middle_rect, split_rect

    def _hit_zone(self, pos):
        """判断鼠标位于哪个区域"""
        if not self._expanded:
            return self.ZONE_MIDDLE
        insert_rect, middle_rect, split_rect = self._zone_rects()
        if insert_rect.contains(pos):
            return self.ZONE_INSERT
        elif split_rect.contains(pos):
            return self.ZONE_SPLIT
        else:
            return self.ZONE_MIDDLE

    def _update_cursor(self, zone):
        """根据区域更新鼠标样式"""
        if zone == self.ZONE_INSERT:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.SizeHorCursor)

    # --- 悬停展开/收回 ---

    def enterEvent(self, event):
        self._leave_timer.stop()
        if not self._expanded:
            self._expanded = True
            self.setFixedWidth(EDGE_HANDLE_EXPANDED_WIDTH)
            # 高度从 _base_height 增长到 _base_height + 2 * EDGE_ZONE_HEIGHT
            expanded_h = self._base_height + 2 * EDGE_ZONE_HEIGHT
            self.setFixedHeight(expanded_h)
            # 通知 InfoBar 扩展窗口
            self.parent_bar.notify_handle_expanded()
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.dragging:
            self._leave_timer.start()
        super().leaveEvent(event)

    def _do_collapse(self):
        """延迟收回，防止因窗口抖动触发的假 leaveEvent"""
        if self.dragging:
            return
        if not self._expanded:
            return
        self._expanded = False
        self.setFixedWidth(EDGE_HANDLE_DEFAULT_WIDTH)
        self.setFixedHeight(self._base_height)
        # 通知 InfoBar 恢复窗口
        self.parent_bar.notify_handle_collapsed()
        self.update()

    # --- 绘制 ---

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._expanded:
            insert_rect, middle_rect, split_rect = self._zone_rects()
            # 插入按钮（上方）
            painter.fillRect(insert_rect, self._top_color)
            # 中区域
            painter.fillRect(middle_rect, self._bg_color)
            # 裂变按钮（下方）
            painter.fillRect(split_rect, self._bottom_color)
            # 插入按钮画 "+" 符号
            painter.setPen(QColor(255, 255, 255, 220))
            cx = insert_rect.center().x()
            cy = insert_rect.center().y()
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
            # 裂变按钮画 "↔" 双箭头
            cx = split_rect.center().x()
            cy = split_rect.center().y()
            painter.drawLine(cx - 7, cy, cx + 7, cy)
            # 左箭头头
            painter.drawLine(cx - 7, cy, cx - 4, cy - 3)
            painter.drawLine(cx - 7, cy, cx - 4, cy + 3)
            # 右箭头头
            painter.drawLine(cx + 7, cy, cx + 4, cy - 3)
            painter.drawLine(cx + 7, cy, cx + 4, cy + 3)
        else:
            painter.fillRect(self.rect(), self._bg_color)
        painter.end()

    # --- 鼠标事件 ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            zone = self._hit_zone(event.pos())
            if zone == self.ZONE_INSERT:
                # 插入按钮：点击插入新格子
                self.parent_bar.insert_at_edge(self.side)
                event.accept()
                return
            # 中区域或裂变按钮：开始拖拽
            self.dragging = True
            self._drag_zone = zone
            self.drag_start_x = event.globalPos().x()
            self.drag_start_width = self.parent_bar.width()
            self.drag_start_pos = self.parent_bar.pos()
            # 裂变区域需要记录边缘格子初始宽度
            if zone == self.ZONE_SPLIT:
                sizes = self.parent_bar.splitter.sizes()
                if self.side == 'left':
                    self._drag_edge_start_width = sizes[0] if sizes else 0
                else:
                    self._drag_edge_start_width = sizes[-1] if sizes else 0
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            if self._drag_zone == self.ZONE_MIDDLE:
                self._handle_middle_drag(event)
            elif self._drag_zone == self.ZONE_SPLIT:
                self._handle_bottom_drag(event)
            event.accept()
        else:
            # 非拖拽时更新光标
            zone = self._hit_zone(event.pos())
            self._update_cursor(zone)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self._drag_zone = None
            self.parent_bar.save_config()
            # 如果鼠标已经不在手柄区域内，则收回
            if not self.rect().contains(event.pos()):
                self._do_collapse()
            event.accept()

    # --- 中区域拖拽：移动总宽度，所有格子保持平均等宽 ---

    def _handle_middle_drag(self, event):
        delta = event.globalPos().x() - self.drag_start_x
        count = len(self.parent_bar.fields)
        if count == 0:
            return

        if self.side == 'left':
            new_width = self.drag_start_width - delta
            if new_width >= 100:
                new_x = self.drag_start_pos.x() + delta
                self.parent_bar.move(new_x, self.drag_start_pos.y())
                self.parent_bar.resize(new_width, self.parent_bar.height())
                # 所有格子保持平均等宽
                self._set_equal_sizes()
        else:  # right
            new_width = self.drag_start_width + delta
            if new_width >= 100:
                self.parent_bar.resize(new_width, self.parent_bar.height())
                self._set_equal_sizes()

    def _set_equal_sizes(self):
        """设置所有格子为平均等宽"""
        count = len(self.parent_bar.fields)
        if count == 0:
            return
        total = self.parent_bar.splitter.width()
        avg = total // count
        self.parent_bar.splitter.setSizes([avg] * count)

    # --- 下区域拖拽：裂变/删除格子 ---

    def _handle_bottom_drag(self, event):
        delta = event.globalPos().x() - self.drag_start_x
        fields = self.parent_bar.fields
        count = len(fields)
        if count == 0:
            return

        sizes = self.parent_bar.splitter.sizes()
        total_splitter = sum(sizes)
        if total_splitter == 0:
            return

        # 计算标准宽度（平均宽度）
        avg_width = total_splitter / count

        if self.side == 'left':
            # 向左拖（delta < 0）= 拉伸，向右拖（delta > 0）= 收缩
            edge_idx = 0
            edge_new_width = self._drag_edge_start_width - delta
        else:
            # 向右拖（delta > 0）= 拉伸，向左拖（delta < 0）= 收缩
            edge_idx = count - 1
            edge_new_width = self._drag_edge_start_width + delta

        # 拉伸方向：边缘格子变宽
        if edge_new_width > self._drag_edge_start_width:
            # 调整窗口宽度
            width_delta = edge_new_width - sizes[edge_idx]
            new_window_width = self.parent_bar.width() + width_delta
            if new_window_width < 100:
                return

            if self.side == 'left':
                # 左侧拉伸需要移动窗口位置
                self.parent_bar.move(
                    self.parent_bar.pos().x() - width_delta,
                    self.parent_bar.pos().y()
                )

            self.parent_bar.resize(int(new_window_width), self.parent_bar.height())

            # 更新 sizes
            sizes = self.parent_bar.splitter.sizes()
            if edge_idx < len(sizes):
                sizes[edge_idx] = int(edge_new_width)
                self.parent_bar.splitter.setSizes(sizes)

            # 检查是否需要裂变
            sizes = self.parent_bar.splitter.sizes()
            if edge_idx < len(sizes) and sizes[edge_idx] >= avg_width * SPLIT_FACTOR:
                # 裂变：在边缘插入新空格子
                split_width = sizes[edge_idx] // 2
                remainder = sizes[edge_idx] - split_width

                if self.side == 'left':
                    # 左侧：在最左插入新格子
                    self.parent_bar.insert_at_edge('left', text="", adjust_window=False)
                    new_sizes = self.parent_bar.splitter.sizes()
                    new_sizes[0] = split_width
                    new_sizes[1] = remainder
                    self.parent_bar.splitter.setSizes(new_sizes)
                else:
                    # 右侧：在最右插入新格子
                    self.parent_bar.insert_at_edge('right', text="", adjust_window=False)
                    new_sizes = self.parent_bar.splitter.sizes()
                    new_sizes[-1] = split_width
                    new_sizes[-2] = remainder
                    self.parent_bar.splitter.setSizes(new_sizes)

                # 更新拖拽状态
                self._drag_edge_start_width = split_width
                self.drag_start_x = event.globalPos().x()

        # 收缩方向：边缘格子缩窄
        elif edge_new_width < self._drag_edge_start_width:
            edge_new_width = max(edge_new_width, 1)

            # 检查是否需要删除边缘空格子
            if edge_idx < len(fields):
                edge_field = fields[edge_idx]
                field_text = edge_field.toPlainText().strip()

                if edge_new_width <= MIN_FIELD_WIDTH and field_text == "" and count > 1:
                    # 空格子缩到阈值以下，删除
                    removed_width = sizes[edge_idx]
                    self.parent_bar.delete_field_shrink(edge_field)

                    # 更新拖拽状态
                    new_sizes = self.parent_bar.splitter.sizes()
                    new_count = len(self.parent_bar.fields)
                    if new_count > 0:
                        if self.side == 'left':
                            self._drag_edge_start_width = new_sizes[0] if new_sizes else 0
                        else:
                            self._drag_edge_start_width = new_sizes[-1] if new_sizes else 0
                        self.drag_start_x = event.globalPos().x()
                    return

            # 调整窗口宽度
            width_delta = sizes[edge_idx] - edge_new_width
            new_window_width = self.parent_bar.width() - width_delta
            if new_window_width < 100:
                return

            if self.side == 'left':
                self.parent_bar.move(
                    self.parent_bar.pos().x() + width_delta,
                    self.parent_bar.pos().y()
                )

            self.parent_bar.resize(int(new_window_width), self.parent_bar.height())

            # 更新 sizes
            sizes = self.parent_bar.splitter.sizes()
            if edge_idx < len(sizes):
                # 有内容的格子不能小于最小宽度
                edge_field = fields[edge_idx] if edge_idx < len(fields) else None
                if edge_field and edge_field.toPlainText().strip():
                    sizes[edge_idx] = max(int(edge_new_width), MIN_FIELD_WIDTH)
                else:
                    sizes[edge_idx] = max(int(edge_new_width), 1)
                self.parent_bar.splitter.setSizes(sizes)
