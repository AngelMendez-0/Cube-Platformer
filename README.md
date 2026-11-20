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
