"""ui/gradient_panel.py

Gradient panel for the Frost Dune Background Generator.

This widget provides a UI to edit:
- Gradient angle (0–360°)
- Up to 6 GradientStops (position, color, opacity)
- A small live gradient preview bar

The panel emits a GradientChanged signal whenever the underlying
GradientConfig has been modified. It does **not** trigger a full image
render on its own; the main window controls when to start rendering.

Naming follows a C#-like convention (PascalCase for classes, methods,
properties) where possible, while still integrating with Qt.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    # Project layout imports
    from model.gradient_model import GradientConfig, GradientStop
    from core.gradient import ApplyGradient, RgbFloatToUint8
except ImportError:  # pragma: no cover - fallback for flat layout
    from gradient_model import GradientConfig, GradientStop  # type: ignore
    from gradient import ApplyGradient, RgbFloatToUint8  # type: ignore


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def NumpyRgbaToQPixmap(rgba: np.ndarray) -> QPixmap:
    """Convert an RGBA uint8 NumPy array (H, W, 4) to a QPixmap."""

    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("rgba must be a uint8 array of shape (H, W, 4)")

    height, width, _ = rgba.shape

    image = QImage(
        rgba.data,
        width,
        height,
        rgba.strides[0],
        QImage.Format_RGBA8888,
    ).copy()

    return QPixmap.fromImage(image)


# ---------------------------------------------------------------------------
# GradientPanel
# ---------------------------------------------------------------------------


class GradientPanel(QGroupBox):
    """UI panel for editing a GradientConfig."""

    GradientChanged = Signal(object)  # emits the updated GradientConfig

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Gradient", parent)

        self._Gradient: Optional[GradientConfig] = None

        self._CreateUi()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _CreateUi(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Angle controls -------------------------------------------------
        angleLayout = QHBoxLayout()
        angleLabel = QLabel("Angle (deg):", self)
        self._AngleSlider = QSlider(Qt.Horizontal, self)
        self._AngleSlider.setRange(0, 360)

        self._AngleSpin = QSpinBox(self)
        self._AngleSpin.setRange(0, 360)

        angleLayout.addWidget(angleLabel)
        angleLayout.addWidget(self._AngleSlider, 1)
        angleLayout.addWidget(self._AngleSpin)

        layout.addLayout(angleLayout)

        self._AngleSlider.valueChanged.connect(self._OnAngleSliderChanged)
        self._AngleSpin.valueChanged.connect(self._OnAngleSpinChanged)

        # Stops table ----------------------------------------------------
        stopsLabel = QLabel("Gradient Stops (max 6):", self)
        layout.addWidget(stopsLabel)

        self._StopsTable = QTableWidget(self)
        self._StopsTable.setColumnCount(3)
        self._StopsTable.setHorizontalHeaderLabels(["Position", "Color", "Opacity"])
        self._StopsTable.horizontalHeader().setStretchLastSection(True)
        self._StopsTable.setSelectionBehavior(QTableWidget.SelectRows)
        self._StopsTable.setSelectionMode(QTableWidget.SingleSelection)
        self._StopsTable.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self._StopsTable, 1)

        buttonsLayout = QHBoxLayout()
        self._AddStopButton = QPushButton("Add Stop", self)
        self._RemoveStopButton = QPushButton("Remove Stop", self)

        self._AddStopButton.clicked.connect(self._OnAddStopClicked)
        self._RemoveStopButton.clicked.connect(self._OnRemoveStopClicked)

        buttonsLayout.addWidget(self._AddStopButton)
        buttonsLayout.addWidget(self._RemoveStopButton)
        buttonsLayout.addStretch(1)

        layout.addLayout(buttonsLayout)

        # Gradient preview ----------------------------------------------
        previewLabel = QLabel("Preview:", self)
        layout.addWidget(previewLabel)

        self._PreviewBar = QLabel(self)
        self._PreviewBar.setMinimumHeight(32)
        self._PreviewBar.setAlignment(Qt.AlignCenter)
        self._PreviewBar.setStyleSheet("background-color: #111111; border: 1px solid #333333;")

        layout.addWidget(self._PreviewBar)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def BindGradient(self, gradient: GradientConfig) -> None:
        """Bind the panel to an existing GradientConfig instance.

        The panel will directly update this instance when the user edits
        values, and emit GradientChanged with the updated object.
        """

        self._Gradient = gradient

        # Initialize controls from the gradient
        self._AngleSlider.blockSignals(True)
        self._AngleSpin.blockSignals(True)

        angle = int(round(self._Gradient.AngleDeg))
        self._AngleSlider.setValue(angle)
        self._AngleSpin.setValue(angle)

        self._AngleSlider.blockSignals(False)
        self._AngleSpin.blockSignals(False)

        self._ReloadStopsFromGradient()
        self._UpdatePreview()

    def GetGradient(self) -> Optional[GradientConfig]:
        return self._Gradient

    # ------------------------------------------------------------------
    # Angle handling
    # ------------------------------------------------------------------

    def _OnAngleSliderChanged(self, value: int) -> None:
        self._AngleSpin.blockSignals(True)
        self._AngleSpin.setValue(value)
        self._AngleSpin.blockSignals(False)
        self._UpdateAngle(float(value))

    def _OnAngleSpinChanged(self, value: int) -> None:
        self._AngleSlider.blockSignals(True)
        self._AngleSlider.setValue(value)
        self._AngleSlider.blockSignals(False)
        self._UpdateAngle(float(value))

    def _UpdateAngle(self, angle: float) -> None:
        if self._Gradient is None:
            return

        self._Gradient.AngleDeg = float(angle)
        self._UpdatePreview()
        self.GradientChanged.emit(self._Gradient)

    # ------------------------------------------------------------------
    # Stops handling
    # ------------------------------------------------------------------

    def _ReloadStopsFromGradient(self) -> None:
        if self._Gradient is None:
            self._StopsTable.setRowCount(0)
            return

        stops = sorted(self._Gradient.Stops, key=lambda s: s.Position)
        self._StopsTable.setRowCount(0)

        for stop in stops:
            self._AddStopRow(stop)

    def _AddStopRow(self, stop: GradientStop) -> None:
        row = self._StopsTable.rowCount()
        self._StopsTable.insertRow(row)

        # Position
        posSpin = QDoubleSpinBox(self._StopsTable)
        posSpin.setRange(0.0, 1.0)
        posSpin.setDecimals(3)
        posSpin.setSingleStep(0.01)
        posSpin.setValue(float(stop.Position))
        posSpin.valueChanged.connect(self._OnStopsEdited)

        self._StopsTable.setCellWidget(row, 0, posSpin)
        self._StopsTable.setItem(row, 0, QTableWidgetItem())

        # Color
        colorButton = QPushButton(stop.Color, self._StopsTable)
        colorButton.setProperty("hexColor", stop.Color)
        colorButton.clicked.connect(lambda _=False, btn=colorButton: self._OnColorButtonClicked(btn))
        self._UpdateColorButtonStyle(colorButton)

        self._StopsTable.setCellWidget(row, 1, colorButton)
        self._StopsTable.setItem(row, 1, QTableWidgetItem())

        # Opacity
        opacitySpin = QDoubleSpinBox(self._StopsTable)
        opacitySpin.setRange(0.0, 1.0)
        opacitySpin.setDecimals(2)
        opacitySpin.setSingleStep(0.05)
        opacitySpin.setValue(float(stop.Opacity))
        opacitySpin.valueChanged.connect(self._OnStopsEdited)

        self._StopsTable.setCellWidget(row, 2, opacitySpin)
        self._StopsTable.setItem(row, 2, QTableWidgetItem())

    def _OnColorButtonClicked(self, button: QPushButton) -> None:
        currentHex = button.property("hexColor") or "#ffffff"
        color = QColor(currentHex)

        dlg = QColorDialog(color, self)
        dlg.setOption(QColorDialog.ShowAlphaChannel, False)

        if dlg.exec() == QColorDialog.Accepted:
            chosen = dlg.selectedColor()
            newHex = chosen.name(QColor.HexRgb)
            button.setProperty("hexColor", newHex)
            button.setText(newHex)
            self._UpdateColorButtonStyle(button)
            self._OnStopsEdited()

    def _UpdateColorButtonStyle(self, button: QPushButton) -> None:
        hexColor = button.property("hexColor") or "#ffffff"
        button.setStyleSheet(
            "QPushButton { background-color: %s; color: #ffffff; border: 1px solid #555555; }" % hexColor
        )

    def _OnAddStopClicked(self) -> None:
        if self._Gradient is None:
            return

        if self._StopsTable.rowCount() >= 6:
            return  # max 6 stops

        # Default new stop: mid-position, use last stop's color if available
        defaultPos = 0.5
        defaultColor = "#ffffff"
        defaultOpacity = 1.0

        if self._Gradient.Stops:
            last = sorted(self._Gradient.Stops, key=lambda s: s.Position)[-1]
            defaultColor = last.Color

        newStop = GradientStop(Position=defaultPos, Color=defaultColor, Opacity=defaultOpacity)
        self._AddStopRow(newStop)
        self._OnStopsEdited()

    def _OnRemoveStopClicked(self) -> None:
        if self._Gradient is None:
            return

        row = self._StopsTable.currentRow()
        if row < 0:
            return

        if self._StopsTable.rowCount() <= 1:
            return  # keep at least one stop

        self._StopsTable.removeRow(row)
        self._OnStopsEdited()

    def _OnStopsEdited(self) -> None:
        """Rebuild Gradient.Stops from the table and emit change."""

        if self._Gradient is None:
            return

        stops = []
        rows = self._StopsTable.rowCount()

        for row in range(rows):
            posWidget = self._StopsTable.cellWidget(row, 0)
            colorWidget = self._StopsTable.cellWidget(row, 1)
            opacityWidget = self._StopsTable.cellWidget(row, 2)

            if not isinstance(posWidget, QDoubleSpinBox) or not isinstance(colorWidget, QPushButton) or not isinstance(opacityWidget, QDoubleSpinBox):
                continue

            position = float(posWidget.value())
            hexColor = colorWidget.property("hexColor") or colorWidget.text() or "#ffffff"
            opacity = float(opacityWidget.value())

            # Clamp and clean up
            if not isinstance(hexColor, str):
                hexColor = str(hexColor)
            if not hexColor.startswith("#"):
                hexColor = "#" + hexColor

            position = max(0.0, min(1.0, position))
            opacity = max(0.0, min(1.0, opacity))

            stops.append(GradientStop(Position=position, Color=hexColor, Opacity=opacity))

        # Sort by position and assign back
        stops.sort(key=lambda s: s.Position)
        self._Gradient.Stops = stops

        self._UpdatePreview()
        self.GradientChanged.emit(self._Gradient)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _UpdatePreview(self) -> None:
        if self._Gradient is None:
            self._PreviewBar.setText("No gradient")
            self._PreviewBar.setPixmap(QPixmap())
            return

        try:
            width = 256
            height = 32
            r, g, b, a = ApplyGradient(self._Gradient, width, height)
            r8, g8, b8 = RgbFloatToUint8(r, g, b)
            a8 = (np.clip(a, 0.0, 1.0) * 255.0).astype(np.uint8)
            rgba = np.dstack([r8, g8, b8, a8])

            pix = NumpyRgbaToQPixmap(rgba)
            self._PreviewBar.setPixmap(pix)
            self._PreviewBar.setText("")
        except Exception:
            self._PreviewBar.setText("Preview error")
            self._PreviewBar.setPixmap(QPixmap())