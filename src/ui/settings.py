"""Settings window for runtime preferences."""

from copy import deepcopy

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.theme import load_themes


class SettingsWindow(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, settings: dict, hud=None) -> None:
        # This must remain top-level instead of becoming a panel owned by the
        # frameless HUD.
        super().__init__(windowTitle="Glint Settings")
        self.settings = deepcopy(settings)
        self.resize(440, 360)
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
        form = QFormLayout(appearance)
        self.opacity = QSpinBox(minimum=20, maximum=100, suffix=" %", value=round(settings["opacity"] * 100))
        self.theme = QComboBox()
        self.theme.addItems(load_themes().keys())
        self.theme.setCurrentText(settings["theme"])
        form.addRow("Opacity", self.opacity)
        form.addRow("Theme", self.theme)
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
        self.theme.currentTextChanged.connect(self._emit)
        self.title.textChanged.connect(self._emit)
        self.update_notify.toggled.connect(self._emit)

    def _emit(self) -> None:
        self.settings["refresh_interval_ms"] = self.refresh.value()
        self.settings["opacity"] = self.opacity.value() / 100
        self.settings["theme"] = self.theme.currentText()
        self.settings["title"] = self.title.text() or "Glint"
        self.settings["check_updates"] = self.update_notify.isChecked()
        self.settings_changed.emit(deepcopy(self.settings))
