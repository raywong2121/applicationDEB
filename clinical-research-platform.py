#!/usr/bin/env python3
"""Dr.R 临床科研一体机浏览器.

该模块提供了 RUIYI TECH 定制的锁定全屏浏览器容器，用于 Ubuntu
20.04 等桌面环境的一体机场景。界面带有品牌化的顶部状态栏、快捷
入口侧边栏以及精简的导航控制，普通用户无法随意退出。
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from typing import Callable, Iterable, List, Sequence, Tuple

from branding_assets import load_dr_r_icon_bytes

APP_DISPLAY_NAME = "Dr.R"
APP_AUTHOR = "RUIYI TECH"
APP_VERSION = "1.0.0"
PORTAL_BASE = "http://127.0.0.1:8182/aiportal"
HOME_URL = f"{PORTAL_BASE}/user/login"
METADATA_FLAGS = {"--print-version", "--print-author"}


def parse_runtime_args(argv: Sequence[str]) -> tuple[argparse.Namespace, List[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--print-version", action="store_true", help="仅输出版本号")
    parser.add_argument("--print-author", action="store_true", help="仅输出开发者信息")
    known, remaining = parser.parse_known_args(argv[1:])
    return known, [argv[0], *remaining]


def _maybe_handle_metadata_request(argv: Sequence[str]) -> None:
    parsed_args, _ = parse_runtime_args(argv)
    if parsed_args.print_version:
        print(APP_VERSION)
        raise SystemExit(0)
    if parsed_args.print_author:
        print(APP_AUTHOR)
        raise SystemExit(0)


if METADATA_FLAGS.intersection(sys.argv[1:]):
    _maybe_handle_metadata_request(sys.argv)


from PyQt5.QtCore import QTimer, QTime, QUrl, Qt
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView


# 侧边栏快捷入口配置（标题, URL）
QUICK_LINKS: Sequence[Tuple[str, str]] = (
    ("科研门户", HOME_URL),
    ("数据填报", f"{PORTAL_BASE}/data-entry"),
    ("试验管理", f"{PORTAL_BASE}/trial"),
    ("分析驾驶舱", f"{PORTAL_BASE}/dashboard"),
    ("知识库", f"{PORTAL_BASE}/library"),
)


class InputAssistant(QDialog):
    """为全屏场景提供的输入法缓冲器."""

    def __init__(self, parent: QWidget | None = None, commit_callback: Callable[[str], None] | None = None):
        super().__init__(parent)
        self.setWindowTitle("输入法辅助面板")
        self.setWindowFlag(Qt.Tool)
        self.setModal(False)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self._commit_callback = commit_callback
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        description = QLabel(
            "在此输入框中可自由使用系统输入法，点击“注入”后会将文本写入"
            "当前网页的光标位置。"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("请输入内容…")
        self.text_area.setAttribute(Qt.WA_InputMethodEnabled, True)
        layout.addWidget(self.text_area)

        button_box = QDialogButtonBox()
        self.inject_button = button_box.addButton("注入", QDialogButtonBox.AcceptRole)
        self.clear_button = button_box.addButton("清空", QDialogButtonBox.ResetRole)
        self.close_button = button_box.addButton("关闭", QDialogButtonBox.RejectRole)
        layout.addWidget(button_box)

        self.inject_button.clicked.connect(self._handle_accept)
        self.clear_button.clicked.connect(self.text_area.clear)
        self.close_button.clicked.connect(self.hide)

    def show_panel(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.text_area.setFocus()

    def take_text(self) -> str:
        return self.text_area.toPlainText().strip()

    def _handle_accept(self) -> None:
        text = self.take_text()
        if not text:
            return
        if self._commit_callback:
            self._commit_callback(text)
        self.text_area.clear()

@lru_cache(maxsize=1)
def build_window_icon() -> QIcon:
    """从内嵌的 Base64 资源构建窗口图标."""

    pixmap = QPixmap()
    pixmap.loadFromData(load_dr_r_icon_bytes(), "PNG")
    return QIcon(pixmap)


class KioskWebEnginePage(QWebEnginePage):
    """自定义 Page，禁止弹出窗口并在主视图内导航."""

    def __init__(self, parent=None, main_view: QWebEngineView | None = None):
        super().__init__(parent)
        self._main_view = main_view

    def createWindow(self, _type):  # noqa: D401
        new_page = QWebEnginePage(self)
        new_page.urlChanged.connect(self._handle_new_window)
        return new_page

    def _handle_new_window(self, url: QUrl) -> None:
        if self._main_view is not None:
            self._main_view.setUrl(url)

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationTypeLinkClicked and is_main_frame:
            if self._main_view is not None:
                self._main_view.setUrl(url)
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)


class FullScreenBrowser(QMainWindow):
    """全屏锁定的浏览器窗口."""

    def __init__(self, url: str, quick_links: Sequence[Tuple[str, str]] | None = None):
        super().__init__()
        self.home_url = QUrl(url)
        self.quick_links = list(quick_links or [])
        self.browser = QWebEngineView()
        self.status_chip = QLabel("准备就绪")
        self.title_label = QLabel(APP_DISPLAY_NAME)
        self.clock_label = QLabel()
        self._admin_unlocked = False
        self.input_helper = InputAssistant(self, self.inject_text_from_input_helper)
        self._build_ui()
        self._install_event_bindings()

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(build_window_icon())
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setObjectName("RootWindow")

        # 顶部状态栏
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 12, 24, 12)
        top_layout.setSpacing(16)

        self.title_label.setObjectName("Title")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.status_chip.setObjectName("StatusChip")
        self.status_chip.setText(f"🔒 {APP_AUTHOR} · 安全模式")

        self.clock_label.setObjectName("Clock")
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top_layout.addWidget(self.title_label, 3)
        top_layout.addWidget(self.status_chip, 2)
        top_layout.addWidget(self.clock_label, 1)

        # 侧边栏
        side_panel = QFrame()
        side_panel.setObjectName("SidePanel")
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(24, 24, 24, 24)
        side_layout.setSpacing(12)

        nav_buttons = self._build_nav_buttons()
        side_layout.addWidget(nav_buttons)

        quick_section = QVBoxLayout()
        quick_label = QLabel("快捷入口")
        quick_label.setObjectName("SectionLabel")
        quick_section.addWidget(quick_label)
        input_helper_btn = QPushButton("输入法辅助面板")
        input_helper_btn.setObjectName("QuickLink")
        input_helper_btn.clicked.connect(self.open_input_helper)
        quick_section.addWidget(input_helper_btn)
        for title, link in self.quick_links:
            quick_section.addWidget(self._create_quick_link_button(title, link))
        quick_section.addStretch()

        quick_container = QFrame()
        quick_container.setLayout(quick_section)
        quick_container.setObjectName("QuickLinks")
        side_layout.addWidget(quick_container, 1)

        # 浏览器主体
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)
        self.browser.setObjectName("Browser")
        self.browser.setPage(KioskWebEnginePage(self.browser, self.browser))
        self.browser.setUrl(self.home_url)
        self.browser.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.browser.setFocusPolicy(Qt.StrongFocus)

        # 组合主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(top_bar)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(side_panel, 0)
        content_layout.addWidget(self.browser, 1)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self._apply_styles()
        self.showFullScreen()

    def _build_nav_buttons(self) -> QWidget:
        nav_container = QFrame()
        nav_container.setObjectName("NavButtons")
        layout = QHBoxLayout(nav_container)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        buttons: Iterable[Tuple[str, str, Callable[[], None]]] = (
            ("⇦", "后退", self.browser.back),
            ("⇨", "前进", self.browser.forward),
            ("⟳", "刷新", self.browser.reload),
            ("⌂", "主页", self.load_home),
        )

        for symbol, tooltip, handler in buttons:
            btn = QPushButton(symbol)
            btn.setToolTip(tooltip)
            btn.setObjectName("NavButton")
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        return nav_container

    def _create_quick_link_button(self, title: str, link: str) -> QPushButton:
        button = QPushButton(title)
        button.setObjectName("QuickLink")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda _=False, url=link: self.navigate_to(url))
        return button

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #RootWindow {
                background-color: #05060B;
                color: #EEF3FF;
            }
            #TopBar {
                background-color: rgba(7, 11, 25, 0.95);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            #Title {
                font-size: 28px;
                font-weight: 600;
            }
            #Clock {
                font-size: 18px;
                color: #8DA2C0;
            }
            #StatusChip {
                background-color: rgba(23, 92, 255, 0.25);
                border-radius: 18px;
                padding: 6px 18px;
                font-size: 16px;
            }
            #SidePanel {
                background-color: rgba(12, 18, 38, 0.9);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
            #NavButtons QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 16px;
                padding: 18px;
                font-size: 22px;
                color: #EEF3FF;
            }
            #NavButtons QPushButton:hover {
                background-color: rgba(0, 200, 255, 0.25);
            }
            #QuickLinks {
                background-color: rgba(5, 8, 20, 0.6);
                border-radius: 24px;
                padding: 16px;
            }
            #SectionLabel {
                font-size: 18px;
                font-weight: 600;
                color: #6DA2FF;
            }
            #QuickLink {
                text-align: left;
                padding: 12px 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.02);
                font-size: 16px;
            }
            #QuickLink:hover {
                border-color: rgba(109, 162, 255, 0.8);
                background-color: rgba(109, 162, 255, 0.15);
            }
        """
        )

    # ------------------------------------------------------------------
    # 行为逻辑
    # ------------------------------------------------------------------
    def _install_event_bindings(self) -> None:
        self.browser.loadStarted.connect(lambda: self._set_status("🌐 页面加载中…"))
        self.browser.loadFinished.connect(self._handle_load_finished)
        self.browser.titleChanged.connect(self._update_page_title)

        self.browser.page().fullScreenRequested.connect(lambda req: req.accept())

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1_000)
        self._update_clock()

        QShortcut(QKeySequence("Ctrl+Alt+Shift+L"), self, activated=self._toggle_admin_lock)
        QShortcut(QKeySequence("Ctrl+Alt+Shift+Q"), self, activated=self._admin_exit)
        QShortcut(QKeySequence("Ctrl+Alt+Shift+H"), self, activated=self.load_home)

    def open_input_helper(self) -> None:
        self.input_helper.show_panel()

    def inject_text_from_input_helper(self, text: str) -> None:
        if not text:
            self._set_status("⚠️ 输入内容为空")
            return

        script = (
            """
            (function(text){
                const el = document.activeElement;
                if (!el) { return false; }
                if (el.isContentEditable) {
                    document.execCommand('insertText', false, text);
                    return true;
                }
                if (typeof el.value === 'string') {
                    const start = el.selectionStart ?? el.value.length;
                    const end = el.selectionEnd ?? el.value.length;
                    const value = el.value;
                    const newValue = value.slice(0, start) + text + value.slice(end);
                    el.value = newValue;
                    if (typeof el.setSelectionRange === 'function') {
                        const pos = start + text.length;
                        el.setSelectionRange(pos, pos);
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            })(%s);
            """
            % json.dumps(text)
        )

        self.browser.page().runJavaScript(script, self._handle_input_helper_result)

    def _handle_input_helper_result(self, success: bool) -> None:
        if success:
            self._set_status("📝 已将辅助输入内容写入页面")
        else:
            self._set_status("⚠️ 当前页面没有可写入的输入框")

    def _update_clock(self) -> None:
        self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def _update_page_title(self, title: str) -> None:
        self.title_label.setText(f"{APP_DISPLAY_NAME} · {title}")

    def _handle_load_finished(self, success: bool) -> None:
        if success:
            self._set_status("✅ 页面加载完成")
        else:
            self._set_status("⚠️ 页面加载失败，请检查网络")

    def _set_status(self, message: str) -> None:
        self.status_chip.setText(message)

    def navigate_to(self, url: str) -> None:
        self.browser.setUrl(QUrl(url))

    def load_home(self) -> None:
        self.browser.setUrl(self.home_url)

    def _toggle_admin_lock(self) -> None:
        self._admin_unlocked = not self._admin_unlocked
        if self._admin_unlocked:
            self._set_status("🔓 管理员模式：允许退出")
        else:
            self._set_status(f"🔒 {APP_AUTHOR} · 安全模式")

    def _admin_exit(self) -> None:
        if self._admin_unlocked:
            QApplication.instance().quit()

    # ------------------------------------------------------------------
    # 键盘与关闭控制
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):  # noqa: D401
        if (event.key() == Qt.Key_F4 and event.modifiers() & Qt.AltModifier) or event.key() == Qt.Key_Escape:
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):  # noqa: D401
        if self._admin_unlocked:
            event.accept()
        else:
            event.ignore()


def create_application(argv: List[str]) -> QApplication:
    """创建 QApplication 并启用高分屏优化."""

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(argv)
    app.setOrganizationName(APP_AUTHOR)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setApplicationVersion(APP_VERSION)
    return app


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv or sys.argv)
    parsed_args, qt_argv = parse_runtime_args(argv)

    if parsed_args.print_version:
        print(APP_VERSION)
        return 0
    if parsed_args.print_author:
        print(APP_AUTHOR)
        return 0

    app = create_application(qt_argv)
    window = FullScreenBrowser(HOME_URL, QUICK_LINKS)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
