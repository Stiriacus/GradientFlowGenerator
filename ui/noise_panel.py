"""ui/noise_panel.py

Noise panel for the Frost Dune Background Generator.

This widget provides a UI to edit a list of NoiseLayerConfig objects
(Base, Detail, Warp). It focuses on the most important parameters:
- Enabled
- Type (Base / Detail / Warp) [read-only display for now]
- Seed
- ScaleX, ScaleY
- Octaves
- Persistence
- Lacunarity
- RidgePower
- HeightPower
- Amplitude

The panel emits a NoiseLayersChanged signal whenever the underlying
NoiseLayers list has been modified.

Naming follows a C#-like convention (PascalCase for classes, methods,
properties) where possible, while still integrating with Qt.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    # Project layout imports
    from model.noise_layer import NoiseLayerConfig, NoiseLayerType
except ImportError:  # pragma: no cover - fallback for flat layout
    from noise_layer import NoiseLayerConfig, NoiseLayerType  # type: ignore


class NoisePanel(QGroupBox):
    """UI panel for editing a list of NoiseLayerConfig objects."""

    NoiseLayersChanged = Signal(object)  # emits the updated List[NoiseLayerConfig]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Noise", parent)

        self._NoiseLayers: List[NoiseLayerConfig] = []
        self._CurrentIndex: int = -1

        self._CreateUi()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _CreateUi(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Top: layer list + add/remove buttons
        listLayout = QHBoxLayout()

        self._LayerList = QListWidget(self)
        self._LayerList.setSelectionMode(QListWidget.SingleSelection)
        self._LayerList.currentRowChanged.connect(self._OnLayerSelectionChanged)

        listLayout.addWidget(self._LayerList, 1)

        buttonsLayout = QVBoxLayout()
        self._AddBaseButton = QPushButton("Add Base", self)
        self._AddDetailButton = QPushButton("Add Detail", self)
        self._AddWarpButton = QPushButton("Add Warp", self)
        self._RemoveButton = QPushButton("Remove", self)

        self._AddBaseButton.clicked.connect(lambda: self._OnAddLayerClicked(NoiseLayerType.Base))
        self._AddDetailButton.clicked.connect(lambda: self._OnAddLayerClicked(NoiseLayerType.Detail))
        self._AddWarpButton.clicked.connect(lambda: self._OnAddLayerClicked(NoiseLayerType.Warp))
        self._RemoveButton.clicked.connect(self._OnRemoveLayerClicked)

        for btn in (self._AddBaseButton, self._AddDetailButton, self._AddWarpButton, self._RemoveButton):
            buttonsLayout.addWidget(btn)
        buttonsLayout.addStretch(1)

        listLayout.addLayout(buttonsLayout)

        layout.addLayout(listLayout, 1)

        # Bottom: layer detail editor
        self._DetailGroup = QGroupBox("Layer Settings", self)
        formLayout = QFormLayout(self._DetailGroup)
        formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Enabled
        self._EnabledCheck = QCheckBox("Enabled", self._DetailGroup)
        self._EnabledCheck.stateChanged.connect(self._OnDetailChanged)
        formLayout.addRow("", self._EnabledCheck)

        # Type (read-only display via label)
        self._TypeLabel = QLabel("", self._DetailGroup)
        formLayout.addRow("Type:", self._TypeLabel)

        # Seed
        self._SeedSpin = QSpinBox(self._DetailGroup)
        self._SeedSpin.setRange(-999999, 999999)
        self._SeedSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Seed:", self._SeedSpin)

        # ScaleX / ScaleY
        self._ScaleXSpin = QDoubleSpinBox(self._DetailGroup)
        self._ScaleXSpin.setRange(0.01, 50.0)
        self._ScaleXSpin.setSingleStep(0.1)
        self._ScaleXSpin.setDecimals(3)
        self._ScaleXSpin.valueChanged.connect(self._OnDetailChanged)

        self._ScaleYSpin = QDoubleSpinBox(self._DetailGroup)
        self._ScaleYSpin.setRange(0.01, 50.0)
        self._ScaleYSpin.setSingleStep(0.1)
        self._ScaleYSpin.setDecimals(3)
        self._ScaleYSpin.valueChanged.connect(self._OnDetailChanged)

        formLayout.addRow("Scale X:", self._ScaleXSpin)
        formLayout.addRow("Scale Y:", self._ScaleYSpin)

        # Octaves
        self._OctavesSpin = QSpinBox(self._DetailGroup)
        self._OctavesSpin.setRange(1, 10)
        self._OctavesSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Octaves:", self._OctavesSpin)

        # Persistence
        self._PersistenceSpin = QDoubleSpinBox(self._DetailGroup)
        self._PersistenceSpin.setRange(0.1, 1.0)
        self._PersistenceSpin.setSingleStep(0.05)
        self._PersistenceSpin.setDecimals(2)
        self._PersistenceSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Persistence:", self._PersistenceSpin)

        # Lacunarity
        self._LacunaritySpin = QDoubleSpinBox(self._DetailGroup)
        self._LacunaritySpin.setRange(1.0, 5.0)
        self._LacunaritySpin.setSingleStep(0.1)
        self._LacunaritySpin.setDecimals(2)
        self._LacunaritySpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Lacunarity:", self._LacunaritySpin)

        # RidgePower
        self._RidgePowerSpin = QDoubleSpinBox(self._DetailGroup)
        self._RidgePowerSpin.setRange(0.5, 8.0)
        self._RidgePowerSpin.setSingleStep(0.1)
        self._RidgePowerSpin.setDecimals(2)
        self._RidgePowerSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Ridge Power:", self._RidgePowerSpin)

        # HeightPower
        self._HeightPowerSpin = QDoubleSpinBox(self._DetailGroup)
        self._HeightPowerSpin.setRange(0.5, 5.0)
        self._HeightPowerSpin.setSingleStep(0.1)
        self._HeightPowerSpin.setDecimals(2)
        self._HeightPowerSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Height Power:", self._HeightPowerSpin)

        # Amplitude
        self._AmplitudeSpin = QDoubleSpinBox(self._DetailGroup)
        self._AmplitudeSpin.setRange(0.0, 5.0)
        self._AmplitudeSpin.setSingleStep(0.1)
        self._AmplitudeSpin.setDecimals(2)
        self._AmplitudeSpin.valueChanged.connect(self._OnDetailChanged)
        formLayout.addRow("Amplitude:", self._AmplitudeSpin)

        layout.addWidget(self._DetailGroup, 0)

        self._SetDetailEnabled(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def BindNoiseLayers(self, layers: List[NoiseLayerConfig]) -> None:
        """Bind the panel to the list of NoiseLayerConfig.

        The list is referenced directly; modifications in the panel
        update the same list object and emit NoiseLayersChanged.
        """

        self._NoiseLayers = layers
        self._ReloadLayerList()

    def GetNoiseLayers(self) -> List[NoiseLayerConfig]:
        return self._NoiseLayers

    # ------------------------------------------------------------------
    # Layer list handling
    # ------------------------------------------------------------------

    def _ReloadLayerList(self) -> None:
        self._LayerList.blockSignals(True)
        self._LayerList.clear()

        for i, layer in enumerate(self._NoiseLayers):
            text = f"{i}: {layer.LayerType.value.capitalize()}"
            if not layer.Enabled:
                text += " (disabled)"
            item = QListWidgetItem(text)
            self._LayerList.addItem(item)

        self._LayerList.blockSignals(False)

        if self._NoiseLayers:
            self._LayerList.setCurrentRow(0)
        else:
            self._CurrentIndex = -1
            self._SetDetailEnabled(False)

    def _OnAddLayerClicked(self, layerType: NoiseLayerType) -> None:
        # Reasonable defaults based on the spec
        if layerType == NoiseLayerType.Warp:
            layer = NoiseLayerConfig(
                LayerType=NoiseLayerType.Warp,
                Enabled=True,
                Seed=42,
                ScaleX=0.2,
                ScaleY=0.05,
                Octaves=2,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=1.0,
                HeightPower=1.0,
                Amplitude=0.5,
            )
        elif layerType == NoiseLayerType.Base:
            layer = NoiseLayerConfig(
                LayerType=NoiseLayerType.Base,
                Enabled=True,
                Seed=43,
                ScaleX=1.5,
                ScaleY=0.3,
                Octaves=5,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=2.0,
                HeightPower=1.7,
                Amplitude=1.0,
            )
        else:  # Detail
            layer = NoiseLayerConfig(
                LayerType=NoiseLayerType.Detail,
                Enabled=True,
                Seed=44,
                ScaleX=6.0,
                ScaleY=2.0,
                Octaves=3,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=2.0,
                HeightPower=1.3,
                Amplitude=0.4,
            )

        self._NoiseLayers.append(layer)
        self._ReloadLayerList()
        self.NoiseLayersChanged.emit(self._NoiseLayers)

    def _OnRemoveLayerClicked(self) -> None:
        row = self._LayerList.currentRow()
        if row < 0 or row >= len(self._NoiseLayers):
            return

        del self._NoiseLayers[row]
        self._ReloadLayerList()
        self.NoiseLayersChanged.emit(self._NoiseLayers)

    def _OnLayerSelectionChanged(self, index: int) -> None:
        self._CurrentIndex = index
        self._LoadCurrentLayerIntoDetail()

    # ------------------------------------------------------------------
    # Detail editor handling
    # ------------------------------------------------------------------

    def _SetDetailEnabled(self, enabled: bool) -> None:
        self._DetailGroup.setEnabled(enabled)

    def _LoadCurrentLayerIntoDetail(self) -> None:
        if self._CurrentIndex < 0 or self._CurrentIndex >= len(self._NoiseLayers):
            self._SetDetailEnabled(False)
            return

        layer = self._NoiseLayers[self._CurrentIndex]

        self._SetDetailEnabled(True)

        # Block signals to avoid feedback while populating
        self._EnabledCheck.blockSignals(True)
        self._SeedSpin.blockSignals(True)
        self._ScaleXSpin.blockSignals(True)
        self._ScaleYSpin.blockSignals(True)
        self._OctavesSpin.blockSignals(True)
        self._PersistenceSpin.blockSignals(True)
        self._LacunaritySpin.blockSignals(True)
        self._RidgePowerSpin.blockSignals(True)
        self._HeightPowerSpin.blockSignals(True)
        self._AmplitudeSpin.blockSignals(True)

        self._EnabledCheck.setChecked(layer.Enabled)
        self._TypeLabel.setText(layer.LayerType.value)
        self._SeedSpin.setValue(layer.Seed)
        self._ScaleXSpin.setValue(layer.ScaleX)
        self._ScaleYSpin.setValue(layer.ScaleY)
        self._OctavesSpin.setValue(layer.Octaves)
        self._PersistenceSpin.setValue(layer.Persistence)
        self._LacunaritySpin.setValue(layer.Lacunarity)
        self._RidgePowerSpin.setValue(layer.RidgePower)
        self._HeightPowerSpin.setValue(layer.HeightPower)
        self._AmplitudeSpin.setValue(layer.Amplitude)

        self._EnabledCheck.blockSignals(False)
        self._SeedSpin.blockSignals(False)
        self._ScaleXSpin.blockSignals(False)
        self._ScaleYSpin.blockSignals(False)
        self._OctavesSpin.blockSignals(False)
        self._PersistenceSpin.blockSignals(False)
        self._LacunaritySpin.blockSignals(False)
        self._RidgePowerSpin.blockSignals(False)
        self._HeightPowerSpin.blockSignals(False)
        self._AmplitudeSpin.blockSignals(False)

    def _OnDetailChanged(self) -> None:
        if self._CurrentIndex < 0 or self._CurrentIndex >= len(self._NoiseLayers):
            return

        layer = self._NoiseLayers[self._CurrentIndex]

        layer.Enabled = self._EnabledCheck.isChecked()
        # Type is not editable in this panel
        layer.Seed = int(self._SeedSpin.value())
        layer.ScaleX = float(self._ScaleXSpin.value())
        layer.ScaleY = float(self._ScaleYSpin.value())
        layer.Octaves = int(self._OctavesSpin.value())
        layer.Persistence = float(self._PersistenceSpin.value())
        layer.Lacunarity = float(self._LacunaritySpin.value())
        layer.RidgePower = float(self._RidgePowerSpin.value())
        layer.HeightPower = float(self._HeightPowerSpin.value())
        layer.Amplitude = float(self._AmplitudeSpin.value())

        # Update list entry text (e.g. to show disabled state)
        item = self._LayerList.item(self._CurrentIndex)
        if item is not None:
            text = f"{self._CurrentIndex}: {layer.LayerType.value.capitalize()}"
            if not layer.Enabled:
                text += " (disabled)"
            item.setText(text)

        self.NoiseLayersChanged.emit(self._NoiseLayers)