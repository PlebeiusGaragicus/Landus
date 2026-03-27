import platform
from dataclasses import dataclass, field
from pathlib import Path

import arcade


@dataclass
class Config:
    title: str = "Landus Arcade"
    screen_width: int = 1280
    screen_height: int = 720
    fullscreen: bool = field(init=False)
    games_dir: Path = field(init=False)

    # Player 1 joystick
    P1_UP: int = arcade.key.W
    P1_DOWN: int = arcade.key.S
    P1_LEFT: int = arcade.key.A
    P1_RIGHT: int = arcade.key.D

    # Player 2 joystick
    P2_UP: int = arcade.key.UP
    P2_DOWN: int = arcade.key.DOWN
    P2_LEFT: int = arcade.key.LEFT
    P2_RIGHT: int = arcade.key.RIGHT

    # Player 1 action buttons
    P1_ACTION1: int = arcade.key.F
    P1_ACTION2: int = arcade.key.G
    P1_ACTION3: int = arcade.key.T

    # Player 2 action buttons
    P2_ACTION1: int = arcade.key.K
    P2_ACTION2: int = arcade.key.L
    P2_ACTION3: int = arcade.key.O

    MENU_QUIT: int = arcade.key.ESCAPE

    def __post_init__(self):
        is_linux = platform.system() == "Linux"
        self.fullscreen = is_linux
        self.games_dir = Path(__file__).resolve().parent.parent / "games"

    @property
    def is_production(self) -> bool:
        return platform.system() == "Linux"
