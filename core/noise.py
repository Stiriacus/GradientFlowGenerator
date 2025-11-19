"""core/noise.py

Noise utilities for the Frost Dune Background Generator.

This module provides:
- SimplexNoiseSource: wrapper around opensimplex.OpenSimplex.
- GenerateFbmRidge: ridge-style FBM for BASE/DETAIL noise layers.
- GenerateWarpOffsets: domain-warp offsets for WARP layers.
- CombineWarpLayers: merges multiple warp layers into a single field.

Conventions
----------
- Naming follows a C#-like style (PascalCase for classes, methods,
  and properties).
- Coordinates are assumed to be normalized in [0, 1]. ScaleX/ScaleY
  from NoiseLayerConfig act as frequency multipliers.
"""

from __future__ import annotations

from typing import Tuple, Sequence, List

import numpy as np
from opensimplex import OpenSimplex

# Assuming a package structure like:
# from model.noise_layer import NoiseLayerConfig, NoiseLayerType
# If you put this file flat next to the models, adjust the import accordingly.
try:
    from model.noise_layer import NoiseLayerConfig, NoiseLayerType
except ImportError:  # pragma: no cover - fallback when used in a flat layout
    # If everything is in a single directory without packages, try a plain import
    from noise_layer import NoiseLayerConfig, NoiseLayerType  # type: ignore


