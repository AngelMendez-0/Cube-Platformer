import os
import random
from operator import truediv

import pygame
import math
from os import listdir
from os.path import isfile, join

from pygame.display import update

# ---- Variables ----

# INIT
pygame.init()
pygame.display.set_caption("Platformer Game")

# Window
background_img = "background_tile.png"
Width, Height = 800, 600
Fps = 60
Jump_velocity = 6.5
Player_Velocity = 5
Crouch_velocity = 3
Gravity = 0.2

# Animation
Squash_frames = 5  # frames the cube squashes before jumping
Squash_scale = (1.3, 0.7)  # wide and short before the jump
Stretch_scale = (0.7, 1.3)  # skinny and tall when launching
Land_scale = (1.2, 0.8)  # little squash when landing
Ease_speed = 0.2  # how fast the shape goes back to normal
Run_bob_speed = 0.3  # how fast the running bounce is
Run_bob_amount = 0.08  # how big the running bounce is

window = pygame.display.set_mode((Width, Height))  # sets the window height and width


# ---- Logic ----

# anything to do with the player
class Player(pygame.sprite.Sprite):
    # --- Player ---

    color = (255, 0, 0)  # player color

    def __init__(self, x, y, width, height):  # INIT self
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)  # creating a rectangle for the player
        self.hitbox = self.rect # creating hitbox for player

        # how fast the player is moving
        self.xVel = 0
        self.yVel = 0

        self.mask = None

        self.direction = "left"  # current facing direction
        self.animationcount = 0  # counts the current animation frame
        self.crouching = False
        self.standing_height = height

        # drawn shape (hitbox stays the same size)
        self.jump_timer = 0
        self.scale_x = 1
        self.scale_y = 1

    # --- Movement ---

    # moves self based on the displacement (dx, dy)
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy


    def move_left(self):
        self.xVel = -Crouch_velocity if self.crouching else -Player_Velocity

        if self.direction != "left":
            self.direction = "left"
            self.animationcount = 0

    def move_right(self):
        self.xVel = Crouch_velocity if self.crouching else Player_Velocity
        if self.direction != "right":
            self.direction = "right"
            self.animationcount = 0

    # checks if the player is standing on the floor
    def on_ground(self):
        return self.hitbox.bottom == Height

    # starts the squash, the actual jump happens in loop
    def jump(self):
        if self.on_ground() and self.jump_timer == 0:
            self.jump_timer = Squash_frames

    def crouch(self):
        if not self.crouching:
            bottom = self.rect.bottom
            self.rect.height = self.standing_height // 2
            self.rect.bottom = bottom
            self.crouching = True

    def stand(self):
        if self.crouching:
            bottom = self.rect.bottom
            self.rect.height = self.standing_height
            self.rect.bottom = bottom
            self.crouching = False

    # updating loop
    def loop(self, Fps):
        target_x, target_y = 1, 1  # normal shape

        # squash before jumping, then launch stretched
        if self.jump_timer > 0:
            self.jump_timer -= 1
            self.scale_x, self.scale_y = Squash_scale
            if self.jump_timer == 0:
                self.yVel = -Jump_velocity
                self.scale_x, self.scale_y = Stretch_scale
        else:
            # little bounce while running on the ground
            if self.on_ground() and self.xVel != 0:
                self.animationcount += 1
                bob = math.sin(self.animationcount * Run_bob_speed) * Run_bob_amount
                target_x, target_y = 1 - bob, 1 + bob

            # ease the shape toward the target
            self.scale_x += (target_x - self.scale_x) * Ease_speed
            self.scale_y += (target_y - self.scale_y) * Ease_speed

        self.yVel += Gravity # updating for gravity
        self.move(self.xVel, self.yVel)  # updating to move based on xVel and yVel

        # x axis detection
        if self.hitbox.left < 0:
            self.hitbox.left = 0
        elif self.hitbox.right > Width:
            self.hitbox.right = Width

        # y axis detection
        if self.hitbox.top < 0:
            self.hitbox.top = 0
            self.yVel = 0
        elif self.hitbox.bottom > Height:
            if self.yVel > 2:
                self.scale_x, self.scale_y = Land_scale
            self.hitbox.bottom = Height
            self.yVel = 0


    # draws the player
    def draw(self, win):
        width = int(self.hitbox.width * self.scale_x)
        height = int(self.hitbox.height * self.scale_y)
        visual = pygame.Rect(0, 0, width, height)
        visual.midbottom = self.hitbox.midbottom
        pygame.draw.rect(win, self.color, visual)

    def window_collision(self,hit_box, Width, Height):
        # horizontal boundaries
        if hit_box.left < 0:
            hit_box.left = 0
        elif hit_box.right > Width:
            hit_box.right = Width

       # vertical boundaries
        if hit_box.top < 0:
            hit_box.top = 0
        elif hit_box.bottom > Height:
            hit_box.bottom = Height

# anything background related
def get_background(background_img):
    image = pygame.image.load(background_img)  # load the image
    _, _, width, height = image.get_rect()  # create the tiles for the image
    tiles = []  # create an empty list for tiles

    # load each tiles in grid pattern based on height and width
    for x in range(Width // width + 1):
        for y in range(Height // height + 1):
            pos = [x * width, y * height]
            tiles.append(pos)

    return tiles, image


# draws to the given frame
def draw(window, tiles, image, player):
    for tile in tiles:
        window.blit(image, tuple(tile))

    player.draw(window)

    pygame.display.update()

# checks keys being pressed and moves based on that
def handle_movement(player):
    keys = pygame.key.get_pressed() # creating keys for when a key is pressed

    player.xVel = 0

    # moving based on key
    if keys[pygame.K_a] and not keys[pygame.K_d]:
        player.move_left()

    elif keys[pygame.K_d] and not keys[pygame.K_a]:
        player.move_right()

    if keys[pygame.K_w]:
        player.jump()

    if keys[pygame.K_s]:
        player.crouch()

    else:
        player.stand()


# Main method
def main(window):
    clock = pygame.time.Clock()  # creates a clock for the game to run off of
    background, image = get_background(background_img)

    # INIT player
    player = Player(100, 100, 32, 32)

    # Running Game
    run = True
    while run:
        clock.tick(Fps)  # runs at whatever the FPS is set to

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # if they quit
                run = False  # stop the game
                break

        handle_movement(player) # calls player movement
        player.loop(Fps) # calls the loop
        draw(window, background, image, player) # calls the drawer for the window

    # quits out
    pygame.quit()
    quit()


if __name__ == '__main__':
    main(window)