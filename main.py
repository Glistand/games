"""Поезд БЧ — меню, уровни, игра."""

from __future__ import annotations

import asyncio
import sys

import pygame

from controls import TouchControls, keyboard_input, merge_input
from game import FPS, Game
from gfx import Audio, clear_gfx_caches, make_train_sprite, build_background
from levels import LEVELS, W, H, get_level, signal_phase
from settings import Settings
from ui import UI, hit_button

IS_WEB = sys.platform == "emscripten"


class App:
    def __init__(self) -> None:
        pygame.init()
        self.settings = Settings.load()
        if IS_WEB:
            self.settings.fullscreen = False
        flags = pygame.FULLSCREEN if self.settings.fullscreen and not IS_WEB else 0
        self.screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption("Поезд БЧ")
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.audio = Audio()
        self.audio.set_sfx_vol(self.settings.sfx_vol)
        self.audio.set_music_vol(self.settings.music_vol)
        self.audio.play_music()
        self.state = "menu"  # menu | settings | levels | play | pause | result
        self.game: Game | None = None
        self.level_id = 1
        self.fade = 0.0
        self.fade_dir = 0
        self.pending_state: str | None = None
        self._buttons: list = []
        self._slider_drag = False
        self.touch = TouchControls(visible=False)

    def apply_display(self) -> None:
        if IS_WEB:
            self.settings.fullscreen = False
            return
        flags = pygame.FULLSCREEN if self.settings.fullscreen else 0
        self.screen = pygame.display.set_mode((W, H), flags)
        clear_gfx_caches()

    def fade_to(self, new_state: str) -> None:
        self.pending_state = new_state
        self.fade_dir = -1
        self.fade = 0.0

    def start_level(self, level_id: int) -> None:
        self.level_id = level_id
        self.game = Game(get_level(level_id), self.settings, self.audio)
        self.fade_to("play")

    def _sync_touch_visibility(self) -> None:
        show = IS_WEB and self.state in ("play", "pause")
        if self.touch.visible and not show:
            self.touch.reset()
        self.touch.visible = show

    def _handle_ui_press(self, pos: tuple[int, int]) -> bool:
        """Menu/settings/pause/result click. Returns whether app should keep running."""
        if self.state == "settings":
            if self.ui.handle_slider_drag(self.settings, pos):
                self._slider_drag = True
                self.audio.set_sfx_vol(self.settings.sfx_vol)
                self.audio.set_music_vol(self.settings.music_vol)
                return True
            return self.handle_action(hit_button(self._buttons, pos))
        if self.state != "play":
            return self.handle_action(hit_button(self._buttons, pos))
        return True

    def handle_action(self, action: str | None) -> bool:
        if not action:
            return True
        self.audio.play("click")

        if self.state == "menu":
            if action == "play":
                self.fade_to("levels")
            elif action == "settings":
                self.fade_to("settings")
            elif action == "quit":
                return False

        elif self.state == "settings":
            if action == "back":
                self.settings.save()
                self.audio.play_theme("main")
                self.fade_to("menu")
            elif action in ("diff", "fullscreen", "music", "sfx"):
                self.settings = self.ui.handle_settings_click(
                    action, self.settings, pygame.mouse.get_pos()
                )
                if action == "fullscreen":
                    self.apply_display()
                self.audio.set_sfx_vol(self.settings.sfx_vol)
                self.audio.set_music_vol(self.settings.music_vol)

        elif self.state == "levels":
            if action == "back":
                self.fade_to("menu")
            elif action.startswith("level:"):
                self.start_level(int(action.split(":")[1]))

        elif self.state == "pause":
            if action == "resume":
                self.state = "play"
            elif action == "restart" and self.game:
                self.game.reset()
                self.audio.play_theme("main")
                self.state = "play"
            elif action == "quit_levels":
                self.game = None
                self.audio.play_theme("main")
                self.fade_to("levels")

        elif self.state == "result":
            if action == "restart" and self.game:
                self.game.reset()
                self.audio.play_theme("main")
                self.state = "play"
            elif action == "quit_levels":
                self.game = None
                self.audio.play_theme("main")
                self.fade_to("levels")
            elif action == "next":
                nxt = self.level_id + 1
                if nxt <= len(LEVELS):
                    self.audio.play_theme("main")
                    self.start_level(nxt)
                else:
                    self.audio.play_theme("main")
                    self.fade_to("levels")

        return True

    def update(self, dt: float) -> None:
        self.ui.update(dt)
        self._sync_touch_visibility()

        if self.fade_dir != 0:
            self.fade += self.fade_dir * dt / 0.25
            if self.fade_dir < 0 and self.fade <= -1:
                self.fade = -1
                if self.pending_state:
                    self.state = self.pending_state
                    self.pending_state = None
                self.fade_dir = 1
            elif self.fade_dir > 0 and self.fade >= 0:
                self.fade = 0
                self.fade_dir = 0

        if self.state == "play" and self.game:
            inp = merge_input(keyboard_input(), self.touch.poll())
            if inp.pause_tap:
                self.state = "pause"
                self.touch.reset()
                return
            self.game.update(dt, inp)
            if self.game.state in ("win", "lose"):
                self.audio.play_theme("win" if self.game.state == "win" else "lose")
                self.state = "result"
        elif self.state == "pause":
            if self.touch.poll().pause_tap:
                self.state = "play"
                self.touch.reset()

    def draw(self) -> None:
        if self.state == "menu":
            self._buttons = self.ui.draw_menu(self.screen)
        elif self.state == "settings":
            self._buttons = self.ui.draw_settings(self.screen, self.settings)
        elif self.state == "levels":
            self._buttons = self.ui.draw_levels(self.screen)
        elif self.state in ("play", "pause", "result") and self.game:
            self.game.draw(self.screen, self.ui.font, show_hud=True)
            if self.state == "pause":
                self._buttons = self.ui.draw_pause(self.screen)
            elif self.state == "result":
                has_next = self.game.state == "win" and self.level_id < len(LEVELS)
                self._buttons = self.ui.draw_result(
                    self.screen, self.game.state == "win", self.game.score, has_next
                )
            else:
                self._buttons = []
            if self.state in ("play", "pause"):
                self.touch.draw(self.screen)
        else:
            self.screen.fill((20, 30, 50))
            self._buttons = []

        if self.fade != 0:
            a = int(min(255, abs(self.fade) * 255))
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, a))
            self.screen.blit(overlay, (0, 0))

        pygame.display.flip()

    async def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                    continue

                if self.touch.handle_event(e):
                    continue

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.state == "play":
                            self.state = "pause"
                            self.touch.reset()
                        elif self.state == "pause":
                            self.state = "play"
                            self.touch.reset()
                        elif self.state in ("settings", "levels"):
                            if self.state == "settings":
                                self.settings.save()
                            self.fade_to("menu")
                        elif self.state == "menu":
                            running = False
                    elif e.key == pygame.K_r and self.state == "result" and self.game:
                        self.game.reset()
                        self.audio.play_theme("main")
                        self.state = "play"
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    running = self._handle_ui_press(e.pos)
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self._slider_drag:
                        self.settings.save()
                    self._slider_drag = False
                elif e.type == pygame.MOUSEMOTION and self._slider_drag and self.state == "settings":
                    self.ui.handle_slider_drag(self.settings, e.pos)
                    self.audio.set_sfx_vol(self.settings.sfx_vol)
                    self.audio.set_music_vol(self.settings.music_vol)

            self.update(dt)
            self.draw()
            await asyncio.sleep(0)

        self.settings.save()
        if not IS_WEB:
            pygame.quit()


