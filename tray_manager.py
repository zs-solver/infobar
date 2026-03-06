"""
系统托盘管理器
"""
import sys
import os
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QKeySequence
from PyQt5.QtCore import Qt


def create_tray_icon(size=32):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    font = QFont("Arial", int(size * 0.6), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor(100, 180, 255))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "i")
    painter.end()
    return QIcon(pixmap)


class TrayManager:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.tray_icon = QSystemTrayIcon(self.parent)
        self.tray_icon.setIcon(create_tray_icon())

        tray_menu = QMenu()

        self.toggle_action = QAction("显示/隐藏(&S)", self.parent)
        self.toggle_action.setShortcut(QKeySequence("S"))
        self.toggle_action.triggered.connect(self.toggle_window)

        self.theme_action = QAction("主题设置(&T)", self.parent)
        self.theme_action.setShortcut(QKeySequence("T"))
        self.theme_action.triggered.connect(self.parent.open_theme_dialog)

        self.reset_pos_action = QAction("重置窗口位置(&P)", self.parent)
        self.reset_pos_action.setShortcut(QKeySequence("P"))
        self.reset_pos_action.triggered.connect(self.reset_position)

        self.restart_action = QAction("重启程序(&R)", self.parent)
        self.restart_action.setShortcut(QKeySequence("R"))
        self.restart_action.triggered.connect(self.restart_program)

        self.quit_action = QAction("退出(&Q)", self.parent)
        self.quit_action.setShortcut(QKeySequence("Q"))
        self.quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(self.toggle_action)
        tray_menu.addAction(self.theme_action)
        tray_menu.addAction(self.reset_pos_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.restart_action)
        tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_focus()

    def toggle_window(self):
        if self.parent.isVisible():
            self.parent.hide()
        else:
            self.show_and_focus()

    def show_and_focus(self):
        self.parent.show()
        self.parent.setWindowState(
            self.parent.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
        )
        self.parent.activateWindow()
        self.parent.raise_()

    def reset_position(self):
        """重置窗口到主屏幕左上角安全位置"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.parent.move(screen.x() + 50, screen.y() + 50)
        self.parent.save_config()
        self.show_and_focus()

    def restart_program(self):
        self.parent.save_config()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def quit_app(self):
        self.parent.save_config()
        QApplication.instance().quit()
