"""Light/dark themes in the spirit of Windows 11 (Fluent) design.

The accent colour follows the Windows personalisation setting. Chart and
graph colours come from a categorical palette validated for colour-vision
deficiencies in both modes (fixed order; never cycled - extra groups fold
into a neutral "other" colour).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

CATEGORICAL_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CATEGORICAL_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
_DARK_STEP = {light.lower(): dark for light, dark in zip(CATEGORICAL_LIGHT, CATEGORICAL_DARK)}

UI_FONTS = ["Segoe UI Variable Text", "Segoe UI", "Arial"]


@dataclass(frozen=True)
class Theme:
    dark: bool
    window: str
    surface: str
    surface_alt: str
    sidebar: str
    hover: str
    pressed: str
    border: str
    border_strong: str
    text: str
    text_secondary: str
    text_muted: str
    accent: str
    accent_hover: str
    on_accent: str
    accent_subtle: str
    grid: str
    axis: str
    danger: str
    success: str
    categorical: list[str] = field(default_factory=list)

    def q(self, name: str) -> QColor:
        return QColor(getattr(self, name))

    def category(self, index: int) -> QColor:
        """Colour for group *index*; groups beyond the palette share a neutral grey."""
        if 0 <= index < len(self.categorical):
            return QColor(self.categorical[index])
        return QColor(self.text_muted)

    def entity(self, hex_color: str) -> QColor:
        """A stored entity colour (e.g. a link type), stepped for dark mode when known."""
        if self.dark:
            return QColor(_DARK_STEP.get(hex_color.lower(), hex_color))
        return QColor(hex_color)


def _windows_accent(dark: bool) -> str | None:
    if sys.platform != "win32":
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent") as key:
            data, _ = winreg.QueryValueEx(key, "AccentPalette")
        # Eight RGBA entries from lightest to darkest; Windows uses entry 1 on
        # dark backgrounds and entry 4 on light ones.
        r, g, b = data[4 * (1 if dark else 4): 4 * (1 if dark else 4) + 3]
        return f"#{r:02x}{g:02x}{b:02x}"
    except (OSError, ValueError, TypeError):
        return None


def system_prefers_dark() -> bool:
    hints = QGuiApplication.styleHints()
    try:
        return hints.colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:  # pragma: no cover - Qt < 6.5
        return False


def build_theme(mode: str = "system") -> Theme:
    dark = system_prefers_dark() if mode == "system" else mode == "dark"
    accent = _windows_accent(dark) or ("#60cdff" if dark else "#005fb8")
    a = QColor(accent)
    if dark:
        return Theme(
            dark=True, window="#202020", surface="#2b2b2b", surface_alt="#272727", sidebar="#1c1c1c",
            hover="#12ffffff", pressed="#0cffffff", border="#3a3a3a", border_strong="#4d4d4d",
            text="#f3f3f3", text_secondary="#c5c5c5", text_muted="#9a9a9a",
            accent=accent, accent_hover=a.lighter(112).name(), on_accent="#000000",
            accent_subtle=f"#{0x33:02x}{a.red():02x}{a.green():02x}{a.blue():02x}",
            grid="#383835", axis="#4a4a47", danger="#ff99a4", success="#6ccb5f",
            categorical=CATEGORICAL_DARK,
        )
    return Theme(
        dark=False, window="#f3f3f3", surface="#ffffff", surface_alt="#fafafa", sidebar="#ebebeb",
        hover="#0a000000", pressed="#06000000", border="#e5e5e5", border_strong="#cfcfcf",
        text="#1b1b1b", text_secondary="#5d5d5d", text_muted="#8a8a8a",
        accent=accent, accent_hover=a.lighter(115).name(), on_accent="#ffffff",
        accent_subtle=f"#{0x24:02x}{a.red():02x}{a.green():02x}{a.blue():02x}",
        grid="#e1e0d9", axis="#c3c2b7", danger="#c42b1c", success="#0f7b0f",
        categorical=CATEGORICAL_LIGHT,
    )


_current: Theme = build_theme("light")


def current() -> Theme:
    return _current


def ui_font(point_size: float = 10.0, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont()
    font.setFamilies(UI_FONTS)
    font.setPointSizeF(point_size)
    font.setWeight(weight)
    return font


def _indicator_images(t: Theme) -> str:
    """Render check mark and chevrons (Windows icon font) to PNGs that QSS can reference."""
    from zettelapp.paths import local_data_dir
    from zettelapp.ui import icons

    folder = local_data_dir() / "Cache" / f"theme-{'dark' if t.dark else 'light'}-{t.accent.lstrip('#')}"
    folder.mkdir(parents=True, exist_ok=True)
    for name, glyph, color in (("check", "check", t.on_accent), ("down", "chevron_down", t.text_secondary),
                               ("up", "chevron_up", t.text_secondary)):
        path = folder / f"{name}.png"
        if not path.exists():
            icons.icon(glyph, color, 16).pixmap(32, 32).save(str(path), "PNG")
    return folder.as_posix()


def _css(color: str) -> str:
    """QSS colour; #AARRGGBB values become rgba() so translucency is explicit."""
    c = QColor(color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {c.alpha()})" if c.alpha() < 255 else c.name()


