"""
单行信息条工具 - 可调整列宽的置顶窗口
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from widgets import EditableField, EdgeHandle, EDGE_ZONE_HEIGHT
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
        self._expanded_handle_count = 0  # 当前展开的手柄数量
        self._base_height = 0            # 文本区域基准高度
        self.init_ui()
        self.tray = TrayManager(self)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.left_handle = EdgeHandle('left', self)
        self.right_handle = EdgeHandle('right', self)

        self.splitter = QSplitter(Qt.Horizontal)
        font = QFont("Microsoft YaHei", 10)

        for col in self.config["columns"]:
            field = self._create_field(col, font)
            self.fields.append(field)
            self.splitter.addWidget(field)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.left_handle)
        layout.addWidget(self.splitter, 1)  # splitter 获取拉伸优先级
        layout.addWidget(self.right_handle)
        self.setLayout(layout)

        win = self.config["window"]
        self.resize(win["width"], win["height"])
        self.move(win["x"], win["y"])
        self.sync_heights()
        self.apply_handle_theme()

    def _create_field(self, text, font=None):
        """工厂方法：创建并配置一个 EditableField"""
        if font is None:
            font = QFont("Microsoft YaHei", 10)
        field = EditableField(text, self)
        field.setFont(font)
        field.setStyleSheet(self.theme.get_stylesheet())
        field.contentChanged.connect(self.save_config)
        field.contentChanged.connect(self.sync_heights)
        return field

    def _get_non_splitter_width(self):
        """获取非 splitter 部分的宽度（边缘手柄 + 布局间距等）"""
        return self.width() - self.splitter.width()

    def sync_heights(self):
        """统一所有字段高度，并用 set_base_height 通知边缘手柄"""
        max_height = max(field.get_content_height() for field in self.fields)
        self._base_height = max_height
        for field in self.fields:
            field.setFixedHeight(max_height)
        # 使用 set_base_height 而非 setFixedHeight —— 手柄自行管理展开/收回高度
        self.left_handle.set_base_height(max_height)
        self.right_handle.set_base_height(max_height)

    # --- 手柄展开/收回时调整窗口纵向尺寸 ---

    def notify_handle_expanded(self):
        """手柄展开时调用：窗口仅向下扩展，不移动位置"""
        self._expanded_handle_count += 1
        if self._expanded_handle_count == 1:
            expanded_h = self._base_height + 2 * EDGE_ZONE_HEIGHT
            self.resize(self.width(), expanded_h)

    def notify_handle_collapsed(self):
        """手柄收回时调用：窗口恢复原高度"""
        self._expanded_handle_count = max(0, self._expanded_handle_count - 1)
        if self._expanded_handle_count == 0:
            self.resize(self.width(), self._base_height)

    def save_config(self):
        self.config["columns"] = [field.toPlainText() for field in self.fields]

        pos = self.pos()
        self.config["window"] = {
            "x": pos.x(), "y": pos.y(),
            "width": self.width(), "height": self._base_height
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
        hide_action = menu.addAction("隐藏到托盘")
        hide_action.triggered.connect(self.hide)
        theme_action = menu.addAction("主题设置")
        theme_action.triggered.connect(self.open_theme_dialog)
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
        self.apply_handle_theme()

    def apply_handle_theme(self):
        """将边缘手柄颜色设为与 QSplitter handle 一致的半透明背景色"""
        handle_color = self.theme.get_handle_color()
        self.left_handle.set_handle_color(handle_color)
        self.right_handle.set_handle_color(handle_color)

    def insert_field_at(self, target_field, position):
        """在目标字段的左侧或右侧插入新格子（窗口总宽度增大）"""
        index = self.fields.index(target_field)
        if position == 'right':
            index += 1

        # 计算新格子宽度 = 当前各格子平均宽度
        sizes = self.splitter.sizes()
        avg_width = sum(sizes) // len(sizes) if sizes else 100

        # 创建新字段
        new_field = self._create_field("")

        # 插入到列表和 splitter
        self.fields.insert(index, new_field)
        self.splitter.insertWidget(index, new_field)
        self.config["columns"].insert(index, "")

        # 窗口总宽度增大
        new_window_width = self.width() + avg_width
        if position == 'left':
            # 向左扩展时移动窗口位置
            self.move(self.pos().x() - avg_width, self.pos().y())
        self.resize(new_window_width, self.height())

        # 设置 sizes：插入位置为 avg_width，其余保持不变
        old_sizes = sizes[:]
        new_sizes = old_sizes[:index] + [avg_width] + old_sizes[index:]
        self.splitter.setSizes(new_sizes)

        self.sync_heights()
        self.save_config()

    def insert_at_edge(self, side, text="", adjust_window=True):
        """在边缘（最左或最右）插入新格子

        Args:
            side: 'left' 或 'right'
            text: 新格子文本内容
            adjust_window: 是否调整窗口宽度（True = 增大窗口，False = 不调整）
        """
        # 计算新格子宽度 = 当前各格子平均宽度
        sizes = self.splitter.sizes()
        avg_width = sum(sizes) // len(sizes) if sizes else 100

        new_field = self._create_field(text)

        if side == 'left':
            self.fields.insert(0, new_field)
            self.splitter.insertWidget(0, new_field)
            self.config["columns"].insert(0, text)

            if adjust_window:
                self.move(self.pos().x() - avg_width, self.pos().y())
                self.resize(self.width() + avg_width, self.height())
                # 设置 sizes：新格子 = avg_width，已有格子保持不变
                new_sizes = [avg_width] + sizes
                self.splitter.setSizes(new_sizes)
        else:  # right
            self.fields.append(new_field)
            self.splitter.addWidget(new_field)
            self.config["columns"].append(text)

            if adjust_window:
                self.resize(self.width() + avg_width, self.height())
                new_sizes = sizes + [avg_width]
                self.splitter.setSizes(new_sizes)

        self.sync_heights()
        self.save_config()

    def delete_field_shrink(self, target_field):
        """删除格子（窗口缩小）：删掉格子后，其他格子宽度不变，窗口总宽度减小"""
        if len(self.fields) <= 1:
            return

        index = self.fields.index(target_field)
        sizes = self.splitter.sizes()
        removed_width = sizes[index] if index < len(sizes) else 0

        # 计算 splitter handle 宽度（删除一个格子少一个 handle）
        handle_width = self.splitter.handleWidth() if len(self.fields) > 2 else 0

        # 从列表和 splitter 中移除
        self.fields.pop(index)
        self.config["columns"].pop(index)
        target_field.setParent(None)
        target_field.deleteLater()

        # 缩小窗口宽度
        shrink = removed_width + handle_width
        new_width = max(100, self.width() - shrink)

        # 如果删除的是左侧的格子，窗口位置需要右移
        if index == 0:
            self.move(self.pos().x() + shrink, self.pos().y())

        self.resize(new_width, self.height())

        # 其他格子宽度保持不变
        remaining_sizes = sizes[:index] + sizes[index + 1:]
        if remaining_sizes:
            self.splitter.setSizes(remaining_sizes)

        self.sync_heights()
        self.save_config()

    def delete_field_keep_width(self, target_field):
        """删除格子（宽度不变）：删掉格子后，窗口总宽度不变，剩余格子重新分配空间"""
        if len(self.fields) <= 1:
            return

        index = self.fields.index(target_field)

        # 从列表和 splitter 中移除
        self.fields.pop(index)
        self.config["columns"].pop(index)
        target_field.setParent(None)
        target_field.deleteLater()

        # 窗口宽度不变，剩余格子重新平均分配
        count = len(self.fields)
        if count > 0:
            total = self.splitter.width()
            avg = total // count
            self.splitter.setSizes([avg] * count)

        self.sync_heights()
        self.save_config()

    def delete_field(self, target_field):
        """删除指定格子（兼容旧调用，默认行为 = 窗口宽度不变）"""
        self.delete_field_keep_width(target_field)

    def move_field(self, target_field, direction):
        """移动格子位置"""
        current_index = self.fields.index(target_field)
        new_index = current_index

        if direction == 'first':
            new_index = 0
        elif direction == 'last':
            new_index = len(self.fields) - 1
        elif direction == 'left':
            new_index = max(0, current_index - 1)
        elif direction == 'right':
            new_index = min(len(self.fields) - 1, current_index + 1)

        if new_index == current_index:
            return  # 无需移动

        # 移动字段
        field = self.fields.pop(current_index)
        self.fields.insert(new_index, field)

        # 移动配置
        col_data = self.config["columns"].pop(current_index)
        self.config["columns"].insert(new_index, col_data)

        # 重建 splitter（QSplitter 没有直接的移动方法）
        self.rebuild_splitter()
        self.save_config()

    def reset_all_widths(self):
        """重置所有格子为平均宽度"""
        count = len(self.fields)
        if count == 0:
            return

        total_width = self.splitter.width()
        avg_width = total_width // count
        sizes = [avg_width] * count
        self.splitter.setSizes(sizes)
        self.save_config()

    def rebuild_splitter(self):
        """重建 splitter 中的所有 widget（用于重新排序）"""
        # 保存当前宽度比例
        old_sizes = self.splitter.sizes()
        old_total = sum(old_sizes) if old_sizes else 1

        # 移除所有 widget
        for field in self.fields:
            self.splitter.widget(0).setParent(None)

        # 按新顺序添加
        for field in self.fields:
            self.splitter.addWidget(field)

        # 恢复宽度比例
        if old_total > 0:
            new_total = self.splitter.width()
            new_sizes = [int(s / old_total * new_total) for s in old_sizes]
            self.splitter.setSizes(new_sizes)

        self.sync_heights()
