import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from src.watchdog import Watchdog

log = logging.getLogger(__name__)


class GameInfo:
    """Parsed from a game's game.json manifest."""

    def __init__(self, game_dir: Path):
        self.game_dir = game_dir
        manifest = game_dir / "game.json"
        with open(manifest) as f:
            data = json.load(f)
        self.name: str = data["name"]
        self.entry: str = data["entry"]
        self.players: list[int] = data.get("players", [1])
        cover = data.get("cover_art")
        self.cover_art: Optional[Path] = (game_dir / cover) if cover else None
        theme = data.get("theme_song")
        self.theme_song: Optional[Path] = (game_dir / theme) if theme else None


def discover_games(games_dir: Path) -> list[GameInfo]:
    """Scan games directory for valid game.json manifests."""
    found = []
    if not games_dir.is_dir():
        return found
    for child in sorted(games_dir.iterdir()):
        manifest = child / "game.json"
        if manifest.is_file():
            try:
                found.append(GameInfo(child))
            except Exception as exc:
                log.warning("Skipping %s: %s", child.name, exc)
    return found


def launch_game(game: GameInfo, watchdog_timeout: float = 30.0) -> int:
    """
    Spawn a game subprocess and block until it exits.
    Returns the exit code (0 = clean, non-zero = crash).
    """
    cmd = game.entry.split()
    if cmd[0] == "python":
        cmd[0] = sys.executable

    log.info("Launching %s: %s (cwd=%s)", game.name, cmd, game.game_dir)
    try:
        proc = subprocess.Popen(cmd, cwd=game.game_dir)
    except Exception as exc:
        log.error("Failed to start %s: %s", game.name, exc)
        return 1

    wd = Watchdog(proc, timeout=watchdog_timeout)
    wd.start()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait(timeout=5)
    finally:
        wd.stop()

    exit_code = proc.returncode
    if exit_code != 0:
        log.warning("%s exited with code %d", game.name, exit_code)
    else:
        log.info("%s exited cleanly", game.name)
    return exit_code
