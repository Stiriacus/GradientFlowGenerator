"""ui/lighting_panel.py

Lighting panel for the Frost Dune Background Generator.

This widget provides a UI to edit LightingConfig:
- LightAzimuthDeg (0–360°)
- LightElevationDeg (0–90°)
- Intensity (0–1)

It emits a LightingChanged signal whenever the LightingConfig has been
modified.

Naming follows a C#-like convention (PascalCase for classes, methods,
properties) where possible, while still integrating with Qt.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

try:
    # Project layout imports
    from model.lighting_config import LightingConfig
except ImportError:  # pragma: no cover - fallback for flat layout
    from lighting_config import LightingConfig  # type: ignore


class LightingPanel(QGroupBox):
    """UI panel for editing LightingConfig."""

    LightingChanged = Signal(object)  # emits the updated LightingConfig

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Lighting", parent)

        self._Lighting: Optional[LightingConfig] = None

        self._CreateUi()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _CreateUi(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Azimuth --------------------------------------------------------
        azLayout = QHBoxLayout()
        self._AzimuthSlider = QSlider(Qt.Horizontal, self)
        self._AzimuthSlider.setRange(0, 360)

        self._AzimuthSpin = QDoubleSpinBox(self)
        self._AzimuthSpin.setRange(0.0, 360.0)
        self._AzimuthSpin.setDecimals(1)

        self._AzimuthSlider.valueChanged.connect(self._OnAzimuthSliderChanged)
        self._AzimuthSpin.valueChanged.connect(self._OnAzimuthSpinChanged)

        azLayout.addWidget(self._AzimuthSlider, 1)
        azLayout.addWidget(self._AzimuthSpin)

        form.addRow(QLabel("Azimuth (deg):", self), azLayout)

        # Elevation ------------------------------------------------------
        elLayout = QHBoxLayout()
        self._ElevationSlider = QSlider(Qt.Horizontal, self)
        self._ElevationSlider.setRange(0, 90)

        self._ElevationSpin = QDoubleSpinBox(self)
        self._ElevationSpin.setRange(0.0, 90.0)
        self._ElevationSpin.setDecimals(1)

        self._ElevationSlider.valueChanged.connect(self._OnElevationSliderChanged)
        self._ElevationSpin.valueChanged.connect(self._OnElevationSpinChanged)

        elLayout.addWidget(self._ElevationSlider, 1)
        elLayout.addWidget(self._ElevationSpin)

        form.addRow(QLabel("Elevation (deg):", self), elLayout)

        # Intensity ------------------------------------------------------
        intLayout = QHBoxLayout()
        self._IntensitySlider = QSlider(Qt.Horizontal, self)
        self._IntensitySlider.setRange(0, 100)

        self._IntensitySpin = QDoubleSpinBox(self)
        self._IntensitySpin.setRange(0.0, 1.0)
        self._IntensitySpin.setDecimals(2)

        self._IntensitySlider.valueChanged.connect(self._OnIntensitySliderChanged)
        self._IntensitySpin.valueChanged.connect(self._OnIntensitySpinChanged)

        intLayout.addWidget(self._IntensitySlider, 1)
        intLayout.addWidget(self._IntensitySpin)

        form.addRow(QLabel("Intensity:", self), intLayout)

        layout.addLayout(form)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def BindLighting(self, lighting: LightingConfig) -> None:
        """Bind the panel to an existing LightingConfig instance."""

        self._Lighting = lighting
        self._LoadFromLighting()

    def GetLighting(self) -> Optional[LightingConfig]:
        return self._Lighting

    # ------------------------------------------------------------------
    # Loading / saving helpers
    # ------------------------------------------------------------------

    def _LoadFromLighting(self) -> None:
        if self._Lighting is None:
            return

        self._AzimuthSlider.blockSignals(True)
        self._AzimuthSpin.blockSignals(True)
        self._ElevationSlider.blockSignals(True)
        self._ElevationSpin.blockSignals(True)
        self._IntensitySlider.blockSignals(True)
        self._IntensitySpin.blockSignals(True)

        self._AzimuthSlider.setValue(int(round(self._Lighting.LightAzimuthDeg)))
        self._AzimuthSpin.setValue(float(self._Lighting.LightAzimuthDeg))

        self._ElevationSlider.setValue(int(round(self._Lighting.LightElevationDeg)))
        self._ElevationSpin.setValue(float(self._Lighting.LightElevationDeg))

        self._IntensitySlider.setValue(int(round(self._Lighting.Intensity * 100.0)))
        self._IntensitySpin.setValue(float(self._Lighting.Intensity))

        self._AzimuthSlider.blockSignals(False)
        self._AzimuthSpin.blockSignals(False)
        self._ElevationSlider.blockSignals(False)
        self._ElevationSpin.blockSignals(False)
        self._IntensitySlider.blockSignals(False)
        self._IntensitySpin.blockSignals(False)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _OnAzimuthSliderChanged(self, value: int) -> None:
        self._AzimuthSpin.blockSignals(True)
        self._AzimuthSpin.setValue(float(value))
        self._AzimuthSpin.blockSignals(False)
        self._UpdateAzimuth(float(value))

    def _OnAzimuthSpinChanged(self, value: float) -> None:
        self._AzimuthSlider.blockSignals(True)
        self._AzimuthSlider.setValue(int(round(value)))
        self._AzimuthSlider.blockSignals(False)
        self._UpdateAzimuth(float(value))

    def _UpdateAzimuth(self, value: float) -> None:
        if self._Lighting is None:
            return

        self._Lighting.LightAzimuthDeg = float(value)
        self.LightingChanged.emit(self._Lighting)

    def _OnElevationSliderChanged(self, value: int) -> None:
        self._ElevationSpin.blockSignals(True)
        self._ElevationSpin.setValue(float(value))
        self._ElevationSpin.blockSignals(False)
        self._UpdateElevation(float(value))

    def _OnElevationSpinChanged(self, value: float) -> None:
        self._ElevationSlider.blockSignals(True)
        self._ElevationSlider.setValue(int(round(value)))
        self._ElevationSlider.blockSignals(False)
        self._UpdateElevation(float(value))

    def _UpdateElevation(self, value: float) -> None:
        if self._Lighting is None:
            return

        self._Lighting.LightElevationDeg = float(value)
        self.LightingChanged.emit(self._Lighting)

    def _OnIntensitySliderChanged(self, value: int) -> None:
        # Map 0–100 -> 0.0–1.0
        f = float(value) / 100.0
        self._IntensitySpin.blockSignals(True)
        self._IntensitySpin.setValue(f)
        self._IntensitySpin.blockSignals(False)
        self._UpdateIntensity(f)

    def _OnIntensitySpinChanged(self, value: float) -> None:
        # Map 0.0–1.0 -> 0–100
        i = int(round(max(0.0, min(1.0, value)) * 100.0))
        self._IntensitySlider.blockSignals(True)
        self._IntensitySlider.setValue(i)
        self._IntensitySlider.blockSignals(False)
        self._UpdateIntensity(float(value))

    def _UpdateIntensity(self, value: float) -> None:
        if self._Lighting is None:
            return

        v = max(0.0, min(1.0, float(value)))
        self._Lighting.Intensity = v
        self.LightingChanged.emit(self._Lighting)
