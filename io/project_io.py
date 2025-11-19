from __future__ import annotations

from pathlib import Path
from typing import Union
import json

# WICHTIG: ProjectConfig importieren
from model.project_config import ProjectConfig


def SaveProject(config: ProjectConfig, path: Union[str, Path]) -> None:
    file_path = Path(path)
    data = config.ToDict()
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def LoadProject(path: Union[str, Path]) -> ProjectConfig:
    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return ProjectConfig.FromDict(data)
