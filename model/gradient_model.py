
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

@dataclass
class GradientStop:
    Position: float  # 0.0 – 1.0
    Color: str       # "#rrggbb"
    Opacity: float   # 0.0 – 1.0

    def ToDict(self) -> Dict[str, Any]:
        return {
            "position": float(self.Position),
            "color": self.Color,
            "opacity": float(self.Opacity),
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "GradientStop":
        return GradientStop(
            Position=float(data.get("position", 0.0)),
            Color=str(data.get("color", "#000000")),
            Opacity=float(data.get("opacity", 1.0)),
        )


@dataclass
class GradientConfig:
    Stops: List[GradientStop] = field(default_factory=list)
    AngleDeg: float = 20.0  # 0–360°

    def ToDict(self) -> Dict[str, Any]:
        # Ensure stops are sorted by Position
        sorted_stops = sorted(self.Stops, key=lambda s: s.Position)
        return {
            "angle_deg": float(self.AngleDeg),
            "stops": [stop.ToDict() for stop in sorted_stops],
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "GradientConfig":
        angle = float(data.get("angle_deg", 20.0))
        stops_data = data.get("stops", [])

        stops: List[GradientStop] = [
            GradientStop.FromDict(stop_dict) for stop_dict in stops_data
        ]

        # Sort to guarantee ascending position order
        stops.sort(key=lambda s: s.Position)

        return GradientConfig(Stops=stops, AngleDeg=angle)

    @staticmethod
    def CreateDefaultFrostGradient() -> "GradientConfig":
        """Create the default Frost/Dune style gradient from the spec."""

        return GradientConfig(
            AngleDeg=20.0,
            Stops=[
                GradientStop(Position=0.0, Color="#000814", Opacity=1.0),
                GradientStop(Position=0.3, Color="#0a1628", Opacity=1.0),
                GradientStop(Position=0.6, Color="#1a2e45", Opacity=1.0),
                GradientStop(Position=1.0, Color="#caf0f8", Opacity=1.0),
            ],
        )