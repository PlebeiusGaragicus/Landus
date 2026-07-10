# Landus — Employee Manual

Staff reference for running and fixing the Landus arcade cabinet.

## How It Works

- The cabinet boots into the **launcher**: a game-selection carousel (Python / Arcade).
- Each game is a **separate program**. Selecting a game closes the launcher window, runs the game, and returns to the carousel when the game exits.
- A **watchdog** monitors every running game. Holding ESC 3 seconds force-kills a frozen game (SIGTERM, then SIGKILL after 5 s). Games themselves quit cleanly on a 1-second ESC hold.
- Games live in `games/<name>/`, each with a `game.json` manifest (name, launch command, cover art, theme song). The launcher auto-discovers them at startup — no registration step.

## Layers of ESC

| Hold ESC for | What happens |
|--------------|--------------|
| 1 second | Game quits itself cleanly (normal exit) |
| 3 seconds | Watchdog force-kills the game (use when frozen) |

## Fix If…

| Symptom | Fix |
|---------|-----|
| Game frozen / not responding | Hold ESC 3 s → watchdog kills it, carousel returns |
| Frozen and ESC does nothing | Power-cycle the cabinet; it boots back into the launcher |
| "crashed (code N)" banner on carousel | Informational; banner clears in 3 s. Recurs every time → note the game name, report it |
| Carousel shows "No games found" | `games/` dir is missing or empty of `game.json` files — see Maintenance |
| A game is missing from the carousel | Its `game.json` is missing/invalid (bad JSON). Check the launcher log for "Skipping <name>" |
| No theme music on a game | That game has no `theme_song` in its manifest, or the file is missing — harmless |
| Blank/black cover art on a card | Cover image missing or failed to load — cosmetic only |
| Buttons dead in launcher AND games | Keyboard encoder issue — check the USB connection to the encoder board inside the cabinet |
| Whole screen black / launcher gone | Power-cycle the cabinet |

## Maintenance (technical staff)

- **Access**: SSH into the cabinet (Debian Linux). Launcher repo lives at the Landus checkout.
- **Run manually (dev/debug)**: `python -m src.main` from the repo root. Windowed on macOS, fullscreen on Linux.
- **Logs**: launcher logs to stdout (timestamps, watchdog events, game exit codes). Capture via the service journal or terminal.
- **Add/update a game**: games are git submodules. `git submodule update --remote games/<name>`, then restart the launcher. New game: add the submodule with a valid `game.json` at its root (see `docs/game-integration.md`).
- **Dependencies**: launcher needs `arcade` and `pynput` (`pip install -r requirements.txt`). Games have their own `requirements.txt`.
- **Restart the launcher**: quit or kill it and relaunch (or power-cycle — the cabinet boots into it).

## Rules of Thumb

- Never edit game files on the cabinet — fix in the game's repo and update the submodule.
- Power-cycling is always safe: no state is stored between sessions.
- If a game repeatedly crashes or freezes, note the game name and exit code from the banner/log and report it.
