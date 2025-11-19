#!/usr/bin/env python3
# fullscreen_app.py

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import sys

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None, main_view=None):
        super().__init__(parent)
        self.main_view = main_view

    def createWindow(self, _type):
        # 创建一个新的 QWebEnginePage
        new_page = QWebEnginePage(self)
        new_page.urlChanged.connect(self.on_url_changed)
        return new_page

    def on_url_changed(self, url):
        # 将新页面的 URL 设置到主视图
        self.main_view.setUrl(url)

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationTypeLinkClicked and is_main_frame:
            print(f"Navigating to: {url.toString()}")  # 调试信息
            self.main_view.setUrl(url)  # 在主视图中加载链接
            return False  # 阻止默认行为（即不在新窗口中打开）
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

class FullScreenBrowser(QMainWindow):
    def __init__(self, url):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("临床科研一体化平台")
        self.setGeometry(0, 0, 1920, 1080)

        # 创建 WebView
        self.browser = QWebEngineView()
        self.custom_page = CustomWebEnginePage(self.browser, self.browser)
        self.browser.setPage(self.custom_page)
        self.browser.setUrl(QUrl(url))  # 设置初始加载的 URL

        # 禁用右键菜单
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)

        # 连接信号以进行调试
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadFinished.connect(self.on_load_finished)

        # 创建导航按钮
        back_button = QPushButton("后退")
        back_button.clicked.connect(self.browser.back)

        forward_button = QPushButton("前进")
        forward_button.clicked.connect(self.browser.forward)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.browser.reload)

        # 创建导航按钮的布局
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(back_button)
        nav_layout.addWidget(forward_button)
        nav_layout.addWidget(refresh_button)

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.browser)

        # 设置中央窗口
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 显示全屏模式
        self.showFullScreen()

    def on_load_started(self):
        print("页面开始加载...")

    def on_load_finished(self, success):
        if success:
            print("页面加载成功。")
        else:
            print("页面加载失败。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    url = "http://127.0.0.1:8181/aiportal/unifiedEntry"  # 替换为你想显示的网页地址
    window = FullScreenBrowser(url)
    sys.exit(app.exec_())

