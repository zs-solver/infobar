"""
InfoBar 程序入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from info_bar import InfoBar

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    bar = InfoBar()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