def stylesheet(t: Theme) -> str:
    images = _indicator_images(t)
    t = Theme(**{k: (_css(v) if isinstance(v, str) and k in ("hover", "pressed", "accent_subtle") else v)
                 for k, v in t.__dict__.items()})
    return f"""
QCheckBox::indicator, QGroupBox::indicator, QTableWidget::indicator {{ width: 16px; height: 16px;
    border: 1px solid {t.border_strong}; border-radius: 4px; background: {t.surface}; }}
QCheckBox::indicator:hover, QTableWidget::indicator:hover {{ border-color: {t.text_secondary}; }}
QCheckBox::indicator:checked, QGroupBox::indicator:checked, QTableWidget::indicator:checked {{
    background: {t.accent}; border-color: {t.accent}; image: url({images}/check.png); }}
QRadioButton::indicator {{ width: 16px; height: 16px; border: 1px solid {t.border_strong}; border-radius: 9px;
    background: {t.surface}; }}
QRadioButton::indicator:checked {{ width: 8px; height: 8px; border: 5px solid {t.accent}; background: {t.on_accent}; }}
QComboBox::down-arrow {{ image: url({images}/down.png); width: 10px; height: 10px; }}
QSpinBox, QDoubleSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    border: none; background: transparent; width: 20px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover {{ background: {t.hover}; border-radius: 3px; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({images}/up.png); width: 9px; height: 9px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({images}/down.png); width: 9px; height: 9px; }}
QToolButton::menu-indicator {{ image: url({images}/down.png); width: 8px; height: 8px;
    subcontrol-origin: padding; subcontrol-position: right center; }}
QToolButton[noindicator="true"]::menu-indicator {{ image: none; width: 0; }}
QToolButton[popupMode="1"] {{ padding-right: 18px; }}
QToolButton::menu-button {{ border: none; width: 16px; }}
QToolButton::menu-arrow {{ image: url({images}/down.png); width: 8px; height: 8px; }}
QMainWindow, QDialog {{ background: {t.window}; }}
QWidget {{ color: {t.text}; }}
QWidget#Page, QWidget#Pane {{ background: {t.window}; }}
QFrame#Card, QWidget#Card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 8px; }}
QWidget#NavRail {{ background: {t.sidebar}; }}
QWidget#ListPane {{ background: {t.surface_alt}; border-right: 1px solid {t.border}; }}
QWidget#EditorPane {{ background: {t.surface}; }}
QWidget#SidePane {{ background: {t.surface_alt}; border-left: 1px solid {t.border}; }}
QLabel {{ background: transparent; }}
QLabel[role="title"] {{ font-size: 20pt; font-weight: 600; }}
QLabel[role="heading"] {{ font-size: 13pt; font-weight: 600; }}
QLabel[role="section"] {{ font-size: 10pt; font-weight: 600; }}
QLabel[role="secondary"] {{ color: {t.text_secondary}; }}
QLabel[role="caption"] {{ color: {t.text_muted}; font-size: 8.5pt; }}
QLabel[role="hero"] {{ font-size: 24pt; font-weight: 600; }}
QLabel[role="danger"] {{ color: {t.danger}; }}
QLabel a {{ color: {t.accent}; }}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {t.surface}; border: 1px solid {t.border}; border-bottom-color: {t.border_strong};
    border-radius: 4px; padding: 5px 8px; selection-background-color: {t.accent}; selection-color: {t.on_accent};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{ background: {t.surface_alt}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-bottom: 2px solid {t.accent}; padding-bottom: 4px;
}}
QLineEdit#TitleEdit {{ border: none; background: transparent; font-size: 20pt; font-weight: 600; padding: 0; }}
QLineEdit#TitleEdit:focus {{ border: none; padding: 0; }}
QLineEdit#Search {{ padding-left: 30px; border-radius: 6px; }}
QPlainTextEdit#BodyEdit, QTextBrowser#Preview {{ border: none; background: {t.surface}; padding: 0; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 6px;
    padding: 4px; selection-background-color: {t.hover}; selection-color: {t.text}; outline: 0; }}
QPushButton {{ background: {t.surface}; border: 1px solid {t.border}; border-bottom-color: {t.border_strong};
    border-radius: 4px; padding: 5px 14px; min-height: 20px; }}
QPushButton:hover {{ background: {t.surface_alt}; }}
QPushButton:pressed {{ background: {t.window}; color: {t.text_secondary}; }}
QPushButton:disabled {{ color: {t.text_muted}; }}
QPushButton[accent="true"] {{ background: {t.accent}; color: {t.on_accent}; border: 1px solid {t.accent}; font-weight: 600; }}
QPushButton[accent="true"]:hover {{ background: {t.accent_hover}; border-color: {t.accent_hover}; }}
QPushButton[accent="true"]:disabled {{ background: {t.border}; border-color: {t.border}; color: {t.text_muted}; }}
QPushButton[flat="true"] {{ background: transparent; border: none; color: {t.accent}; padding: 4px 6px; }}
QPushButton[flat="true"]:hover {{ background: {t.hover}; }}
QToolButton {{ background: transparent; border: none; border-radius: 4px; padding: 5px; }}
QToolButton:hover {{ background: {t.hover}; }}
QToolButton:pressed {{ background: {t.pressed}; }}
QToolButton:checked {{ background: {t.accent_subtle}; }}
QToolButton#NavButton {{ border-radius: 6px; padding: 6px 2px; font-size: 8pt; color: {t.text_secondary}; }}
QToolButton#NavButton:checked {{ background: {t.surface}; color: {t.text}; }}
QToolButton#Chip {{ background: {t.accent_subtle}; border-radius: 11px; padding: 2px 10px; }}
QToolButton#Chip:hover {{ background: {t.hover}; }}
QListView, QListWidget, QTreeView, QTreeWidget, QTableView, QTableWidget {{ background: transparent; border: none;
    outline: 0; alternate-background-color: {t.surface_alt}; }}
QListWidget::item, QTreeWidget::item {{ border-radius: 4px; padding: 5px 6px; }}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {t.hover}; }}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{ background: {t.accent_subtle}; color: {t.text}; }}
QHeaderView::section {{ background: transparent; border: none; border-bottom: 1px solid {t.border};
    padding: 6px 8px; color: {t.text_secondary}; font-weight: 600; }}
QTabWidget::pane {{ border: none; }}
QTabBar {{ qproperty-drawBase: 0; }}
QTabBar::tab {{ background: transparent; border: none; padding: 7px 14px; margin-right: 2px; color: {t.text_secondary}; }}
QTabBar::tab:hover {{ color: {t.text}; }}
QTabBar::tab:selected {{ color: {t.text}; border-bottom: 2px solid {t.accent}; font-weight: 600; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {t.border_strong}; border-radius: 3px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {t.text_muted}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ width: 0; height: 0; background: none; }}
QMenuBar {{ background: {t.window}; padding: 2px 4px; }}
QMenuBar::item {{ padding: 5px 10px; border-radius: 4px; background: transparent; }}
QMenuBar::item:selected {{ background: {t.hover}; }}
QMenu {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 6px 28px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {t.hover}; color: {t.text}; }}
QMenu::item:disabled {{ color: {t.text_muted}; }}
QMenu::separator {{ height: 1px; background: {t.border}; margin: 4px 8px; }}
QMenu::icon {{ padding-left: 8px; }}
QStatusBar {{ background: {t.window}; color: {t.text_secondary}; border-top: 1px solid {t.border}; }}
QStatusBar::item {{ border: none; }}
QSplitter::handle {{ background: transparent; }}
QToolTip {{ background: {t.surface}; color: {t.text}; border: 1px solid {t.border}; padding: 6px 8px; border-radius: 4px; }}
QProgressBar {{ background: {t.border}; border: none; border-radius: 2px; max-height: 4px; text-align: center; }}
QProgressBar::chunk {{ background: {t.accent}; border-radius: 2px; }}
QSlider::groove:horizontal {{ height: 4px; background: {t.border_strong}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {t.surface}; border: 4px solid {t.accent}; width: 12px; height: 12px;
    margin: -7px 0; border-radius: 10px; }}
QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QGroupBox {{ border: 1px solid {t.border}; border-radius: 8px; margin-top: 14px; padding: 12px; background: {t.surface}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; font-weight: 600; }}
QGraphicsView {{ border: none; background: {t.surface}; }}
"""


