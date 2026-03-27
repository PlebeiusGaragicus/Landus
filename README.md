# Landus

This repo handles an arcade system.  It should be structured as such:

this main `Landus/` folder is the main repo - it holds the "system" code and has submodules (one for each game).  We need a docs/ folder as well which can be plain markdown files.  Each submodule game also needs a docs/ folder of the same.  The docs should be written for agent/AI consumption first - avoid verbosity and write for easy system retrieval.

We must include our first game to this repo: git@github.com:PlebeiusGaragicus/game-donttouchme.git

This README file should be edited - again, for agent consumption.  Write skills and/or agents.md files as needed.

The agent should handle all development steps, as directed by the human (important: game testing should be handled only by the human and the human will run the game on their own as needed without prompting)

Each game may use a different language / game engine / design.

Our arcade will run on debian for production and MacOS for testing.  Our arcade system needs to load on startup and should take the full screen (but be window'ed in testing) - it should show a selection of available games.  Once a game is selected to run it should take over the screen and the system should be paused.  The exact mechanism for this should be developed by the agent: spawning and handling processes, etc.  Each game will have a cover art and theme song - the system software needs to be paused when the game is run, of course.  We also need to handle game errors and crashes so that the system never freezes and needs to be restarted by facility staff.  We should catch and handle system freezes on our own, as a catch all.

The arcade will have two joysticks (one for each player, or single player with two joystick control: move and aim, for example).  Next to each joystick will be three action buttons.  We also have a MENU/QUIT button which will be used to PAUSE the game / hold to force quit.

For development we'll use WASD and arrow keys for joystick control.  The production joysticks are basic arcade 4-way instead of analogue, so WASD and arrow keys will work.  We'll use FGT for our action buttons for player one, KLO for player 2 and ESC for MENU/QUIT.