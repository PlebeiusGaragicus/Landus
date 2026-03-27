# Input Mapping

## Keyboard Layout

| Function | Player 1 | Player 2 |
|----------|----------|----------|
| Up | W | Up Arrow |
| Down | S | Down Arrow |
| Left | A | Left Arrow |
| Right | D | Right Arrow |
| Action 1 | F | K |
| Action 2 | G | L |
| Action 3 | T | O |
| Menu/Quit | ESC | ESC |

## Production Hardware

- Two 4-way arcade joysticks (no analog)
- Three action buttons per player
- One shared MENU/QUIT button

## Notes

- WASD and arrow keys map 1:1 to 4-way joystick directions.
- Diagonal input is possible by pressing two directions simultaneously.
- Games replicate this mapping internally; there is no shared input library across the process boundary.
- The launcher uses `arcade.key` constants via `InputHandler` in `src/input_handler.py`.
