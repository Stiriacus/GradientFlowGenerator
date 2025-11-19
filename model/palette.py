
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

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
