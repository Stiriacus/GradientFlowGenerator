"""ui/export_panel.py

Export panel for the Frost Dune Background Generator.

This widget provides a UI to configure export resolution and trigger a
PNG export using the current ProjectConfig.

Features
--------
- Preset resolutions (16:9, 4:3, portrait, etc.).
- Landscape/Portrait toggle (swaps width/height for presets).
- Custom width/height spin boxes.
- Export button that emits a signal with the chosen width/height.

The panel itself does **not** perform rendering or file I/O; it only
emits ExportRequested(width, height). The MainWindow (or controller
layer) is responsible for calling the renderer and saving the image.

Naming follows a C#-like convention (PascalCase for classes, methods,
properties) where possible, while still integrating with Qt.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ExportPanel(QGroupBox):
    """UI panel for configuring export resolution and triggering export."""

    ExportRequested = Signal(int, int)  # width, height

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Export", parent)

        self._PresetResolutions: Dict[str, Tuple[int, int]] = {
            "1920 x 1080 (16:9)": (1920, 1080),
            "1280 x 720 (16:9)": (1280, 720),
            "1080 x 1920 (Portrait 16:9)": (1080, 1920),
            "1024 x 768 (4:3)": (1024, 768),
        }

        self._CreatingUi = False

        self._CreateUi()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _CreateUi(self) -> None:
        self._CreatingUi = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Presets --------------------------------------------------------
        self._PresetCombo = QComboBox(self)
        for label in self._PresetResolutions.keys():
            self._PresetCombo.addItem(label)
        self._PresetCombo.currentIndexChanged.connect(self._OnPresetChanged)

        form.addRow(QLabel("Preset:", self), self._PresetCombo)

        # Orientation ----------------------------------------------------
        orientationLayout = QHBoxLayout()
        self._LandscapeRadio = QRadioButton("Landscape", self)
        self._PortraitRadio = QRadioButton("Portrait", self)

        self._LandscapeRadio.setChecked(True)

        self._LandscapeRadio.toggled.connect(self._OnOrientationChanged)
        self._PortraitRadio.toggled.connect(self._OnOrientationChanged)

        orientationLayout.addWidget(self._LandscapeRadio)
        orientationLayout.addWidget(self._PortraitRadio)

        form.addRow(QLabel("Orientation:", self), orientationLayout)

        # Custom width/height -------------------------------------------
        self._WidthSpin = QSpinBox(self)
        self._WidthSpin.setRange(16, 16384)
        self._WidthSpin.setSingleStep(16)

        self._HeightSpin = QSpinBox(self)
        self._HeightSpin.setRange(16, 16384)
        self._HeightSpin.setSingleStep(16)

        self._WidthSpin.valueChanged.connect(self._OnCustomResolutionChanged)
        self._HeightSpin.valueChanged.connect(self._OnCustomResolutionChanged)

        form.addRow(QLabel("Width:", self), self._WidthSpin)
        form.addRow(QLabel("Height:", self), self._HeightSpin)

        layout.addLayout(form)

        # Export button --------------------------------------------------
        self._ExportButton = QPushButton("Export PNG…", self)
        self._ExportButton.clicked.connect(self._OnExportClicked)

        layout.addWidget(self._ExportButton)

        # Initialize with first preset
        self._CreatingUi = False
        self._ApplyPresetResolution()

    # ------------------------------------------------------------------
    # Preset/orientation handling
    # ------------------------------------------------------------------

    def _CurrentPresetResolution(self) -> Tuple[int, int]:
        label = self._PresetCombo.currentText()
        return self._PresetResolutions.get(label, (1920, 1080))

    def _ApplyPresetResolution(self) -> None:
        width, height = self._CurrentPresetResolution()

        # Swap for orientation
        if self._PortraitRadio.isChecked() and width > height:
            width, height = height, width
        elif self._LandscapeRadio.isChecked() and height > width:
            width, height = height, width

        self._WidthSpin.blockSignals(True)
        self._HeightSpin.blockSignals(True)

        self._WidthSpin.setValue(width)
        self._HeightSpin.setValue(height)

        self._WidthSpin.blockSignals(False)
        self._HeightSpin.blockSignals(False)

    def _OnPresetChanged(self, index: int) -> None:
        if self._CreatingUi:
            return
        self._ApplyPresetResolution()

    def _OnOrientationChanged(self, checked: bool) -> None:
        if self._CreatingUi:
            return
        # Only react when a radio is checked
        if not checked:
            return
        self._ApplyPresetResolution()

    def _OnCustomResolutionChanged(self, _value: int) -> None:
        if self._CreatingUi:
            return
        # If the user modifies custom resolution manually, we do not
        # change the preset selection – the custom size simply overrides.
        pass

    # ------------------------------------------------------------------
    # Export trigger
    # ------------------------------------------------------------------

    def _OnExportClicked(self) -> None:
        width = int(self._WidthSpin.value())
        height = int(self._HeightSpin.value())

        if width <= 0 or height <= 0:
            return

        self.ExportRequested.emit(width, height)