from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from model.palette import Palette
from model.gradient_model import GradientConfig
from model.noise_layer import NoiseLayerConfig, NoiseLayerType
from model.lighting_config import LightingConfig


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
