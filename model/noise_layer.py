
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

class NoiseLayerType(str, Enum):
    Base = "base"
    Detail = "detail"
    Warp = "warp"


@dataclass
class NoiseLayerConfig:
    LayerType: NoiseLayerType
    Enabled: bool = True
    Seed: int = 0
    ScaleX: float = 1.5
    ScaleY: float = 0.3
    Octaves: int = 5
    Persistence: float = 0.5
    Lacunarity: float = 2.0
    RidgePower: float = 2.0
    HeightPower: float = 1.7
    Amplitude: float = 1.0

    def ToDict(self) -> Dict[str, Any]:
        return {
            "layer_type": self.LayerType.value,
            "enabled": bool(self.Enabled),
            "seed": int(self.Seed),
            "scale_x": float(self.ScaleX),
            "scale_y": float(self.ScaleY),
            "octaves": int(self.Octaves),
            "persistence": float(self.Persistence),
            "lacunarity": float(self.Lacunarity),
            "ridge_power": float(self.RidgePower),
            "height_power": float(self.HeightPower),
            "amplitude": float(self.Amplitude),
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "NoiseLayerConfig":
        layer_type_str = str(data.get("layer_type", "base"))
        try:
            layer_type = NoiseLayerType(layer_type_str)
        except ValueError:
            layer_type = NoiseLayerType.Base

        return NoiseLayerConfig(
            LayerType=layer_type,
            Enabled=bool(data.get("enabled", True)),
            Seed=int(data.get("seed", 0)),
            ScaleX=float(data.get("scale_x", 1.5)),
            ScaleY=float(data.get("scale_y", 0.3)),
            Octaves=int(data.get("octaves", 5)),
            Persistence=float(data.get("persistence", 0.5)),
            Lacunarity=float(data.get("lacunarity", 2.0)),
            RidgePower=float(data.get("ridge_power", 2.0)),
            HeightPower=float(data.get("height_power", 1.7)),
            Amplitude=float(data.get("amplitude", 1.0)),
        )