class SimplexNoiseSource:
    """Wrapper around OpenSimplex to provide seeded 2D simplex noise.

    The Sample2D method expects NumPy arrays for x and y and returns a
    float32 array of the same shape with values in approximately [-1, 1].
    """

    def __init__(self, seed: int) -> None:
        self.Seed = int(seed)
        self._Noise = OpenSimplex(seed=self.Seed)

        # Vectorized callable for noise2 (x, y) -> value
        self._Noise2DVectorized = np.vectorize(self._Noise.noise2)

    def Sample2D(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Sample 2D simplex noise for the given coordinate arrays.

        Parameters
        ----------
        x, y : np.ndarray
            Arrays (same shape) with coordinates where noise should be
            sampled.

        Returns
        -------
        np.ndarray
            Float32 array in approximately [-1, 1].
        """

        values = self._Noise2DVectorized(x, y)
        return np.asarray(values, dtype=np.float32)


def GenerateFbmRidge(
    layerConfig: "NoiseLayerConfig",
    baseX: np.ndarray,
    baseY: np.ndarray,
) -> np.ndarray:
    """Generate a ridge-style FBM noise field for a BASE/DETAIL layer.

    Algorithm (per the project spec):
    - Use simplex noise with the given seed.
    - For each octave:
      - Sample simplex noise at the current frequency.
      - Apply ridge transform: n -> 1 - |n|, then raise to RidgePower.
      - Accumulate with amplitude and Persistence.
    - Normalize by total amplitude sum.

    The result is clipped into [0, 1].

    Parameters
    ----------
    layerConfig : NoiseLayerConfig
        Configuration describing scale, octaves, persistence, etc.
    baseX, baseY : np.ndarray
        Normalized coordinate grids in [0, 1]. Must have the same shape.

    Returns
    -------
    np.ndarray
        Float32 heightmap in [0, 1] (approximately).
    """

    from model.noise_layer import NoiseLayerType as _NLT  # local alias for clarity

    if layerConfig.LayerType not in (_NLT.Base, _NLT.Detail):
        raise ValueError("GenerateFbmRidge is intended for BASE or DETAIL layers only.")

    if not layerConfig.Enabled:
        return np.zeros_like(baseX, dtype=np.float32)

    noiseSource = SimplexNoiseSource(layerConfig.Seed)

    frequencyX = float(layerConfig.ScaleX)
    frequencyY = float(layerConfig.ScaleY)
    amplitude = 1.0

    total = np.zeros_like(baseX, dtype=np.float32)
    amplitudeSum = 0.0

    octaves = max(1, int(layerConfig.Octaves))
    persistence = float(layerConfig.Persistence)
    lacunarity = float(layerConfig.Lacunarity)
    ridgePower = float(layerConfig.RidgePower)

    for _ in range(octaves):
        # Scale coordinates for this octave
        x = baseX * frequencyX
        y = baseY * frequencyY

        n = noiseSource.Sample2D(x, y)  # [-1, 1]

        # Ridge transform: values in [0, 1]
        n = 1.0 - np.abs(n)
        n = np.clip(n, 0.0, 1.0)

        if ridgePower != 1.0:
            n = np.power(n, ridgePower, dtype=np.float32)

        total += n.astype(np.float32) * amplitude
        amplitudeSum += amplitude

        amplitude *= persistence
        frequencyX *= lacunarity
        frequencyY *= lacunarity

    if amplitudeSum > 0.0:
        total /= amplitudeSum

    # Ensure the output is within [0, 1]
    np.clip(total, 0.0, 1.0, out=total)
    return total


def GenerateWarpOffsets(
    layerConfig: "NoiseLayerConfig",
    baseX: np.ndarray,
    baseY: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate domain-warping offsets (wx, wy) for a WARP layer.

    We use FBM (without ridge) to compute two noise fields for x- and
    y-offsets, then normalize by the amplitude sum and finally apply the
    configured Amplitude from the NoiseLayerConfig.

    Conceptually:
        wx, wy ~ FBM(simplex(baseX, baseY)) in [-1, 1]
        wx *= Amplitude
        wy *= Amplitude

    Parameters
    ----------
    layerConfig : NoiseLayerConfig
        Must have LayerType == Warp.
    baseX, baseY : np.ndarray
        Normalized coordinate grids in [0, 1].

    Returns
    -------
    (wx, wy) : Tuple[np.ndarray, np.ndarray]
        Float32 arrays with the same shape as baseX/baseY containing the
        coordinate offsets to add to (x, y).
    """

    from model.noise_layer import NoiseLayerType as _NLT  # local alias

    if layerConfig.LayerType is not _NLT.Warp:
        raise ValueError("GenerateWarpOffsets is intended for WARP layers only.")

    if not layerConfig.Enabled:
        zeros = np.zeros_like(baseX, dtype=np.float32)
        return zeros, zeros

    noiseSource = SimplexNoiseSource(layerConfig.Seed)

    frequencyX = float(layerConfig.ScaleX)
    frequencyY = float(layerConfig.ScaleY)
    amplitude = 1.0

    wx = np.zeros_like(baseX, dtype=np.float32)
    wy = np.zeros_like(baseY, dtype=np.float32)
    amplitudeSum = 0.0

    octaves = max(1, int(layerConfig.Octaves))
    persistence = float(layerConfig.Persistence)
    lacunarity = float(layerConfig.Lacunarity)

    for _ in range(octaves):
        x = baseX * frequencyX
        y = baseY * frequencyY

        # Two different noise samples for x and y offsets (shifted coords)
        wx_oct = noiseSource.Sample2D(x, y)
        wy_oct = noiseSource.Sample2D(x + 1000.0, y + 1000.0)

        wx += wx_oct.astype(np.float32) * amplitude
        wy += wy_oct.astype(np.float32) * amplitude
        amplitudeSum += amplitude

        amplitude *= persistence
        frequencyX *= lacunarity
        frequencyY *= lacunarity

    if amplitudeSum > 0.0:
        wx /= amplitudeSum
        wy /= amplitudeSum

    warpAmplitude = float(layerConfig.Amplitude)
    wx *= warpAmplitude
    wy *= warpAmplitude

    return wx, wy


def CombineWarpLayers(
    warpLayers: Sequence["NoiseLayerConfig"],
    baseX: np.ndarray,
    baseY: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Combine multiple WARP layers into a single warp field.

    Each enabled layer contributes its own warp offsets which are added
    together. This allows complex multi-scale domain warping.

    Parameters
    ----------
    warpLayers : sequence of NoiseLayerConfig
        Only layers with LayerType == Warp and Enabled == True are used.
    baseX, baseY : np.ndarray
        Normalized coordinate grids in [0, 1].

    Returns
    -------
    (wx, wy) : Tuple[np.ndarray, np.ndarray]
        The combined warp offsets.
    """

    from model.noise_layer import NoiseLayerType as _NLT  # local alias

    wxTotal = np.zeros_like(baseX, dtype=np.float32)
    wyTotal = np.zeros_like(baseY, dtype=np.float32)

    for layer in warpLayers:
        if not layer.Enabled or layer.LayerType is not _NLT.Warp:
            continue

        wx, wy = GenerateWarpOffsets(layer, baseX, baseY)
        wxTotal += wx
        wyTotal += wy

    return wxTotal, wyTotal