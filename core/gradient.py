"""core/gradient.py

Gradient utilities for the Frost Dune Background Generator.

This module provides functions to:
- Convert hex colors to / from float RGB triples.
- Evaluate a GradientConfig (with up to 6 GradientStops).
- Compute a per-pixel gradient parameter `t` in [0, 1] based on an angle.
- Map a `t`-field to an RGB image using the gradient.

Conventions
----------
- Naming uses C#-style (PascalCase for classes and methods where relevant).
- All color computations are done in linear float space [0, 1].
- Angles: 0° = left->right, 90° = bottom->top (screen space Y grows down).
"""

from __future__ import annotations

from typing import Tuple

import math
import numpy as np

try:
    # Project layout imports
    from model.gradient_model import GradientConfig, GradientStop
except ImportError:  # pragma: no cover - fallback for flat layout
    from gradient_model import GradientConfig, GradientStop  # type: ignore


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def HexToRgbFloat(hexColor: str) -> Tuple[float, float, float]:
    """Convert a hex color string (#rrggbb) to an RGB triple in [0, 1]."""

    hexColor = hexColor.strip()
    if hexColor.startswith("#"):
        hexColor = hexColor[1:]

    if len(hexColor) != 6:
        raise ValueError(f"Invalid hex color: {hexColor!r}")

    r = int(hexColor[0:2], 16) / 255.0
    g = int(hexColor[2:4], 16) / 255.0
    b = int(hexColor[4:6], 16) / 255.0

    return float(r), float(g), float(b)


def RgbFloatToUint8(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert float RGB arrays in [0, 1] to uint8 [0, 255]."""

    r8 = np.clip(r, 0.0, 1.0) * 255.0
    g8 = np.clip(g, 0.0, 1.0) * 255.0
    b8 = np.clip(b, 0.0, 1.0) * 255.0

    return r8.astype(np.uint8), g8.astype(np.uint8), b8.astype(np.uint8)


# ---------------------------------------------------------------------------
# Gradient evaluation
# ---------------------------------------------------------------------------


def _SortStops(gradient: "GradientConfig") -> Tuple["GradientStop", ...]:
    """Return the gradient's stops sorted by Position."""

    stops = list(gradient.Stops)
    stops.sort(key=lambda s: s.Position)
    return tuple(stops)


def EvaluateGradientAt(
    gradient: "GradientConfig",
    t: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate the gradient at each position in t.

    Parameters
    ----------
    gradient : GradientConfig
        Gradient configuration with up to 6 GradientStops.
    t : np.ndarray
        Float32 array in [0, 1] specifying the gradient coordinate per pixel.

    Returns
    -------
    (r, g, b, a) : Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        Float32 arrays in [0, 1], each the same shape as t.
    """

    if t.ndim != 2:
        raise ValueError("t must be a 2D array")

    stops = _SortStops(gradient)
    if not stops:
        # Fallback: solid black
        shape = t.shape
        zeros = np.zeros(shape, dtype=np.float32)
        return zeros, zeros, zeros, zeros

    # Pre-compute arrays of stop positions and colors
    positions = np.array([s.Position for s in stops], dtype=np.float32)
    colors = np.array([HexToRgbFloat(s.Color) for s in stops], dtype=np.float32)  # (N, 3)
    opacities = np.array([s.Opacity for s in stops], dtype=np.float32)  # (N,)

    # Clamp t to [0, 1]
    tClamped = np.clip(t, 0.0, 1.0)

    # For each t, we find the surrounding stops: left index i, right index i+1
    # np.searchsorted gives us the insertion index for each t
    indices = np.searchsorted(positions, tClamped, side="right")

    # Left indices are one step to the left (but at least 0)
    leftIndices = np.clip(indices - 1, 0, len(positions) - 1)
    rightIndices = np.clip(indices, 0, len(positions) - 1)

    leftPos = positions[leftIndices]
    rightPos = positions[rightIndices]

    # Avoid division by zero: where leftPos == rightPos, set factor to 0
    denom = rightPos - leftPos
    denom[denom == 0.0] = 1.0

    factor = (tClamped - leftPos) / denom

    leftColors = colors[leftIndices]        # shape: (*t.shape, 3)
    rightColors = colors[rightIndices]

    leftAlpha = opacities[leftIndices]
    rightAlpha = opacities[rightIndices]

    # Interpolate RGB and alpha
    r = (1.0 - factor) * leftColors[..., 0] + factor * rightColors[..., 0]
    g = (1.0 - factor) * leftColors[..., 1] + factor * rightColors[..., 1]
    b = (1.0 - factor) * leftColors[..., 2] + factor * rightColors[..., 2]

    a = (1.0 - factor) * leftAlpha + factor * rightAlpha

    return r.astype(np.float32), g.astype(np.float32), b.astype(np.float32), a.astype(np.float32)


# ---------------------------------------------------------------------------
# Gradient coordinate (t) from angle
# ---------------------------------------------------------------------------


def ComputeGradientTFromAngle(
    width: int,
    height: int,
    angleDeg: float,
) -> np.ndarray:
    """Compute a 2D field `t` in [0, 1] along a gradient axis.

    Angle convention:
    - 0°  = left -> right
    - 90° = bottom -> top

    Implementation details:
    - We create normalized coordinates (xNorm, yNorm) in [0, 1].
    - We shift them so the center is (0, 0).
    - We project the coordinates onto a unit direction vector derived
      from angleDeg.
    - The result is remapped to [0, 1].
    """

    # Normalized coordinate grid in [0, 1]
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)
    xNorm, yNorm = np.meshgrid(xs, ys)

    # Center the coordinates around (0, 0)
    xCentered = xNorm - 0.5
    yCentered = yNorm - 0.5

    # Angle in radians
    angleRad = math.radians(float(angleDeg))

    # Direction vector: 0° -> +X, 90° -> +Y (bottom), but we want 90° to
    # correspond to bottom->top, so we invert the Y part
    dirX = math.cos(angleRad)
    dirY = -math.sin(angleRad)

    # Normalize direction vector (safety)
    length = math.sqrt(dirX * dirX + dirY * dirY) or 1.0
    dirX /= length
    dirY /= length

    # Projection of each pixel onto the direction vector
    proj = xCentered * dirX + yCentered * dirY

    # proj is roughly in [-0.5 * sqrt(2), 0.5 * sqrt(2)] for angles, but
    # we can remap linearly by finding min/max for this grid.
    minProj = float(proj.min())
    maxProj = float(proj.max())

    if maxProj <= minProj + 1e-8:
        # Degenerate case (should not happen), fallback to zeros
        return np.zeros_like(proj, dtype=np.float32)

    t = (proj - minProj) / (maxProj - minProj)
    return t.astype(np.float32)


# ---------------------------------------------------------------------------
# Full gradient mapping convenience
# ---------------------------------------------------------------------------


def ApplyGradient(
    gradient: "GradientConfig",
    width: int,
    height: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute the gradient RGBA image for the given size.

    This is a convenience function often used for previews. The main
    renderer will typically call ComputeGradientTFromAngle separately
    (to possibly reuse `t`) and EvaluateGradientAt.

    Returns four float32 arrays in [0, 1] for R, G, B, A.
    """

    t = ComputeGradientTFromAngle(width, height, gradient.AngleDeg)
    return EvaluateGradientAt(gradient, t)