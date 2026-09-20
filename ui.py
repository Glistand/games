"""Menus, buttons, overlays (Russian UI)."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from levels import LEVELS, W, H
from settings import DIFFICULTY_MULT, Settings


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str

    def hit(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class UI:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont("Segoe UI", 28)
        self.big = pygame.font.SysFont("Segoe UI", 56, bold=True)
        self.small = pygame.font.SysFont("Segoe UI", 22)
        self.title_t = 0.0

    def update(self, dt: float) -> None:
        self.title_t += dt

    def _btn(self, surf: pygame.Surface, b: Button, mouse: tuple[int, int]) -> None:
        hover = b.rect.collidepoint(mouse)
        bg = (50, 110, 180) if hover else (30, 70, 130)
        pygame.draw.rect(surf, bg, b.rect, border_radius=10)
        pygame.draw.rect(surf, (180, 220, 255), b.rect, 2, border_radius=10)
        text = self.font.render(b.label, True, (245, 250, 255))
        pad = 16
        max_w = b.rect.w - pad
        if text.get_width() > max_w:
            size = 26
            while size > 14 and text.get_width() > max_w:
                size -= 2
                text = pygame.font.SysFont("Segoe UI", size, bold=True).render(
                    b.label, True, (245, 250, 255)
                )
        surf.blit(text, text.get_rect(center=b.rect.center))

    def menu_buttons(self) -> list[Button]:
        cx = W // 2
        return [
            Button(pygame.Rect(cx - 140, 280, 280, 54), "Играть", "play"),
            Button(pygame.Rect(cx - 140, 350, 280, 54), "Настройки", "settings"),
            Button(pygame.Rect(cx - 140, 420, 280, 54), "Выход", "quit"),
        ]

    def draw_menu(self, surf: pygame.Surface, mouse: tuple[int, int] | None = None) -> list[Button]:
        import math

        from gfx import build_background, make_train_sprite

        surf.blit(build_background("meadow", W, H), (0, 0))
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((10, 30, 60, 130))
        surf.blit(overlay, (0, 0))

        title = self.big.render("Поезд БЧ", True, (255, 245, 200))
        tr = title.get_rect(center=(W // 2, int(130 + 6 * math.sin(self.title_t * 3))))
        surf.blit(title, tr)
        sub = self.small.render(
            "Тач: ◀ ▶ и прыжок · Клавиатура: стрелки / WASD / пробел",
            True,
            (210, 230, 255),
        )
        surf.blit(sub, sub.get_rect(center=(W // 2, 200)))

        spr = make_train_sprite()
        surf.blit(spr, spr.get_rect(center=(W // 2, 250)))

        buttons = self.menu_buttons()
        if mouse is None:
            mouse = pygame.mouse.get_pos()
        for b in buttons:
            self._btn(surf, b, mouse)
        return buttons

    def level_buttons(self) -> list[Button]:
        short = {1: "Поляна", 2: "Лес", 3: "Болото", 4: "Заборы", 5: "Зима"}
        buttons: list[Button] = []
        for i, lv in enumerate(LEVELS):
            row, col = divmod(i, 3)
            x = 90 + col * 260
            y = 190 + row * 140
            buttons.append(
                Button(
                    pygame.Rect(x, y, 240, 100),
                    f"{lv.id}. {short.get(lv.id, lv.name)}",
                    f"level:{lv.id}",
                )
            )
        buttons.append(Button(pygame.Rect(W // 2 - 100, H - 90, 200, 48), "Назад", "back"))
        return buttons

    def draw_levels(self, surf: pygame.Surface, mouse: tuple[int, int] | None = None) -> list[Button]:
        from gfx import build_background

        surf.blit(build_background("forest", W, H), (0, 0))
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surf.blit(overlay, (0, 0))
        title = self.big.render("Уровни", True, (255, 240, 200))
        surf.blit(title, title.get_rect(center=(W // 2, 80)))
        buttons = self.level_buttons()
        if mouse is None:
            mouse = pygame.mouse.get_pos()
        theme_ru = {
            "meadow": "поляна",
            "forest": "лес",
            "swamp": "болото",
            "fences": "заборы",
            "dusk": "зима",
        }
        weather_ru = {"none": "ясно", "rain": "дождь", "snow": "снег", "fog": "туман"}
        for b in buttons:
            hover = b.rect.collidepoint(mouse)
            bg = (50, 110, 180) if hover else (30, 70, 130)
            pygame.draw.rect(surf, bg, b.rect, border_radius=12)
            pygame.draw.rect(surf, (180, 220, 255), b.rect, 2, border_radius=12)
            if b.action.startswith("level:"):
                lid = int(b.action.split(":")[1])
                lv = LEVELS[lid - 1]
                z = lv.zones[0]
                name = self.font.render(b.label, True, (245, 250, 255))
                if name.get_width() > b.rect.w - 20:
                    name = pygame.font.SysFont("Segoe UI", 22, bold=True).render(
                        b.label, True, (245, 250, 255)
                    )
                surf.blit(name, name.get_rect(center=(b.rect.centerx, b.rect.y + 34)))
                tip_s = f"{theme_ru.get(z.theme, z.theme)} · {weather_ru.get(z.weather, z.weather)}"
                tip = self.small.render(tip_s, True, (190, 215, 240))
                if tip.get_width() > b.rect.w - 16:
                    tip = pygame.font.SysFont("Segoe UI", 16).render(tip_s, True, (190, 215, 240))
                surf.blit(tip, tip.get_rect(center=(b.rect.centerx, b.rect.y + 70)))
            else:
                label = self.font.render(b.label, True, (245, 250, 255))
                surf.blit(label, label.get_rect(center=b.rect.center))
        return buttons

    def settings_layout(self, settings: Settings) -> list[Button]:
        return [
            Button(pygame.Rect(120, 200, 180, 44), f"Музыка {settings.music_vol}", "music"),
            Button(pygame.Rect(120, 270, 180, 44), f"Звук {settings.sfx_vol}", "sfx"),
            Button(pygame.Rect(120, 340, 220, 44), f"Сложность: {settings.difficulty}", "diff"),
            Button(
                pygame.Rect(120, 410, 240, 44),
                f"Полный экран: {'ДА' if settings.fullscreen else 'НЕТ'}",
                "fullscreen",
            ),
            Button(pygame.Rect(W // 2 - 100, H - 90, 200, 48), "Назад", "back"),
        ]

    def draw_settings(self, surf: pygame.Surface, settings: Settings, mouse: tuple[int, int] | None = None) -> list[Button]:
        from gfx import build_background

        surf.blit(build_background("dusk", W, H), (0, 0))
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))
        title = self.big.render("Настройки", True, (220, 230, 255))
        surf.blit(title, title.get_rect(center=(W // 2, 80)))

        for _label, val, y in (("Музыка", settings.music_vol, 200), ("Звук", settings.sfx_vol, 270)):
            pygame.draw.rect(surf, (40, 40, 50), (340, y + 14, 400, 16), border_radius=6)
            fill = int(400 * val / 100)
            pygame.draw.rect(surf, (80, 150, 220), (340, y + 14, fill, 16), border_radius=6)
            pygame.draw.circle(surf, (240, 240, 240), (340 + fill, y + 22), 10)

        hint = self.small.render(
            "Сложность по кругу · тяните ползунки · полный экран", True, (180, 190, 200)
        )
        surf.blit(hint, (120, 480))

        buttons = self.settings_layout(settings)
        if mouse is None:
            mouse = pygame.mouse.get_pos()
        for b in buttons:
            self._btn(surf, b, mouse)
        return buttons

    def handle_settings_click(self, action: str, settings: Settings, pos: tuple[int, int]) -> Settings:
        diffs = list(DIFFICULTY_MULT.keys())
        if action == "diff":
            i = diffs.index(settings.difficulty) if settings.difficulty in diffs else 1
            settings.difficulty = diffs[(i + 1) % len(diffs)]
        elif action == "fullscreen":
            settings.fullscreen = not settings.fullscreen
        elif action == "music":
            settings.music_vol = min(100, settings.music_vol + 10)
        elif action == "sfx":
            settings.sfx_vol = min(100, settings.sfx_vol + 10)
        return settings

    def handle_slider_drag(self, settings: Settings, pos: tuple[int, int]) -> bool:
        x, y = pos
        changed = False
        if 340 <= x <= 740 and 200 <= y <= 240:
            settings.music_vol = max(0, min(100, int((x - 340) / 400 * 100)))
            changed = True
        if 340 <= x <= 740 and 270 <= y <= 310:
            settings.sfx_vol = max(0, min(100, int((x - 340) / 400 * 100)))
            changed = True
        return changed

    def pause_buttons(self) -> list[Button]:
        cx = W // 2
        return [
            Button(pygame.Rect(cx - 140, 260, 280, 50), "Продолжить", "resume"),
            Button(pygame.Rect(cx - 140, 330, 280, 50), "Заново", "restart"),
            Button(pygame.Rect(cx - 140, 400, 280, 50), "К уровням", "quit_levels"),
        ]

    def draw_pause(self, surf: pygame.Surface, mouse: tuple[int, int] | None = None) -> list[Button]:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        title = self.big.render("Пауза", True, (255, 255, 255))
        surf.blit(title, title.get_rect(center=(W // 2, 180)))
        buttons = self.pause_buttons()
        if mouse is None:
            mouse = pygame.mouse.get_pos()
        for b in buttons:
            self._btn(surf, b, mouse)
        return buttons

    def result_buttons(self, won: bool, has_next: bool) -> list[Button]:
        cx = W // 2
        buttons = [
            Button(pygame.Rect(cx - 140, 300, 280, 50), "Заново", "restart"),
            Button(pygame.Rect(cx - 140, 370, 280, 50), "К уровням", "quit_levels"),
        ]
        if won and has_next:
            buttons.insert(0, Button(pygame.Rect(cx - 140, 230, 280, 50), "Дальше", "next"))
        return buttons

    def draw_result(
        self,
        surf: pygame.Surface,
        won: bool,
        score: int,
        has_next: bool,
        mouse: tuple[int, int] | None = None,
    ) -> list[Button]:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        msg = "Уровень пройден!" if won else "Жизни закончились"
        col = (100, 230, 140) if won else (230, 90, 90)
        title = self.big.render(msg, True, col)
        surf.blit(title, title.get_rect(center=(W // 2, 150)))
        sc = self.font.render(f"Очки: {score}", True, (240, 240, 240))
        surf.blit(sc, sc.get_rect(center=(W // 2, 210)))
        buttons = self.result_buttons(won, has_next)
        if mouse is None:
            mouse = pygame.mouse.get_pos()
        for b in buttons:
            self._btn(surf, b, mouse)
        return buttons


def hit_button(buttons: list[Button], pos: tuple[int, int]) -> str | None:
    for b in buttons:
        if b.hit(pos):
            return b.action
    return None
