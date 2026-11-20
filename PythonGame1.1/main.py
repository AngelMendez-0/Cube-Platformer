import os
import random
from operator import truediv

import pygame
import math
from os import listdir
from os.path import isfile, join

from pygame.display import update
from pygame.time import wait

# ---- Variables ----

# INIT
pygame.init()
pygame.display.set_caption("Platformer Game")

# Window
Width, Height = 800, 600
Fps = 60
Jump_velocity = 6.5
Player_Velocity = 5
Crouch_velocity = 3
Gravity = 0.2
Tile_size = 32

# Animation
Squash_frames = 5  # frames the cube squashes before jumping
Squash_scale = (1.3, 0.7)  # wide and short before the jump
Stretch_scale = (0.7, 1.3)  # skinny and tall when launching
Land_scale = (1.2, 0.8)  # little squash when landing
Ease_speed = 0.2  # how fast the shape goes back to normal
Run_bob_speed = 0.3  # how fast the running bounce is
Run_bob_amount = 0.08  # how big the running bounce is

Wall_jump_push = 7
Wall_jump_lock_frames = 12
Air_control = 0.15

Camera_smooth = 0.1
Parallax = 0.5

window = pygame.display.set_mode((Width, Height))  # sets the window height and width

# Images
ground_tile = "ground_tile.png"
wall_tile = "wall_tile.png"
background_img = "background_tile.png"

# ---- Levels ----

LEVEL_1 = [
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..........................................................W",
    "W..............GGGGG........................GGGGG..........W",
    "W..........................................................W",
    "W..........................................................W",
    "W.........GGGG................W...WGGGGGG..................W",
    "W.............................W...W........................W",
    "W.............................W...W........................W",
    "W....GGG......................W...W........................W",
    "W.............................W...W........................W",
    "W.............................W...W........................W",
    "W........GGG..................W...W........................W",
    "W.............................W...W........................W",
    "W.............................W...W........................W",
    "W....GGG..........................W.................GGGG...W",
    "W.................................W........................W",
    "W.P...............................W........................W",
    "WGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG...GGGGGGGGGG....GGGGGGGGG..W",
]

# ---- Logic ----

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = image.get_rect(topleft=(x, y))


def load_level(layout, ground_img, wall_img):
    tiles = pygame.sprite.Group()
    spawn = (0, 0)

    for row, line in enumerate(layout):
        for col, char in enumerate(line):
            x, y = col * Tile_size, row * Tile_size
            if char == "G":
                tiles.add(Tile(x, y, ground_img))
            elif char == "W":
                tiles.add(Tile(x, y, wall_img))
            elif char == "P":
                spawn = (x, y)

    level_width = len(layout[0]) * Tile_size
    level_height = len(layout) * Tile_size
    return tiles, spawn, level_width, level_height


