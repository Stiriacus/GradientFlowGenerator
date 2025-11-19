
"""workers/render_worker.py

Background render worker for the Frost Dune Background Generator.

This module provides a QRunnable-based worker that can be used with a
QThreadPool to render previews and noise previews in the background.

Features
--------
- Emits signals for started, progress (elapsed time), finished, canceled.
- Renders the main preview image using core.renderer.
- Optionally renders noise preview maps (base/detail/combined heightmaps).

Conventions
----------
- Naming uses a C#-like style (PascalCase for classes, properties, and
  public methods where possible) while still complying with Qt's
  expectations (e.g. `run()` method for QRunnable).
"""

from __future__ import annotations

from dataclasses import replace
from time import perf_counter
from typing import Dict, Optional, Tuple

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal

try:
    # Project layout imports
    from model.project_config import ProjectConfig
    from core.renderer import RenderImageToArrays
    from core.heightmap import BuildHeightmapWithLayerMaps
except ImportError:  # pragma: no cover - fallback for flat layout / prototyping
    from project_config import ProjectConfig  # type: ignore
    from renderer import RenderImageToArrays  # type: ignore
    from heightmap import BuildHeightmapWithLayerMaps  # type: ignore


class RenderWorkerSignals(QObject):
    """Signals used by RenderWorker.

    All signals are defined with generic `object` payloads where needed
    to keep the interface flexible for the GUI layer.
    """

    Started = Signal()
    Progress = Signal(float)  # elapsed seconds
    Finished = Signal(object, object, float)  # finalImage, noisePreviews, totalTime
    Canceled = Signal()


class RenderWorker(QRunnable):
    """Background worker that renders a Frost Dune scene.

    Usage (from the GUI layer):

        worker = RenderWorker(projectConfig)
        worker.Signals.Started.connect(...)
        worker.Signals.Progress.connect(...)
        worker.Signals.Finished.connect(...)
        worker.Signals.Canceled.connect(...)
        QThreadPool.globalInstance().start(worker)

    A shallow copy of ProjectConfig is stored to reduce the risk of
    concurrent modification issues, but the GUI should still avoid
    mutating the config while a render job is running.
    """

    def __init__(
        self,
        projectConfig: "ProjectConfig",
        previewWidth: Optional[int] = None,
        previewHeight: Optional[int] = None,
        generateNoisePreviews: bool = True,
    ) -> None:
        super().__init__()

        # Make a shallow copy of the config to decouple from the GUI's
        # current instance. This avoids obvious race conditions if the
        # user tweaks parameters during rendering.
        self._ProjectConfig = replace(projectConfig)

        self._PreviewWidth = int(previewWidth or projectConfig.PreviewWidth)
        self._PreviewHeight = int(previewHeight or projectConfig.PreviewHeight)

        self._GenerateNoisePreviews = bool(generateNoisePreviews)

        self._IsCanceled = False

        self.Signals = RenderWorkerSignals()

    # ------------------------------------------------------------------
    # Public API (from GUI)
    # ------------------------------------------------------------------

    def RequestCancel(self) -> None:
        """Ask the worker to cancel as soon as possible."""

        self._IsCanceled = True

    @property
    def IsCanceled(self) -> bool:
        return self._IsCanceled

    # ------------------------------------------------------------------
    # QRunnable entry point
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: N802  # Qt expects this exact name
        """Execute the render job.

        This method is called by QThreadPool. Do not call it directly;
        instead, create an instance of RenderWorker and hand it to the
        thread pool.
        """

        startTime = perf_counter()
        self.Signals.Started.emit()

        # Early cancellation check
        if self._IsCanceled:
            self.Signals.Canceled.emit()
            return

        # ------------------------------------------------------------------
        # 1. Render main preview image
        # ------------------------------------------------------------------
        try:
            r8, g8, b8, a8 = RenderImageToArrays(
                self._ProjectConfig,
                self._PreviewWidth,
                self._PreviewHeight,
            )
        except Exception:
            # On any rendering error, treat as canceled for now. The GUI
            # can differentiate later if more sophisticated error
            # handling is desired.
            self.Signals.Canceled.emit()
            return

        if self._IsCanceled:
            self.Signals.Canceled.emit()
            return

        elapsed = perf_counter() - startTime
        self.Signals.Progress.emit(float(elapsed))

        # Pack RGBA into a single array for easier handling on the GUI side
        finalImage = np.dstack([r8, g8, b8, a8])

        # ------------------------------------------------------------------
        # 2. Optional noise previews (base/detail/combined heightmaps)
        # ------------------------------------------------------------------
        noisePreviews: Dict[str, np.ndarray]
        noisePreviews = {}

        if self._GenerateNoisePreviews and not self._IsCanceled:
            try:
                noiseWidth = int(self._ProjectConfig.NoisePreviewWidth)
                noiseHeight = int(self._ProjectConfig.NoisePreviewHeight)

                _, baseMap, detailMap, combinedMap = BuildHeightmapWithLayerMaps(
                    self._ProjectConfig,
                    noiseWidth,
                    noiseHeight,
                )

                # Convert normalized [0, 1] maps to uint8 grayscale
                def ToGray(img: np.ndarray) -> np.ndarray:
                    return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)

                noisePreviews = {
                    "base": ToGray(baseMap),
                    "detail": ToGray(detailMap),
                    "combined": ToGray(combinedMap),
                }
            except Exception:
                # If noise preview rendering fails, still return the
                # main image; just report an empty dict.
                noisePreviews = {}

            elapsed = perf_counter() - startTime
            self.Signals.Progress.emit(float(elapsed))

        if self._IsCanceled:
            self.Signals.Canceled.emit()
            return

        totalTime = perf_counter() - startTime

        # Emit finished with the final image, noise previews, and total time
        self.Signals.Finished.emit(finalImage, noisePreviews, float(totalTime))
