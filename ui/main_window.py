"""ui/main_window.py

Main application window for the Frost Dune Background Generator.

This module provides a QMainWindow subclass that:
- Sets up the basic layout (sidebar + preview area).
- Integrates the RenderWorker for background rendering.
- Displays the main preview image and noise previews.
- Shows elapsed render time in the status bar and allows canceling.

This is a foundational skeleton; detailed parameter panels (Global,
Noise, Lighting, Export) are represented as placeholders and can be
implemented in separate modules later.

Naming follows a C#-style convention (PascalCase for classes, methods,
properties) where possible, while respecting Qt's requirements.
"""

from __future__ import annotations

import sys
from typing import Optional, Dict

import numpy as np
from model.gradient_model import GradientConfig 
from ui.gradient_panel import GradientPanel
from ui.noise_panel import NoisePanel
from model.noise_layer import NoiseLayerConfig 
from ui.lighting_panel import LightingPanel
from model.lighting_config import LightingConfig
from core.renderer import RenderImageToPillow
from ui.export_panel import ExportPanel
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QSpacerItem,
)

try:
    # Project layout imports
    from model.project_config import ProjectConfig
    from workers.render_worker import RenderWorker
except ImportError:  # pragma: no cover - fallback for flat layout
    from project_config import ProjectConfig  # type: ignore
    from render_worker import RenderWorker  # type: ignore


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def NumpyRgbaToQPixmap(rgba: np.ndarray) -> QPixmap:
    """Convert an RGBA uint8 NumPy array (H, W, 4) to a QPixmap."""

    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("rgba must be a uint8 array of shape (H, W, 4)")

    height, width, _ = rgba.shape

    # Create QImage from raw data; copy to detach from NumPy buffer
    image = QImage(
        rgba.data,
        width,
        height,
        rgba.strides[0],  # bytes per line
        QImage.Format_RGBA8888,
    ).copy()

    return QPixmap.fromImage(image)


