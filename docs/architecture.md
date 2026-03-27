# Architecture

## Overview

Landus is a two-layer system:

1. **Launcher** (`src/`) -- Python/Arcade app that displays a game carousel, plays theme songs, and spawns game subprocesses.
2. **Games** (`games/*/`) -- Self-contained submodule repos. Any language/engine. Discovered via `game.json`.

## Flow

1. `src/main.py` boots an `arcade.Window` and shows `LauncherView`.
2. `LauncherView` scans `games/*/game.json` to discover games.
3. Player navigates with A/D, selects with F.
4. On selection: launcher closes its window, spawns game via `subprocess.Popen`.
5. Watchdog thread monitors the game process.
6. On game exit (or crash/force-kill): launcher reopens its window and returns to selection.

## Process Isolation

Games run as independent OS processes. The launcher does not share memory, event loops, or display contexts with games. This means:

- A game crash cannot crash the launcher.
- Games can use any library/engine.
- The launcher frees the display before spawning (closes its window).

## Watchdog

Threaded monitor with heartbeat. If the game process is alive but hasn't exited within the timeout, escalation: SIGTERM -> grace period -> SIGKILL. All events logged.
