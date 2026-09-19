"""Mario-style levels: platforms, hazards, biome zones."""

from __future__ import annotations

from dataclasses import dataclass

W, H = 900, 700
GROUND_Y = 560
TRAIN_SCREEN_X = 220
START_LIVES = 3


@dataclass(frozen=True)
class Zone:
    start_x: float
    theme: str
    weather: str


@dataclass(frozen=True)
class Platform:
    """Solid top you can stand on (world coords; y = top)."""

    x: float
    y: float
    w: float
    h: float = 18
    kind: str = "solid"  # solid | crumble | blink


@dataclass(frozen=True)
class Hazard:
    """Hurts on touch (world coords; y = top)."""

    kind: str  # stump | crate | fence | rock | puddle | spike | barrier
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class Prop:
    """Railway props: signal, barrier, worker, booth (world x on ground)."""

    kind: str  # signal | barrier | worker | booth
    x: float
    link: float = 0.0  # for barrier: x of controlling signal (0 = auto)


@dataclass(frozen=True)
class Level:
    id: int
    name: str
    length: float
    zones: tuple[Zone, ...]
    platforms: tuple[Platform, ...]
    coins: tuple[tuple[float, float], ...]
    hazards: tuple[Hazard, ...]
    start: tuple[float, float]
    props: tuple[Prop, ...] = ()
    lives: int = START_LIVES


def _plat(x: float, y: float, w: float, h: float = 18, kind: str = "solid") -> Platform:
    return Platform(x, y, w, h, kind)


def _hz(kind: str, x: float, y: float, w: float, h: float) -> Hazard:
    return Hazard(kind, x, y, w, h)


def _prop(kind: str, x: float, link: float = 0.0) -> Prop:
    return Prop(kind, x, link)


def _ground_hazards(items: list[tuple[str, float, float, float]]) -> tuple[Hazard, ...]:
    """(kind, x, w, h) sitting on GROUND_Y."""
    return tuple(_hz(k, x, GROUND_Y - h, w, h) for k, x, w, h in items)


def signal_phase(t: float, x: float) -> int:
    """0=green, 1=yellow, 2=red — staggered by position."""
    cycle = 5.0
    local = (t + x * 0.02) % cycle
    if local < 2.2:
        return 0
    if local < 2.9:
        return 1
    return 2


