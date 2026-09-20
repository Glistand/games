"""Device-sized window with letterboxed logical game canvas (900×700)."""

from __future__ import annotations

import sys

import pygame

from levels import W, H

IS_WEB = sys.platform == "emscripten"


def query_device_size() -> tuple[int, int]:
    """Best-effort browser/window size; falls back to design resolution."""
    if IS_WEB:
        try:
            import platform as pl  # pygbag window bridge

            win = getattr(pl, "window", None)
            if win is not None:
                iw = int(getattr(win, "innerWidth", 0) or 0)
                ih = int(getattr(win, "innerHeight", 0) or 0)
                if iw >= 320 and ih >= 240:
                    return iw, ih
        except Exception:
            pass
        try:
            sw, sh = pygame.display.get_window_size()
            if sw >= 320 and sh >= 240:
                return sw, sh
        except Exception:
            pass
        info = pygame.display.Info()
        if info.current_w >= 320 and info.current_h >= 240:
            return int(info.current_w), int(info.current_h)
    return W, H


class Viewport:
    """Maps between screen pixels and logical (W×H) game coordinates."""

    __slots__ = ("sw", "sh", "scale", "ox", "oy", "dw", "dh")

    def __init__(self, sw: int, sh: int) -> None:
        self.sw = max(1, sw)
        self.sh = max(1, sh)
        self.scale = min(self.sw / W, self.sh / H)
        self.dw = max(1, int(W * self.scale))
        self.dh = max(1, int(H * self.scale))
        self.ox = (self.sw - self.dw) // 2
        self.oy = (self.sh - self.dh) // 2

    @classmethod
    def identity(cls) -> Viewport:
        return cls(W, H)

    def fit(self, sw: int, sh: int) -> bool:
        """Update if size changed. Returns True when geometry changed."""
        if sw == self.sw and sh == self.sh:
            return False
        self.__init__(sw, sh)
        return True

    def to_logical(self, pos: tuple[int, int]) -> tuple[int, int]:
        x, y = pos
        if self.scale <= 0:
            return 0, 0
        lx = (x - self.ox) / self.scale
        ly = (y - self.oy) / self.scale
        return int(lx), int(ly)

    def present(self, screen: pygame.Surface, canvas: pygame.Surface) -> None:
        screen.fill((10, 16, 28))
        if self.dw == W and self.dh == H and self.ox == 0 and self.oy == 0:
            screen.blit(canvas, (0, 0))
            return
        scaled = pygame.transform.smoothscale(canvas, (self.dw, self.dh))
        screen.blit(scaled, (self.ox, self.oy))
