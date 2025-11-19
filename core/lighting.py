"""core/lighting.py

Lighting and normal calculation for the Frost Dune Background Generator.

This module provides utilities to:
- Compute surface normals from a heightmap via finite differences.
- Build a directional light vector from azimuth/elevation angles.
- Compute a shade/brightness map from normals and the light vector.

Conventions
----------
- Naming uses C#-style (PascalCase for classes and methods).
- Heightmaps are NumPy float32 arrays in [0, 1].
- Coordinates: X increases left-to-right, Y increases top-to-bottom.
"""

from __future__ import annotations

from typing import Tuple

import math
import numpy as np

try:
    # Project layout import
    from model.lighting_config import LightingConfig
except ImportError:  # pragma: no cover - fallback when everything is flat
    from lighting_config import LightingConfig  # type: ignore


# ---------------------------------------------------------------------------
# Normal Calculation
# ---------------------------------------------------------------------------


def ComputeNormals(height: np.ndarray, scaleZ: float = 1.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute surface normals from a heightmap using finite differences.

    Parameters
    ----------
    height : np.ndarray
        2D float32 heightmap in [0, 1].
    scaleZ : float
        Scaling factor for the Z component. Larger values make the
        surface appear steeper, which increases shading contrast.

    Returns
    -------
    (nx, ny, nz) : Tuple[np.ndarray, np.ndarray, np.ndarray]
        Normal components as float32 arrays in [-1, 1].
    """

    if height.ndim != 2:
        raise ValueError("height must be a 2D array")

    # Pad the heightmap at the border to avoid dealing with edges separately
    pad = np.pad(height, 1, mode="edge")

    # Central differences in X and Y (note that Y is rows, X is columns)
    dx = pad[1:-1, 2:] - pad[1:-1, :-2]
    dy = pad[2:, 1:-1] - pad[:-2, 1:-1]

    nx = -dx
    ny = -dy
    nz = np.ones_like(height, dtype=np.float32) * float(scaleZ)

    # Normalize the normal vectors
    length = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
    nx = nx / length
    ny = ny / length
    nz = nz / length

    return nx.astype(np.float32), ny.astype(np.float32), nz.astype(np.float32)


# ---------------------------------------------------------------------------
# Light Vector Utilities
# ---------------------------------------------------------------------------


def BuildLightVector(config: "LightingConfig") -> Tuple[float, float, float]:
    """Build a directional light vector from azimuth and elevation.

    Angle conventions (must match the rest of the renderer):
    - Azimuth 0°  : light comes from the right (+X).
    - Azimuth 90° : light comes from the top (-Y in screen space), but we
      treat the up-direction consistently via sin/cos mapping.
    - Elevation 0°: light is in the plane.
    - Elevation 90°: light is straight from above (+Z).

    The vector is normalized to length 1.
    """

    az = math.radians(float(config.LightAzimuthDeg))
    el = math.radians(float(config.LightElevationDeg))

    # Standard spherical coordinates mapping:
    # x = cos(el) * cos(az)
    # y = cos(el) * sin(az)
    # z = sin(el)
    lx = math.cos(el) * math.cos(az)
    ly = math.cos(el) * math.sin(az)
    lz = math.sin(el)

    # Normalize for safety (should already be unit length)
    length = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0

    return (lx / length, ly / length, lz / length)


# ---------------------------------------------------------------------------
# Shading
# ---------------------------------------------------------------------------


def ComputeShade(
    nx: np.ndarray,
    ny: np.ndarray,
    nz: np.ndarray,
    lightVector: Tuple[float, float, float],
    intensity: float = 1.0,
    minBrightness: float = 0.0,
    maxBrightness: float = 1.0,
) -> np.ndarray:
    """Compute a shade/brightness map from normals and a light vector.

    Parameters
    ----------
    nx, ny, nz : np.ndarray
        Normal components in [-1, 1]. All must have the same shape.
    lightVector : (lx, ly, lz)
        Normalized light direction.
    intensity : float
        Global intensity multiplier (0–1 range typically).
    minBrightness : float
        Minimum brightness level after mapping (e.g. 0.3).
    maxBrightness : float
        Maximum brightness level after mapping (e.g. 1.0).

    Returns
    -------
    shade : np.ndarray
        Float32 array in [minBrightness, maxBrightness], representing
        per-pixel brightness factor.
    """

    if nx.shape != ny.shape or nx.shape != nz.shape:
        raise ValueError("nx, ny, nz must have the same shape")

    lx, ly, lz = lightVector

    # Dot product between normal and light direction
    dot = nx * lx + ny * ly + nz * lz

    # Keep only the lit side; clamp to [0, 1]
    shade = np.clip(dot, 0.0, 1.0)

    # Apply global intensity
    intensity = float(intensity)
    if intensity < 0.0:
        intensity = 0.0
    if intensity > 1.0:
        intensity = 1.0

    shade *= intensity

    # Map to [minBrightness, maxBrightness]
    minB = float(minBrightness)
    maxB = float(maxBrightness)

    if maxB < minB:
        maxB, minB = minB, maxB

    shade = minB + (maxB - minB) * shade

    return shade.astype(np.float32)


def ComputeShadeFromHeightmap(
    height: np.ndarray,
    lightingConfig: "LightingConfig",
    scaleZ: float = 1.0,
    minBrightness: float = 0.35,
    maxBrightness: float = 1.0,
) -> np.ndarray:
    """Convenience function: normals + light vector + shade in one call.

    This is the typical entry point used by the renderer:
    - Compute normals from the heightmap.
    - Build the light vector from LightingConfig.
    - Compute the shade/brightness map.

    Returns a float32 array in [minBrightness, maxBrightness].
    """

    nx, ny, nz = ComputeNormals(height, scaleZ=scaleZ)
    lightVector = BuildLightVector(lightingConfig)

    shade = ComputeShade(
        nx,
        ny,
        nz,
        lightVector,
        intensity=lightingConfig.Intensity,
        minBrightness=minBrightness,
        maxBrightness=maxBrightness,
    )

    return shade