"""
Frost Dune Background Generator – Model & IO Layer

This file contains the core data models (ProjectConfig, Palette, Gradient,
NoiseLayers, Lighting) and JSON (de-)serialization helpers.

The code is written in Python but uses C#-style naming conventions for
classes, methods, and properties, as requested.

The JSON format follows the specification from the prompt, e.g.:
- snake_case keys like "light_azimuth_deg", "noise_layers", ...
- layer_type values: "base", "detail", "warp"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json


# ---------------------------------------------------------------------------
# model/palette.py
# ---------------------------------------------------------------------------


@dataclass
class Palette:
    Name: str
    Colors: List[str]  # Hex colors like "#0a1628"

    def ToDict(self) -> Dict[str, Any]:
        """Serialize Palette to a JSON-compatible dict.

        Keys follow the spec (name, colors).
        """

        return {
            "name": self.Name,
            "colors": list(self.Colors),
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "Palette":
        return Palette(
            Name=data.get("name", "unnamed"),
            Colors=list(data.get("colors", [])),
        )


# ---------------------------------------------------------------------------
# model/gradient_model.py
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# model/noise_layer.py
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# model/lighting_config.py
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# model/project_config.py
# ---------------------------------------------------------------------------


@dataclass
class ProjectConfig:
    Palette: Palette
    Gradient: GradientConfig
    NoiseLayers: List[NoiseLayerConfig]
    Lighting: LightingConfig

    PreviewWidth: int = 960
    PreviewHeight: int = 540
    NoisePreviewWidth: int = 480
    NoisePreviewHeight: int = 270

    SeedGlobal: int = 42

    def ToDict(self) -> Dict[str, Any]:
        """Serialize the entire project configuration to a dict
        compatible with the JSON example in the spec.
        """

        return {
            "palette": self.Palette.ToDict(),
            "gradient": self.Gradient.ToDict(),
            "noise_layers": [layer.ToDict() for layer in self.NoiseLayers],
            "lighting": self.Lighting.ToDict(),
            "preview_width": int(self.PreviewWidth),
            "preview_height": int(self.PreviewHeight),
            "noise_preview_width": int(self.NoisePreviewWidth),
            "noise_preview_height": int(self.NoisePreviewHeight),
            "seed_global": int(self.SeedGlobal),
        }

    @staticmethod
    def FromDict(data: Dict[str, Any]) -> "ProjectConfig":
        # Palette
        palette_data = data.get("palette") or {}
        palette = Palette.FromDict(palette_data)

        # Gradient
        gradient_data = data.get("gradient") or {}
        gradient = GradientConfig.FromDict(gradient_data)

        # Noise layers
        noise_layers_data = data.get("noise_layers", [])
        noise_layers: List[NoiseLayerConfig] = [
            NoiseLayerConfig.FromDict(layer_dict) for layer_dict in noise_layers_data
        ]

        # Lighting
        lighting_data = data.get("lighting") or {}
        lighting = LightingConfig.FromDict(lighting_data)

        # Dimensions & global seed
        preview_width = int(data.get("preview_width", 960))
        preview_height = int(data.get("preview_height", 540))
        noise_preview_width = int(data.get("noise_preview_width", 480))
        noise_preview_height = int(data.get("noise_preview_height", 270))
        seed_global = int(data.get("seed_global", 42))

        return ProjectConfig(
            Palette=palette,
            Gradient=gradient,
            NoiseLayers=noise_layers,
            Lighting=lighting,
            PreviewWidth=preview_width,
            PreviewHeight=preview_height,
            NoisePreviewWidth=noise_preview_width,
            NoisePreviewHeight=noise_preview_height,
            SeedGlobal=seed_global,
        )

    @staticmethod
    def CreateDefaultFrostProject() -> "ProjectConfig":
        """Create the default project configuration exactly matching the
        JSON example from the specification.
        """

        palette = Palette(
            Name="frost",
            Colors=[
                "#000814",
                "#0a1628",
                "#1a2e45",
                "#caf0f8",
                "#64ffda",
                "#4ecdc4",
            ],
        )

        gradient = GradientConfig.CreateDefaultFrostGradient()

        noise_layers: List[NoiseLayerConfig] = [
            NoiseLayerConfig(
                LayerType=NoiseLayerType.Warp,
                Enabled=True,
                Seed=42,
                ScaleX=0.2,
                ScaleY=0.05,
                Octaves=2,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=1.0,
                HeightPower=1.0,
                Amplitude=0.5,
            ),
            NoiseLayerConfig(
                LayerType=NoiseLayerType.Base,
                Enabled=True,
                Seed=43,
                ScaleX=1.5,
                ScaleY=0.3,
                Octaves=5,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=2.0,
                HeightPower=1.7,
                Amplitude=1.0,
            ),
            NoiseLayerConfig(
                LayerType=NoiseLayerType.Detail,
                Enabled=True,
                Seed=44,
                ScaleX=6.0,
                ScaleY=2.0,
                Octaves=3,
                Persistence=0.5,
                Lacunarity=2.0,
                RidgePower=2.0,
                HeightPower=1.3,
                Amplitude=0.4,
            ),
        ]

        lighting = LightingConfig(
            LightAzimuthDeg=45.0,
            LightElevationDeg=60.0,
            Intensity=0.8,
        )

        return ProjectConfig(
            Palette=palette,
            Gradient=gradient,
            NoiseLayers=noise_layers,
            Lighting=lighting,
            PreviewWidth=960,
            PreviewHeight=540,
            NoisePreviewWidth=480,
            NoisePreviewHeight=270,
            SeedGlobal=42,
        )


# ---------------------------------------------------------------------------
# io/palette_io.py
# ---------------------------------------------------------------------------


def SavePalette(palette: Palette, path: Union[str, Path]) -> None:
    """Save a single Palette as JSON to the given path."""

    file_path = Path(path)
    data = palette.ToDict()
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadPalette(path: Union[str, Path]) -> Palette:
    """Load a single Palette from a JSON file."""

    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return Palette.FromDict(data)


def SavePalettes(palettes: List[Palette], path: Union[str, Path]) -> None:
    """Optional helper: save multiple palettes into one JSON file.

    The resulting JSON is a list of palette objects.
    """

    file_path = Path(path)
    data = [palette.ToDict() for palette in palettes]
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadPalettes(path: Union[str, Path]) -> List[Palette]:
    """Optional helper: load multiple palettes from one JSON file."""

    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data_list = json.loads(raw)

    palettes: List[Palette] = []
    if isinstance(data_list, list):
        for item in data_list:
            if isinstance(item, dict):
                palettes.append(Palette.FromDict(item))
    else:
        # Fallback: maybe the file contains a single palette dict
        if isinstance(data_list, dict):
            palettes.append(Palette.FromDict(data_list))

    return palettes


# ---------------------------------------------------------------------------
# io/project_io.py
# ---------------------------------------------------------------------------


def SaveProject(config: ProjectConfig, path: Union[str, Path]) -> None:
    """Save a ProjectConfig instance as JSON to disk.

    The output format is compatible with the example JSON from the spec.
    """

    file_path = Path(path)
    data = config.ToDict()
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadProject(path: Union[str, Path]) -> ProjectConfig:
    """Load a ProjectConfig instance from a JSON file."""

    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return ProjectConfig.FromDict(data)