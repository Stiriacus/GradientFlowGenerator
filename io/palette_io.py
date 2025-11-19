from __future__ import annotations

from pathlib import Path
from typing import List, Union
import json

# WICHTIG: Palette aus dem model-Paket importieren
from model.palette import Palette


def SavePalette(palette: Palette, path: Union[str, Path]) -> None:
    file_path = Path(path)
    data = palette.ToDict()
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadPalette(path: Union[str, Path]) -> Palette:
    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return Palette.FromDict(data)


def SavePalettes(palettes: List[Palette], path: Union[str, Path]) -> None:
    file_path = Path(path)
    data = [p.ToDict() for p in palettes]
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadPalettes(path: Union[str, Path]) -> List[Palette]:
    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data_list = json.loads(raw)

    result: List[Palette] = []
    if isinstance(data_list, list):
        for item in data_list:
            if isinstance(item, dict):
                result.append(Palette.FromDict(item))
    elif isinstance(data_list, dict):
        # Fallback: single palette stored as dict
        result.append(Palette.FromDict(data_list))

    return result
