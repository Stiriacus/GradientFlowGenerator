"""core/heightmap.py

Heightmap construction for the Frost Dune Background Generator.

This module combines the configured noise layers (BASE, DETAIL, WARP)
into a single heightmap suitable for lighting and shading.

Responsibilities:
- Build normalized coordinate grids.
- Combine all WARP layers into a domain-warping field.
- Evaluate BASE and DETAIL layers as ridge-style FBM on warped coords.
- Combine, normalize, and apply per-layer HeightPower.
- Provide optional per-category maps (Base/Detail/Combined) for previews.

Naming follows a C#-like style (PascalCase for classes and methods).
"""

from __future__ import annotations

from typing import Tuple, List

import numpy as np

try:
    # When used in a package layout
    from model.project_config import ProjectConfig
    from model.noise_layer import NoiseLayerConfig, NoiseLayerType
    from core.noise import GenerateFbmRidge, CombineWarpLayers
except ImportError:  # pragma: no cover - fallback for single-file prototyping
    # Assume the symbols are available in the global namespace when all
    # code is placed into a single file during early experimentation.
    from typing import Any  # type: ignore  # noqa

    pass


# ---------------------------------------------------------------------------
# Coordinate Grid Utilities
# ---------------------------------------------------------------------------


def BuildCoordinateGrid(width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    """Build normalized coordinate grids in [0, 1] for the given dimensions.

    The returned arrays have shape (height, width) and can be used as
    input to the noise functions. X increases left-to-right, Y increases
    top-to-bottom.
    """

    # Note: use float32 to keep memory and performance reasonable.
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)

    baseX, baseY = np.meshgrid(xs, ys)
    return baseX, baseY


# ---------------------------------------------------------------------------
# Heightmap Construction
# ---------------------------------------------------------------------------


def _SplitNoiseLayers(
    layers: List["NoiseLayerConfig"],
) -> Tuple[List["NoiseLayerConfig"], List["NoiseLayerConfig"]]:
    """Split a list of layers into (warpLayers, nonWarpLayers)."""

    warpLayers: List[NoiseLayerConfig] = []
    nonWarpLayers: List[NoiseLayerConfig] = []

    for layer in layers:
        if layer.LayerType is NoiseLayerType.Warp:
            warpLayers.append(layer)
        else:
            nonWarpLayers.append(layer)

    return warpLayers, nonWarpLayers


def _BuildWarpField(
    warpLayers: List["NoiseLayerConfig"],
    baseX: np.ndarray,
    baseY: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Build a combined warp field from all WARP layers.

    Returns wxTotal, wyTotal which are offsets to be added to baseX/baseY.
    If there are no active warp layers, the offsets will be zeros.
    """

    if not warpLayers:
        zerosX = np.zeros_like(baseX, dtype=np.float32)
        zerosY = np.zeros_like(baseY, dtype=np.float32)
        return zerosX, zerosY

    wxTotal, wyTotal = CombineWarpLayers(warpLayers, baseX, baseY)
    return wxTotal, wyTotal


def _EvaluateNonWarpLayers(
    layers: List["NoiseLayerConfig"],
    warpedX: np.ndarray,
    warpedY: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate all BASE/DETAIL layers on the warped coordinates.

    Returns three heightmaps:
    - baseMap: sum of all BASE layers (before normalization),
    - detailMap: sum of all DETAIL layers (before normalization),
    - combinedMap: sum of both (before normalization).

    Layer-specific HeightPower and Amplitude are applied.
    """

    baseMap = np.zeros_like(warpedX, dtype=np.float32)
    detailMap = np.zeros_like(warpedX, dtype=np.float32)

    for layer in layers:
        if not layer.Enabled:
            continue

        if layer.LayerType not in (NoiseLayerType.Base, NoiseLayerType.Detail):
            continue

        layerHeight = GenerateFbmRidge(layer, warpedX, warpedY)

        # Apply per-layer height shaping
        heightPower = float(layer.HeightPower)
        if heightPower != 1.0:
            layerHeight = np.power(layerHeight, heightPower, dtype=np.float32)

        # Apply layer amplitude
        layerHeight *= float(layer.Amplitude)

        if layer.LayerType is NoiseLayerType.Base:
            baseMap += layerHeight
        elif layer.LayerType is NoiseLayerType.Detail:
            detailMap += layerHeight

    combinedMap = baseMap + detailMap
    return baseMap, detailMap, combinedMap


def _NormalizeHeightmap(heightmap: np.ndarray) -> np.ndarray:
    """Normalize a heightmap to the [0, 1] range.

    If the map is constant, returns zeros.
    """

    minVal = float(heightmap.min())
    maxVal = float(heightmap.max())

    if maxVal <= minVal + 1e-8:
        return np.zeros_like(heightmap, dtype=np.float32)

    normalized = (heightmap - minVal) / (maxVal - minVal)
    return normalized.astype(np.float32)


def BuildHeightmap(
    projectConfig: "ProjectConfig",
    width: int,
    height: int,
) -> np.ndarray:
    """Build the final normalized heightmap for the given project config.

    This function is optimized for use in the main render pipeline.
    It does not return per-layer maps; use BuildHeightmapWithLayerMaps
    if you need those for previews.

    Steps:
    - Build coordinate grid in [0, 1].
    - Combine all WARP layers -> warp field.
    - Distort coordinates.
    - Evaluate BASE + DETAIL layers.
    - Normalize combined heightmap to [0, 1].
    """

    baseX, baseY = BuildCoordinateGrid(width, height)

    warpLayers, nonWarpLayers = _SplitNoiseLayers(projectConfig.NoiseLayers)

    wxTotal, wyTotal = _BuildWarpField(warpLayers, baseX, baseY)

    warpedX = baseX + wxTotal
    warpedY = baseY + wyTotal

    _, _, combinedMap = _EvaluateNonWarpLayers(nonWarpLayers, warpedX, warpedY)

    normalized = _NormalizeHeightmap(combinedMap)
    return normalized


def BuildHeightmapWithLayerMaps(
    projectConfig: "ProjectConfig",
    width: int,
    height: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build the final heightmap plus Base/Detail/Combined maps.

    Returns
    -------
    finalHeight : np.ndarray
        Normalized combined heightmap in [0, 1].
    baseMapNorm : np.ndarray
        Normalized sum of BASE layers in [0, 1].
    detailMapNorm : np.ndarray
        Normalized sum of DETAIL layers in [0, 1].
    combinedMapNorm : np.ndarray
        Normalized sum of BASE + DETAIL before final normalization
        (usually this is the same as finalHeight, but kept separate
        for clarity in previews).
    """

    baseX, baseY = BuildCoordinateGrid(width, height)
    warpLayers, nonWarpLayers = _SplitNoiseLayers(projectConfig.NoiseLayers)

    wxTotal, wyTotal = _BuildWarpField(warpLayers, baseX, baseY)

    warpedX = baseX + wxTotal
    warpedY = baseY + wyTotal

    baseMap, detailMap, combinedMap = _EvaluateNonWarpLayers(
        nonWarpLayers, warpedX, warpedY
    )

    baseMapNorm = _NormalizeHeightmap(baseMap)
    detailMapNorm = _NormalizeHeightmap(detailMap)
    combinedMapNorm = _NormalizeHeightmap(combinedMap)

    # For now, the final heightmap is simply the normalized combined map.
    # If you later want an additional global shaping (e.g. HeightPower),
    # you can add it here.
    finalHeight = combinedMapNorm.copy()

    return finalHeight, baseMapNorm, detailMapNorm, combinedMapNorm