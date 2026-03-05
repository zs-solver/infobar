"""
主题管理 - 颜色和透明度
"""
from PyQt5.QtGui import QColor


class ThemeManager:
    def __init__(self, theme_config):
        self.bg_color = theme_config.get("bg_color", "#2b2b2b")
        self.bg_opacity = theme_config.get("bg_opacity", 1.0)
        self.text_color = theme_config.get("text_color", "#ffffff")
        self.text_opacity = theme_config.get("text_opacity", 1.0)

    def get_stylesheet(self):
        """生成样式表"""
        bg_opacity = max(self.bg_opacity, 0.01)
        bg_rgba = self._hex_to_rgba(self.bg_color, bg_opacity)
        text_rgba = self._hex_to_rgba(self.text_color, self.text_opacity)
        return f"padding: 5px; background: {bg_rgba}; color: {text_rgba}; border: none;"

    def get_handle_color(self):
        """生成与 QSplitter handle 外观一致的颜色（基于背景色）"""
        hex_color = self.bg_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        bg_opacity = max(self.bg_opacity, 0.01)
        return QColor(r, g, b, int(bg_opacity * 255))

    def _hex_to_rgba(self, hex_color, opacity):
        """转换十六进制颜色为 RGBA"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"

    def to_dict(self):
        return {
            "bg_color": self.bg_color,
            "bg_opacity": self.bg_opacity,
            "text_color": self.text_color,
            "text_opacity": self.text_opacity
        }
