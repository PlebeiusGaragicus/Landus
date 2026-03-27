# Landus

Arcade cabinet system. Launcher selects and runs games; each game is a self-contained git submodule.

## Repo Structure

```
Landus/
├── src/                  # Launcher source (Python / Arcade library)
│   ├── main.py           # Entry point
│   ├── config.py         # Platform detection, key mappings
│   ├── launcher.py       # Game selection UI (arcade.View)
│   ├── input_handler.py  # Unified input abstraction
│   ├── process_manager.py# Spawn/monitor/kill game subprocesses
│   ├── audio.py          # Theme song playback
│   └── watchdog.py       # Freeze/crash detection
├── assets/               # Launcher assets (fonts, backgrounds)
├── games/                # Game submodules (one dir per game)
│   └── game-donttouchme/ # First game
├── docs/                 # System documentation
├── AGENTS.md             # Agent instructions
└── requirements.txt      # arcade
```

## Setup

```bash
git clone --recurse-submodules <repo-url>
pip install -r requirements.txt
```

## Run (dev)

```bash
python -m src.main
```

Windowed on macOS, fullscreen on Linux (auto-detected).

## Input Mapping

| Function | Player 1 | Player 2 |
|----------|----------|----------|
| Joystick | W/A/S/D | Arrow keys |
| Action 1 | F | K |
| Action 2 | G | L |
| Action 3 | T | O |
| Menu/Quit | ESC | ESC |

## Adding a Game

See [docs/game-integration.md](docs/game-integration.md). Each game submodule must have a `game.json` at its root.
