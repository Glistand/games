"""Virtual touch controls + unified input state for keyboard/touch."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from levels import W, H

# Button geometry (logical 900×700)
_PAD = 18
_BTN = 78
_GAP = 14
_JUMP = 96
_PAUSE = 52


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
    """On-screen pads for web/mobile. Tracks held pointers by finger id / mouse."""

    visible: bool = False
    left_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    right_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    jump_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    pause_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    # pointer id -> action name currently held
    _held: dict[int, str] = field(default_factory=dict)
    _pause_armed: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        y = H - _PAD - _BTN
        self.left_rect = pygame.Rect(_PAD, y, _BTN, _BTN)
        self.right_rect = pygame.Rect(_PAD + _BTN + _GAP, y, _BTN, _BTN)
        self.jump_rect = pygame.Rect(W - _PAD - _JUMP, H - _PAD - _JUMP, _JUMP, _JUMP)
        self.pause_rect = pygame.Rect(W - _PAD - _PAUSE, _PAD, _PAUSE, _PAUSE)

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
        # FINGER* events use normalized 0..1 coords
        return (int(e.x * W), int(e.y * H))

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
        # pause fires once when pressed (armed on down, consumed here)
        pause_tap = False
        for pid in list(self._pause_armed):
            if self._held.get(pid) == "pause":
                pause_tap = True
                self._pause_armed.discard(pid)
                # keep held so we don't re-fire until release
        return InputState(left=left, right=right, jump=jump, pause_tap=pause_tap)

    def draw(self, surf: pygame.Surface) -> None:
        if not self.visible:
            return
        font = pygame.font.SysFont("Segoe UI", 36, bold=True)
        small = pygame.font.SysFont("Segoe UI", 28, bold=True)
        for rect, label, active in (
            (self.left_rect, "◀", any(a == "left" for a in self._held.values())),
            (self.right_rect, "▶", any(a == "right" for a in self._held.values())),
            (self.jump_rect, "⬆", any(a == "jump" for a in self._held.values())),
            (self.pause_rect, "II", any(a == "pause" for a in self._held.values())),
        ):
            overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            alpha = 160 if active else 100
            pygame.draw.rect(overlay, (20, 40, 70, alpha), overlay.get_rect(), border_radius=16)
            pygame.draw.rect(overlay, (180, 220, 255, 200), overlay.get_rect(), 2, border_radius=16)
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