def apply_theme(app: QApplication, mode: str = "system", font_size: float = 10.0) -> Theme:
    global _current
    t = build_theme(mode)
    _current = t
    try:
        QGuiApplication.styleHints().setColorScheme(
            Qt.ColorScheme.Dark if t.dark else Qt.ColorScheme.Light if mode != "system" else Qt.ColorScheme.Unknown)
    except AttributeError:  # pragma: no cover - Qt < 6.8
        pass
    app.setStyle("Fusion")
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: t.window, QPalette.ColorRole.WindowText: t.text,
        QPalette.ColorRole.Base: t.surface, QPalette.ColorRole.AlternateBase: t.surface_alt,
        QPalette.ColorRole.Text: t.text, QPalette.ColorRole.Button: t.surface,
        QPalette.ColorRole.ButtonText: t.text, QPalette.ColorRole.Highlight: t.accent,
        QPalette.ColorRole.HighlightedText: t.on_accent, QPalette.ColorRole.ToolTipBase: t.surface,
        QPalette.ColorRole.ToolTipText: t.text, QPalette.ColorRole.PlaceholderText: t.text_muted,
        QPalette.ColorRole.Link: t.accent, QPalette.ColorRole.Mid: t.border_strong,
        QPalette.ColorRole.Midlight: t.border, QPalette.ColorRole.Light: t.surface,
        QPalette.ColorRole.Dark: t.border_strong, QPalette.ColorRole.Shadow: "#000000",
    }
    for role, color in roles.items():
        pal.setColor(role, QColor(color))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(t.text_muted))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(t.text_muted))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(t.text_muted))
    if hasattr(QPalette.ColorRole, "Accent"):
        pal.setColor(QPalette.ColorRole.Accent, QColor(t.accent))
    app.setPalette(pal)
    app.setFont(ui_font(font_size))
    app.setStyleSheet(stylesheet(t))
    from zettelapp.ui import icons
    icons.clear_cache()
    return t
