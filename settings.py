"""Persistable game settings."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"
IS_WEB = sys.platform == "emscripten"

DIFFICULTY_MULT = {
    "easy": 0.85,
    "normal": 1.0,
    "hard": 1.25,
}


@dataclass
class Settings:
    music_vol: int = 60
    sfx_vol: int = 80
    difficulty: str = "normal"  # easy | normal | hard
    fullscreen: bool = False

    def speed_mult(self) -> float:
        return DIFFICULTY_MULT.get(self.difficulty, 1.0)

    def time_mult(self) -> float:
        return {"easy": 1.35, "normal": 1.0, "hard": 0.75}.get(self.difficulty, 1.0)

    def save(self) -> None:
        if IS_WEB:
            return
        try:
            SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass

    @classmethod
    def load(cls) -> Settings:
        if IS_WEB or not SETTINGS_PATH.exists():
            return cls()
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            s = cls(
                music_vol=int(data.get("music_vol", 60)),
                sfx_vol=int(data.get("sfx_vol", 80)),
                difficulty=str(data.get("difficulty", "normal")),
                fullscreen=bool(data.get("fullscreen", False)),
            )
            if s.difficulty not in DIFFICULTY_MULT:
                s.difficulty = "normal"
            s.music_vol = max(0, min(100, s.music_vol))
            s.sfx_vol = max(0, min(100, s.sfx_vol))
            return s
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return cls()
