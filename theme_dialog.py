"""
主题设置对话框
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QColorDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class ThemeDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.setWindowTitle("主题设置")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 背景色
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("背景色:"))
        self.bg_btn = QPushButton("选择颜色")
        self.bg_btn.clicked.connect(self.choose_bg_color)
        bg_layout.addWidget(self.bg_btn)
        layout.addLayout(bg_layout)

        # 背景透明度
        bg_opacity_layout = QHBoxLayout()
        bg_opacity_layout.addWidget(QLabel("背景透明度:"))
        self.bg_opacity_slider = QSlider(Qt.Horizontal)
        self.bg_opacity_slider.setRange(0, 100)
        self.bg_opacity_slider.setValue(int(self.theme.bg_opacity * 100))
        bg_opacity_layout.addWidget(self.bg_opacity_slider)
        layout.addLayout(bg_opacity_layout)

        # 文字色
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("文字色:"))
        self.text_btn = QPushButton("选择颜色")
        self.text_btn.clicked.connect(self.choose_text_color)
        text_layout.addWidget(self.text_btn)
        layout.addLayout(text_layout)

        # 文字透明度
        text_opacity_layout = QHBoxLayout()
        text_opacity_layout.addWidget(QLabel("文字透明度:"))
        self.text_opacity_slider = QSlider(Qt.Horizontal)
        self.text_opacity_slider.setRange(0, 100)
        self.text_opacity_slider.setValue(int(self.theme.text_opacity * 100))
        text_opacity_layout.addWidget(self.text_opacity_slider)
        layout.addLayout(text_opacity_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def choose_bg_color(self):
        color = QColorDialog.getColor(QColor(self.theme.bg_color), self, "选择背景色")
        if color.isValid():
            self.theme.bg_color = color.name()

    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.theme.text_color), self, "选择文字色")
        if color.isValid():
            self.theme.text_color = color.name()

    def get_theme_config(self):
        self.theme.bg_opacity = self.bg_opacity_slider.value() / 100.0
        self.theme.text_opacity = self.text_opacity_slider.value() / 100.0
        return self.theme.to_dict()
