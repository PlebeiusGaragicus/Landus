from dataclasses import dataclass, field

import arcade

from src.config import Config


@dataclass
class PlayerInput:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    action1: bool = False
    action2: bool = False
    action3: bool = False


@dataclass
class InputState:
    player1: PlayerInput = field(default_factory=PlayerInput)
    player2: PlayerInput = field(default_factory=PlayerInput)
    menu_quit: bool = False


class InputHandler:
    """Maps raw key events to the unified InputState."""

    def __init__(self, config: Config):
        self.config = config
        self.state = InputState()
        self._key_map = self._build_key_map()

    def _build_key_map(self) -> dict:
        c = self.config
        return {
            c.P1_UP:      ("player1", "up"),
            c.P1_DOWN:    ("player1", "down"),
            c.P1_LEFT:    ("player1", "left"),
            c.P1_RIGHT:   ("player1", "right"),
            c.P1_ACTION1: ("player1", "action1"),
            c.P1_ACTION2: ("player1", "action2"),
            c.P1_ACTION3: ("player1", "action3"),
            c.P2_UP:      ("player2", "up"),
            c.P2_DOWN:    ("player2", "down"),
            c.P2_LEFT:    ("player2", "left"),
            c.P2_RIGHT:   ("player2", "right"),
            c.P2_ACTION1: ("player2", "action1"),
            c.P2_ACTION2: ("player2", "action2"),
            c.P2_ACTION3: ("player2", "action3"),
            c.MENU_QUIT:  ("menu", "quit"),
        }

    def on_key_press(self, key: int):
        mapping = self._key_map.get(key)
        if not mapping:
            return
        if mapping[0] == "menu":
            self.state.menu_quit = True
        else:
            player = getattr(self.state, mapping[0])
            setattr(player, mapping[1], True)

    def on_key_release(self, key: int):
        mapping = self._key_map.get(key)
        if not mapping:
            return
        if mapping[0] == "menu":
            self.state.menu_quit = False
        else:
            player = getattr(self.state, mapping[0])
            setattr(player, mapping[1], False)
