"""
单行信息条工具 - 可调整列宽的置顶窗口
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from widgets import EditableField, EdgeHandle
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

        self.left_handle = EdgeHandle('left', self)
        self.right_handle = EdgeHandle('right', self)

        self.splitter = QSplitter(Qt.Horizontal)
        font = QFont("Microsoft YaHei", 10)

        for col in self.config["columns"]:
            field = EditableField(col, self)
            field.setFont(font)
            field.setStyleSheet(self.theme.get_stylesheet())
            field.contentChanged.connect(self.save_config)
            field.contentChanged.connect(self.sync_heights)
            self.fields.append(field)
            self.splitter.addWidget(field)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.left_handle)
        layout.addWidget(self.splitter)
        layout.addWidget(self.right_handle)
        self.setLayout(layout)

        win = self.config["window"]
        self.resize(win["width"], win["height"])
        self.move(win["x"], win["y"])
        self.sync_heights()
        self.apply_handle_theme()

    def sync_heights(self):
        """统一所有字段和边缘手柄高度为最高字段的高度，避免透明穿透"""
        max_height = max(field.get_content_height() for field in self.fields)
        for field in self.fields:
            field.setFixedHeight(max_height)
        self.left_handle.setFixedHeight(max_height)
        self.right_handle.setFixedHeight(max_height)

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
        self.apply_handle_theme()

    def apply_handle_theme(self):
        """将边缘手柄颜色设为与 QSplitter handle 一致的半透明背景色"""
        handle_color = self.theme.get_handle_color()
        self.left_handle.set_handle_color(handle_color)
        self.right_handle.set_handle_color(handle_color)

    def insert_field_at(self, target_field, position):
        """在目标字段的左侧或右侧插入新格子"""
        index = self.fields.index(target_field)
        if position == 'right':
            index += 1

        # 创建新字段
        new_field = EditableField("新格子", self)
        new_field.setFont(target_field.font())
        new_field.setStyleSheet(self.theme.get_stylesheet())
        new_field.contentChanged.connect(self.save_config)
        new_field.contentChanged.connect(self.sync_heights)

        # 插入到列表和 splitter
        self.fields.insert(index, new_field)
        self.splitter.insertWidget(index, new_field)
        self.config["columns"].insert(index, "新格子")

        self.sync_heights()
        self.save_config()

    def delete_field(self, target_field):
        """删除指定格子"""
        if len(self.fields) <= 1:
            return  # 至少保留一个格子

        index = self.fields.index(target_field)
        self.fields.pop(index)
        self.config["columns"].pop(index)

        # 从 splitter 中移除
        target_field.setParent(None)
        target_field.deleteLater()

        self.sync_heights()
        self.save_config()

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