def NumpyGrayToQPixmap(gray: np.ndarray) -> QPixmap:
    """Convert a grayscale uint8 NumPy array (H, W) to a QPixmap."""

    if gray.dtype != np.uint8 or gray.ndim != 2:
        raise ValueError("gray must be a uint8 array of shape (H, W)")

    height, width = gray.shape

    image = QImage(
        gray.data,
        width,
        height,
        gray.strides[0],
        QImage.Format_Grayscale8,
    ).copy()

    return QPixmap.fromImage(image)


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """Main application window for the Frost Dune Background Generator."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.SetWindowTitle("Frost Dune Background Generator")
        self._ThreadPool = QThreadPool.globalInstance()

        # Project configuration (will later be updated via the UI panels)
        self.ProjectConfig = ProjectConfig.CreateDefaultFrostProject()

        # Render worker management
        self._CurrentWorker: Optional[RenderWorker] = None
        self._LastElapsedSeconds: float = 0.0

        # Status bar timer (optional, in case we want smoother updates later)
        self._ProgressTimer = QTimer(self)
        self._ProgressTimer.setInterval(200)
        self._ProgressTimer.timeout.connect(self._OnProgressTimerTick)

        self._CreateActions()
        self._CreateStatusBar()
        self._CreateCentralWidgets()
        
    def OnGradientChanged(self, gradient: GradientConfig) -> None:
        self.ProjectConfig.Gradient = gradient
        pass
            
    def OnNoiseLayersChanged(self, layers: list[NoiseLayerConfig]) -> None:
        self.ProjectConfig.NoiseLayers = layers
        pass
    
    def OnLightingChanged(self, lighting: LightingConfig) -> None:
        self.ProjectConfig.Lighting = lighting
        pass
    
    def OnExportRequested(self, width: int, height: int) -> None:
        # Dateidialog
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PNG",
            "frost_dune_export.png",
            "PNG Images (*.png)",   
        )
        if not path:
            return

        try:
            img = RenderImageToPillow(self.ProjectConfig, width, height)
            img.save(path, format="PNG")
            self._SetStatusText(f"Exported {width} x {height} to {path}")
        except Exception as ex:
            QMessageBox.critical(self, "Export Error", str(ex))
            self._SetStatusText("Export failed")
    
    
    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def SetWindowTitle(self, title: str) -> None:
        """Helper to set the window title (C#-style naming wrapper)."""

        self.setWindowTitle(title)

    def _CreateActions(self) -> None:
        self._ActionExit = QAction("Exit", self)
        self._ActionExit.triggered.connect(self.close)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("File")
        fileMenu.addAction(self._ActionExit)

    def _CreateStatusBar(self) -> None:
        statusBar = QStatusBar(self)
        self._StatusLabel = QLabel("Ready", self)
        self._CancelButton = QPushButton("Cancel", self)
        self._CancelButton.setEnabled(False)
        self._CancelButton.clicked.connect(self.OnCancelRenderClicked)

        statusBar.addWidget(self._StatusLabel)
        statusBar.addPermanentWidget(self._CancelButton)

        self.setStatusBar(statusBar)

    def _CreateCentralWidgets(self) -> None:
        centralWidget = QWidget(self)
        mainLayout = QHBoxLayout(centralWidget)
        mainLayout.setContentsMargins(8, 8, 8, 8)
        mainLayout.setSpacing(8)

        # Sidebar on the left
        sidebarWidget = self._CreateSidebar()
        sidebarWidget.setFixedWidth(220)
        mainLayout.addWidget(sidebarWidget)

        # Preview area on the right
        previewWidget = self._CreatePreviewArea()
        mainLayout.addWidget(previewWidget, 1)

        self.setCentralWidget(centralWidget)

    def _CreateSidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._NavList = QListWidget(widget)
        for name in ("Global", "Noise", "Lighting", "Export"):
            self._NavList.addItem(QListWidgetItem(name))
        self._NavList.setCurrentRow(0)
        layout.addWidget(self._NavList)

        # Navigation
        self._NavList = QListWidget(widget)
        for name in ("Global", "Noise", "Lighting", "Export"):
            self._NavList.addItem(QListWidgetItem(name))
        self._NavList.setCurrentRow(0)
        layout.addWidget(self._NavList)

        # Gradient panel (könnte eher in „Global“ gehören)
        self._GradientPanel = GradientPanel(widget)
        self._GradientPanel.BindGradient(self.ProjectConfig.Gradient)
        self._GradientPanel.GradientChanged.connect(self.OnGradientChanged)
        layout.addWidget(self._GradientPanel, 1)

        # Noise panel
        self._NoisePanel = NoisePanel(widget)
        self._NoisePanel.BindNoiseLayers(self.ProjectConfig.NoiseLayers)
        self._NoisePanel.NoiseLayersChanged.connect(self.OnNoiseLayersChanged)
        layout.addWidget(self._NoisePanel, 1)

        # Lighting panel
        self._LightingPanel = LightingPanel(widget)
        self._LightingPanel.BindLighting(self.ProjectConfig.Lighting)
        self._LightingPanel.LightingChanged.connect(self.OnLightingChanged)
        layout.addWidget(self._LightingPanel)
        
        #Export panel
        self._ExportPanel = ExportPanel(widget)
        self._ExportPanel.ExportRequested.connect(self.OnExportRequested)
        layout.addWidget(self._ExportPanel)
        
        # Spacer + Generate button
        layout.addItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self._GenerateButton = QPushButton("Generate", widget)
        self._GenerateButton.clicked.connect(self.OnGenerateClicked)
        layout.addWidget(self._GenerateButton)

        return widget

    def _CreatePreviewArea(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Main (final) preview
        self._PreviewLabel = QLabel("Preview", widget)
        self._PreviewLabel.setAlignment(Qt.AlignCenter)
        self._PreviewLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._PreviewLabel.setMinimumSize(400, 225)  # approx 16:9
        self._PreviewLabel.setStyleSheet("background-color: #111111; border: 1px solid #333333;")

        layout.addWidget(self._PreviewLabel, 1)

        # Noise preview area with tabs
        self._NoiseTabs = QTabWidget(widget)

        self._NoiseBaseLabel = QLabel("Base Heightmap", self._NoiseTabs)
        self._NoiseDetailLabel = QLabel("Detail Heightmap", self._NoiseTabs)
        self._NoiseCombinedLabel = QLabel("Combined Heightmap", self._NoiseTabs)

        for lbl in (self._NoiseBaseLabel, self._NoiseDetailLabel, self._NoiseCombinedLabel):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background-color: #111111; border: 1px solid #333333;")
            lbl.setMinimumHeight(120)

        self._NoiseTabs.addTab(self._NoiseBaseLabel, "Base")
        self._NoiseTabs.addTab(self._NoiseDetailLabel, "Detail")
        self._NoiseTabs.addTab(self._NoiseCombinedLabel, "Combined")

        layout.addWidget(self._NoiseTabs, 0)

        return widget


    # ------------------------------------------------------------------
    # Render control
    # ------------------------------------------------------------------

    def OnGenerateClicked(self) -> None:
        """Start a new render job using the current ProjectConfig."""

        if self._CurrentWorker is not None:
            # Already rendering
            return

        self._SetStatusText("Rendering… 0.0s")
        self._GenerateButton.setEnabled(False)
        self._CancelButton.setEnabled(True)

        self._LastElapsedSeconds = 0.0
        self._ProgressTimer.start()

        worker = RenderWorker(self.ProjectConfig)
        self._CurrentWorker = worker

        worker.Signals.Started.connect(self.OnRenderStarted)
        worker.Signals.Progress.connect(self.OnRenderProgress)
        worker.Signals.Finished.connect(self.OnRenderFinished)
        worker.Signals.Canceled.connect(self.OnRenderCanceled)

        self._ThreadPool.start(worker)

    def OnCancelRenderClicked(self) -> None:
        if self._CurrentWorker is not None:
            self._CurrentWorker.RequestCancel()

    def OnRenderStarted(self) -> None:
        # Can be used to provide additional UI feedback if desired
        pass

    def OnRenderProgress(self, elapsedSeconds: float) -> None:
        self._LastElapsedSeconds = max(0.0, float(elapsedSeconds))
        self._UpdateStatusWithElapsedTime()

    def OnRenderFinished(self, finalImage: np.ndarray, noisePreviews: Dict[str, np.ndarray], totalTime: float) -> None:
        self._ProgressTimer.stop()

        # Display main preview
        try:
            pix = NumpyRgbaToQPixmap(finalImage)
            self._PreviewLabel.setPixmap(pix.scaled(
                self._PreviewLabel.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            ))
        except Exception:
            self._PreviewLabel.setText("Failed to display preview")

        # Display noise previews (if available)
        try:
            base = noisePreviews.get("base")
            detail = noisePreviews.get("detail")
            combined = noisePreviews.get("combined")

            if base is not None:
                self._NoiseBaseLabel.setPixmap(NumpyGrayToQPixmap(base).scaled(
                    self._NoiseBaseLabel.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                ))
            if detail is not None:
                self._NoiseDetailLabel.setPixmap(NumpyGrayToQPixmap(detail).scaled(
                    self._NoiseDetailLabel.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                ))
            if combined is not None:
                self._NoiseCombinedLabel.setPixmap(NumpyGrayToQPixmap(combined).scaled(
                    self._NoiseCombinedLabel.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                ))
        except Exception:
            # If anything goes wrong, silently ignore for now.
            pass

        self._SetStatusText(f"Finished in {totalTime:.2f}s")

        self._GenerateButton.setEnabled(True)
        self._CancelButton.setEnabled(False)
        self._CurrentWorker = None

    def OnRenderCanceled(self) -> None:
        self._ProgressTimer.stop()
        self._SetStatusText("Rendering canceled")

        self._GenerateButton.setEnabled(True)
        self._CancelButton.setEnabled(False)
        self._CurrentWorker = None

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _SetStatusText(self, text: str) -> None:
        self._StatusLabel.setText(text)

    def _UpdateStatusWithElapsedTime(self) -> None:
        self._SetStatusText(f"Rendering… {self._LastElapsedSeconds:.1f}s")

    def _OnProgressTimerTick(self) -> None:
        # Timer-based refresh in case we later want smoother animations or
        # interpolation; currently just re-applies the last known elapsed
        # time to the status label.
        if self._CurrentWorker is not None:
            self._UpdateStatusWithElapsedTime()
        else:
            self._ProgressTimer.stop()


# ---------------------------------------------------------------------------
# Application entry point (for manual testing)
# ---------------------------------------------------------------------------


def Main() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1280, 720)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    Main()
