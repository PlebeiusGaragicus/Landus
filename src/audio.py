import logging
from pathlib import Path
from typing import Optional

import arcade

log = logging.getLogger(__name__)


class AudioManager:
    """Handle theme song playback for the launcher."""

    def __init__(self):
        self._current_sound: Optional[arcade.Sound] = None
        self._current_player = None

    def play(self, path: Path, loop: bool = True, volume: float = 0.5):
        self.stop()
        if not path.is_file():
            log.warning("Audio file not found: %s", path)
            return
        try:
            self._current_sound = arcade.load_sound(str(path))
            self._current_player = self._current_sound.play(volume=volume, loop=loop)
        except Exception as exc:
            log.warning("Failed to play %s: %s", path, exc)

    def stop(self):
        if self._current_player:
            self._current_player.pause()
            self._current_player = None
        self._current_sound = None

    def set_volume(self, volume: float):
        if self._current_player:
            self._current_player.volume = volume
