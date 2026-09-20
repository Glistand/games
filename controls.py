"""Virtual touch controls + unified input state for keyboard/touch."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from levels import W, H


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    jump: bool = False
    pause_tap: bool = False

    def clear_taps(self) -> None:
        self.pause_tap = False


@dataclass
class TouchControls:
    """On-screen pads in *screen* pixels (device-sized)."""

    visible: bool = False
    sw: int = W
    sh: int = H
    left_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    right_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    jump_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    pause_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    _held: dict[int, str] = field(default_factory=dict)
    _pause_armed: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.layout(self.sw, self.sh)

    def layout(self, sw: int, sh: int) -> None:
        """Size pads from the shorter screen side so they stay fat-finger friendly."""
        self.sw = max(1, sw)
        self.sh = max(1, sh)
        short = min(self.sw, self.sh)
        pad = max(20, int(short * 0.035))
        btn = max(110, int(short * 0.15))
        gap = max(16, int(short * 0.025))
        jump = max(128, int(short * 0.175))
        pause = max(64, int(short * 0.09))
        y = self.sh - pad - btn
        self.left_rect = pygame.Rect(pad, y, btn, btn)
        self.right_rect = pygame.Rect(pad + btn + gap, y, btn, btn)
        self.jump_rect = pygame.Rect(self.sw - pad - jump, self.sh - pad - jump, jump, jump)
        self.pause_rect = pygame.Rect(self.sw - pad - pause, pad, pause, pause)

    def reset(self) -> None:
        self._held.clear()
        self._pause_armed.clear()

    def _hit_action(self, pos: tuple[int, int]) -> str | None:
        if self.pause_rect.collidepoint(pos):
            return "pause"
        if self.left_rect.collidepoint(pos):
            return "left"
        if self.right_rect.collidepoint(pos):
            return "right"
        if self.jump_rect.collidepoint(pos):
            return "jump"
        return None

    def _finger_pos(self, e: pygame.event.Event) -> tuple[int, int]:
        return (int(e.x * self.sw), int(e.y * self.sh))

    def handle_event(self, e: pygame.event.Event) -> bool:
        """Update held state. Returns True if event was consumed by overlay."""
        if not self.visible:
            return False

        et = e.type
        if et == pygame.MOUSEBUTTONDOWN and e.button == 1:
            action = self._hit_action(e.pos)
            if not action:
                return False
            pid = -1
            self._held[pid] = action
            if action == "pause":
                self._pause_armed.add(pid)
            return True
        if et == pygame.MOUSEBUTTONUP and e.button == 1:
            pid = -1
            if pid in self._held:
                del self._held[pid]
                self._pause_armed.discard(pid)
                return True
            return False
        if et == pygame.MOUSEMOTION and e.buttons[0]:
            pid = -1
            if pid not in self._held and pid not in self._pause_armed:
                return False
            action = self._hit_action(e.pos)
            if action and action != "pause":
                self._held[pid] = action
            elif action == "pause":
                self._held[pid] = "pause"
            else:
                self._held.pop(pid, None)
            return pid in self._held

        finger_down = getattr(pygame, "FINGERDOWN", None)
        finger_up = getattr(pygame, "FINGERUP", None)
        finger_motion = getattr(pygame, "FINGERMOTION", None)
        if finger_down is not None and et == finger_down:
            pos = self._finger_pos(e)
            action = self._hit_action(pos)
            if not action:
                return False
            pid = int(getattr(e, "finger_id", getattr(e, "fingerId", 0)))
            self._held[pid] = action
            if action == "pause":
                self._pause_armed.add(pid)
            return True
        if finger_up is not None and et == finger_up:
            pid = int(getattr(e, "finger_id", getattr(e, "fingerId", 0)))
            if pid in self._held or pid in self._pause_armed:
                self._held.pop(pid, None)
                self._pause_armed.discard(pid)
                return True
            return False
        if finger_motion is not None and et == finger_motion:
            pid = int(getattr(e, "finger_id", getattr(e, "fingerId", 0)))
            if pid not in self._held and pid not in self._pause_armed:
                return False
            pos = self._finger_pos(e)
            action = self._hit_action(pos)
            if action and action != "pause":
                self._held[pid] = action
            elif action == "pause":
                self._held[pid] = "pause"
            else:
                self._held.pop(pid, None)
            return True

        return False

    def poll(self) -> InputState:
        left = any(a == "left" for a in self._held.values())
        right = any(a == "right" for a in self._held.values())
        jump = any(a == "jump" for a in self._held.values())
        pause_tap = False
        for pid in list(self._pause_armed):
            if self._held.get(pid) == "pause":
                pause_tap = True
                self._pause_armed.discard(pid)
        return InputState(left=left, right=right, jump=jump, pause_tap=pause_tap)

    def draw(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        short = min(self.sw, self.sh)
        font = pygame.font.SysFont("Segoe UI", max(40, int(short * 0.07)), bold=True)
        small = pygame.font.SysFont("Segoe UI", max(28, int(short * 0.045)), bold=True)
        for rect, label, active in (
            (self.left_rect, "◀", any(a == "left" for a in self._held.values())),
            (self.right_rect, "▶", any(a == "right" for a in self._held.values())),
            (self.jump_rect, "⬆", any(a == "jump" for a in self._held.values())),
            (self.pause_rect, "II", any(a == "pause" for a in self._held.values())),
        ):
            overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            alpha = 190 if active else 130
            radius = max(16, rect.w // 6)
            pygame.draw.rect(overlay, (20, 40, 70, alpha), overlay.get_rect(), border_radius=radius)
            pygame.draw.rect(
                overlay, (180, 220, 255, 220), overlay.get_rect(), 3, border_radius=radius
            )
            surf.blit(overlay, rect.topleft)
            f = small if rect is self.pause_rect else font
            text = f.render(label, True, (245, 250, 255))
            surf.blit(text, text.get_rect(center=rect.center))


def keyboard_input() -> InputState:
    keys = pygame.key.get_pressed()
    return InputState(
        left=bool(keys[pygame.K_LEFT] or keys[pygame.K_a]),
        right=bool(keys[pygame.K_RIGHT] or keys[pygame.K_d]),
        jump=bool(
            keys[pygame.K_SPACE]
            or keys[pygame.K_UP]
            or keys[pygame.K_w]
            or keys[pygame.K_k]
        ),
    )


def merge_input(a: InputState, b: InputState) -> InputState:
    return InputState(
        left=a.left or b.left,
        right=a.right or b.right,
        jump=a.jump or b.jump,
        pause_tap=a.pause_tap or b.pause_tap,
    )
