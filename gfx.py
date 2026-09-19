"""Procedural side-view BCh train, backgrounds, weather, FX, SFX."""

from __future__ import annotations

import math
import random
from typing import Callable

import pygame

W, H = 900, 700

_bg_cache: dict[tuple[str, int, int], pygame.Surface] = {}
_train_base: pygame.Surface | None = None
_coin_cache: pygame.Surface | None = None


def _shade(c: tuple[int, int, int], f: float) -> tuple[int, int, int]:
    return (
        max(0, min(255, int(c[0] * f))),
        max(0, min(255, int(c[1] * f))),
        max(0, min(255, int(c[2] * f))),
    )


def _gradient(surf: pygame.Surface, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    w, h = surf.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        col = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(surf, col, (0, y), (w, y))


def _clouds(surf: pygame.Surface, rng: random.Random, alpha: int = 180) -> None:
    w, h = surf.get_size()
    for _ in range(6):
        cx = rng.randint(40, w - 40)
        cy = rng.randint(30, int(h * 0.28))
        blob = pygame.Surface((120, 50), pygame.SRCALPHA)
        for ox, oy, r in ((30, 28, 22), (55, 22, 26), (80, 28, 20)):
            pygame.draw.circle(blob, (255, 255, 255, alpha), (ox, oy), r)
        surf.blit(blob, (cx - 60, cy - 25))


def _grass_field(
    surf: pygame.Surface,
    rng: random.Random,
    top_y: int,
    base: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> None:
    w, h = surf.get_size()
    pygame.draw.rect(surf, base, (0, top_y, w, h - top_y))
    pygame.draw.ellipse(surf, _shade(base, 1.08), (-80, top_y - 30, w // 2 + 100, 120))
    pygame.draw.ellipse(surf, _shade(base, 0.92), (w // 3, top_y - 20, w // 2 + 80, 100))
    for _ in range(700):
        x = rng.randint(0, w - 1)
        y = rng.randint(top_y, h - 1)
        pygame.draw.circle(surf, accent if rng.random() < 0.35 else _shade(base, 0.88), (x, y), 1)
    for _ in range(30):
        x = rng.randint(20, w - 20)
        y = rng.randint(top_y + 20, h - 80)
        col = rng.choice([(240, 90, 120), (255, 220, 80), (255, 160, 200), (120, 180, 255)])
        pygame.draw.circle(surf, col, (x, y), 3)
        pygame.draw.line(surf, (40, 120, 50), (x, y + 2), (x, y + 10), 1)


def _bg_meadow(surf: pygame.Surface, rng: random.Random) -> None:
    _gradient(surf, (135, 200, 255), (190, 230, 255))
    _clouds(surf, rng)
    pygame.draw.circle(surf, (255, 240, 120), (780, 70), 42)
    pygame.draw.circle(surf, (255, 255, 200), (780, 70), 28)
    _grass_field(surf, rng, 110, (90, 170, 70), (110, 190, 85))


def _bg_forest(surf: pygame.Surface, rng: random.Random) -> None:
    _gradient(surf, (90, 120, 150), (130, 155, 170))
    _clouds(surf, rng, 80)
    _grass_field(surf, rng, 100, (45, 100, 50), (60, 120, 60))
    w = surf.get_width()
    for i in range(12):
        x = 40 + i * 75
        pygame.draw.rect(surf, (90, 55, 30), (x + 18, 70, 12, 40))
        pygame.draw.circle(surf, (30, 90, 40), (x + 24, 60), 28)
        pygame.draw.circle(surf, (40, 110, 50), (x + 10, 70), 20)
        pygame.draw.circle(surf, (40, 110, 50), (x + 38, 70), 20)
    wet = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    wet.fill((60, 90, 120, 35))
    surf.blit(wet, (0, 0))


def _bg_swamp(surf: pygame.Surface, rng: random.Random) -> None:
    _gradient(surf, (120, 140, 115), (80, 100, 85))
    _clouds(surf, rng, 70)
    _grass_field(surf, rng, 100, (60, 90, 50), (75, 105, 60))
    w, h = surf.get_size()
    for _ in range(10):
        rx = rng.randint(40, w - 80)
        ry = rng.randint(160, h - 100)
        rw = rng.randint(50, 120)
        rh = rng.randint(28, 55)
        pygame.draw.ellipse(surf, (45, 80, 65), (rx, ry, rw, rh))
        pygame.draw.ellipse(surf, (65, 105, 80), (rx + 8, ry + 6, rw - 16, rh - 12))
    mist = pygame.Surface((w, h), pygame.SRCALPHA)
    mist.fill((180, 190, 170, 45))
    surf.blit(mist, (0, 0))


def _bg_fences(surf: pygame.Surface, rng: random.Random) -> None:
    _gradient(surf, (160, 200, 240), (210, 230, 245))
    _clouds(surf, rng, 140)
    _grass_field(surf, rng, 100, (120, 165, 75), (135, 180, 90))
    w = surf.get_width()
    for i in range(8):
        x = 60 + i * 110
        pygame.draw.rect(surf, (140, 100, 55), (x, 150, 8, 50))
        pygame.draw.rect(surf, (140, 100, 55), (x + 40, 150, 8, 50))
        pygame.draw.rect(surf, (160, 115, 65), (x, 160, 48, 6))
        pygame.draw.rect(surf, (160, 115, 65), (x, 180, 48, 6))


def _bg_dusk(surf: pygame.Surface, rng: random.Random) -> None:
    """Winter evening — snow ground, dusk sky, snowy pines."""
    _gradient(surf, (255, 150, 100), (50, 40, 90))
    w, h = surf.get_size()
    pygame.draw.circle(surf, (255, 220, 140), (w // 2, 90), 50)
    pygame.draw.circle(surf, (255, 240, 180), (w // 2, 90), 34)
    for _ in range(60):
        pygame.draw.circle(
            surf,
            (255, 245, 220),
            (rng.randint(0, w), rng.randint(15, 110)),
            rng.choice([1, 1, 2]),
        )
    snow_top = 130
    pygame.draw.rect(surf, (235, 240, 250), (0, snow_top, w, h - snow_top))
    pygame.draw.ellipse(surf, (250, 252, 255), (-60, snow_top - 25, w // 2 + 80, 100))
    pygame.draw.ellipse(surf, (220, 228, 240), (w // 3, snow_top - 15, w // 2 + 60, 90))
    for _ in range(500):
        x = rng.randint(0, w - 1)
        y = rng.randint(snow_top, h - 1)
        col = (255, 255, 255) if rng.random() < 0.5 else (210, 220, 235)
        pygame.draw.circle(surf, col, (x, y), 1)
    for i in range(10):
        x = 30 + i * 90
        pygame.draw.rect(surf, (80, 55, 35), (x + 16, 95, 10, 40))
        pygame.draw.polygon(surf, (40, 90, 55), [(x, 110), (x + 20, 70), (x + 40, 110)])
        pygame.draw.polygon(surf, (250, 252, 255), [(x + 4, 95), (x + 20, 72), (x + 36, 95)])
    dusk = pygame.Surface((w, h), pygame.SRCALPHA)
    dusk.fill((50, 30, 70, 40))
    surf.blit(dusk, (0, 0))


_THEMES: dict[str, Callable[[pygame.Surface, random.Random], None]] = {
    "meadow": _bg_meadow,
    "forest": _bg_forest,
    "swamp": _bg_swamp,
    "fences": _bg_fences,
    "dusk": _bg_dusk,
}


def build_background(theme: str, w: int = W, h: int = H) -> pygame.Surface:
    key = (theme, w, h)
    if key in _bg_cache:
        return _bg_cache[key]
    surf = pygame.Surface((w, h))
    rng = random.Random(hash(theme) & 0xFFFFFFFF)
    fn = _THEMES.get(theme, _bg_meadow)
    fn(surf, rng)
    _bg_cache[key] = surf
    return surf


def make_train_sprite(_angle_deg: int = 0) -> pygame.Surface:
    """Compact side-view BCh EMU head: corporate blue + white stripe."""
    global _train_base
    if _train_base is not None:
        return _train_base

    # Short cab + one section (jump-friendly length)
    base = pygame.Surface((110, 64), pygame.SRCALPHA)
    BLUE = (20, 70, 150)
    BLUE_D = (12, 45, 110)
    WHITE = (245, 248, 255)
    GREY = (55, 60, 70)

    pygame.draw.rect(base, BLUE, (6, 16, 78, 32), border_radius=7)
    pygame.draw.rect(base, WHITE, (6, 26, 78, 10))
    pygame.draw.rect(base, BLUE_D, (6, 16, 78, 32), 2, border_radius=7)

    # Cab nose
    pygame.draw.ellipse(base, BLUE, (68, 14, 38, 36))
    pygame.draw.ellipse(base, BLUE_D, (68, 14, 38, 36), 2)
    pygame.draw.rect(base, WHITE, (78, 26, 24, 10))

    # Windshield
    pygame.draw.rect(base, (140, 200, 240), (82, 18, 16, 12), border_radius=3)
    pygame.draw.rect(base, (30, 50, 80), (82, 18, 16, 12), 1, border_radius=3)

    # Side windows
    for wx in (14, 36, 56):
        pygame.draw.rect(base, (160, 210, 245), (wx, 20, 14, 10), border_radius=2)
        pygame.draw.rect(base, (30, 50, 90), (wx, 20, 14, 10), 1, border_radius=2)

    # Face
    pygame.draw.circle(base, WHITE, (90, 34), 3)
    pygame.draw.circle(base, WHITE, (98, 34), 3)
    pygame.draw.circle(base, (25, 30, 40), (91, 34), 1)
    pygame.draw.circle(base, (25, 30, 40), (99, 34), 1)
    pygame.draw.arc(base, (25, 30, 40), (88, 36, 14, 10), 3.5, 5.9, 2)

    # Pantograph
    pygame.draw.line(base, GREY, (40, 16), (40, 4), 2)
    pygame.draw.line(base, GREY, (30, 4), (55, 4), 2)
    pygame.draw.line(base, GREY, (35, 4), (42, 1), 2)
    pygame.draw.line(base, GREY, (42, 1), (50, 4), 2)

    pygame.draw.circle(base, (220, 40, 40), (102, 24), 3)
    pygame.draw.circle(base, (220, 40, 40), (102, 44), 3)

    for bx in (18, 58):
        pygame.draw.rect(base, GREY, (bx, 44, 26, 8), border_radius=2)
        pygame.draw.circle(base, (35, 35, 40), (bx + 5, 56), 6)
        pygame.draw.circle(base, (35, 35, 40), (bx + 20, 56), 6)
        pygame.draw.circle(base, (160, 160, 170), (bx + 5, 56), 2)
        pygame.draw.circle(base, (160, 160, 170), (bx + 20, 56), 2)

    try:
        font = pygame.font.SysFont("Segoe UI", 13, bold=True)
        mark = font.render("БЧ", True, BLUE_D)
        base.blit(mark, (16, 26))
    except pygame.error:
        pass

    _train_base = base
    return base


def make_coin_sprite() -> pygame.Surface:
    global _coin_cache
    if _coin_cache is not None:
        return _coin_cache
    s = pygame.Surface((28, 28), pygame.SRCALPHA)
    cx = cy = 14
    pygame.draw.circle(s, (220, 170, 40), (cx, cy), 12)
    pygame.draw.circle(s, (255, 220, 80), (cx, cy), 10)
    pygame.draw.circle(s, (180, 130, 30), (cx, cy), 10, 2)
    pygame.draw.circle(s, (255, 255, 200), (cx - 3, cy - 3), 3)
    try:
        font = pygame.font.SysFont("Segoe UI", 12, bold=True)
        s.blit(font.render("$", True, (160, 110, 20)), (9, 6))
    except pygame.error:
        pass
    _coin_cache = s
    return s


def draw_rails(surf: pygame.Surface, ground_y: int, camera_x: float, theme: str = "meadow") -> None:
    """Scrolling ground + rails; snowy for dusk."""
    w = surf.get_width()
    if theme == "dusk":
        pygame.draw.rect(surf, (230, 235, 245), (0, ground_y, w, H - ground_y))
        pygame.draw.rect(surf, (200, 210, 225), (0, ground_y, w, 8))
        start = int(-(camera_x % 40))
        for x in range(start, w + 40, 40):
            pygame.draw.rect(surf, (180, 190, 205), (x, ground_y + 10, 28, 8))
        pygame.draw.line(surf, (160, 170, 185), (0, ground_y + 6), (w, ground_y + 6), 3)
        pygame.draw.line(surf, (160, 170, 185), (0, ground_y + 22), (w, ground_y + 22), 3)
        for x in range(start, w + 40, 20):
            pygame.draw.circle(surf, (255, 255, 255), (x + 8, ground_y + 4), 2)
    elif theme == "swamp":
        pygame.draw.rect(surf, (70, 85, 55), (0, ground_y, w, H - ground_y))
        pygame.draw.rect(surf, (55, 70, 45), (0, ground_y, w, 8))
        start = int(-(camera_x % 40))
        for x in range(start, w + 40, 40):
            pygame.draw.rect(surf, (90, 70, 40), (x, ground_y + 10, 28, 8))
        pygame.draw.line(surf, (140, 150, 160), (0, ground_y + 6), (w, ground_y + 6), 3)
        pygame.draw.line(surf, (140, 150, 160), (0, ground_y + 22), (w, ground_y + 22), 3)
    else:
        pygame.draw.rect(surf, (90, 85, 70), (0, ground_y, w, H - ground_y))
        pygame.draw.rect(surf, (70, 65, 55), (0, ground_y, w, 8))
        start = int(-(camera_x % 40))
        for x in range(start, w + 40, 40):
            pygame.draw.rect(surf, (110, 80, 45), (x, ground_y + 10, 28, 8))
        pygame.draw.line(surf, (180, 185, 195), (0, ground_y + 6), (w, ground_y + 6), 3)
        pygame.draw.line(surf, (180, 185, 195), (0, ground_y + 22), (w, ground_y + 22), 3)


def draw_platform(
    surf: pygame.Surface,
    sx: float,
    y: float,
    w: float,
    h: float,
    theme: str,
    kind: str = "solid",
    crack: float = 0.0,
    alpha: int = 255,
) -> None:
    """kind: solid|crumble|blink; crack 0..1; alpha for blink fade."""
    if alpha <= 0:
        return
    rect = pygame.Rect(int(sx), int(y), int(w), int(h))
    layer = surf if alpha >= 250 else pygame.Surface((max(1, rect.w), max(1, rect.h)), pygame.SRCALPHA)
    r = rect if layer is surf else pygame.Rect(0, 0, rect.w, rect.h)

    if theme == "dusk":
        base, top = (210, 220, 235), (255, 255, 255)
    elif theme == "swamp":
        base, top = (90, 70, 40), (60, 110, 70)
    elif theme == "forest":
        base, top = (100, 65, 35), (50, 120, 55)
    else:
        base, top = (150, 100, 55), (80, 160, 70)

    if kind == "blink":
        base = tuple(min(255, c + 35) for c in base)
        top = (180, 220, 255) if theme != "dusk" else (255, 240, 200)
    elif kind == "crumble":
        base = tuple(max(0, c - 25) for c in base)

    pygame.draw.rect(layer, base if layer is surf else (*base, alpha), r, border_radius=4)
    pygame.draw.rect(
        layer,
        top if layer is surf else (*top, alpha),
        (r.x, r.y, r.w, 5),
        border_radius=3,
    )
    pygame.draw.rect(
        layer,
        (40, 40, 50) if layer is surf else (40, 40, 50, alpha),
        r,
        1,
        border_radius=4,
    )

    # crack lines when crumbling underfoot
    if crack > 0.05 and kind == "crumble":
        n = 1 + int(crack * 4)
        for i in range(n):
            x0 = r.x + int(r.w * (0.15 + i * 0.2))
            y0 = r.y + 3
            pygame.draw.line(
                layer,
                (30, 25, 20) if layer is surf else (30, 25, 20, alpha),
                (x0, y0),
                (x0 + 8 - i * 3, r.bottom - 2),
                2,
            )
            if crack > 0.45:
                pygame.draw.line(
                    layer,
                    (20, 15, 10) if layer is surf else (20, 15, 10, alpha),
                    (x0 + 10, y0 + 2),
                    (x0 - 4, r.bottom - 3),
                    1,
                )

    if layer is not surf:
        surf.blit(layer, rect.topleft)


def draw_obstacle(surf: pygame.Surface, kind: str, sx: float, top_y: float, w: float, h: float) -> None:
    """Hazard; sx = screen center x, top_y = top of hazard."""
    left = int(sx - w / 2)
    top = int(top_y)
    rect = pygame.Rect(left, top, int(w), int(h))
    if kind == "stump":
        pygame.draw.rect(surf, (110, 70, 35), rect, border_radius=4)
        pygame.draw.ellipse(surf, (90, 55, 25), (left - 4, top - 6, int(w) + 8, 14))
    elif kind == "crate":
        pygame.draw.rect(surf, (180, 130, 70), rect, border_radius=3)
        pygame.draw.rect(surf, (120, 80, 40), rect, 2, border_radius=3)
        pygame.draw.line(surf, (120, 80, 40), rect.topleft, rect.bottomright, 2)
    elif kind == "fence":
        for i in range(3):
            px = left + 4 + i * max(8, int(w) // 3)
            pygame.draw.rect(surf, (130, 90, 50), (px, top, 6, int(h)))
        pygame.draw.rect(surf, (150, 105, 55), (left, top + 8, int(w), 6))
        pygame.draw.rect(surf, (150, 105, 55), (left, top + int(h * 0.55), int(w), 6))
    elif kind == "rock":
        pygame.draw.ellipse(surf, (110, 115, 120), rect)
        pygame.draw.ellipse(surf, (80, 85, 90), rect.inflate(-8, -8))
    elif kind == "puddle":
        pygame.draw.ellipse(surf, (50, 100, 80), rect)
        pygame.draw.ellipse(surf, (80, 150, 120), rect.inflate(-10, -6))
    elif kind == "spike":
        n = max(2, int(w) // 12)
        for i in range(n):
            cx = left + int((i + 0.5) * w / n)
            pygame.draw.polygon(
                surf,
                (200, 60, 60),
                [(cx - 6, top + int(h)), (cx + 6, top + int(h)), (cx, top)],
            )


def draw_prop(
    surf: pygame.Surface,
    kind: str,
    sx: float,
    ground_y: float,
    t: float,
    barrier_closed: bool = False,
    signal_phase: int | None = None,
) -> None:
    """Railway signal, boom barrier, station booth, track worker.
    signal_phase: 0=green 1=yellow 2=red (None = derive from t alone).
    """
    gx = int(sx)
    gy = int(ground_y)

    if kind == "signal":
        # mast
        pygame.draw.rect(surf, (60, 65, 75), (gx - 4, gy - 110, 8, 110))
        pygame.draw.rect(surf, (40, 45, 55), (gx - 14, gy - 118, 28, 52), border_radius=4)
        phase = 0 if signal_phase is None else int(signal_phase) % 3
        lit = [(40, 200, 70), (240, 200, 40), (220, 40, 40)]
        dark = (40, 40, 40)
        for i, cy in enumerate((gy - 108, gy - 92, gy - 76)):
            col = lit[i] if phase == i else dark
            pygame.draw.circle(surf, col, (gx, cy), 7)
            if phase == i:
                glow = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*col, 80), (10, 10), 10)
                surf.blit(glow, (gx - 10, cy - 10))

    elif kind == "barrier":
        # post
        pygame.draw.rect(surf, (90, 90, 100), (gx - 6, gy - 70, 12, 70))
        pygame.draw.rect(surf, (200, 40, 40), (gx - 8, gy - 74, 16, 8))
        # boom arm — closed horizontal, open nearly vertical
        arm_len = 90
        if barrier_closed:
            # striped arm across track
            for i in range(6):
                col = (240, 200, 40) if i % 2 == 0 else (220, 40, 40)
                pygame.draw.rect(surf, col, (gx + 4 + i * 14, gy - 58, 14, 10))
            pygame.draw.rect(surf, (50, 50, 60), (gx + 4, gy - 58, arm_len, 10), 2)
        else:
            # raised
            for i in range(5):
                col = (240, 200, 40) if i % 2 == 0 else (220, 40, 40)
                pygame.draw.rect(surf, col, (gx - 5, gy - 70 - i * 14, 10, 14))
            pygame.draw.rect(surf, (50, 50, 60), (gx - 5, gy - 140, 10, 70), 2)

    elif kind == "booth":
        # small station booth
        pygame.draw.rect(surf, (30, 90, 150), (gx - 28, gy - 70, 56, 70), border_radius=2)
        pygame.draw.rect(surf, (20, 60, 110), (gx - 32, gy - 82, 64, 14), border_radius=2)
        pygame.draw.rect(surf, (160, 210, 240), (gx - 16, gy - 55, 18, 16), border_radius=2)
        pygame.draw.rect(surf, (80, 50, 30), (gx + 4, gy - 40, 14, 38))
        try:
            f = pygame.font.SysFont("Segoe UI", 11, bold=True)
            surf.blit(f.render("БЧ", True, (255, 255, 255)), (gx - 12, gy - 78))
        except pygame.error:
            pass

    elif kind == "worker":
        # railway worker in orange vest, waving
        wave = math.sin(t * 5) * 10
        # legs
        pygame.draw.rect(surf, (40, 50, 90), (gx - 8, gy - 22, 7, 22))
        pygame.draw.rect(surf, (40, 50, 90), (gx + 2, gy - 22, 7, 22))
        # body / vest
        pygame.draw.rect(surf, (240, 120, 30), (gx - 12, gy - 48, 24, 28), border_radius=3)
        pygame.draw.rect(surf, (255, 220, 60), (gx - 12, gy - 40, 24, 5))
        # head
        pygame.draw.circle(surf, (240, 200, 160), (gx, gy - 56), 9)
        pygame.draw.rect(surf, (40, 70, 120), (gx - 10, gy - 66, 20, 6), border_radius=2)  # cap
        # arm with flag waving
        ax = gx + 14
        ay = gy - 42 + int(wave * 0.3)
        pygame.draw.line(surf, (240, 200, 160), (gx + 10, gy - 40), (ax + int(wave), ay - 8), 3)
        pygame.draw.rect(surf, (220, 40, 40), (ax + int(wave) - 2, ay - 22, 14, 16), border_radius=2)
        # smile
        pygame.draw.arc(surf, (60, 40, 30), (gx - 5, gy - 58, 10, 8), 3.5, 5.9, 1)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "r")

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        color: tuple[int, int, int],
        r: float = 3.0,
    ):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.r = r

    @classmethod
    def burst(cls, x: float, y: float, color: tuple[int, int, int], n: int = 16) -> list[Particle]:
        out: list[Particle] = []
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(40, 160)
            out.append(
                cls(
                    x,
                    y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 40,
                    random.uniform(0.35, 0.7),
                    color,
                    random.uniform(2, 5),
                )
            )
        return out

    @classmethod
    def smoke(cls, x: float, y: float) -> Particle:
        return cls(
            x + random.uniform(-4, 4),
            y + random.uniform(-4, 4),
            random.uniform(-40, -10),
            random.uniform(-50, -20),
            random.uniform(0.4, 0.8),
            (200, 200, 210),
            random.uniform(4, 8),
        )

    @classmethod
    def dust(cls, x: float, y: float) -> Particle:
        return cls(
            x,
            y,
            random.uniform(-60, -10),
            random.uniform(-10, 20),
            random.uniform(0.2, 0.45),
            (160, 140, 90),
            random.uniform(2, 4),
        )

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 80 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf: pygame.Surface, camera_x: float = 0.0) -> None:
        t = self.life / self.max_life
        a = max(0, min(255, int(220 * t)))
        r = max(1, int(self.r * (0.4 + 0.6 * t)))
        blob = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(blob, (*self.color, a), (r + 1, r + 1), r)
        surf.blit(blob, (int(self.x - camera_x - r - 1), int(self.y - r - 1)))


class WeatherFX:
    def __init__(self, kind: str, w: int = W, h: int = H) -> None:
        self.kind = kind
        self.w, self.h = w, h
        self.drops: list[list[float]] = []
        if kind == "rain":
            self.drops = [
                [random.uniform(0, w), random.uniform(0, h), random.uniform(380, 520)]
                for _ in range(90)
            ]
        elif kind == "snow":
            self.drops = [
                [
                    random.uniform(0, w),
                    random.uniform(0, h),
                    random.uniform(35, 80),
                    random.uniform(-25, 25),
                    random.uniform(2.5, 5.5),
                ]
                for _ in range(140)
            ]
        self._fog = None
        if kind == "fog":
            self._fog = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(h):
                a = int(40 + 80 * (y / h))
                pygame.draw.line(self._fog, (200, 210, 200, a), (0, y), (w, y))

    def set_kind(self, kind: str) -> None:
        if kind == self.kind:
            return
        self.__init__(kind, self.w, self.h)

    def update(self, dt: float) -> None:
        if self.kind == "rain":
            for d in self.drops:
                d[1] += d[2] * dt
                d[0] += 40 * dt
                if d[1] > self.h:
                    d[1] = random.uniform(-40, 0)
                    d[0] = random.uniform(0, self.w)
                if d[0] > self.w:
                    d[0] -= self.w
        elif self.kind == "snow":
            for d in self.drops:
                d[1] += d[2] * dt
                d[0] += d[3] * dt
                if d[1] > self.h:
                    d[1] = random.uniform(-20, 0)
                    d[0] = random.uniform(0, self.w)
                if d[0] < 0:
                    d[0] += self.w
                elif d[0] > self.w:
                    d[0] -= self.w

    def draw(self, surf: pygame.Surface) -> None:
        if self.kind == "rain":
            for d in self.drops:
                pygame.draw.line(
                    surf,
                    (170, 200, 230),
                    (int(d[0]), int(d[1])),
                    (int(d[0] + 2), int(d[1] + 12)),
                    1,
                )
        elif self.kind == "snow":
            for d in self.drops:
                pygame.draw.circle(surf, (240, 245, 255), (int(d[0]), int(d[1])), int(d[4]))
        elif self.kind == "fog" and self._fog is not None:
            surf.blit(self._fog, (0, 0))

    @property
    def coin_alpha(self) -> int:
        return 150 if self.kind == "fog" else 255


class Shockwave:
    __slots__ = ("x", "y", "r", "life", "color")

    def __init__(self, x: float, y: float, color: tuple[int, int, int] = (255, 220, 80)):
        self.x, self.y = x, y
        self.r = 10.0
        self.life = 0.4
        self.color = color

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.r += 200 * dt
        return self.life > 0

    def draw(self, surf: pygame.Surface, camera_x: float = 0.0) -> None:
        a = max(0, min(255, int(180 * self.life / 0.4)))
        ring = pygame.Surface((int(self.r * 2 + 4), int(self.r * 2 + 4)), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, a), (int(self.r + 2), int(self.r + 2)), int(self.r), 3)
        surf.blit(ring, (int(self.x - camera_x - self.r - 2), int(self.y - self.r - 2)))


class Audio:
    """Procedural cheerful music loop + SFX."""

    def __init__(self) -> None:
        self.ok = False
        self.sfx_vol = 0.8
        self.music_vol = 0.5
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._music: pygame.mixer.Sound | None = None
        self._music_ch: pygame.mixer.Channel | None = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.ok = True
            self._sounds["coin"] = self._blip(988, 0.09, bright=True)
            self._sounds["click"] = self._blip(720, 0.04)
            self._sounds["win"] = self._fanfare()
            self._sounds["lose"] = self._tone(110, 0.35, decay=True)
            self._sounds["chug"] = self._blip(160, 0.05)
            self._sounds["jump"] = self._sweep(360, 720, 0.1)
            self._sounds["hit"] = self._tone(80, 0.18, decay=True)
            self._themes: dict[str, pygame.mixer.Sound] = {
                "main": self._make_music_loop(),
                "win": self._make_win_theme(),
                "lose": self._make_lose_theme(),
            }
            self._music = self._themes["main"]
            self._music_ch = pygame.mixer.Channel(0)
            self._current_theme = "main"
        except pygame.error:
            self.ok = False
            self._themes = {}
            self._current_theme = "main"

    def _tone(self, freq: float, dur: float, decay: bool = True) -> pygame.mixer.Sound:
        import array

        sample_rate = 22050
        n = int(sample_rate * dur)
        buf = array.array("h")
        for i in range(n):
            t = i / sample_rate
            env = (1 - i / n) if decay else 1.0
            amp = int(9000 * env * math.sin(2 * math.pi * freq * t))
            buf.append(amp)
            buf.append(amp)
        return pygame.mixer.Sound(buffer=buf)

    def _blip(self, freq: float, dur: float, bright: bool = False) -> pygame.mixer.Sound:
        import array

        sample_rate = 22050
        n = int(sample_rate * dur)
        buf = array.array("h")
        for i in range(n):
            t = i / sample_rate
            env = math.exp(-i / (n * 0.35))
            wave = math.sin(2 * math.pi * freq * t)
            if bright:
                wave += 0.35 * math.sin(2 * math.pi * freq * 2 * t)
            amp = int(10000 * env * wave)
            buf.append(amp)
            buf.append(amp)
        return pygame.mixer.Sound(buffer=buf)

    def _sweep(self, f0: float, f1: float, dur: float) -> pygame.mixer.Sound:
        import array

        sample_rate = 22050
        n = int(sample_rate * dur)
        buf = array.array("h")
        phase = 0.0
        for i in range(n):
            t = i / n
            freq = f0 + (f1 - f0) * t
            phase += 2 * math.pi * freq / sample_rate
            env = math.sin(t * math.pi)
            amp = int(9000 * env * math.sin(phase))
            buf.append(amp)
            buf.append(amp)
        return pygame.mixer.Sound(buffer=buf)

    def _fanfare(self) -> pygame.mixer.Sound:
        import array

        sample_rate = 22050
        notes = [(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.22)]
        buf = array.array("h")
        for freq, dur in notes:
            n = int(sample_rate * dur)
            for i in range(n):
                t = i / sample_rate
                env = 1 - i / n
                amp = int(8500 * env * math.sin(2 * math.pi * freq * t))
                buf.append(amp)
                buf.append(amp)
        return pygame.mixer.Sound(buffer=buf)

    def _make_music_loop(self) -> pygame.mixer.Sound:
        """Cheerful looping chiptune-ish melody (~3.5s)."""
        import array

        sample_rate = 22050
        melody = [
            523, 659, 784, 880, 784, 659, 587, 523,
            587, 659, 784, 659, 523, 392, 440, 523,
        ]
        beat = 0.22
        bass = [261, 196, 220, 174, 261, 196, 247, 261]
        buf = array.array("h")
        total_n = int(sample_rate * beat * len(melody))
        for i in range(total_n):
            t = i / sample_rate
            idx = min(len(melody) - 1, int(t / beat))
            local = t - idx * beat
            env = max(0.0, 1.0 - local / beat) ** 2
            lead = 0.55 * math.sin(2 * math.pi * melody[idx] * t) * env
            lead += 0.18 * (1.0 if math.sin(2 * math.pi * melody[idx] * t) > 0 else -1.0) * env
            bidx = (idx // 2) % len(bass)
            bas = 0.28 * math.sin(2 * math.pi * bass[bidx] * t)
            click = 0.0
            if local < 0.02:
                click = 0.25 * (1 - local / 0.02) * math.sin(2 * math.pi * 1200 * t)
            sample = int(7000 * (lead + bas + click))
            sample = max(-32767, min(32767, sample))
            buf.append(sample)
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    def _make_win_theme(self) -> pygame.mixer.Sound:
        """Bright victory loop — rising major fanfare."""
        melody = [
            523, 659, 784, 1046,
            784, 1046, 1175, 1318,
            1046, 784, 880, 1046,
            1318, 1175, 1046, 784,
        ]
        bass = [262, 330, 392, 523, 392, 330, 294, 262]
        return self._render_loop(melody, bass, 0.18, bright=True)

    def _make_lose_theme(self) -> pygame.mixer.Sound:
        """Sad descending minor tune for game over."""
        melody = [
            392, 370, 349, 330,
            311, 294, 277, 262,
            294, 277, 262, 247,
            233, 220, 208, 196,
        ]
        bass = [196, 185, 175, 165, 156, 147, 139, 131]
        return self._render_loop(melody, bass, 0.28, bright=False)

    def _render_loop(
        self,
        melody: list[float],
        bass: list[float],
        beat: float,
        bright: bool,
    ) -> pygame.mixer.Sound:
        import array

        sample_rate = 22050
        buf = array.array("h")
        total_n = int(sample_rate * beat * len(melody))
        for i in range(total_n):
            t = i / sample_rate
            idx = min(len(melody) - 1, int(t / beat))
            local = t - idx * beat
            env = max(0.0, 1.0 - local / beat) ** 2
            lead = 0.55 * math.sin(2 * math.pi * melody[idx] * t) * env
            if bright:
                lead += 0.2 * (1.0 if math.sin(2 * math.pi * melody[idx] * t) > 0 else -1.0) * env
            else:
                lead *= 0.85
                lead += 0.12 * math.sin(2 * math.pi * (melody[idx] * 0.5) * t) * env
            bidx = (idx // 2) % len(bass)
            bas = 0.3 * math.sin(2 * math.pi * bass[bidx] * t)
            click = 0.0
            if bright and local < 0.015:
                click = 0.2 * (1 - local / 0.015) * math.sin(2 * math.pi * 1400 * t)
            sample = int(7000 * (lead + bas + click))
            sample = max(-32767, min(32767, sample))
            buf.append(sample)
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    def play(self, name: str) -> None:
        if not self.ok or name not in self._sounds:
            return
        s = self._sounds[name]
        s.set_volume(self.sfx_vol)
        s.play()

    def play_music(self) -> None:
        self.play_theme("main")

    def play_theme(self, name: str) -> None:
        """Switch looping BGM: main | win | lose."""
        if not self.ok or self._music_ch is None:
            return
        theme = self._themes.get(name)
        if theme is None:
            return
        if self._current_theme == name and self._music_ch.get_busy():
            theme.set_volume(self.music_vol)
            return
        self._current_theme = name
        self._music = theme
        theme.set_volume(self.music_vol)
        self._music_ch.stop()
        self._music_ch.play(theme, loops=-1)

    def stop_music(self) -> None:
        if self._music_ch is not None:
            self._music_ch.stop()
        self._current_theme = ""

    def set_sfx_vol(self, pct: int) -> None:
        self.sfx_vol = max(0.0, min(1.0, pct / 100.0))

    def set_music_vol(self, pct: int) -> None:
        self.music_vol = max(0.0, min(1.0, pct / 100.0))
        if self._music is not None:
            self._music.set_volume(self.music_vol)



def clear_gfx_caches() -> None:
    _bg_cache.clear()
    global _train_base, _coin_cache
    _train_base = None
    _coin_cache = None
