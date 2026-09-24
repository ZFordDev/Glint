"""Settings window for runtime preferences."""

from copy import deepcopy

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.theme import THEME_COLOR_KEYS, load_theme, load_themes

_COLOR_LABELS = {
    "background": "Background",
    "overlay_top": "Top highlight",
    "overlay_bottom": "Bottom highlight",
    "border": "Border",
    "text": "Text",
    "track": "Progress track",
    "good": "Good (low load)",
    "warning": "Warning accent",
    "critical": "Critical (high load)",
    "header": "Header title",
    "footer": "Footer version",
}


class SettingsWindow(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, settings: dict, hud=None) -> None:
        # This must remain top-level instead of becoming a panel owned by the
        # frameless HUD.
        super().__init__(windowTitle="Glint Settings")
        self.settings = deepcopy(settings)
        self.resize(600, 500)
        outer_layout = QVBoxLayout(self)
        layout = QHBoxLayout()
        self.navigation = QListWidget()
        self.navigation.addItems(["General", "Appearance", "Layout"])
        self.pages = QStackedWidget()
        general = QWidget()
        form = QFormLayout(general)
        self.refresh = QSpinBox(minimum=250, maximum=60_000, suffix=" ms", value=settings["refresh_interval_ms"])
        form.addRow("Refresh interval", self.refresh)
        self.title = QLineEdit(settings.get("title", "Glint"))
        form.addRow("Title Name", self.title)
        self.update_notify = QCheckBox("Show a yellow dot when an update is available")
        self.update_notify.setChecked(settings.get("check_updates", False))
        form.addRow("Check for updates", self.update_notify)
        appearance = QWidget()
        outer_form = QFormLayout()
        self.opacity = QSpinBox(minimum=20, maximum=100, suffix=" %", value=round(settings["opacity"] * 100))
        self.theme = QComboBox()
        self.theme.addItems(load_themes().keys())
        self.theme.setCurrentText(settings["theme"])
        outer_form.addRow("Opacity", self.opacity)
        outer_form.addRow("Theme", self.theme)
        self.overrides = dict(settings.get("custom_theme", {}))
        self._base_theme = load_theme(self.theme.currentText())
        self._rows: list[tuple[str, QPushButton, QLabel]] = []
        colors_group = QGroupBox("Custom colors")
        colors_layout = QVBoxLayout(colors_group)
        for key in THEME_COLOR_KEYS:
            colors_layout.addWidget(self._make_color_row(key))
        self._refresh_rows()
        reset_all = QPushButton("Reset all to theme defaults")
        reset_all.clicked.connect(self._reset_all)
        colors_layout.addWidget(reset_all)
        colors_scroll = QScrollArea()
        colors_scroll.setWidgetResizable(True)
        colors_scroll.setWidget(colors_group)
        appearance_layout = QVBoxLayout(appearance)
        appearance_layout.addLayout(outer_form)
        appearance_layout.addWidget(colors_scroll, 1)
        layout_page = QWidget()
        layout_form = QFormLayout(layout_page)
        if hud is not None:
            edit_button = QPushButton("Open Layout Editor")
            edit_button.clicked.connect(hud.enter_edit_mode)
            layout_form.addRow("Edit Layout", edit_button)
            reset_button = QPushButton("Reset to defaults")
            reset_button.clicked.connect(hud.reset_layout)
            layout_form.addRow("Reset Layout", reset_button)
        layout_form.addRow(
            QLabel("Drag widgets directly on the HUD to rearrange them. Changes persist when you Save.")
        )
        for page in (general, appearance, layout_page):
            self.pages.addWidget(page)
        layout.addWidget(self.navigation)
        layout.addWidget(self.pages)
        outer_layout.addLayout(layout)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.refresh.valueChanged.connect(self._emit)
        self.opacity.valueChanged.connect(self._emit)
        self.theme.currentTextChanged.connect(self._on_theme_changed)
        self.title.textChanged.connect(self._emit)
        self.update_notify.toggled.connect(self._emit)

    @staticmethod
    def _swatch_style(value: QColor) -> str:
        return (
            f"background-color: rgba({value.red()}, {value.green()}, {value.blue()}, {value.alpha()});"
            " border: 1px solid #555; border-radius: 3px;"
        )

    def _make_color_row(self, key: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        swatch = QPushButton()
        swatch.setFixedSize(44, 18)
        swatch.setAccessibleName(key)
        swatch.clicked.connect(lambda _checked=False, k=key: self._open_picker(k))
        name = QLabel(_COLOR_LABELS[key])
        name.setMinimumWidth(110)
        hex_label = QLabel()
        hex_label.setStyleSheet("color: #888;")
        reset = QToolButton()
        reset.setText("×")
        reset.setToolTip("Reset to theme default")
        reset.clicked.connect(lambda _checked=False, k=key: self._reset_override(k))
        layout.addWidget(swatch)
        layout.addWidget(name)
        layout.addWidget(hex_label, 1)
        layout.addWidget(reset)
        self._rows.append((key, swatch, hex_label))
        return widget

    def _base_color(self, key: str) -> QColor:
        return QColor(self._base_theme.get("colors", {}).get(key, "#FFFFFF"))

    def _effective_color(self, key: str) -> QColor:
        override = self.overrides.get(key)
        return QColor(override) if override else self._base_color(key)

    def _update_row(self, key: str, value: QColor) -> None:
        for row_key, swatch, hex_label in self._rows:
            if row_key == key:
                swatch.setStyleSheet(self._swatch_style(value))
                hex_label.setText(value.name(QColor.NameFormat.HexArgb))
                return

    def _refresh_rows(self) -> None:
        for key, _swatch, _label in self._rows:
            self._update_row(key, self._effective_color(key))

    def _open_picker(self, key: str) -> None:
        self._picker = QColorDialog(self._effective_color(key), self)
        self._picker.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel)
        self._picker.colorSelected.connect(lambda value, k=key: self.apply_override(k, value))
        self._picker.show()

    def apply_override(self, key: str, value: QColor) -> None:
        self.overrides[key] = value.name(QColor.NameFormat.HexArgb)
        self._update_row(key, value)
        self._emit()

    def _reset_override(self, key: str) -> None:
        self.overrides.pop(key, None)
        self._update_row(key, self._base_color(key))
        self._emit()

    def _reset_all(self) -> None:
        self.overrides.clear()
        self._refresh_rows()
        self._emit()

    def _on_theme_changed(self, name: str) -> None:
        self._base_theme = load_theme(name)
        self._refresh_rows()
        self._emit()

    def _emit(self) -> None:
        self.settings["refresh_interval_ms"] = self.refresh.value()
        self.settings["opacity"] = self.opacity.value() / 100
        self.settings["theme"] = self.theme.currentText()
        self.settings["title"] = self.title.text() or "Glint"
        self.settings["check_updates"] = self.update_notify.isChecked()
        self.settings["custom_theme"] = dict(self.overrides)
        self.settings_changed.emit(deepcopy(self.settings))