class Camera:
    def __init__(self, level_width, level_height):
        self.x = 0
        self.y = 0
        self.level_width = level_width
        self.level_height = level_height

    def clamp(self, x, y):
        x = max(0, min(x, self.level_width - Width))
        y = max(0, min(y, self.level_height - Height))
        return x, y

    def snap(self, target):
        self.x, self.y = self.clamp(target.centerx - Width // 2, target.centery - Height // 2)

    def update(self, target):
        goal_x, goal_y = self.clamp(target.centerx - Width // 2, target.centery - Height // 2)
        self.x += (goal_x - self.x) * Camera_smooth
        self.y += (goal_y - self.y) * Camera_smooth

    def apply(self, rect):
        return rect.move(-round(self.x), -round(self.y))


# anything to do with the player
class Player(pygame.sprite.Sprite):
    # --- Player ---

    color = (255, 0, 0)  # player color

    def __init__(self, x, y, width, height, tiles):  # INIT self
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)  # creating a rectangle for the player
        self.hitbox = self.rect # creating hitbox for player
        self.tiles = tiles

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

        self.jump_dir = 0
        self.wall_jump_lock = 0

    # --- Movement ---

    def move_and_collide(self):
        self.rect.x += self.xVel

        for t in self.tiles:
            if self.rect.colliderect(t.rect):
                if self.xVel > 0:
                    self.rect.right = t.rect.left
                elif self.xVel < 0:
                    self.rect.left = t.rect.right

        self.rect.y += self.yVel

        for t in self.tiles:
            if self.rect.colliderect(t.rect):
                if self.yVel > 0:
                    if self.yVel > 2:
                        self.scale_x, self.scale_y = Land_scale
                    self.rect.bottom = t.rect.top
                elif self.yVel < 0:
                    self.rect.top = t.rect.bottom
                self.yVel = 0

    def touching(self, dx, dy):
        probe = self.hitbox.move(dx, dy)
        return any(probe.colliderect(t.rect) for t in self.tiles)

    def steer(self, target):
        if self.wall_jump_lock > 0:
            self.xVel += (target - self.xVel) * Air_control

        else:
            self.xVel = target

    def move_left(self):
        self.steer(-Crouch_velocity if self.crouching else -Player_Velocity)

        if self.direction != "left":
            self.direction = "left"
            self.animationcount = 0

    def move_right(self):
        self.steer(Crouch_velocity if self.crouching else Player_Velocity)
        if self.direction != "right":
            self.direction = "right"
            self.animationcount = 0

    # checks if the player is standing on the floor
    def on_ground(self):
        return self.yVel >= 0 and self.touching(0, 1)

    def on_wall_right(self):
        return self.touching(1, 0)

    def on_wall_left(self):
        return self.touching(-1, 0)

    # starts the squash, the actual jump happens in loop
    def jump(self):
        if self.jump_timer > 0:
            return

        if self.on_ground():
            self.jump_dir = 0

        elif self.on_wall_left():
            self.jump_dir = 1

        elif self.on_wall_right():
            self.jump_dir = -1

        else:
            return

        self.jump_timer = Squash_frames


    def crouch(self):
        if not self.crouching:
            bottom = self.rect.bottom
            self.rect.height = self.standing_height // 2
            self.rect.bottom = bottom
            self.crouching = True

    def stand(self):
        if self.crouching:
            standing = pygame.Rect(self.rect.x, self.rect.bottom - self.standing_height, self.rect.width, self.standing_height)
            if any(standing.colliderect(t.rect) for t in self.tiles):
                return

            bottom = self.rect.bottom
            self.rect.height = self.standing_height
            self.rect.bottom = bottom
            self.crouching = False

    def respawn(self, spawn):
        self.rect.topleft = spawn
        self.xVel = 0
        self.yVel = 0
        self.jump_timer = 0
        self.wall_jump_lock = 0

    # updating loop
    def loop(self, Fps):
        target_x, target_y = 1, 1  # normal shape

        if self.wall_jump_lock > 0:
            self.wall_jump_lock -= 1

        # squash before jumping, then launch stretched
        if self.jump_timer > 0:
            self.jump_timer -= 1
            self.scale_x, self.scale_y = Squash_scale

            if self.jump_dir != 0:
                self.yVel = 0

            if self.jump_timer == 0:
                self.yVel = -Jump_velocity

                if self.jump_dir != 0:
                    self.xVel = self.jump_dir * Wall_jump_push
                    self.wall_jump_lock = Wall_jump_lock_frames
                    self.direction = "right" if self.jump_dir > 0 else "left"
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
        self.move_and_collide()


    # draws the player
    def draw(self, win, camera):
        width = int(self.hitbox.width * self.scale_x)
        height = int(self.hitbox.height * self.scale_y)
        visual = pygame.Rect(0, 0, width, height)
        visual.midbottom = camera.apply(self.hitbox).midbottom
        pygame.draw.rect(win, self.color, visual)

# anything background related
def get_background(background_img):
    image = pygame.image.load(background_img)  # load the image
    _, _, width, height = image.get_rect()  # create the tiles for the image
    tiles = []  # create an empty list for tiles

    # load each tiles in grid pattern based on height and width
    for x in range(Width // width + 2):
        for y in range(Height // height + 2):
            pos = [x * width, y * height]
            tiles.append(pos)

    return tiles, image


# draws to the given frame
def draw(window, tiles, image, level_tiles, player, camera):
    offset_x = int(camera.x * Parallax) % image.get_width()
    offset_y = int(camera.y * Parallax) % image.get_height()
    for tile in tiles:
        window.blit(image, (tile[0] - offset_x, tile[1] - offset_y))

    screen = window.get_rect()
    for t in level_tiles:
        pos = camera.apply(t.rect)
        if screen.colliderect(pos):
            window.blit(t.image, pos)

    player.draw(window, camera)

    pygame.display.update()

# checks keys being pressed and moves based on that
def handle_movement(player):
    keys = pygame.key.get_pressed() # creating keys for when a key is pressed

    if player.wall_jump_lock == 0:
        player.xVel = 0

    # moving based on key
    if keys[pygame.K_a] and not keys[pygame.K_d]:
        player.move_left()

    elif keys[pygame.K_d] and not keys[pygame.K_a]:
        player.move_right()

    if keys[pygame.K_w] and not keys[pygame.K_s]:
        player.jump()

    if keys[pygame.K_s] and not keys[pygame.K_w]:
        player.crouch()

    else:
        player.stand()


# Main method
def main(window):
    clock = pygame.time.Clock()  # creates a clock for the game to run off of
    background, image = get_background(background_img)

    ground_img = pygame.image.load(ground_tile).convert_alpha()
    wall_img = pygame.image.load(wall_tile).convert_alpha()
    level_tiles, spawn, level_width, level_height = load_level(LEVEL_1, ground_img, wall_img)

    # INIT player
    player = Player(spawn[0], spawn[1], 32, 32, level_tiles)

    camera = Camera(level_width, level_height)
    camera.snap(player.rect)

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

        if player.rect.top > level_height:
            player.respawn(spawn)
            camera.snap(player.rect)

        camera.update(player.rect)
        draw(window, background, image, level_tiles, player, camera) # calls the drawer for the window

    # quits out
    pygame.quit()
    quit()


if __name__ == '__main__':
    main(window)