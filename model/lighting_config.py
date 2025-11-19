
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

@dataclass
class LightingConfig:
    LightAzimuthDeg: float = 45.0   # 0–360°
    LightElevationDeg: float = 60.0 # 0–90°
    Intensity: float = 0.8          # 0–1

    def ToDict(self) -> Dict[str, Any]:
        return {
            "light_azimuth_deg": float(self.LightAzimuthDeg),
            "light_elevation_deg": float(self.LightElevationDeg),
            "intensity": float(self.Intensity),
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "LightingConfig":
        return LightingConfig(
            LightAzimuthDeg=float(data.get("light_azimuth_deg", 45.0)),
            LightElevationDeg=float(data.get("light_elevation_deg", 60.0)),
            Intensity=float(data.get("intensity", 0.8)),
        )
