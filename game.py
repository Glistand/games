"""Mario-style BCh platformer: move, jump platforms, lives, biomes."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

from gfx import (
    Audio,
    Particle,
    Shockwave,
    WeatherFX,
    build_background,
    draw_obstacle,
    draw_platform,
    draw_prop,
    draw_rails,
    make_coin_sprite,
    make_train_sprite,
)
from levels import (
    GROUND_Y,
    TRAIN_SCREEN_X,
    Hazard,
    Level,
    Platform,
    Prop,
    W,
    H,
    signal_phase,
    zone_at,
)
from settings import Settings

FPS = 60
GRAVITY = 1550.0
JUMP_V = -780.0
MOVE_ACCEL = 2800.0
MOVE_MAX = 320.0
FRICTION = 12.0
HIT_W = 48
HIT_H = 40
COYOTE = 0.16
INVULN = 1.4
CRUMBLE_WARN = 0.35
CRUMBLE_BREAK = 0.7
CRUMBLE_GONE = 2.4
BLINK_ON = 2.1
BLINK_CYCLE = 3.6


@dataclass
class Coin:
    x: float
    y: float
    taken: bool = False
    pulse: float = field(default_factory=lambda: random.uniform(0, math.tau))


@dataclass
class Train:
    x: float
    y: float  # feet
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = True
    facing: int = 1  # 1 right, -1 left


@dataclass
class PlatLive:
    """Runtime state for solid / crumble / blink platforms."""

    plat: Platform
    stress: float = 0.0  # crumble: time stood on
    gone: float = 0.0  # crumble: seconds remaining while collapsed

    @property
    def x(self) -> float:
        return self.plat.x

    @property
    def y(self) -> float:
        return self.plat.y

    @property
    def w(self) -> float:
        return self.plat.w

    @property
    def h(self) -> float:
        return self.plat.h

    @property
    def kind(self) -> str:
        return self.plat.kind

    def blink_phase(self, t: float) -> float:
        return (t + self.plat.x * 0.017) % BLINK_CYCLE

    def is_solid(self, t: float) -> bool:
        if self.plat.kind == "crumble":
            return self.gone <= 0.0
        if self.plat.kind == "blink":
            return self.blink_phase(t) < BLINK_ON
        return True

    def crack(self) -> float:
        if self.plat.kind != "crumble" or self.gone > 0:
            return 0.0
        if self.stress <= CRUMBLE_WARN:
            return 0.0
        return min(1.0, (self.stress - CRUMBLE_WARN) / (CRUMBLE_BREAK - CRUMBLE_WARN))

    def draw_alpha(self, t: float) -> int:
        if self.plat.kind == "crumble":
            if self.gone > 0:
                # brief fade-out then invisible
                return int(max(0, min(255, 255 * (self.gone - CRUMBLE_GONE + 0.35) / 0.35)))
            return 255
        if self.plat.kind == "blink":
            ph = self.blink_phase(t)
            if ph < BLINK_ON - 0.35:
                return 255
            if ph < BLINK_ON:
                return int(255 * (BLINK_ON - ph) / 0.35)
            if ph < BLINK_ON + 0.3:
                return 0
            # fade in near end of cycle
            fade = BLINK_CYCLE - ph
            if fade < 0.3:
                return int(255 * (1.0 - fade / 0.3))
            return 0
        return 255


class Game:
    def __init__(self, level: Level, settings: Settings, audio: Audio | None) -> None:
        self.level = level
        self.settings = settings
        self.audio = audio
        self.particles: list[Particle] = []
        self.waves: list[Shockwave] = []
        self.score = 0
        self.state = "playing"
        self.shake = 0.0
        self._smoke_t = 0.0
        self._jump_buf = 0.0
        self._coyote = 0.0
        self.camera_x = 0.0
        self.lives = level.lives
        self.invuln = 0.0
        self.time = 0.0
        self.theme = level.zones[0].theme
        self.weather = WeatherFX(level.zones[0].weather, W, H)
        self.bg = build_background(self.theme, W, H)
        self._bg_next: pygame.Surface | None = None
        self._blend = 0.0
        self._red_hits: set[float] = set()
        self._stood_on: PlatLive | None = None
        sx, sy = level.start
        self.train = Train(sx, sy)
        self.coins = [Coin(x, y) for x, y in level.coins]
        self.total_coins = len(self.coins)
        self._plats: list[PlatLive] = [PlatLive(p) for p in level.platforms]
        self._ground = Platform(-200, float(GROUND_Y), level.length + 800, 80, "solid")

    def reset(self) -> None:
        self.__init__(self.level, self.settings, self.audio)

    @property
    def collected(self) -> int:
        return sum(1 for c in self.coins if c.taken)

    def _sync_zone(self) -> None:
        z = zone_at(self.level, self.train.x)
        if z.theme != self.theme:
            self._bg_next = build_background(z.theme, W, H)
            self._blend = 0.01
            self.theme = z.theme
        if z.weather != self.weather.kind:
            self.weather.set_kind(z.weather)

    def _hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.train.x - HIT_W / 2),
            int(self.train.y - HIT_H),
            HIT_W,
            HIT_H,
        )

    def _try_jump(self) -> None:
        if self.train.on_ground or self._coyote > 0:
            self.train.vy = JUMP_V * (1.05 if self.settings.difficulty == "easy" else 1.0)
            self.train.on_ground = False
            self._coyote = 0.0
            self._jump_buf = 0.0
            if self.audio:
                self.audio.play("jump")

    def _hurt(self) -> None:
        if self.invuln > 0 or self.state != "playing":
            return
        self.lives -= 1
        self.invuln = INVULN
        self.shake = 0.35
        self.train.vy = -280
        self.train.on_ground = False
        if self.audio:
            self.audio.play("hit")
        if self.lives <= 0:
            self.state = "lose"
            if self.audio:
                self.audio.play("lose")

    def _resolve_platforms(self, prev_y: float) -> None:
        box = self._hitbox()
        self.train.on_ground = False
        self._stood_on = None
        if self.train.vy < -40:
            return  # still going up — don't snap
        solids: list[Platform | PlatLive] = [
            p for p in self._plats if p.is_solid(self.time)
        ] + [self._ground]
        for p in solids:
            top = p.y
            if box.right <= p.x + 2 or box.left >= p.x + p.w - 2:
                continue
            feet = self.train.y
            if prev_y <= top + 12 and feet >= top - 2:
                self.train.y = top
                self.train.vy = 0.0
                self.train.on_ground = True
                if isinstance(p, PlatLive):
                    self._stood_on = p
                break

    def _tick_platforms(self, dt: float) -> None:
        stood = self._stood_on
        for p in self._plats:
            if p.kind == "crumble":
                if p.gone > 0:
                    p.gone = max(0.0, p.gone - dt)
                    p.stress = 0.0
                    continue
                if stood is p and self.train.on_ground:
                    p.stress += dt
                    if p.stress >= CRUMBLE_BREAK:
                        p.gone = CRUMBLE_GONE
                        p.stress = 0.0
                        self.train.on_ground = False
                        self.train.vy = 80
                        self._stood_on = None
                        self.particles.extend(
                            Particle.burst(p.x + p.w / 2, p.y, (120, 90, 50), 14)
                        )
                        if self.audio:
                            self.audio.play("hit")
                else:
                    p.stress = max(0.0, p.stress - dt * 1.8)
            elif p.kind == "blink" and stood is p and not p.is_solid(self.time):
                self.train.on_ground = False
                self.train.vy = max(self.train.vy, 60)
                self._stood_on = None

    def _barrier_signal_x(self, prop: Prop) -> float:
        if prop.link:
            return prop.link
        # nearest signal to the left, else nearest any
        signals = [q.x for q in self.level.props if q.kind == "signal"]
        if not signals:
            return prop.x
        left = [x for x in signals if x <= prop.x]
        if left:
            return max(left)
        return min(signals, key=lambda x: abs(x - prop.x))

    def _barrier_closed(self, prop: Prop) -> bool:
        """Boom closed on yellow+red of linked signal."""
        return signal_phase(self.time, self._barrier_signal_x(prop)) >= 1

    def _dynamic_hazards(self) -> list:
        """Closed barriers act as jumpable hazards."""
        extra = []
        for p in self.level.props:
            if p.kind == "barrier" and self._barrier_closed(p):
                extra.append(Hazard("barrier", p.x + 45, GROUND_Y - 28, 88, 28))
        return extra

    def _check_red_signals(self) -> None:
        """Passing a red signal costs a life."""
        for prop in self.level.props:
            if prop.kind != "signal":
                continue
            phase = signal_phase(self.time, prop.x)
            if phase != 2:
                self._red_hits.discard(prop.x)
                continue
            if abs(self.train.x - prop.x) < 36 and prop.x not in self._red_hits:
                self._red_hits.add(prop.x)
                self._hurt()
                self.particles.extend(
                    Particle.burst(prop.x, GROUND_Y - 90, (220, 40, 40), 12)
                )
                break

    def update(self, dt: float) -> None:
        if self.state != "playing":
            self.time += dt
            self.weather.update(dt)
            self.particles = [p for p in self.particles if p.update(dt)]
            self.waves = [w for w in self.waves if w.update(dt)]
            if self.shake > 0:
                self.shake = max(0.0, self.shake - dt)
            return

        self.time += dt
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump_held = (
            keys[pygame.K_SPACE]
            or keys[pygame.K_UP]
            or keys[pygame.K_w]
            or keys[pygame.K_k]
        )

        if jump_held:
            self._jump_buf = 0.14
        else:
            self._jump_buf = max(0.0, self._jump_buf - dt)

        if self.train.on_ground:
            self._coyote = COYOTE
        else:
            self._coyote = max(0.0, self._coyote - dt)

        if self._jump_buf > 0 and (self.train.on_ground or self._coyote > 0):
            self._try_jump()

        # horizontal Mario move (full control in air too)
        speed_m = self.settings.speed_mult()
        max_v = MOVE_MAX * speed_m
        air = 0.85 if not self.train.on_ground else 1.0
        if left and not right:
            self.train.vx -= MOVE_ACCEL * air * dt
            self.train.facing = -1
        elif right and not left:
            self.train.vx += MOVE_ACCEL * air * dt
            self.train.facing = 1
        else:
            damp = FRICTION if self.train.on_ground else FRICTION * 0.35
            self.train.vx *= math.exp(-damp * dt)

        self.train.vx = max(-max_v, min(max_v, self.train.vx))

        prev_y = self.train.y
        self.train.x += self.train.vx * dt
        self.train.x = max(40.0, min(self.level.length + 40, self.train.x))

        # gravity
        if not self.train.on_ground:
            grav = GRAVITY
            if not jump_held and self.train.vy < 0:
                grav *= 1.7  # shorter hop only if release early
            self.train.vy += grav * dt
            self.train.y += self.train.vy * dt
        else:
            self.train.vy = 0.0

        self._resolve_platforms(prev_y)
        self._tick_platforms(dt)

        # fall death
        if self.train.y > H + 80:
            self._hurt()
            if self.state == "playing":
                self.train.x = max(80.0, self.train.x - 120)
                self.train.y = float(GROUND_Y)
                self.train.vx = self.train.vy = 0.0
                self.train.on_ground = True

        self.camera_x = max(0.0, min(self.level.length - W + 100, self.train.x - TRAIN_SCREEN_X))
        self._sync_zone()
        self.invuln = max(0.0, self.invuln - dt)

        if self._blend > 0 and self._bg_next is not None:
            self._blend = min(1.0, self._blend + dt * 0.8)
            if self._blend >= 1.0:
                self.bg = self._bg_next
                self._bg_next = None
                self._blend = 0.0

        moving = abs(self.train.vx) > 30
        self._smoke_t -= dt
        if moving and self._smoke_t <= 0:
            self._smoke_t = 0.1
            back = self.train.x - self.train.facing * 40
            self.particles.append(Particle.smoke(back, self.train.y - 50))
            if self.train.on_ground:
                self.particles.append(Particle.dust(self.train.x, self.train.y - 2))

        # coins
        box = self._hitbox()
        for coin in self.coins:
            if coin.taken:
                continue
            coin.pulse += dt * 4
            if box.inflate(20, 20).collidepoint(int(coin.x), int(coin.y)):
                coin.taken = True
                self.score += 100
                self.particles.extend(Particle.burst(coin.x, coin.y, (255, 220, 80)))
                self.waves.append(Shockwave(coin.x, coin.y))
                if self.audio:
                    self.audio.play("coin")

        # red signals + hazards (+ closed barriers)
        if self.invuln <= 0:
            self._check_red_signals()
        if self.invuln <= 0:
            all_hz = list(self.level.hazards) + self._dynamic_hazards()
            for hz in all_hz:
                hr = pygame.Rect(int(hz.x - hz.w / 2 + 4), int(hz.y), max(6, int(hz.w) - 8), int(hz.h))
                if box.colliderect(hr):
                    if self.train.vy > 0 and prev_y <= hz.y + 4:
                        self.train.y = hz.y
                        self.train.vy = JUMP_V * 0.55
                        self.train.on_ground = False
                        self.score += 25
                        self.particles.extend(Particle.burst(hz.x, hz.y, (200, 100, 80), 10))
                        if self.audio:
                            self.audio.play("jump")
                    else:
                        self._hurt()
                    break

        if self.train.x >= self.level.length and self.state == "playing":
            self.state = "win"
            self.shake = 0.4
            self.waves.append(Shockwave(self.train.x, self.train.y - 30, (100, 200, 255)))
            if self.audio:
                self.audio.play("win")

        self.weather.update(dt)
        self.particles = [p for p in self.particles if p.update(dt)]
        self.waves = [w for w in self.waves if w.update(dt)]
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, show_hud: bool = True) -> None:
        ox = oy = 0
        if self.shake > 0:
            ox = random.randint(-4, 4)
            oy = random.randint(-3, 3)

        layer = pygame.Surface((W, H))
        layer.blit(self.bg, (0, 0))
        if self._bg_next is not None and self._blend > 0:
            tmp = self._bg_next.copy()
            tmp.set_alpha(int(255 * self._blend))
            layer.blit(tmp, (0, 0))

        draw_rails(layer, GROUND_Y, self.camera_x, self.theme)

        # railway props (signals, barriers, workers, booths)
        for prop in self.level.props:
            sx = prop.x - self.camera_x
            if -120 < sx < W + 120:
                closed = self._barrier_closed(prop) if prop.kind == "barrier" else False
                phase = signal_phase(self.time, prop.x) if prop.kind == "signal" else None
                draw_prop(layer, prop.kind, sx, float(GROUND_Y), self.time, closed, phase)

        # finish flag
        flag_x = self.level.length - self.camera_x
        if -20 < flag_x < W + 20:
            pygame.draw.rect(layer, (180, 180, 190), (int(flag_x), GROUND_Y - 120, 6, 120))
            pygame.draw.polygon(
                layer,
                (40, 160, 70),
                [(int(flag_x) + 6, GROUND_Y - 120), (int(flag_x) + 50, GROUND_Y - 100), (int(flag_x) + 6, GROUND_Y - 80)],
            )

        for p in self._plats:
            alpha = p.draw_alpha(self.time)
            if alpha <= 0:
                continue
            sx = p.x - self.camera_x
            if -p.w < sx < W + 20:
                draw_platform(
                    layer,
                    sx,
                    p.y,
                    p.w,
                    p.h,
                    self.theme,
                    kind=p.kind,
                    crack=p.crack(),
                    alpha=alpha,
                )

        for hz in self.level.hazards:
            sx = hz.x - self.camera_x
            if -80 < sx < W + 80:
                draw_obstacle(layer, hz.kind, sx, hz.y, hz.w, hz.h)

        coin_spr = make_coin_sprite()
        coin_a = self.weather.coin_alpha
        for coin in self.coins:
            if coin.taken:
                continue
            sx = coin.x - self.camera_x
            if -40 < sx < W + 40:
                scale = 1.0 + 0.12 * math.sin(coin.pulse)
                size = max(8, int(28 * scale))
                spr = pygame.transform.smoothscale(coin_spr, (size, size))
                if coin_a < 255:
                    spr = spr.copy()
                    spr.set_alpha(coin_a)
                layer.blit(spr, spr.get_rect(center=(int(sx), int(coin.y))))

        for p in self.particles:
            p.draw(layer, self.camera_x)
        for w in self.waves:
            w.draw(layer, self.camera_x)

        train_spr = make_train_sprite()
        if self.train.facing < 0:
            train_spr = pygame.transform.flip(train_spr, True, False)
        # blink when invulnerable
        if self.invuln <= 0 or int(self.invuln * 12) % 2 == 0:
            tx = int(self.train.x - self.camera_x)
            ty = int(self.train.y - train_spr.get_height() + 6)
            layer.blit(train_spr, (tx - train_spr.get_width() // 2, ty))

        self.weather.draw(layer)

        if show_hud:
            bar = pygame.Surface((W, 56), pygame.SRCALPHA)
            bar.fill((15, 35, 70, 175))
            layer.blit(bar, (0, 0))
            title = font.render(self.level.name, True, (240, 245, 255))
            layer.blit(title, (16, 14))
            hearts = "♥" * max(0, self.lives) + "♡" * max(0, self.level.lives - self.lives)
            life_txt = font.render(f"Жизни {hearts}", True, (255, 120, 140))
            layer.blit(life_txt, (W // 2 - life_txt.get_width() // 2 - 40, 14))
            coins_txt = font.render(
                f"Монеты: {self.collected}/{self.total_coins}", True, (255, 230, 120)
            )
            layer.blit(coins_txt, (W - coins_txt.get_width() - 16, 14))
            hint = font.render(
                "←→ — ехать · Пробел — прыжок · жди зелёный · не стой на трещинах",
                True,
                (180, 200, 230),
            )
            layer.blit(hint, (16, H - 36))

        surf.blit(layer, (ox, oy))
