from functools import partial
import platform
import ctypes
from typing import Optional

from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QIcon, QPalette
from PyQt5.QtWidgets import QToolButton, QTabBar, QTabWidget, QWidget, QApplication


# ---------- tiny helpers ----------

def _luminance(qcolor: QColor) -> float:
    # relative luminance 0..1 (sRGB)
    r, g, b = qcolor.redF(), qcolor.greenF(), qcolor.blueF()
    return 0.2126*r + 0.7152*g + 0.0722*b

def _make_x_pixmap(px: int, rgb: tuple[int, int, int], thickness: float) -> QPixmap:
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(*rgb))
    pen.setWidthF(thickness)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    m = 3
    p.drawLine(m, m, px - m, px - m)
    p.drawLine(px - m, m, m, px - m)
    p.end()
    return pm


# ---------- public: icons / hover ----------

def make_adaptive_close_icons(palette: QPalette, px: int = 14, thickness: float = 1.9):
    bg = palette.color(palette.Window)
    is_light = _luminance(bg) > 0.5

    if is_light:
        normal_rgb = (120, 120, 120)   # neutral gray
        hover_rgb  = (70, 70, 70)      # darker on hover
    else:
        normal_rgb = (210, 210, 210)   # light gray
        hover_rgb  = (255, 255, 255)   # pure white on hover
    disabled_rgb = (160, 160, 160) if not is_light else (180, 180, 180)

    normal   = QIcon(_make_x_pixmap(px, normal_rgb, thickness))
    hover    = QIcon(_make_x_pixmap(px, hover_rgb, thickness))
    disabled = QIcon(_make_x_pixmap(px, disabled_rgb, thickness))
    return normal, hover, disabled


def apply_simple_hover(button: QToolButton, normal: QIcon, hover: QIcon, disabled: QIcon):
    # flat, no outlines
    button.setStyleSheet(
        "QToolButton{border:none;background:transparent;padding:0;margin:0;}"
        "QToolButton:hover{background:transparent;}"
        "QToolButton::menu-indicator{image:none;}"
    )
    button.setIcon(normal)

    def _filter(_obj, ev):
        et = ev.type()
        if et == QEvent.EnabledChange:
            button.setIcon(normal if button.isEnabled() else disabled)
        elif et == QEvent.Enter:
            if button.isEnabled():
                button.setIcon(hover)
        elif et == QEvent.Leave:
            if button.isEnabled():
                button.setIcon(normal)
        return False

    # Keep the filter simple and self-contained
    button.installEventFilter(button)
    button._hover_filter_cb = _filter  # keep ref
    button.eventFilter = lambda o, e, cb=_filter: cb(o, e)


# ---------- public: tabs close buttons ----------

def update_tab_close_buttons(
    tabs: QTabWidget,
    settings_tab: Optional[QWidget],
    close_widget_callback,  # Callable[[QWidget], None]
    px: int = 14,
    thickness: float = 1.9,
):
    """
    Inject per-tab close buttons with palette-aware icons and hover behavior.
    """
    tab_bar = tabs.tabBar()
    tabs.setTabsClosable(False)  # we inject our own

    normal, hover, disabled = make_adaptive_close_icons(tabs.window().palette(), px, thickness)

    for index in range(tabs.count()):
        w = tabs.widget(index)
        if settings_tab is not None and w is settings_tab:
            for side in (QTabBar.LeftSide, QTabBar.RightSide):
                tab_bar.setTabButton(index, side, None)
            continue

        btn = QToolButton(tab_bar)
        btn.setAutoRaise(True)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setCursor(Qt.ArrowCursor)
        btn.setIconSize(QSize(px, px))
        apply_simple_hover(btn, normal, hover, disabled)
        btn.clicked.connect(partial(close_widget_callback, w))
        tab_bar.setTabButton(index, QTabBar.RightSide, btn)


# ---------- public: app palette / dark mode ----------

def apply_app_palette(app: QApplication, use_dark_mode: bool):
    """
    Apply (or reset) an application-wide palette and minimal style overrides.
    """
    if use_dark_mode:
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        # Subtle grey for disabled text
        disabled_text = QColor(160, 160, 160)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
        dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_text)

        # Tone down bevel/shadow highlights
        shadow_col = QColor(53, 53, 53)
        dark_palette.setColor(QPalette.Shadow, shadow_col)
        dark_palette.setColor(QPalette.Disabled, QPalette.Shadow, shadow_col)
        dark_palette.setColor(QPalette.Light, QColor(70, 70, 70))
        dark_palette.setColor(QPalette.Midlight, QColor(60, 60, 60))
        dark_palette.setColor(QPalette.Mid, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.Dark, QColor(35, 35, 35))

        app.setPalette(dark_palette)

        extra_css = """
        /* Brighter, visible separators in dark menus */
        QMenu::separator {
            height: 1px;
            margin: 6px 8px;
            background: #8A8A8A;
        }
        """
        app.setStyleSheet((app.styleSheet() or "") + extra_css)
    else:
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet("")


# ---------- public: Windows title bar tweak ----------

def enable_os_override_title_bar(hwnd: int):
    """Force a dark title bar on Windows 10 (1809+) and Windows 11 when dark mode is enabled."""
    if platform.system() == "Windows":
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Win10 1809+ / Win11
            is_dark_mode = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(is_dark_mode),
                ctypes.sizeof(is_dark_mode),
            )
        except Exception:
            # fail silently – not critical
            pass