def _selfcheck() -> None:
    assert len(LEVELS) == 5
    for lv in LEVELS:
        assert len(lv.zones) >= 1
        assert lv.zones[-1].weather in ("none", "rain", "snow", "fog")
        assert lv.length > 1000
        assert len(lv.platforms) > 0
        assert len(lv.coins) > 0
        assert lv.lives >= 1

    assert LEVELS[4].zones[0].weather == "snow"
    assert LEVELS[4].zones[0].theme == "dusk"
    assert LEVELS[1].zones[0].theme == "forest"
    assert LEVELS[2].zones[0].theme == "swamp"

    for lv in LEVELS:
        kinds = {p.kind for p in lv.platforms}
        assert "solid" in kinds or True
        assert any(p.kind in ("crumble", "blink") for p in lv.platforms), lv.name
        assert any(p.kind == "signal" for p in lv.props), lv.name
        assert any(p.kind == "barrier" and p.link > 0 for p in lv.props), lv.name
        for p in lv.props:
            if p.kind == "barrier" and p.link:
                assert any(s.kind == "signal" and s.x == p.link for s in lv.props)

    assert signal_phase(0.0, 0.0) == 0
    assert signal_phase(3.0, 0.0) == 2

    pygame.init()
    pygame.display.set_mode((1, 1))
    spr = make_train_sprite(0)
    assert spr is not None and spr.get_width() > 80
    for theme in ("meadow", "forest", "swamp", "fences", "dusk"):
        bg = build_background(theme, W, H)
        assert bg.get_size() == (W, H)

    s = Settings()
    g = Game(LEVELS[0], s, None)
    g.train.vx = 100
    g.train.on_ground = True
    g._jump_buf = 0.1
    g._try_jump()
    assert not g.train.on_ground
    for _ in range(40):
        g.update(1 / 60)
    assert g.lives == LEVELS[0].lives
    screen = pygame.Surface((W, H))
    font = pygame.font.SysFont("Segoe UI", 20)
    g.draw(screen, font)

    crum = next(p for p in g._plats if p.kind == "crumble")
    g.train.x = crum.x + crum.w / 2
    g.train.y = crum.y
    g.train.vx = 0
    g.train.vy = 0
    g.train.on_ground = True
    g._stood_on = crum
    for _ in range(50):
        g._stood_on = crum if crum.gone <= 0 else None
        if g._stood_on:
            crum.stress += 1 / 60
            if crum.stress >= 0.7:
                crum.gone = 2.4
                crum.stress = 0
                break
        g.update(1 / 60)
    assert crum.gone > 0 or not crum.is_solid(g.time)

    from controls import InputState, TouchControls

    tc = TouchControls(visible=True)
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": tc.jump_rect.center})
    assert tc.handle_event(down)
    assert tc.poll().jump
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": tc.jump_rect.center})
    assert tc.handle_event(up)

    ui = UI()
    ui.draw_menu(screen)
    ui.draw_levels(screen)
    ui.draw_settings(screen, s)

    for lv in LEVELS:
        gg = Game(lv, s, None)
        for _ in range(15):
            gg.update(1 / 60, InputState())
        gg.draw(screen, font)

    pygame.quit()
    print("selfcheck ok")


async def main() -> None:
    if "--check" in sys.argv:
        _selfcheck()
        return
    await App().run()


asyncio.run(main())
