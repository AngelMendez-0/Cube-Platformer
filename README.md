# Cube-Platformer
A 2D platformer prototype built in Python with pygame. It's a movement-focused foundation: the player is a simple cube with physics and squash-and-stretch animation, so the controls feel responsive before any art or levels are added.


## Version 1.0 Features
Gravity and jumping: frame-based physics with tunable gravity and jump strength.
Squash-and-stretch jump: the cube flattens as it winds up, launches tall and thin, then eases back to its normal shape in the air.
Landing squash: a small impact squash when landing after a fall.
Running bounce: a subtle bounce animation while moving on the ground.
Crouching: halves the player's height and hitbox, and slows movement while crouched.
Simultaneous inputs: run, jump and crouch can be combined freely. Pressing left and right together cancels out.
Window-bound collision: the player stays inside the play area.
Resolution-independent window: the game renders at 800×600 and scales to any window size or to fullscreen without stretching.
Tiled background: a seamless 32×32 tile repeated across the screen.

## v1.1 Update

- **Wall jump rework:** Wall jumps no longer move the player instantly across the screen. The player clings briefly, then pushes off the wall in a smooth arc that carries momentum, and works the same on both sides.
- **Tile-based levels:** Levels are now written as text (`G` ground, `W` wall, `P` spawn), and the player collides with tiles instead of the window edges.
- **New art:** Added a grass-topped ground tile and a stone brick wall tile.
- **Scrolling camera:** A smooth camera follows the player through levels larger than the screen, with a parallax background.
- **New level:** A larger level with platforms, pits that respawn you, and a narrow shaft you climb with wall jumps.
- **Fixes:** Jumps no longer fail randomly, and you can't stand up into a ceiling while crouching.