LEVELS: list[Level] = [
    # 1 — sunny meadow, easy platforms
    Level(
        id=1,
        name="Солнечная поляна",
        length=3600,
        zones=(Zone(0, "meadow", "none"),),
        start=(80, GROUND_Y),
        platforms=(
            _plat(350, 465, 160),
            _plat(580, 432, 160, kind="crumble"),
            _plat(820, 465, 160),
            _plat(1100, 443, 160, kind="blink"),
            _plat(1400, 421, 160, kind="crumble"),
            _plat(1650, 459.5, 160),
            _plat(1950, 432, 160),
            _plat(2250, 410, 160, kind="crumble"),
            _plat(2550, 448.5, 160),
            _plat(2900, 426.5, 160),
            _plat(3200, 459.5, 180, kind="crumble"),
        ),
        coins=(
            (400, 428),
            (620, 395),
            (860, 428),
            (1150, 406),
            (1450, 384),
            (1700, 422.5),
            (2000, 395),
            (2300, 373),
            (2600, 411.5),
            (2950, 389.5),
            (3250, 422.5),
            (500, GROUND_Y - 50),
            (1000, GROUND_Y - 50),
            (1800, GROUND_Y - 50),
            (2700, GROUND_Y - 50),
            (3400, GROUND_Y - 50),
        ),
        hazards=_ground_hazards(
            [
                ("stump", 480, 36, 32),
                ("crate", 980, 40, 36),
                ("rock", 1550, 44, 36),
                ("stump", 2100, 36, 32),
                ("crate", 2750, 40, 36),
                ("rock", 3100, 44, 36),
            ]
        ),
        props=(
            _prop("signal", 250),
            _prop("booth", 750),
            _prop("worker", 800),
            _prop("barrier", 1250, link=250),
            _prop("signal", 1800),
            _prop("worker", 2400),
            _prop("barrier", 3000, link=1800),
            _prop("signal", 3450),
        ),
    ),
    Level(
        id=2,
        name="Край леса",
        length=4200,
        zones=(Zone(0, "forest", "rain"),),
        start=(80, GROUND_Y),
        platforms=(
            _plat(300, 470.5, 160, kind="blink"),
            _plat(520, 437.5, 160),
            _plat(780, 459.5, 160, kind="crumble"),
            _plat(1100, 432, 160),
            _plat(1400, 410, 160, kind="blink"),
            _plat(1650, 443, 160, kind="crumble"),
            _plat(1900, 415.5, 160),
            _plat(2200, 448.5, 160),
            _plat(2500, 421, 160, kind="crumble"),
            _plat(2850, 399, 160),
            _plat(3200, 432, 160),
            _plat(3550, 459.5, 160, kind="crumble"),
            _plat(3850, 432, 160, kind="blink"),
        ),
        coins=(
            (340, 433.5),
            (560, 400.5),
            (820, 422.5),
            (1150, 395),
            (1450, 373),
            (1700, 406),
            (1950, 378.5),
            (2250, 411.5),
            (2550, 384),
            (2900, 362),
            (3250, 395),
            (3600, 422.5),
            (3900, 395),
            (700, GROUND_Y - 50),
            (1600, GROUND_Y - 50),
            (2400, GROUND_Y - 50),
            (3400, GROUND_Y - 50),
        ),
        hazards=_ground_hazards(
            [
                ("stump", 450, 36, 32),
                ("fence", 950, 34, 42),
                ("rock", 1350, 44, 38),
                ("crate", 1750, 40, 36),
                ("fence", 2150, 34, 42),
                ("stump", 2650, 36, 32),
                ("rock", 3050, 44, 38),
                ("fence", 3450, 34, 42),
                ("crate", 3750, 40, 36),
            ]
        ),
        props=(
            _prop("signal", 280),
            _prop("barrier", 700, link=280),
            _prop("booth", 1500),
            _prop("worker", 1550),
            _prop("signal", 2000),
            _prop("barrier", 2550, link=2000),
            _prop("worker", 3200),
            _prop("signal", 3800),
            _prop("barrier", 4000, link=3800),
        ),
    ),
    # 3 — swamp + fog
    Level(
        id=3,
        name="Болото",
        length=4600,
        zones=(Zone(0, "swamp", "fog"),),
        start=(80, GROUND_Y),
        platforms=(
            _plat(320, 470.5, 160),
            _plat(560, 443, 160, kind="crumble"),
            _plat(850, 465, 160),
            _plat(1200, 432, 160, kind="blink"),
            _plat(1500, 410, 160, kind="crumble"),
            _plat(1800, 443, 160),
            _plat(2150, 415.5, 160),
            _plat(2500, 448.5, 160, kind="crumble"),
            _plat(2850, 421, 160),
            _plat(3200, 399, 160),
            _plat(3550, 432, 160, kind="crumble"),
            _plat(3900, 459.5, 160, kind="blink"),
            _plat(4200, 432, 160),
        ),
        coins=(
            (360, 433.5),
            (600, 406),
            (890, 428),
            (1250, 395),
            (1550, 373),
            (1850, 406),
            (2200, 378.5),
            (2550, 411.5),
            (2900, 384),
            (3250, 362),
            (3600, 395),
            (3950, 422.5),
            (4250, 395),
            (1000, GROUND_Y - 50),
            (2000, GROUND_Y - 50),
            (3000, GROUND_Y - 50),
            (4000, GROUND_Y - 50),
        ),
        hazards=(
            *_ground_hazards(
                [
                    ("puddle", 480, 56, 20),
                    ("stump", 900, 36, 32),
                    ("puddle", 1450, 60, 20),
                    ("rock", 1900, 44, 38),
                    ("puddle", 2400, 58, 20),
                    ("crate", 2750, 40, 36),
                    ("puddle", 3300, 60, 20),
                    ("fence", 3700, 34, 42),
                    ("puddle", 4050, 56, 20),
                    ("rock", 4400, 44, 38),
                ]
            ),
            _hz("spike", 1600, 390, 40, 18),
            _hz("spike", 2900, 403, 40, 18),
        ),
        props=(
            _prop("signal", 300),
            _prop("barrier", 900, link=300),
            _prop("booth", 1700),
            _prop("worker", 1760),
            _prop("signal", 2200),
            _prop("barrier", 2800, link=2200),
            _prop("worker", 3500),
            _prop("signal", 4100),
            _prop("barrier", 4400, link=4100),
        ),
    ),
    # 4 — fences / platforms maze
    Level(
        id=4,
        name="Заборчики",
        length=5000,
        zones=(Zone(0, "fences", "none"),),
        start=(80, GROUND_Y),
        platforms=(
            _plat(280, 476, 160, kind="crumble"),
            _plat(480, 443, 160),
            _plat(700, 410, 160, kind="blink"),
            _plat(950, 443, 160, kind="crumble"),
            _plat(1200, 421, 160),
            _plat(1450, 390, 160),
            _plat(1750, 421, 160, kind="crumble"),
            _plat(2000, 454, 160),
            _plat(2300, 421, 160),
            _plat(2600, 390, 160, kind="crumble"),
            _plat(2900, 421, 160, kind="blink"),
            _plat(3200, 454, 160),
            _plat(3550, 421, 160, kind="crumble"),
            _plat(3900, 390, 160),
            _plat(4250, 432, 160, kind="blink"),
            _plat(4600, 459.5, 160, kind="crumble"),
        ),
        coins=(
            (320, 439),
            (520, 406),
            (740, 373),
            (990, 406),
            (1240, 384),
            (1500, 360),
            (1790, 384),
            (2050, 417),
            (2340, 384),
            (2650, 360),
            (2940, 384),
            (3250, 417),
            (3600, 384),
            (3950, 360),
            (4300, 395),
            (4650, 422.5),
            (1100, GROUND_Y - 50),
            (2500, GROUND_Y - 50),
            (4000, GROUND_Y - 50),
        ),
        hazards=_ground_hazards(
            [
                ("fence", 400, 34, 42),
                ("fence", 850, 34, 42),
                ("crate", 1300, 40, 36),
                ("fence", 1650, 34, 42),
                ("rock", 2100, 44, 38),
                ("fence", 2450, 34, 42),
                ("fence", 2800, 34, 42),
                ("crate", 3150, 40, 36),
                ("fence", 3500, 34, 42),
                ("fence", 3850, 34, 42),
                ("rock", 4200, 44, 38),
                ("fence", 4500, 34, 42),
            ]
        ),
        props=(
            _prop("booth", 350),
            _prop("worker", 400),
            _prop("signal", 900),
            _prop("barrier", 1500, link=900),
            _prop("signal", 2200),
            _prop("booth", 3000),
            _prop("worker", 3060),
            _prop("barrier", 3700, link=2200),
            _prop("signal", 4400),
            _prop("barrier", 4800, link=4400),
        ),
    ),
    # 5 — winter evening WITH snow
    Level(
        id=5,
        name="Зимний вечер",
        length=5400,
        zones=(Zone(0, "dusk", "snow"),),
        start=(80, GROUND_Y),
        platforms=(
            _plat(300, 470.5, 160),
            _plat(550, 437.5, 160),
            _plat(850, 459.5, 160, kind="crumble"),
            _plat(1150, 426.5, 160),
            _plat(1450, 399, 160),
            _plat(1750, 432, 160, kind="crumble"),
            _plat(2100, 404.5, 160, kind="blink"),
            _plat(2450, 437.5, 160),
            _plat(2800, 410, 160, kind="crumble"),
            _plat(3200, 390, 160),
            _plat(3550, 421, 160, kind="blink"),
            _plat(3900, 448.5, 160, kind="crumble"),
            _plat(4300, 415.5, 160),
            _plat(4700, 443, 160),
            _plat(5050, 465, 180, kind="crumble"),
        ),
        coins=(
            (340, 433.5),
            (590, 400.5),
            (890, 422.5),
            (1200, 389.5),
            (1500, 362),
            (1800, 395),
            (2150, 367.5),
            (2500, 400.5),
            (2850, 373),
            (3250, 360),
            (3600, 384),
            (3950, 411.5),
            (4350, 378.5),
            (4750, 406),
            (5100, 428),
            (700, GROUND_Y - 50),
            (2000, GROUND_Y - 50),
            (3500, GROUND_Y - 50),
            (4800, GROUND_Y - 50),
        ),
        hazards=(
            *_ground_hazards(
                [
                    ("rock", 450, 44, 38),
                    ("fence", 1000, 34, 42),
                    ("crate", 1400, 40, 36),
                    ("stump", 1850, 36, 32),
                    ("rock", 2300, 44, 38),
                    ("fence", 2700, 34, 42),
                    ("puddle", 3100, 56, 18),
                    ("crate", 3450, 40, 36),
                    ("fence", 3800, 34, 42),
                    ("rock", 4200, 44, 38),
                    ("fence", 4600, 34, 42),
                    ("stump", 5000, 36, 32),
                ]
            ),
            _hz("spike", 1500, 372, 40, 18),
            _hz("spike", 2850, 392, 40, 18),
            _hz("spike", 4350, 397, 40, 18),
        ),
        props=(
            _prop("signal", 320),
            _prop("barrier", 800, link=320),
            _prop("booth", 1600),
            _prop("worker", 1660),
            _prop("signal", 2400),
            _prop("barrier", 3000, link=2400),
            _prop("worker", 3800),
            _prop("signal", 4500),
            _prop("booth", 5000),
            _prop("worker", 5060),
            _prop("barrier", 5200, link=4500),
        ),
    ),
]


def get_level(level_id: int) -> Level:
    for lv in LEVELS:
        if lv.id == level_id:
            return lv
    return LEVELS[0]


def zone_at(level: Level, x: float) -> Zone:
    current = level.zones[0]
    for z in level.zones:
        if x >= z.start_x:
            current = z
        else:
            break
    return current
