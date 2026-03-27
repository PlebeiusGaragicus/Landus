"""Landus Arcade System -- entry point."""

import logging

import arcade

from src.config import Config
from src.launcher import LauncherView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


def main():
    config = Config()
    window = arcade.open_window(
        config.screen_width,
        config.screen_height,
        config.title,
        fullscreen=config.fullscreen,
    )
    view = LauncherView(config)
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()
