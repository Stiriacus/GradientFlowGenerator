"""core/renderer.py

Main rendering orchestration for the Frost Dune Background Generator.

This module ties together:
- Heightmap generation (core.heightmap)
- Lighting & shading (core.lighting)
- Gradient mapping (core.gradient)

The primary entry point is RenderImage, which takes a ProjectConfig and
produces a Pillow Image (RGBA) or raw NumPy arrays.

Conventions
----------
- Naming uses C#-style (PascalCase for classes and methods where possible).
- Heightmaps and intermediate maps are float32 arrays in [0, 1].
- Final output is uint8 in [0, 255].
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from PIL import Image

try:
    # Project layout imports
    from model.project_config import ProjectConfig
    from core.heightmap import BuildHeightmapWithLayerMaps
    from core.lighting import ComputeShadeFromHeightmap
    from core.gradient import (
        ComputeGradientTFromAngle,
        EvaluateGradientAt,
        RgbFloatToUint8,
    )
except ImportError:  # pragma: no cover - fallback for flat layout / prototyping
    from project_config import ProjectConfig  # type: ignore
    from heightmap import BuildHeightmapWithLayerMaps  # type: ignore
    from lighting import ComputeShadeFromHeightmap  # type: ignore
    from gradient import ComputeGradientTFromAngle, EvaluateGradientAt, RgbFloatToUint8  # type: ignore


# ---------------------------------------------------------------------------
# Core render helpers
# ---------------------------------------------------------------------------


def ComposeColor(
    baseR: np.ndarray,
    baseG: np.ndarray,
    baseB: np.ndarray,
    shade: np.ndarray,
    height: np.ndarray,
    heightInfluence: float = 0.2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Combine base gradient color, shade, and height into final RGB.

    Parameters
    ----------
    baseR, baseG, baseB : np.ndarray
        Base gradient color channels in [0, 1].
    shade : np.ndarray
        Brightness factor in [0, 1] (or narrower range like 0.35–1.0).
    height : np.ndarray
        Heightmap in [0, 1].
    heightInfluence : float
        Blending factor for height-based brightness modulation.
        0 = ignore height, 1 = full height influence.

    Returns
    -------
    (r, g, b) : Tuple[np.ndarray, np.ndarray, np.ndarray]
        Final color channels in [0, 1].
    """

    if baseR.shape != shade.shape or baseR.shape != height.shape:
        raise ValueError("baseR, shade, and height must have the same shape")

    # Optional: height-based modulation: Kämme etwas heller, Täler dunkler
    influence = float(heightInfluence)
    if influence < 0.0:
        influence = 0.0
    if influence > 1.0:
        influence = 1.0

    # Map height to a factor around 1.0, e.g. 0.8–1.2
    heightFactor = 1.0 - 0.2 * (1.0 - height)  # slightly darken low areas
    # Blend between no height influence (1.0) and full heightFactor
    combinedFactor = (1.0 - influence) * 1.0 + influence * heightFactor

    brightness = shade * combinedFactor

    r = baseR * brightness
    g = baseG * brightness
    b = baseB * brightness

    return r.astype(np.float32), g.astype(np.float32), b.astype(np.float32)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def RenderImageToArrays(
    projectConfig: "ProjectConfig",
    width: int,
    height: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Render the scene to NumPy arrays (R, G, B, A) in uint8.

    This is the low-level entry point; the GUI or export code can use
    this directly or via RenderImageToPillow.

    Steps:
    - Build heightmap (with layer maps if needed).
    - Compute shade from heightmap and lighting config.
    - Compute gradient t-field from angle, then evaluate gradient colors.
    - Combine base colors and shade (+ height influence).
    - Convert to uint8.

    Returns
    -------
    (r8, g8, b8, a8): Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        Each channel is a 2D uint8 array with shape (height, width).
    """

    # Heightmap and layer maps (we only need finalHeight here, but the
    # others may be useful for diagnostic previews in the UI)
    finalHeight, _, _, _ = BuildHeightmapWithLayerMaps(
        projectConfig,
        width,
        height,
    )

    # Shade / brightness map from lighting
    shade = ComputeShadeFromHeightmap(
        finalHeight,
        projectConfig.Lighting,
        scaleZ=1.0,
        minBrightness=0.35,
        maxBrightness=1.0,
    )

    # Gradient parameter and base color
    t = ComputeGradientTFromAngle(width, height, projectConfig.Gradient.AngleDeg)
    baseR, baseG, baseB, alpha = EvaluateGradientAt(projectConfig.Gradient, t)

    # Combine base color with shade and height-based modulation
    r, g, b = ComposeColor(
        baseR,
        baseG,
        baseB,
        shade,
        finalHeight,
        heightInfluence=0.25,
    )

    r8, g8, b8 = RgbFloatToUint8(r, g, b)

    # Alpha: we currently use the gradient alpha (stops' opacity) mapped
    # to [0, 255]. If you prefer fully opaque output, replace this with
    # a constant 255.
    a8 = (np.clip(alpha, 0.0, 1.0) * 255.0).astype(np.uint8)

    return r8, g8, b8, a8


def RenderImageToPillow(
    projectConfig: "ProjectConfig",
    width: int,
    height: int,
) -> Image.Image:
    """Render the scene and return a Pillow RGBA Image."""

    r8, g8, b8, a8 = RenderImageToArrays(projectConfig, width, height)

    # Stack into an RGBA image buffer
    rgba = np.dstack([r8, g8, b8, a8])
    img = Image.fromarray(rgba, mode="RGBA")
    return img