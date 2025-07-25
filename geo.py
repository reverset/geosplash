
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 13:32:55 2023

@author: Sea bass
"""

import itertools as itert
from typing import Iterator

from raylib import CheckCollisionRecs, Vector2Divide, Vector2Negate, Vector2Subtract
try:
    from itertools import pairwise
except ImportError:
    print("Implementing custom version of pairwise()")
    def pairwise(iterable):
        for i in range(1, len(iterable)):
            yield (iterable[i-1], iterable[i])


from pyray import *

import math
import random
import sys
import time
import os

# base color is 127, 127, 127

DEBUG_MODE = False

screen_width = 1280
screen_height = 720
screen_mid = [screen_width//2, screen_height//2]

def clamp(val, mi, ma):
    m = min(val, ma)
    m = max(m, mi)

    return m

class Input:
    @staticmethod
    def jump_pressed():
        return is_key_pressed(KeyboardKey(0).KEY_SPACE) or is_key_pressed(KeyboardKey(0).KEY_UP) or is_mouse_button_pressed(0) or is_key_pressed(KeyboardKey(0).KEY_W)
    
    @staticmethod
    def jump_released():
        return is_key_released(KeyboardKey(0).KEY_SPACE) or is_key_released(KeyboardKey(0).KEY_UP) or is_mouse_button_released(0) or is_key_released(KeyboardKey(0).KEY_W)

    @staticmethod
    def jump_down():
        return is_key_down(KeyboardKey(0).KEY_SPACE) or is_key_down(KeyboardKey(0).KEY_UP) or is_mouse_button_down(0) or is_key_down(KeyboardKey(0).KEY_W)
    
    @staticmethod
    def right_pressed():
        return is_key_pressed(KeyboardKey(0).KEY_RIGHT) or is_key_pressed(KeyboardKey(0).KEY_D)
    
    @staticmethod
    def left_pressed():
        return is_key_pressed(KeyboardKey(0).KEY_LEFT) or is_key_pressed(KeyboardKey(0).KEY_A)

    @staticmethod
    def reset_level():
        return is_key_pressed(KeyboardKey(0).KEY_R)
    
class Vec2i:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    
    def to_raylib(self):
        return Vector2(self.x, self.y)

class VecMath:
    @staticmethod
    def add(v1, v2):
        return Vector2(v1.x + v2.x, v1.y + v2.y)
    
    @staticmethod
    def sub(v1, v2):
        return Vector2(v1.x - v2.x, v1.y - v2.y)
    
    @staticmethod
    def mul(v1, v2):    
        return Vector2(v1.x * v2.x, v1.y * v2.y)
    
    @staticmethod
    def floor(v1):
        return Vector2(math.floor(v1.x), math.floor(v1.y))
    
    @staticmethod
    def int(v1):
        return Vector2(int(v1.x), int(v1.y))
    
    @staticmethod
    def floor_i(v1):
        return Vec2i(v1.x, v1.y)
    
    @staticmethod
    def distance(v1, v2):
        x_dist = abs(v1.x - v2.x)
        y_dist = abs(v1.y - v2.y)
        return math.sqrt((x_dist ** 2) + (y_dist ** 2))

    @staticmethod
    def lerp(v1, v2, dt):
        return Vector2(lerp(v1.x, v2.x, dt), lerp(v1.y, v2.y, dt))

    @staticmethod
    def abs(v1):
        return Vector2(abs(v1.x), abs(v1.y))

class Rect:
    def __init__(self, position, dimension):
        self.position = position
        self.dimension = dimension
    
    def clone(self):
        return Rect(clone_vec(self.position), clone_vec(self.dimension))
    
    def vertices(self):
        up_left = clone_vec(self.position)
        up_right = VecMath.add(self.position, Vector2(self.dimension.x, 0))
        bot_right = VecMath.add(self.position, Vector2(self.dimension.x, self.dimension.y))
        bot_left = VecMath.add(self.position, Vector2(0, self.dimension.y))
        
        return [up_left, up_right, bot_left, bot_right]
    
    def check_collision_with_point(rec, point): # Why 'rec' and not 'self'? I have no clue what i was thinking here.
        v = rec.vertices()
        up_left, up_right, bot_left, bot_right = v[0], v[1], v[2], v[3]
        if up_left.x <= point.x <= bot_right.x:
            if up_left.y <= point.y <= bot_left.y:
                return True
        return False

    def to_raylib(self):
        return Rectangle(
            self.position.x,
            self.position.y,
            self.dimension.x,
            self.dimension.y
        )

    def check_collision_with_rect(self, other_rect): # I should just use raylib functions for the other methods, oh well the more you know.
        my_rect = self.to_raylib()
        other_rec = other_rect.to_raylib()
        return CheckCollisionRecs(my_rect, other_rec)

    def __repr__(self):
        return f"Rect(pos=V2({self.position.x}, {self.position.y}), dim=V2({self.dimension.x}, {self.dimension.y}))"

class RaylibImage:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = None
    
    def __enter__(self):
        self.image = load_image(self.image_path)
        return self.image

    def __exit__(self, *args):
        if self.image is not None:
            unload_image(self.image)
            self.image = None

def clone_vec(vec):
    return Vector2(vec.x, vec.y)

class GameObj:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.area = None # Area should be of type Rect
        self.always_think = False
        self.rotation = 0
        self.origin = None

        self._predrawed = False
    
    def clone(self):
        raise RuntimeError(f"Clone not supported for '{self.__class__}'")

    def manifested(self):
        pass
    
    def logic(self):
        pass

    def predraw(self):
        if self.origin == None:
            return
        rl_push_matrix()
        rl_translatef(self.origin.x, self.origin.y, 0)
        rl_rotatef(self.rotation, 0, 0, -1)
        rl_translatef(-self.origin.x, -self.origin.y, 0)
        self._predrawed = True
    
    def postdraw(self):
        if self._predrawed:
            rl_pop_matrix()
    
    def draw(self):
        pass
    
    def is_ui_element(self):
        return False

    def ui_draw(self):
        pass

    def get_tag(self):
        return ""
    
    def destroyed(self):
        pass

class Game:
    def __init__(self):
        self.game_objects = []
        self.should_end = False
        self.level = None
        self.player = None
        self.deferred = []
        self.camera = None
        self.editor_mode = False
        self.background = None

        self.frozen_cam = None
        self.frozen_y_cam = None
    
    def freeze_cam(self, where):
        self.frozen_cam = where
    
    def reset_cam(self):
        self.frozen_cam = None
        self.frozen_y_cam = None
    
    def freeze_y_cam(self, y_val):
        self.frozen_y_cam = y_val

    def reset_rot(self):
        rl_pop_matrix()
    
    def is_editor_mode(self):
        return self.editor_mode
    
    def set_editor_mode(self, m):
        self.editor_mode = m

    def calc_rot(self, rot, origin):
        rl_push_matrix()
        rl_translatef(origin.x, origin.y, 0)
        rl_rotatef(rot, 0, 0, -1)
        rl_translatef(-origin.x, -origin.y, 0)

    def get_cam(self):
        return self.camera
    
    def defer(self, method):
        self.deferred.append(method)
    
    def _call_deferred(self):
        for i in range(len(self.deferred)-1, -1, -1):
            self.deferred[i]()
            self.deferred.pop(i)
    
    def set_level(self, lvl):
        self.reset()
        self.level = lvl
        self.make(lvl.get())
        if self.get_player() is not None:
            if self.get_player().orientation == -1:
                self.get_player().flip_gravity()
    
    def reload_level(self):
        assert self.level != None, "Attempted to reload level that is not loaded to begin with."
        self.set_level(self.level)
    
    def get_level(self):
        return self.level
    
    def stop(self):
        self.should_end = True
        
    def make(self, objects):
        assert type(objects) is list, "make() method takes a list of game objects"
        for i in objects:
            self.game_objects.append(i)
        for i in objects: # Why? incase an object relies on the existence of another
            i.manifested()
    
    def destroy(self, objs):
        assert type(objs) is list, "destroy() method takes a list of game objects"
        for i in objs:
            i.destroyed()
            self.game_objects.remove(i)
    
    def get_player(self):
        if self.player == None:
            self.player = self.find_by_tag("Player")
        return self.player
    
    def reset(self):
        self.player = None
        self.background = None
        for obj in self.game_objects[:]:
            obj.destroyed()

        self.game_objects.clear()
        get_game().reset_cam()
    
    def find_by_tag(self, name):
        for i in self.game_objects:
            if i.get_tag() == name:
                return i
        return None

    def find_many_by_tag(self, name):
        objs = []
        for i in self.game_objects:
            if i.get_tag() == name:
                objs.append(i)

        return objs

class Level:
    CACHED_LEVEL = (None, None)

    def __init__(self, name, func):
        self.name = name.strip()
        self.func = func
        self.cached = None

    @staticmethod
    def from_file(file):
        if file == Level.CACHED_LEVEL[0]:
            print("Level loaded from file cache!")
            return Level.CACHED_LEVEL[1]
        
        def level_data():
            print("Loading level from file ...")
            with open(file, "r") as f: # should probably only do this when the level data is actually requested
                lines = f.readlines()
                
                name = lines[0]
                code = lines[1]

                c = eval(code) # yes I know this is a vulnerability, I'm not going to fix it since this is just a big test.
                Level.CACHED_LEVEL = (file, Level(name, lambda: eval(code)))
                return c
            
        with open(file, "r") as f:
            name = f.readline()
            l = Level(name, level_data)
        return l

    def get(self):
        return self.func()

_attempts = 0
class AttemptCounter(GameObj):
    def __init__(self, position):
        super().__init__()
        self.position = position
    
    def draw(self):
        global _attempts
        
        p = VecMath.floor_i(self.position)
        draw_text("Attempt #" + repr(_attempts), p.x, p.y, 48, BLACK)

class Player(GameObj):
    COLOR = BLUE

    WIDTH = 50
    HEIGHT = 50
    GRAVITY = 1
    AREA_DIM = Vector2(WIDTH, HEIGHT)

    SHIP_WIDTH = 40
    SHIP_HEIGHT = 20
    SHIP_CLIMB_SPEED = 0.92
    SHIP_GRAVITY = 0.4

    BALL_SIZE = 30

    WAVE_COLOR = DARKBLUE
    WAVE_THICKNESS = 15
    WAVE_AREA_DIM = Vector2(WIDTH//2, HEIGHT//2)

    ROTATE_SPEED = 7


    CUBE_SPRITE_PATH = "./textures/player/cubes/default.png"
    _CUBE_SPRITE = None

    SHIP_SPRITE_PATH = "./textures/player/ships/default.png"
    _SHIP_SPRITE = None
    _SHIP_SPITE_FLIPPED_V = None

    BALL_SPRITE_PATH = "./textures/player/circles/default.png"
    _BALL_SPRITE = None

    @staticmethod
    def get_cube_sprite():
        if Player._CUBE_SPRITE is None:
            with RaylibImage(Player.CUBE_SPRITE_PATH) as image:
                image_resize_nn(image, Player.WIDTH, Player.HEIGHT)
                Player._CUBE_SPRITE = load_texture_from_image(image) 
                # but wait you never unload the player texture! Is it really necessary though? The player always exists.
        
        return Player._CUBE_SPRITE

    @staticmethod
    def get_ship_sprite(orientation):
        if Player._SHIP_SPRITE is None or Player._SHIP_SPITE_FLIPPED_V is None:
            with RaylibImage(Player.SHIP_SPRITE_PATH) as image:
                with RaylibImage(Player.CUBE_SPRITE_PATH) as cube_image:
                    image_resize_nn(image, Player.SHIP_WIDTH*2, Player.SHIP_HEIGHT*4)

                    image_resize_nn(cube_image, Player.WIDTH//2, Player.HEIGHT//2)
                    image_draw(image, cube_image, Rectangle(0, 0, cube_image.width, cube_image.height), Rectangle(20, 5, cube_image.width, cube_image.height), WHITE)

                    Player._SHIP_SPRITE = load_texture_from_image(image)

                    image_flip_vertical(image)
                    Player._SHIP_SPITE_FLIPPED_V = load_texture_from_image(image)
        
        if orientation == 1:
            return Player._SHIP_SPRITE
        else:
            return Player._SHIP_SPITE_FLIPPED_V
    
    @staticmethod
    def get_ball_sprite():
        if Player._BALL_SPRITE is None:
            with RaylibImage(Player.BALL_SPRITE_PATH) as image:
                image_resize_nn(image, Player.BALL_SIZE * 2, Player.BALL_SIZE *2)

                Player._BALL_SPRITE = load_texture_from_image(image)
        
        return Player._BALL_SPRITE

    def __repr__(self):
        return f"Player(Vector2({self.position.x}, {self.position.y}))"

    def clone(self):
        return Player(clone_vec(self.start_pos))
    
    def set_mode(self, mode):
        self.wave_points = []
        if mode not in self.modes:
            raise RuntimeError(f"Attempted to switch to mode '{mode}', which does not exist")
        self.current_mode = mode
        self.rotation = 0

        if self.current_mode == "wave":
            self.wave_points.append(clone_vec(self.position))
            self.area = Rect(
                self.position,
                Player.WAVE_AREA_DIM
            )
        else:
            self.area = Rect(
                self.position,
                Player.AREA_DIM
            )

    def __init__(self, start_pos = Vector2(-400, 0)):
        super().__init__()

        self.modes = {
            "square": (self.square_logic, self.square_draw),
            "ship": (self.ship_logic, self.ship_draw),
            "ball": (self.ball_logic, self.ball_draw),
            "wave": (self.wave_logic, self.wave_draw)
        }

        self.current_mode = "square"

        self.start_pos = clone_vec(start_pos)
        self.position = start_pos
        self.dead = False
        self.area = Rect(
                self.position,
                Vector2(Player.WIDTH, Player.HEIGHT)
            )
        
        self.velocity = Vector2(0, 0)

        self.tappedOrb = False
        
        self.wantJump = False
        self.grounded = False
        self.grounded_y = Ground.ALTITUDE
        self.orientation = 1

        self.halted = False

        self.ball_can_jump = True
        self.wave_points = []

        self.horizontal_speed = 5.5
        
    
    def manifested(self):
        get_game().make([AttemptCounter(clone_vec(self.position))])

    def halt(self):
        self.halted = True
        self.area = None

    def flip_gravity(self):
        if self.orientation == 1:
            self.orientation = -1
            self.grounded_y = Ground.REVERSE_ALTITUDE
        else:
            self.orientation = 1
            self.grounded_y = Ground.ALTITUDE
    
    def kill(self, reason):
        if self.halted: return
        if self.dead: return

        global _attempts
        _attempts += 1
        print("Killed by " + reason)

        self.dead = True
        self.area = None
        
        part = Particle(30)
        get_game().make([part])
        part.emit( clone_vec(self.position) ) # CLONE POSITION VECTORS OR BAD STUFF HAPPENS
        
        timer = TimerObj(1, lambda: get_game().reload_level())
        get_game().make([timer])
        timer.start()

    def get_tag(self):
        return "Player"
    
    def predraw(self):
        self.origin = Vector2( self.position.x + (Player.WIDTH * 0.5), self.position.y + (Player.HEIGHT * 0.5) )
        super().predraw()
    
    def postdraw(self):
        super().postdraw()

        if self.current_mode == "wave":
            last = self.wave_points[0]
            for (p1, p2) in pairwise(self.wave_points):
                draw_line_ex(p1, p2, Player.WAVE_THICKNESS, Player.WAVE_COLOR)
                if p2 is None:
                    last = clone_vec(p1)
                else:
                    last = clone_vec(p2)
            
            if self.wantJump:
                if self.orientation == 1:
                    draw_line_ex(last, VecMath.add(self.position, Vector2(0, Player.HEIGHT)), Player.WAVE_THICKNESS, Player.WAVE_COLOR)
                else:
                    draw_line_ex(last, self.position, Player.WAVE_THICKNESS, Player.WAVE_COLOR)
            else:
                if self.orientation == 1:
                    draw_line_ex(last, self.position, Player.WAVE_THICKNESS, Player.WAVE_COLOR)
                else:
                    draw_line_ex(last, VecMath.add(self.position, Vector2(0, Player.HEIGHT)), Player.WAVE_THICKNESS, Player.WAVE_COLOR)

        if DEBUG_MODE and self.area is not None:
            p = VecMath.floor_i(self.area.position)
            d = VecMath.floor_i(self.area.dimension)
            draw_rectangle_lines(p.x, p.y, d.x+1, d.y+1, RED)
    
    def square_logic(self):
        self._fall(Player.GRAVITY)
        self._square_handle_rotation()

        if self.wantJump and self.grounded:
            self.position.y -= 5 * self.orientation
            self.grounded = False
            self.velocity.y = -15 * self.orientation

    def ship_logic(self):
        self._fall(Player.SHIP_GRAVITY)
        self._ship_handle_rotation()

        if self.wantJump:
            self.velocity.y -= Player.SHIP_CLIMB_SPEED * self.orientation

            if self.grounded:
                self.grounded = False
    
    def ball_logic(self):
        self._fall(Player.GRAVITY)
        self._ball_handle_rotation()

        if self.wantJump and self.ball_can_jump and self.grounded:
            self.ball_can_jump = False
            self.flip_gravity()
            self.position.y += 5 * self.orientation
            self.velocity.y += 5 * self.orientation
        
        if Input.jump_released():
            self.ball_can_jump = True
    
    def wave_add_point(self):
        self.wave_points.append(clone_vec(self.position))
    
    def wave_add_point_offset(self):
        self.wave_points.append(VecMath.add(self.position, Vector2(0, Player.HEIGHT)))

    def wave_logic(self):
        if not self.dead and self.position.y > Ground.ALTITUDE - 50:
            self.position.y = Ground.ALTITUDE - 51

        if Input.jump_released():
            if self.orientation == 1:
                self.wave_add_point()
            else:
                self.wave_add_point_offset()
        elif Input.jump_pressed():
            if self.orientation == 1:
                self.wave_add_point_offset()
            else:
                self.wave_add_point()

        if self.wantJump:
            self.velocity.y = -self.horizontal_speed * self.orientation
            self.rotation = -45 if self.orientation == 1 else -135
        else:
            self.velocity.y = self.horizontal_speed * self.orientation
            self.rotation = -135 if self.orientation == 1 else -45

    def logic(self):
        if self.dead: return
        if self.halted: return
        
        if is_key_released(KeyboardKey(0).KEY_ESCAPE):
            if (preview := get_game().find_by_tag("Preview")) is not None:
                preview.return_to_editor()
            else:
                get_game().defer(lambda: get_game().set_level(LevelSelectScreen()))

        self.velocity.x = self.horizontal_speed
        self._act_on_input()
        
        self.modes[self.current_mode][0]()
        
        if not self.dead:
            self._update_velocity()
            
            desired_area_pos = self.position
            if self.current_mode == "wave":
                desired_area_pos = VecMath.add(self.position, Vector2(Player.WIDTH//4, Player.WIDTH//4))
            self.area.position = desired_area_pos # ensure that hitbox is adjusted to the visible position, can NOT clone the vector here because of timing & pointers 
        
        
    def _act_on_input(self):
        if Input.jump_down():
           self.wantJump = True
        else:
            self.wantJump = False
            self.tappedOrb = False
        
        if Input.reset_level():
            global _attempts
            _attempts += 1
            get_game().reload_level()
    
    @staticmethod
    def _closer(n, options):
        closest = None
        close_value = sys.maxsize
        for i in options:
            if abs(n - i) < close_value:
                closest = i
                close_value = abs(n - i)
        return closest
    
    def _square_handle_rotation(self):
        if not self.grounded:
            if self.rotation >= 360:
                self.rotation = 0
            elif self.rotation <= -360:
                self.rotation = 0

            self.rotation -= Player.ROTATE_SPEED * self.orientation
        elif not Input.jump_down():
            closest = self._closer(self.rotation, [0, 90, 180, 270, -90, -180, -270])
            self.rotation = lerp(self.rotation, closest, 0.6)
    
    def _ship_handle_rotation(self):
        self.rotation = -self.velocity.y * 3
    
    def _ball_handle_rotation(self):
        if self.grounded:
            self.rotation -= self.horizontal_speed * self.orientation
    
    def _update_velocity(self):
        self.velocity.y = clamp(self.velocity.y, -20, 20)
        self.position = VecMath.add(self.position, self.velocity)
        
    def _fall(self, gravity):
        self.velocity.y += gravity * self.orientation
        
        if self.orientation == 1:
            if self.position.y + Player.HEIGHT >= self.grounded_y:
                self.velocity.y = 0
                self.grounded = True
                self.position.y = self.grounded_y - Player.HEIGHT
            else:
                self.grounded = False
        else: # lots of repetition but whatever
            if self.position.y <= self.grounded_y:
                self.velocity.y = 0
                self.grounded = True
                self.position.y = self.grounded_y
            else:
                self.grounded = False
        
    def square_draw(self):
        pos = VecMath.floor_i(self.position)
        draw_texture(Player.get_cube_sprite(), pos.x, pos.y, Player.COLOR)
    
    def ship_draw(self):
        pos = VecMath.floor_i(self.position)
        pos.x -= Player.WIDTH//4
        pos.y -= Player.HEIGHT//4

        draw_texture(Player.get_ship_sprite(self.orientation), pos.x, pos.y, Player.COLOR)

    def ball_draw(self):
        pos = clone_vec(self.position)
        pos = VecMath.sub(pos, Vector2(Player.BALL_SIZE//6, Player.BALL_SIZE//6))
        pos = VecMath.floor_i(pos)

        draw_texture(Player.get_ball_sprite(), pos.x, pos.y, Player.COLOR)
    
    def wave_draw(self):
        pos = VecMath.add(self.position, Vector2(Player.WIDTH//2, Player.HEIGHT))

        top = VecMath.sub(pos, Vector2(0, Spike.HEIGHT))
        left = VecMath.add(top, Vector2(-Spike.MID, Spike.HEIGHT))
        right = VecMath.add(top, Vector2(Spike.MID, Spike.HEIGHT))
        
        draw_triangle(
            top,
            left,
            right,
            Player.COLOR
        )

    def draw(self):
        if self.dead: return
        self.modes[self.current_mode][1]()

class Ground(GameObj):
    ALTITUDE = 300
    REVERSE_ALTITUDE = -10_000

    def __repr__(self):
        return "Ground()"
    
    def get_tag(self):
        return "Ground"

    def clone(self):
        return Ground()

    def __init__(self):
        super().__init__()
        self.position.y = Ground.ALTITUDE
        self.always_think = True
        self.player = None
    
    def manifested(self):
        self.player = get_game().find_by_tag("Player")
    
    def logic(self):
        if self.player is not None:
            if not self.player.dead and self.player.position.y <= -10_000:
               self.player.kill("excessive height")
            if self.player.orientation == 1:
                self.player.grounded_y = self.position.y
            else:
                if not self.player.dead and self.player.position.y+Player.HEIGHT > Ground.ALTITUDE:
                    self.player.kill("Ground")
                self.player.grounded_y = Ground.REVERSE_ALTITUDE
        self.position.x = get_game().get_cam().target.x - 1_000
    
    def draw(self):
        pos = VecMath.floor_i(self.position)
        draw_rectangle(pos.x, pos.y, 2_000, 150, GRAY)

game = None
def get_game():
    return game
    
class Spike(GameObj):
    WIDTH = 50
    HEIGHT = 50
    MID = 25

    def clone(self):
        return Spike(self.start_pos, self.start_rot)
    
    def __repr__(self):
        return f"Spike(Vector2({self.position.x}, {self.position.y}), {self.rotation})"

    def __init__(self, position, rotation=0):
        super().__init__()
        self.start_pos = clone_vec(position)
        self.start_rot = rotation

        self.position = position

        self.origin = Vector2(self.position.x, self.position.y - Player.HEIGHT * 0.5)
        self.rotation = rotation

        desired_pos = VecMath.sub(self.position, Vector2(5, 30))
        if rotation == 180:
            desired_pos.y -= Spike.MID-5
            
        self.area = Rect(
            desired_pos,
            Vector2(10, 30)
        )
        self.player = None
    
    def manifested(self):
        self.player = get_game().find_by_tag("Player")
    
    def logic(self):
        if self.player is None: return
        if self.player.dead:
            return
        player_area = self.player.area
        if player_area is None: return

        for vert in self.area.vertices():
            if Rect.check_collision_with_point(player_area, vert):
                self.player.kill("Spike")
                break
    
    def draw(self):
        #draw_triangle(
        #    Vector2(50, 0), # MID POINT
        #    Vector2(-100, 100), # LEFT
        #    Vector2(100, 100), # RIGHT
        #    GREEN # COLOR
        #)
        
        
        top = VecMath.sub(self.position, Vector2(0, Spike.HEIGHT))
        left = VecMath.add(top, Vector2(-Spike.MID, Spike.HEIGHT))
        right = VecMath.add(top, Vector2(Spike.MID, Spike.HEIGHT))
        
        draw_triangle(
            top,
            left,
            right,
            RED
        )
    
    def postdraw(self):
        super().postdraw()

        # collision shape DEBUGGING
        if DEBUG_MODE:
            pos = VecMath.floor_i(self.area.position)
            dim = VecMath.floor_i(self.area.dimension)
            
            draw_rectangle_lines(pos.x, pos.y, dim.x, dim.y, BLACK)
class Tile(GameObj):

    def clone(self):
        return Tile(clone_vec(self.position), clone_vec(self.dim))

    def __repr__(self):
        return f"Tile(Vector2({self.position.x}, {self.position.y}), Vector2({self.dim.x}, {self.dim.y}))"

    def __init__(self, pos, dim):
        super().__init__()
        self.position = pos
        self.dim = dim
        self.area = Rect(
            self.position, self.dim
        )
        self.player = None
    
    def manifested(self):
        self.player = get_game().get_player()
    
    def logic(self):
        if self.player == None or self.player.area == None:
            return
        
        bump = 0
        verts = self.player.area.vertices()
        if self.player.orientation == 1:
            rel_verts = verts[2:4]
            top_verts = verts[:2]
        else:
            rel_verts = verts[:2]
            top_verts = verts[2:4]

        for i in verts:
            touching = self.area.check_collision_with_point(i)
            ground_threshold = 25
            
            if touching:
                if self.player.current_mode == "wave":
                    self.player.kill("slammed on Tile")
                    break

                if i in top_verts:
                    if self.player.current_mode == "ship":
                        self.player.velocity.y = 1 * self.player.orientation
                    else:
                        self.player.kill("bonked on Tile")
                    continue
                if self.player.orientation == 1:
                    if i.y < self.position.y + ground_threshold:
                        self.player.grounded_y = self.area.position.y + bump
                    else:
                        self.player.kill("side of Tile")
                    break
                else:
                    bump = self.area.dimension.y
                    if i.y > (self.position.y + bump) + (ground_threshold * -1):
                        self.player.grounded_y = self.area.position.y + bump
                    else: # hit side of tile
                        self.player.kill("side of Tile")
                    break
                
    
    def draw(self):
        v = VecMath.floor_i(self.position)
        di = VecMath.floor_i(self.dim)
        
        draw_rectangle(v.x, v.y, di.x, di.y, DARKGRAY)
        if DEBUG_MODE:
            p = self.area.position
            d = self.area.dimension
            
            p = VecMath.floor_i(p)
            d = VecMath.floor_i(d)
            draw_rectangle_lines(p.x, p.y, d.x, d.y, RED)

class Slope(GameObj):
    MID = 25

    def clone(self):
        return Slope(clone_vec(self.position), self.rotation)

    def __repr__(self):
        return f"Slope(Vector2({self.position.x}, {self.position.y}), {self.rotation})"

    def __init__(self, pos, rot):
        super().__init__()
        self.position = pos
        self.rotation = rot
        self.origin = VecMath.add(self.position, Vector2(Slope.MID, Slope.MID))

        self.area = Rect(
            self.position,
            Vector2(50, 50)
        )
        self.player = None
    
    def manifested(self):
        self.player = get_game().get_player()
    
    def logic(self):
        if self.player == None or self.player.area == None:
            return
        
        bump = 0
        verts = self.player.area.vertices()
        if self.player.orientation == 1:
            rel_verts = verts[2:4]
            top_verts = verts[:2]
        else:
            rel_verts = verts[:2]
            top_verts = verts[2:4]

        for i in verts:
            touching = self.area.check_collision_with_point(i)
            ground_threshold = 25
            
            if touching:
                
                # i have no clue what's happening here either.
                if i in rel_verts:
                    if self.player.orientation == 1:
                        if self.rotation == 0:
                            self.player.grounded_y = self.position.y + (abs(self.position.x - self.player.position.x)) - 5
                            if self.player.grounded:
                                self.player.position.y -= 10
                                self.player.velocity.y = -10
                        else:
                            self.player.grounded_y = (self.position.y - (self.position.x - self.player.position.x)) + Player.HEIGHT//2
                    else:
                        if self.rotation == 90:
                            self.player.grounded_y = (self.position.y - (self.position.x - self.player.position.x)) + Player.HEIGHT
                            if self.player.grounded:
                                self.player.position.y += 10
                                self.player.velocity.y = 10
                        else:
                            self.player.grounded_y = self.position.y - (abs(self.position.x - self.player.position.x)) + Player.HEIGHT

                if self.player.current_mode == "wave":
                    if self.player.orientation == 1 and self.player.position.y > self.player.grounded_y:
                        self.player.kill("slope")
                    elif self.player.orientation == -1 and self.player.position.y < self.player.grounded_y:
                        self.player.kill("slope")
                
    
    def draw(self):
        v = VecMath.floor_i(VecMath.add(self.position, Vector2(0, 50)))
        
        draw_triangle_strip((v.to_raylib(), VecMath.int(VecMath.add(v, Vector2(50, 0))), VecMath.int(VecMath.add(v, Vector2(50, -50)))), 3, DARKGRAY)
    
    def postdraw(self):
        super().postdraw()
        if DEBUG_MODE:
            p = self.area.position
            d = self.area.dimension
            
            p = VecMath.floor_i(p)
            d = VecMath.floor_i(d)
            draw_rectangle_lines(p.x, p.y, d.x, d.y, RED)

class DebrisPart:
    def __init__(self, pos, direction):
        self.position = pos
        self.direction = direction

class Particle(GameObj):
    def __init__(self, debris):
        super().__init__()
        self.ready = False
        
        self.color = BLUE
        self.dir_x = 1

        self.debris = debris
        self.start_time = 0
        self.parts = []
    
    def emit(self, where):
        self.position = where
        self.start_time = get_time()
        
        for i in range(self.debris):
            desired_dir = Vector2(random.random() * 10 * self.dir_x, random.random() * 10)
            self.parts.append(DebrisPart( clone_vec(self.position), desired_dir ))
        
        self.ready = True
    
    def elapsed(self):
        return get_time() - self.start_time
    
    def draw(self):
        if self.ready:
            for i in self.parts:
                v = VecMath.floor_i(i.position)
                draw_rectangle(v.x, v.y, 10, 10, self.color)
                
                i.position = VecMath.add(i.position, i.direction)

class TimerObj(GameObj):
    def __init__(self, duration, call_back):
        super().__init__()
        self.start_time = get_time()
        self.duration = duration
        self.call_back = call_back
        self.started = False
        self.finished = False
        self.always_think = True
    
    def start(self):
        self.start_time = get_time()
        self.started = True
    
    def logic(self):
        if self.started and not self.finished:
            if get_time() >= self.start_time + self.duration:
                self.finished = True
                def try_destroy():
                    try:
                        get_game().destroy([self])
                    except ValueError:
                        pass
                get_game().defer(try_destroy)
                self.call_back()

class Orb(GameObj):

    RADIUS = 15

    def clone(self):
        return type(self)(self.position)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(Vector2({self.position.x}, {self.position.y}))"

    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.radius = Orb.RADIUS
        self.color = Color(255, 255, 255, 255)
        self.border_color = Color(0, 0, 0, 255)
        self.player = None
        self.already_tapped = False

        self.area = Rect(
            clone_vec(self.position),
            Vector2(Orb.RADIUS/2, Orb.RADIUS/2)
        )
    
    def tapped(self):
        pass
    
    def manifested(self):
        self.player = get_game().get_player()
    
    def _center_player(self):
        return Vector2( self.player.position.x + Player.WIDTH*0.5, self.player.position.y + Player.HEIGHT*0.5)
    
    def logic(self):
        if self.already_tapped: return
        if self.player is None: return
        
        if not self.player.tappedOrb and Input.jump_down():
            if VecMath.distance(self._center_player(), self.position) <= self.radius + Player.WIDTH:
                self.already_tapped = True
                self.player.tappedOrb = True
                self.tapped()
    
    def draw(self):
        p = VecMath.floor_i(self.position)
        
        draw_circle(p.x, p.y, self.radius, self.color)
        draw_circle_lines(p.x, p.y, self.radius+1, self.border_color)

class JumpOrb(Orb):
    STRENGTH = -22
    
    COLOR = Color(255, 255, 0, 255)
    BORDER_COLOR = Color(255, 165, 0, 255)

    def __init__(self, pos):
        super().__init__(pos)
        self.color = JumpOrb.COLOR
        self.border_color = JumpOrb.BORDER_COLOR
    
    def tapped(self):
        get_game().get_player().velocity.y = JumpOrb.STRENGTH * get_game().get_player().orientation

class GravityOrb(Orb):
    STRENGTH = 18

    COLOR = BLUE
    BORDER_COLOR = DARKBLUE

    def __init__(self, pos):
        super().__init__(pos)
        self.color = BLUE
        self.border_color = DARKBLUE
    
    def tapped(self):
        player = get_game().get_player()
        
        player.flip_gravity()
        player.velocity.y = GravityOrb.STRENGTH * player.orientation

class Pad(GameObj):
    WIDTH = 50
    HEIGHT = 10

    def clone(self):
        return type(self)(self.position)

    def __repr__(self):
        return f"{self.__class__.__name__}(Vector2({self.position.x}, {self.position.y}))"
    
    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.color = Color(0,0,0,255)
        self.already_touched = False
        self.player = None
        
        self.area = Rect(
            clone_vec(self.position),
            Vector2(Pad.WIDTH, Pad.HEIGHT)
        )
    
    def manifested(self):
        self.player = get_game().get_player()
    
    def draw(self):
        p = VecMath.floor_i(self.position)
        draw_rectangle(p.x, p.y, Pad.WIDTH, Pad.HEIGHT, self.color)
        
    def logic(self):
        if self.already_touched: return
        if self.player is None or self.player.area is None: return
        
        if self.area.check_collision_with_rect(self.player.area):
            self.already_touched = True
            self.activate()
            
    def activate(self):
        pass

class JumpPad(Pad):
    COLOR = YELLOW

    def __repr__(self):
        return f"JumpPad(Vector2({self.position.x}, {self.position.y}))"

    def __init__(self, pos):
        super().__init__(pos)
        self.color = JumpPad.COLOR
    
    def activate(self):
        player = get_game().get_player()
        
        player.position.y = self.position.y - (60 * player.orientation)
        # player.position.y -= 10 * player.orientation
        player.velocity.y = JumpOrb.STRENGTH * player.orientation

class GravityPad(Pad):
    COLOR = BLUE

    def __repr__(self):
        return f"GravityPad(Vector2({self.position.x}, {self.position.y}))"

    def __init__(self, pos):
        super().__init__(pos)
        self.color = GravityPad.COLOR
    
    def activate(self):
        player = get_game().get_player()
        
        player.position.y -= 20 * player.orientation
        player.flip_gravity()
        player.velocity.y = GravityOrb.STRENGTH * player.orientation

class Trigger(GameObj):
    RADIUS = 10

    def __repr__(self):
        return f"{self.__class__.__name__}(Vector2({self.position.x}, {self.position.y}))"
    
    def clone(self):
        return type(self)(clone_vec(self.position))
    
    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.color = BLACK
        self.label = "Trigger"

        self.area = Rect(
            clone_vec(self.position),
            Vector2(10, 10)
        )

        self._already_activated = False
    
    def logic(self):
        if self._already_activated: return
        if (player := get_game().get_player()) is None: return
        
        if player.position.x >= self.position.x:
            self.activate()
            self._already_activated = True
    
    def draw(self):
        if not get_game().is_editor_mode(): return
        pos = VecMath.floor(self.position)

        draw_poly(pos, 5, Trigger.RADIUS, 0, self.color)
        draw_text(self.label, int(pos.x-measure_text(self.label, 14)//2), int(pos.y), 14, WHITE)
    
    def activate(self):
        pass

class CameraResetTrigger(Trigger):
    COLOR = BLACK

    def __init__(self, pos):
        super().__init__(pos)
        self.color = CameraResetTrigger.COLOR
        self.label = "Camera Reset"
    
    def activate(self):
        get_game().reset_cam()

class CameraStaticTrigger(Trigger):
    COLOR = BLUE

    def __repr__(self):
        return f"CameraStaticTrigger(Vector2({self.position.x}, {self.position.y}), Vector2({self.where_to.x}, {self.where_to.y}))"

    def clone(self):
        return CameraStaticTrigger(clone_vec(self.position), clone_vec(self.where_to))

    def __init__(self, pos, where_to):
        super().__init__(pos)
        self.where_to = where_to
        self.color = CameraStaticTrigger.COLOR
        self.label = "Camera Static"
    
    def draw(self):
        super().draw()
        if get_game().is_editor_mode():
            draw_line_v(VecMath.int(self.position), VecMath.int(self.where_to), GREEN)
    
    def activate(self):
        get_game().freeze_cam(clone_vec(self.where_to))

class CameraYTrigger(Trigger):
    COLOR = RED

    def __repr__(self):
        return f"CameraYTrigger(Vector2({self.position.x}, {self.position.y}), {self.where_y})"

    def clone(self):
        return CameraYTrigger(clone_vec(self.position), self.where_y)

    def __init__(self, pos, where_y):
        super().__init__(pos)
        self.where_y = where_y
        self.color = CameraYTrigger.COLOR
        self.label = "Camera Y"
    
    def draw(self):
        super().draw()
        if get_game().is_editor_mode():
            draw_line_v(VecMath.int(self.position), VecMath.int(Vector2(self.position.x, self.where_y)), GREEN)
    
    def activate(self):
        get_game().freeze_cam(None)
        get_game().freeze_y_cam(self.where_y)

class BackgroundChangeTrigger(Trigger):
    COLOR = ORANGE

    def __repr__(self):
        return f"BackgroundChangeTrigger(Vector2({self.position.x}, {self.position.y}), {self.background_id})"

    def clone(self):
        return BackgroundChangeTrigger(clone_vec(self.position), self.background_id)
    
    def __init__(self, pos, background_id):
        super().__init__(pos)
        self.color = BackgroundChangeTrigger.COLOR
        self.label = "Background Change"
        self.background_id = background_id
    
    def draw(self):
        super().draw()
        if get_game().is_editor_mode():
            draw_text(f"background: {self.background_id}", int(self.position.x + 10), int(self.position.y - 10), 12, GREEN)
    
    def activate(self):
        back = BackgroundLoader.path_from_id(self.background_id)
        if back is not None:
            get_game().background = Background(back, int(self.position.x), parallax_speed=0.1, fade=True)
        else:
            get_game().background = None


class WinWall(GameObj):

    WIDTH = 1_000
    HEIGHT = 20_000
    Y_POS = -10_000
    COLOR = GREEN

    def __repr__(self):
        return f"WinWall(Vector2({self.position.x}, {self.position.y}))"

    def clone(self):
        return WinWall(clone_vec(self.position))

    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.player = None
        self.passed = False

        self.area = Rect(
            Vector2(self.position.x, WinWall.Y_POS),
            Vector2(WinWall.WIDTH, WinWall.HEIGHT)
        )

        self.velocity = Vector2(0, 0)
        self.rot_vel = 0

    def manifested(self):
        self.player = get_game().get_player()

    def get_tag(self):
        return "Win"

    def end_animation(self):
        if not self.passed and self.player.position.x > self.position.x:
            self.passed = True

            p = Particle(100)
            p.dir_x = -1
            p.color = GREEN
            
            if (preview := get_game().find_by_tag("Preview")):
                l = lambda: preview.return_to_editor()
            else:
                l = lambda: get_game().reload_level()

            timer = TimerObj(5, l)
            get_game().make([timer, p])

            p.emit( clone_vec(self.player.position) )
            timer.start()

        if self.passed:
            self.player.position.x = self.position.x
            self.player.position.y = -11_000
            self.player.velocity = Vector2(0, 0)
        else:
            self.rot_vel += 0.3 * self.player.orientation
            self.velocity.x += 0.3
            self.velocity.y -= 0.3 * self.player.orientation

            self.player.position.x += self.velocity.x
            self.player.position.y += self.velocity.y

            self.player.rotation += int(self.rot_vel)

    def logic(self):
        if self.player is None: return

        if self.player.position.x > self.position.x - 400:
            if not self.player.halted:
                self.player.halt()
                self.logic = self.end_animation

    def draw(self):
        p = VecMath.floor_i(self.position)
        draw_rectangle(p.x, WinWall.Y_POS, WinWall.WIDTH, WinWall.HEIGHT, WinWall.COLOR)

class PlayerSpawn(GameObj):
    RADIUS = 15

    def clone(self):
        return PlayerSpawn(clone_vec(self.position))

    def __repr__(self):
        return f"PlayerSpawn(Vector2({self.position.x}, {self.position.y}))"

    def __init__(self, pos):
        super().__init__()
        self.position = pos
        self.waiting = True
        self.player = None

        self.area = Rect(
            clone_vec(self.position),
            Vector2(PlayerSpawn.RADIUS/2, PlayerSpawn.RADIUS/2)
        )
    
    def destroy(self):
        get_game().defer(lambda: get_game().destroy([self]))

    def check(self):
        self.player = get_game().get_player()
        if self.player is not None:
            self.waiting = False
            self.player.position = clone_vec(self.position)
            self.destroy()

    def manifested(self):
        self.check()
    
    def logic(self):
        if not self.waiting: return

        self.check()
    
    def draw(self):
        p = VecMath.floor_i(self.position)
        draw_circle(p.x, p.y, PlayerSpawn.RADIUS, GRAY)

class Portal(GameObj):
    WIDTH = 10
    HEIGHT = 100

    def __repr__(self):
        return f"{self.__class__.__name__}(Vector2({self.position.x}, {self.position.y}))"
    
    def clone(self):
        return type(self)(clone_vec(self.position))
    
    def __init__(self, pos):
        super().__init__()

        self.position = pos
        self.area = Rect(
            clone_vec(self.position),
            Vector2(Portal.WIDTH, Portal.HEIGHT)
        )
        self.color = BLACK

        self.player = None
        self.enabled = True
    
    def manifested(self):
        self.player = get_game().get_player()

    def logic(self):
        if self.player is None: return
        if not self.enabled: return
        if self.player.area is None: return

        for i in self.player.area.vertices():
            if Rect.check_collision_with_point(self.area, i):
                self.apply()
                self.enabled = False
                break
    
    def draw(self):
        p = VecMath.floor_i(self.position)
        draw_rectangle(p.x, p.y, Portal.WIDTH, Portal.HEIGHT, self.color)
    
    def postdraw(self):
        super().postdraw()
        if DEBUG_MODE:
            p = VecMath.floor_i(self.area.position)
            d = VecMath.floor_i(self.area.dimension)
            draw_rectangle_lines(p.x, p.y, d.x, d.y, RED)

    def apply(self):
        pass

class ShipPortal(Portal):
    COLOR = PURPLE

    def __init__(self, pos):
        super().__init__(pos)
        self.color = ShipPortal.COLOR

    def apply(self):
        self.player.set_mode("ship")

class SquarePortal(Portal):
    COLOR = ORANGE

    def __init__(self, pos):
        super().__init__(pos)
        self.color = SquarePortal.COLOR
    
    def apply(self):
        self.player.set_mode("square")

class BallPortal(Portal):
    COLOR = VIOLET

    def __init__(self, pos):
        super().__init__(pos)
        self.color = BallPortal.COLOR
    
    def apply(self):
        self.player.set_mode("ball")

class WavePortal(Portal):
    COLOR = Player.WAVE_COLOR

    def __init__(self, pos):
        super().__init__(pos)
        self.color = WavePortal.COLOR
    
    def apply(self):
        self.player.set_mode("wave")

class DefaultSpeedPortal(Portal): # could be abstracted but whatever lmao
    SPEED = 5.5

    WIDTH = 50
    HEIGHT = 50

    SPRITE_PATH = "textures/portals/defaultspeed.png"
    _SPRITE = None

    @staticmethod
    def get_sprite():
        if DefaultSpeedPortal._SPRITE is None:
            with RaylibImage(DefaultSpeedPortal.SPRITE_PATH) as image:
                image_resize_nn(image, DefaultSpeedPortal.WIDTH, DefaultSpeedPortal.HEIGHT)
                DefaultSpeedPortal._SPRITE = load_texture_from_image(image)

        return DefaultSpeedPortal._SPRITE

    def __init__(self, pos):
        super().__init__(pos)
        self.area = Rect(
            VecMath.sub(pos, Vector2(0, 10)),
            Vector2(DefaultSpeedPortal.WIDTH, DefaultSpeedPortal.HEIGHT + 20 )
        )
    
    def draw(self):
        pos = VecMath.floor_i(self.position)
        draw_texture(DefaultSpeedPortal.get_sprite(), pos.x, pos.y, WHITE)
    
    def apply(self):
        get_game().get_player().horizontal_speed = DefaultSpeedPortal.SPEED

class FastSpeedPortal(Portal):
    SPEED = 7

    WIDTH = 50
    HEIGHT = 50

    SPRITE_PATH = "textures/portals/fastspeedportal.png"
    _SPRITE = None

    @staticmethod
    def get_sprite():
        if FastSpeedPortal._SPRITE is None:
            with RaylibImage(FastSpeedPortal.SPRITE_PATH) as image:
                image_resize_nn(image, FastSpeedPortal.WIDTH, FastSpeedPortal.HEIGHT)
                FastSpeedPortal._SPRITE = load_texture_from_image(image)

        return FastSpeedPortal._SPRITE

    def __init__(self, pos):
        super().__init__(pos)
        self.area = Rect(
            VecMath.sub(pos, Vector2(0, 10)),
            Vector2(FastSpeedPortal.WIDTH, FastSpeedPortal.HEIGHT + 20 )
        )
    
    def draw(self):
        pos = VecMath.floor_i(self.position)
        draw_texture(FastSpeedPortal.get_sprite(), pos.x, pos.y, WHITE)
    
    def apply(self):
        get_game().get_player().horizontal_speed = FastSpeedPortal.SPEED

class VeryFastSpeedPortal(Portal):
    SPEED = 10

    WIDTH = 70
    HEIGHT = 70

    SPRITE_PATH = "textures/portals/veryfastportal.png"
    _SPRITE = None

    @staticmethod
    def get_sprite():
        if VeryFastSpeedPortal._SPRITE is None:
            with RaylibImage(VeryFastSpeedPortal.SPRITE_PATH) as image:
                image_resize_nn(image, VeryFastSpeedPortal.WIDTH, VeryFastSpeedPortal.HEIGHT)
                VeryFastSpeedPortal._SPRITE = load_texture_from_image(image)

        return VeryFastSpeedPortal._SPRITE

    def __init__(self, pos):
        super().__init__(pos)
        self.area = Rect(
            VecMath.sub(pos, Vector2(-10, 10)),
            Vector2(VeryFastSpeedPortal.WIDTH, VeryFastSpeedPortal.HEIGHT + 20 )
        )
    
    def draw(self):
        pos = VecMath.floor_i(self.position)
        draw_texture(VeryFastSpeedPortal.get_sprite(), pos.x, pos.y, WHITE)
    
    def apply(self):
        get_game().get_player().horizontal_speed = VeryFastSpeedPortal.SPEED


class FastestSpeedPortal(Portal):
    SPEED = 15

    WIDTH = 60
    HEIGHT = 100

    SPRITE_PATH = "textures/portals/fastestspeedportal.png"
    _SPRITE = None

    @staticmethod
    def get_sprite():
        if FastestSpeedPortal._SPRITE is None:
            with RaylibImage(FastestSpeedPortal.SPRITE_PATH) as image:
                image_resize_nn(image, FastestSpeedPortal.WIDTH, FastestSpeedPortal.HEIGHT)
                FastestSpeedPortal._SPRITE = load_texture_from_image(image)

        return FastestSpeedPortal._SPRITE

    def __init__(self, pos):
        super().__init__(pos)
        self.area = Rect(
            clone_vec(pos),
            Vector2(FastestSpeedPortal.WIDTH, FastestSpeedPortal.HEIGHT )
        )
    
    def draw(self):
        pos = VecMath.floor_i(self.position)
        draw_texture(FastestSpeedPortal.get_sprite(), pos.x, pos.y, WHITE)
    
    def apply(self):
        get_game().get_player().horizontal_speed = FastestSpeedPortal.SPEED


class Item:
    def __init__(self, name):
        self.name = name

    def supports_rotation(self):
        return False

    def draw_preview(self, where):
        pass
    
    def offset(self, where):
        return VecMath.floor_i(where)

    def special_trigger(self):
        pass

    def origin(self, where):
        return Vector2(0, 0)

    def place(self, where, _rot):
        sys.stderr.write("Called base-class function 'place()', this should be overwritten!\n")

class PlayerSpawnItem(Item):
    def __init__(self):
        super().__init__("Player Spawn")
    
    def draw_preview(self, where):
        draw_circle(where.x, where.y, PlayerSpawn.RADIUS, GRAY)
    
    def place(self, where, _rot):
        return PlayerSpawn(where)

class SmartTile(Item):
    def __init__(self):
        super().__init__("Smart Tile")
        self.pos1 = None
        self.pos2 = None
        self.dim = None

    def special_trigger(self):
        if self.pos1 is None:
            self.pos1 = EditorLevelManager.get_desired_mouse_pos()
            self.pos1 = self.offset(self.pos1)
        elif self.pos2 is None:
            self.pos2 = EditorLevelManager.get_desired_mouse_pos()
            self.pos2 = self.offset(self.pos2)
        else:
            self.pos1 = None
            self.pos2 = None
    
    def offset(self, where):
        w = super().offset(where)
        w.x -= 5
        w.y -= 10
        return w

    def place(self, where, _rot):
        if self.pos1 is None or self.pos2 is None: return None
        t = Tile(clone_vec(self.pos1), clone_vec(self.dim))
        self.pos1, self.pos2, self.dim = None, None, None
        return t

    def draw_preview(self, where):
        if self.pos1 is None and self.pos2 is None:
            draw_rectangle(where.x, where.y+5, 10, 10, GOLD)

        elif self.pos1 is not None and self.pos2 is None:
            temppos1 = clone_vec(self.pos1)
            temppos2 = self.offset(EditorLevelManager.get_desired_mouse_pos())
            tempdim = VecMath.abs(VecMath.sub(temppos2, self.pos1))
            if temppos1.x > temppos2.x:
                temppos1.x, temppos2.x = temppos2.x, temppos1.x
            if temppos1.y > temppos2.y:
                temppos1.y, temppos2.y = temppos2.y, temppos1.y
            
            mouse = VecMath.floor_i(get_screen_to_world_2d(get_mouse_position(), get_game().get_cam()))
            draw_text(f"{tempdim.x}x{tempdim.y}", mouse.x+20, mouse.y, 24, BLACK)


            draw_rectangle_lines(int(temppos1.x), int(temppos1.y), int(tempdim.x), int(tempdim.y), GREEN)
        else:
            self.dim = VecMath.abs(VecMath.sub(self.pos2, self.pos1))
            if self.pos1.x > self.pos2.x:
                self.pos1.x, self.pos2.x = self.pos2.x, self.pos1.x
            if self.pos1.y > self.pos2.y:
                self.pos1.y, self.pos2.y = self.pos2.y, self.pos1.y


            draw_rectangle(int(self.pos1.x), int(self.pos1.y), int(self.dim.x), int(self.dim.y), GREEN)

class TileItem(Item):
    WIDTH = 50
    HEIGHT = 50

    def __init__(self):
        super().__init__("Tile")

    def offset(self, where):
        w = VecMath.floor_i(where)
        w.x -= TileItem.WIDTH // 2
        w.y -= TileItem.HEIGHT // 2
        return w

    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, 50, 50, DARKGRAY)
    
    def place(self, where, _rot):
        return Tile( where.to_raylib(), Vector2(TileItem.WIDTH, TileItem.HEIGHT) )

class SlopeItem(Item):
    def __init__(self):
        super().__init__("Slope")
    
    def supports_rotation(self):
        return True

    def origin(self, where):
        return Vector2(where.x + Slope.MID, where.y + Slope.MID)

    def offset(self, where):
        w = VecMath.floor_i(where)
        w.x -= TileItem.WIDTH // 2
        w.y -= TileItem.HEIGHT // 2
        return w

    def draw_preview(self, where):
        where.y += 50
        draw_triangle_strip((where.to_raylib(), VecMath.int(VecMath.add(where, Vector2(50, 0))), VecMath.int(VecMath.add(where, Vector2(50, -50)))), 3, DARKGRAY)
    
    def place(self, where, rot):
        return Slope( where.to_raylib(), rot)

class SpikeItem(Item):
    def __init__(self):
        super().__init__("Spike")
    
    def offset(self, where):
        w = VecMath.floor_i(where)
        w.y += Spike.MID
        return w

    def supports_rotation(self):
        return True

    def origin(self, where):
        return Vector2(where.x, where.y - Spike.MID)

    def draw_preview(self, where):
        top = VecMath.sub(where, Vector2(0, Spike.HEIGHT))
        left = VecMath.add(top, Vector2(-Spike.MID, Spike.HEIGHT))
        right = VecMath.add(top, Vector2(Spike.MID, Spike.HEIGHT))
        
        draw_triangle(
            top,
            left,
            right,
            RED
        )
    
    def place(self, where, rot):
        return Spike( where, rot)

class JumpOrbItem(Item):
    def __init__(self):
        super().__init__("Jump Orb")
    
    def place(self, where, _rot):
        return JumpOrb(where)

    def draw_preview(self, where):
        draw_circle(where.x, where.y, Orb.RADIUS, JumpOrb.COLOR)
        draw_circle_lines(where.x, where.y, Orb.RADIUS + 1, JumpOrb.BORDER_COLOR)

class GravityOrbItem(Item):
    def __init__(self):
        super().__init__("Gravity Orb")
    
    def place(self, where, _rot):
        return GravityOrb(where)

    def draw_preview(self, where):
        draw_circle(where.x, where.y, Orb.RADIUS, GravityOrb.COLOR)
        draw_circle_lines(where.x, where.y, Orb.RADIUS + 1, GravityOrb.BORDER_COLOR)

class JumpPadItem(Item):
    def __init__(self):
        super().__init__("Jump Pad")

    def offset(self, where):
        w = VecMath.floor_i(where)
        w.x -= Pad.WIDTH // 2
        w.y += 5 # to align with ground
        return w

    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Pad.WIDTH, Pad.HEIGHT, JumpPad.COLOR)
    
    def place(self, where, _rot):
        return JumpPad(where)

class GravityPadItem(Item):
    def __init__(self):
        super().__init__("Gravity Pad")

    def offset(self, where):
        w = VecMath.floor_i(where)
        w.x -= Pad.WIDTH // 2
        w.y += 5 # to align with ground
        return w

    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Pad.WIDTH, Pad.HEIGHT, GravityPad.COLOR)
    
    def place(self, where, _rot):
        return GravityPad(where)

class CameraStaticTriggerItem(Item):
    def __init__(self):
        super().__init__("Camera Static Trigger")
        self.where_to = None
    
    def special_trigger(self):
        if self.where_to is None:
            self.where_to = get_screen_to_world_2d(get_mouse_position(), get_game().get_cam())
        else:
            self.where_to = None

    def draw_preview(self, where):
        draw_poly(where.to_raylib(), 5, Trigger.RADIUS, 0, CameraStaticTrigger.COLOR)

        if self.where_to is not None:
            draw_line_v(VecMath.int(where), VecMath.int(self.where_to), GREEN)
    
    def place(self, where, _rot):
        if self.where_to is None:
            return None
        wt = clone_vec(self.where_to)
        self.where_to = None
        return CameraStaticTrigger(where, wt)

class CameraResetTriggerItem(Item):
    def __init__(self):
        super().__init__("Camera Reset Trigger")
    
    def draw_preview(self, where):
        draw_poly(where.to_raylib(), 5, Trigger.RADIUS, 0, CameraResetTrigger.COLOR)
    
    def place(self, where, _rot):
        return CameraResetTrigger(where)

class CameraYTriggerItem(Item):
    def __init__(self):
        super().__init__("Camera Y Trigger")
        self.where_y = None
    
    def special_trigger(self):
        if self.where_y is None:
            self.where_y = get_screen_to_world_2d(get_mouse_position(), get_game().get_cam()).y
        else:
            self.where_y = None

    def draw_preview(self, where):
        draw_poly(where.to_raylib(), 5, Trigger.RADIUS, 0, CameraYTrigger.COLOR)
        if self.where_y is not None:
            draw_line_v(VecMath.int(where), VecMath.int(Vector2(where.x, self.where_y)), GREEN)
    
    def place(self, where, _rot):
        if self.where_y is None:
            return None
        w = self.where_y
        self.where_y = None
        return CameraYTrigger(where, w)

class BackgroundChangeTriggerItem(Item):
    def __init__(self):
        super().__init__("Background Change Trigger")
        self.background_id = 0
    
    def special_trigger(self):
        self.background_id += 1
        if self.background_id >= BackgroundLoader.backgrounds():
            self.background_id = 0
    
    def draw_preview(self, where):
        draw_poly(where.to_raylib(), 5, Trigger.RADIUS, 0, BackgroundChangeTrigger.COLOR)
        draw_text(f"background: {self.background_id}", where.x + 10, where.y, 12, GREEN)
    
    def place(self, where, _rot):
        return BackgroundChangeTrigger(where, self.background_id)

class ShipPortalItem(Item):
    def __init__(self):
        super().__init__("Ship Portal")
    
    def place(self, where, _rot):
        return ShipPortal(where)
    
    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, ShipPortal.COLOR)

class SquarePortalItem(Item):
    def __init__(self):
        super().__init__("Square Portal")
    
    def place(self, where, _rot):
        return SquarePortal(where)
    
    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, SquarePortal.COLOR)

class BallPortalItem(Item):
    def __init__(self):
        super().__init__("Ball Portal")
    
    def place(self, where, _rot):
        return BallPortal(where)
    
    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, BallPortal.COLOR)

class DefaultSpeedPortalItem(Item):
    def __init__(self):
        super().__init__("Slow Speed Portal")
    
    def place(self, where, _rot):
        return DefaultSpeedPortal(where)
    
    def draw_preview(self, where):
        draw_texture(DefaultSpeedPortal.get_sprite(), where.x, where.y, WHITE)

class FastSpeedPortalItem(Item):
    def __init__(self):
        super().__init__("Fast Speed Portal")
    
    def place(self, where, _rot):
        return FastSpeedPortal(where)
    
    def draw_preview(self, where):
        draw_texture(FastSpeedPortal.get_sprite(), where.x, where.y, WHITE)

class VeryFastSpeedPortalItem(Item):
    def __init__(self):
        super().__init__("Very Fast Speed Portal")
    
    def place(self, where, _rot):
        return VeryFastSpeedPortal(where)
    
    def draw_preview(self, where):
        draw_texture(VeryFastSpeedPortal.get_sprite(), where.x, where.y, WHITE)

class FastestSpeedPortalItem(Item):
    def __init__(self):
        super().__init__("Fastest Speed Portal")
    
    def place(self, where, _rot):
        return FastestSpeedPortal(where)
    
    def draw_preview(self, where):
        draw_texture(FastestSpeedPortal.get_sprite(), where.x, where.y, WHITE)

class WavePortalItem(Item):
    def __init__(self):
        super().__init__("Wave Portal")
    
    def place(self, where, _rot):
        return WavePortal(where)

    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, WavePortal.COLOR)

class WinWallItem(Item):
    def __init__(self):
        super().__init__("Win Wall")
    
    def draw_preview(self, where):
        draw_rectangle(where.x, WinWall.Y_POS, WinWall.WIDTH, WinWall.HEIGHT, WinWall.COLOR)
    
    def place(self, where, _rot):
        return WinWall(where)


class EditorLevelPreview(GameObj):
    def __repr__(self):
        return "EditorLevelPreview(?)"

    def get_tag(self):
        return "Preview"

    def clone(self):
        return EditorLevelPreview(self.editor)

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.always_think = True
    
    def return_to_editor(self):
        def get_editor_objs():
            objs = self.editor.get_saved()
            for i in objs[:]:
                if i.get_tag() == "Player" or i.get_tag() == "Preview":
                    objs.remove(i)
                    
            objs.append(self.editor)
            return objs

        l = Level(get_game().get_level().name, get_editor_objs)
        get_game().defer(lambda: get_game().set_level(EditorLevel(l)))

    def logic(self):
        if is_key_pressed(KeyboardKey(0).KEY_T):
            self.return_to_editor()

class EditorLevelManager(GameObj):
    ROUND_WIDTH = -1
    CAM_SPEED = 10

    class SaveUIGroup(GameObj):
        def __init__(self):
            super().__init__()
            self.elements = [
                UI.TextField(Vector2(get_screen_width()//4, 100), Vector2(700, 200), 64, banned=[KeyboardKey(0).KEY_BACKSLASH, KeyboardKey(0).KEY_SLASH], placeholder="Enter Name", callback=self.do_save),
                UI.BetterButton(Vector2(get_screen_width()//4+100, 400), Vector2(500, 70), callback=self.do_save),
                UI.TextDisplay(Vector2(get_screen_width()//2-50, 410), "SAVE", 54, WHITE)
            ]
            self.visible = True
            self.elements[0].text = get_game().get_level().name
            self.done = False
            self.always_think = True
        
        def destroyed(self):
            self.done = True

        def do_save(self):
            self.visible = False
            name = self.elements[0].text.strip()
            if name == "":
                sys.stderr.write("Missing level name! Using default name of 'unnamed'.\n")
                name = "unnamed"

            get_game().get_level().name = name
            
            desired_file_name = "./custom_levels/" + name + ".level"
            
            if not os.path.exists("./custom_levels/"):
                os.mkdir("./custom_levels/")
            
            level_data = repr(get_game().find_by_tag("editor_manager").get_actual_saved())

            with open(desired_file_name, "w") as f:
                f.write(name + "\n")
                f.write(level_data)
            
            get_game().defer(lambda: get_game().destroy([self]))

        def get_tag(self):
            return "editor_ui_group"

        def is_ui_element(self):
            return True

        def logic(self):
            if self.visible:
                for i in self.elements:
                    i.logic()

        def ui_draw(self):
            if self.visible:
                for i in self.elements:
                    i.ui_draw()
            else:
                self.elements[0].selected = False
                draw_text("Saving ...", get_screen_width()//2, 100, 44, BLACK)
    
    class HUD(GameObj):

        def __init__(self):
            super().__init__()
            self.always_think = True

        def get_tag(self):
            return "editor_hud"

        def manifested(self):
            self.manager = get_game().find_by_tag("editor_manager")

        def is_ui_element(self):
            return True
        
        def ui_draw(self):
            if self.manager is None:
                self.manager = get_game().find_by_tag("editor_manager")
                return

            cam = get_game().get_cam()

            if self.manager.held_item is not None:
                text = self.manager.held_item.name
                draw_text(text, get_screen_width()//2 - measure_text(text, 24)//2, 5, 24, BLACK)

            draw_text(f"{round(cam.target.x, 2)}, {round(cam.target.y, 2)}", 10, 5, 54, BLACK )
            draw_fps(get_screen_width() - 100, 20)

            if self.manager.esc_tick > 0:
                text = "exiting ... (hold)"
                draw_text(text, get_screen_width()//2 - measure_text(text, 34)//2, 200, 34, BLACK)


    def get_tag(self):
        return "editor_manager"

    def __init__(self):
        super().__init__()
        self.always_think = True

        self.items = [
            None, PlayerSpawnItem(), SmartTile(), SlopeItem(), TileItem(), SpikeItem(), 
            JumpOrbItem(), GravityOrbItem(), JumpPadItem(), GravityPadItem(),
            CameraResetTriggerItem(), CameraStaticTriggerItem(), CameraYTriggerItem(), BackgroundChangeTriggerItem(),
            DefaultSpeedPortalItem(), FastSpeedPortalItem(), VeryFastSpeedPortalItem(), FastestSpeedPortalItem(),
            ShipPortalItem(), SquarePortalItem(), BallPortalItem(), WavePortalItem(),
            WinWallItem()
        ]
        self.held_item_index = 0

        self.held_item = self.items[self.held_item_index]
        self.rotation = 0

        self.hud = EditorLevelManager.HUD()
        get_game().make([self.hud])

        self.saved = []
        
        self.esc_tick = 0

        self.save_window = None
    
    def manifested(self):
        if get_game().find_by_tag("editor_hud") is None:
            self.hud = EditorLevelManager.HUD()
            get_game().make([self.hud])

    def get_saved(self):
        return [o.clone() for o in self.saved]

    def save_objs(self):
        self.saved.clear()
        for i in get_game().game_objects:
            if type(i) == EditorLevelManager or i.get_tag().startswith("editor") or isinstance(i, Background):
                continue
            self.saved.append(i.clone())        

    def pick_item(self):
        mouse_wheel = round(get_mouse_wheel_move())
        if mouse_wheel != 0:
            self.held_item_index += mouse_wheel
            if self.held_item_index > len(self.items)-1:
                self.held_item_index = 0
            elif self.held_item_index < 0:
                self.held_item_index = len(self.items) - 1
            
            self.held_item = self.items[self.held_item_index]
    
    def cam_move(self):
        cam = get_game().get_cam()
        
        speed_mul = 1
        if is_key_down(KeyboardKey(0).KEY_LEFT_SHIFT):
            speed_mul = 2

        if is_key_down(KeyboardKey(0).KEY_D):
            cam.target.x += EditorLevelManager.CAM_SPEED * speed_mul
        elif is_key_down(KeyboardKey(0).KEY_A):
            cam.target.x -= EditorLevelManager.CAM_SPEED * speed_mul
        
        if is_key_down(KeyboardKey(0).KEY_W):
            cam.target.y -= EditorLevelManager.CAM_SPEED * speed_mul
        elif is_key_down(KeyboardKey(0).KEY_S):
            cam.target.y += EditorLevelManager.CAM_SPEED * speed_mul

    @staticmethod
    def get_desired_mouse_pos():
        # pos = VecMath.sub(get_mouse_position(), VecMath.sub(cam.offset, cam.target))
        pos = get_screen_to_world_2d(get_mouse_position(), get_game().get_cam())
        pos.x = round(pos.x, EditorLevelManager.ROUND_WIDTH)
        pos.y = round(pos.y, EditorLevelManager.ROUND_WIDTH)
        return pos

    def get_actual_saved(self):
        self.save_objs()
        saved = self.get_saved()
        player_exists = False
        for i in saved:
            if type(i) == Player:
                player_exists = True
                break
        if not player_exists:
            saved.insert(0, Player())
        
        return saved

    def logic(self):
        get_game().set_editor_mode(True)
        if self.save_window is not None:
            if self.save_window.done:
                self.save_window = None
            if is_key_pressed(KeyboardKey(0).KEY_S) and is_key_down(KeyboardKey(0).KEY_LEFT_CONTROL):
                get_game().destroy([self.save_window])
                self.save_window = None
            elif is_key_released(KeyboardKey(0).KEY_ESCAPE):
                get_game().destroy([self.save_window])
                self.save_window = None
            
            return

        elif is_key_pressed(KeyboardKey(0).KEY_S) and is_key_down(KeyboardKey(0).KEY_LEFT_CONTROL):
            self.save_window = EditorLevelManager.SaveUIGroup()
            get_game().make([self.save_window])

        if is_key_down(KeyboardKey(0).KEY_ESCAPE):
            self.esc_tick += 1 * get_frame_time()
            if self.esc_tick > 3:
                self.esc_tick = 0
                get_game().set_editor_mode(False)
                get_game().defer(lambda: get_game().set_level(LevelSelectScreen()))

        elif is_key_released(KeyboardKey(0).KEY_ESCAPE):
            self.esc_tick = 0

        self.pick_item()
        self.cam_move()

        if is_key_pressed(KeyboardKey(0).KEY_T):
            get_game().set_editor_mode(False)
            objs = [EditorLevelPreview(self), Player()]
            self.save_objs()
            for i in self.saved:
                objs.append(i)
            self.saved = objs

            print("SAVED LEVEL CODE: -=-=-=-=-=")
            print(self.saved)
            print("LEVEL CODE ^^^^^^^-=-=-=-=-=")
            test_level = Level(get_game().get_level().name, self.get_saved)
            get_game().defer(lambda: get_game().set_level(test_level))

        pos = EditorLevelManager.get_desired_mouse_pos()
        
        if is_key_pressed(KeyboardKey(0).KEY_P):
            for i in get_game().game_objects[:]:
                if type(i) == WinWall:
                    get_game().game_objects.remove(i)
                    break

        if is_key_pressed(KeyboardKey(0).KEY_C):
            print("Saving level to clipboard ...")
            saved = self.get_actual_saved()
            set_clipboard_text(repr(saved))
            print(f"Saved level to clipboard! ({len(saved)} objects)")

        if is_key_pressed(KeyboardKey(0).KEY_L):
            print("Loading level from clipboard ...")
            clip = get_clipboard_text()
            objs = None
            try:
                objs = eval(clip)
            except:
                sys.stderr.write("Invalid level data! Please ensure you copied the right stuff\n")
            else:
                if type(objs) is not list:
                    sys.stderr.write("Evaluated 'level' is not a list and therefore, not a level.\n")
                else: 
                    for i in objs[:]:
                        if type(i) in [Player, EditorLevelPreview, EditorLevelManager]:
                            objs.remove(i)
                    objs.insert(0, EditorLevelManager())

                    def level_data():
                        return objs
                    l = Level("Loaded Level", level_data)
                    get_game().defer(lambda: get_game().set_level(l))
                    print("Loaded level!")

        if is_key_pressed(KeyboardKey(0).KEY_B):
            global DEBUG_MODE
            DEBUG_MODE = not DEBUG_MODE

        if is_key_pressed(KeyboardKey(0).KEY_K):
            removed = 0
            for i in get_game().game_objects[:]:
                if type(i) == PlayerSpawn:
                    get_game().game_objects.remove(i)
                    removed += 1
            print(f"Removed {removed} spawnpoints")

        if self.held_item is not None:
            actual = self.held_item.offset(pos)
            actual.y -= 5

            if is_mouse_button_down(1):
                point = get_screen_to_world_2d(get_mouse_position(), get_game().get_cam())
                for i in get_game().game_objects:
                    if i.area is None: continue

                    if Rect.check_collision_with_point(i.area, point):
                        get_game().game_objects.remove(i)
                        break

            if is_mouse_button_pressed(0):
                block = self.held_item.place(actual, self.rotation)
                if block is None:
                    sys.stderr.write("Attempted to place nothing (None).\n")
                else:
                    get_game().make([block])
            
            if is_mouse_button_pressed(2):
                self.held_item.special_trigger()
            
            if is_key_pressed(KeyboardKey(0).KEY_R):
                self.rotation += 45
                if self.rotation > 315:
                    self.rotation = 0
                
    
    def draw(self):
        if self.held_item is not None:
            pos = EditorLevelManager.get_desired_mouse_pos()
            actual = self.held_item.offset(pos)
            actual.y -= 5 # so it aligns with the ground

            if self.held_item.supports_rotation():
                get_game().calc_rot(self.rotation, self.held_item.origin(actual))
            self.held_item.draw_preview(actual)
            get_game().reset_rot()

class EditorLevel(Level):

    def __init__(self, level_get=None):
        if level_get is None:
            super().__init__("Editor", EditorLevel.level_data)
        else:
            def get():
                if issubclass(type(level_get), Level):
                    retrived = level_get.get()
                    self.name = level_get.name
                else:
                    retrived = level_get()
                manager_exists = False
                for i in retrived[:]:
                    if type(i) == Player or type(i) == Ground:
                        retrived.remove(i)
                    if type(i) == EditorLevelManager:
                        manager_exists = True
                if manager_exists:
                    return [Ground()] + retrived
                return EditorLevel.level_data() + retrived
            super().__init__("Editor", get)
    
    @staticmethod
    def level_data():
        return [
            EditorLevelManager(),

            Ground()
        ]

class TestLevel(Level):
    def __init__(self):
        super().__init__("Test Level", TestLevel.level_data)
    
    @staticmethod
    def level_data():
        return [
                    # x = 1_500, first platform
                    # x = 2_700, second platform
                    
                    Player(  ),
                    Ground(),
                    
                    Spike(Vector2(0, 300)),

                    Spike(Vector2(400, 300)),
                    Spike(Vector2(450, 300)),
                    
                    Tile(Vector2(700, 250), Vector2(50, 50)),
                    Tile(Vector2(850, 200), Vector2(50, 100)),
                    Tile(Vector2(1_000, 150), Vector2(50, 150)),
                    
                    # first platform
                    Tile(Vector2(1_500, 200), Vector2(500, 100)),
                    Tile(Vector2(2_000, 200), Vector2(500, 100)),
                    
                    
                    Spike( Vector2(1_700, 200) ),
                    
                    Tile(Vector2(1_900, 150), Vector2(50, 50)),
                    Spike( Vector2(1_925, 150) ),
                    
                    Spike( Vector2(2_100, 200) ),
                    Spike( Vector2(2_150, 200) ),
                    
                    Spike( Vector2(2_475, 200) ),
                    
                    JumpOrb( Vector2(2_600, 200) ),
                    
                    # platform 2
                    Tile( Vector2(2_700, 100), Vector2(300, 50) ),
                    
                    Spike( Vector2(2_525, 300) ),
                    Spike( Vector2(2_575, 300) ),
                    Spike( Vector2(2_625, 300) ),
                    Spike( Vector2(2_675, 300) ),
                    
                    Tile(Vector2(3_000, 100), Vector2(50, 200) ),
                    
                    JumpPad( Vector2(3_000, 90) ),
                    GravityOrb( Vector2(3_200, 0) ),

                    Spike( Vector2(3_075, 300) ),
                    Spike( Vector2(3_125, 300) ),
                    Spike( Vector2(3_175, 300) ),
                    Spike( Vector2(3_225, 300) ),
                    Spike( Vector2(3_275, 300) ),

                    Tile( Vector2(3_100, -300), Vector2(500, 50) ),
                    Tile( Vector2(3_600, -300), Vector2(500, 50) ),

                    GravityPad( Vector2(4_050, -250) ),
                    Spike( Vector2(4_150, -420), 180 ),
                    Spike( Vector2(4_200, -420), 180 ),
                    Spike( Vector2(4_250, -420), 180 ),

                    GravityPad( Vector2(4_200, 290) ),
                    GravityPad( Vector2(4_240, -50) ),
                    GravityPad( Vector2(4_310, 290) ),
                    GravityPad( Vector2(4_390, -50) ),
                    GravityPad( Vector2(4_420, 290) ),
                    GravityPad( Vector2(4_520, -50) ),
                    
                    
                    WinWall( Vector2(5_200, 0) )
                ]
    
class BlankLevel(Level):
    def __init__(self):
        super().__init__("Blank Level", BlankLevel.level_data)
    
    @staticmethod
    def level_data():
        return [Player(), Ground()]

class HardLevel(Level):
    def __init__(self):
        super().__init__("HardLevel", HardLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/hard.level").get()
    
class ShipLevel(Level):
    def __init__(self):
        super().__init__("ShipLevel", ShipLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/ship.level").get()
    
class BallWaveLevel(Level):
    def __init__(self):
        super().__init__("Ball Wave Level", BallWaveLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/ballwave.level").get()

class RadioAngerLevel(Level):
    def __init__(self):
        super().__init__("Radio Anger", RadioAngerLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/radioanger.level").get()

class ImprovementLevel(Level):
    def __init__(self):
        super().__init__("Improvement", ImprovementLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/Improvement.level").get()

class SlippyLevel(Level):
    def __init__(self):
        super().__init__("Slippy", SlippyLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/Slippy.level").get()

class LudicrousLevel(Level):
    def __init__(self):
        super().__init__("Ludicrous", LudicrousLevel.level_data)
    
    @staticmethod
    def level_data():
        return Level.from_file("levels/Ludicrous.level").get()

class UI:
    class Button(GameObj):
        def __init__(self, pos, dim, callback=lambda: None):
            super().__init__()
            self.position = pos
            self.area = Rect(
                clone_vec(pos),
                dim
            )
            self.always_think = True
            self.callback = callback

        def is_ui_element(self):
            return True

        def logic(self):
            if self.is_ui_element():
                mouse = get_mouse_position()
            else:
                mouse = get_screen_to_world_2d(get_mouse_position(), get_game().get_cam())
            if is_mouse_button_released(0) and Rect.check_collision_with_point(self.area, mouse):
                self.apply()
                self.callback()

        def apply(self):
            pass
    
    class BetterButton(Button):
        def __init__(self, pos, dim, color=DARKGRAY, callback=lambda: None):
            super().__init__(pos, dim, callback)
            self.color = color
            self.callback = callback

        def is_ui_element(self):
            return True

        def ui_draw(self):
            pos = VecMath.floor_i(self.position)
            dim = VecMath.floor_i(self.area.dimension)
            draw_rectangle_rounded(Rectangle(pos.x, pos.y, dim.x, dim.y), 0.5, 50, self.color)
    
    class TextField(BetterButton):
        def __init__(self, pos, dim, font_size, multiline=False, max_per_line=12, callback=lambda: None, banned=None, placeholder=""):
            super().__init__(pos, dim)
            self.selected = False
            self.text = ""

            self.font_size = font_size
            self.multiline = multiline
            self.max_per_line = max_per_line

            self.cursor = VecMath.add(self.position, Vector2(100, 50))
            self.callback_enter = callback

            self.banned = banned
            self.placeholder = placeholder
        
        def apply(self):
            self.selected = True

        def logic(self):
            super().logic()
            if self.selected:
                key = get_key_pressed()
                if key != 0:
                    actual = chr(key)
                    if self.banned is not None:
                        if key in self.banned:
                            actual = ""
                    
                    # ugly code but lol
                    if key in [KeyboardKey(0).KEY_LEFT, KeyboardKey(0).KEY_RIGHT, KeyboardKey(0).KEY_UP, KeyboardKey(0).KEY_DOWN]:
                        actual = ""

                    if key == KeyboardKey(0).KEY_BACKSPACE:
                        self.text = self.text[:len(self.text)-1]
                        actual = ""
                    
                    if key == KeyboardKey(0).KEY_LEFT_SHIFT:
                        actual = ""

                    if not is_key_down(KeyboardKey(0).KEY_LEFT_SHIFT):
                        actual = actual.lower()

                    if key == KeyboardKey(0).KEY_ENTER:
                        if self.multiline:
                            if is_key_pressed(KeyboardKey(0).KEY_LEFT_SHIFT):
                                actual = ""
                                self._submit()
                            elif len(self.text) < self.max_per_line:
                                actual = "\n"
                        else:
                            actual = ""
                            self._submit()

                    if len(self.text) < self.max_per_line:
                        self.text += actual

                if is_mouse_button_pressed(0):
                    self.selected = False
                

        def ui_draw(self):
            super().ui_draw()
            pos = VecMath.floor_i(self.position)

            if self.text == "":
                draw_text(self.placeholder, pos.x+100, pos.y+50, self.font_size, BLACK)
            else:
                draw_text(self.text, pos.x+100, pos.y+50, self.font_size, WHITE)

            if self.selected:
                self.cursor.x = pos.x+100 + measure_text(self.text, self.font_size)
                cur = VecMath.floor_i(self.cursor)

                draw_rectangle(cur.x, cur.y, 5, self.font_size, WHITE)
        
        def _submit(self):
            self.submit()
            self.callback_enter()

        def submit(self):
            pass
    
    class TextDisplay(GameObj):
        def __init__(self, pos, text, font_size, color):
            super().__init__()
            self.position = pos
            self.text = text
            self.font_size = font_size
            self.color = color
            self.always_think = True
        
        def is_ui_element(self):
            return True

        def __len__(self):
            return measure_text(self.text, self.font_size)

        def ui_draw(self):
            pos = VecMath.floor_i(self.position)
            draw_text(self.text, pos.x, pos.y, self.font_size, self.color)
                

class LevelSelectScreen(Level):
    LEVELS = [
        SlippyLevel(),
        ImprovementLevel(),
        TestLevel(),
        LudicrousLevel(),
        HardLevel(), 
        ShipLevel(), 
        BallWaveLevel(),
        RadioAngerLevel(),
        BlankLevel()
    ]

    class LevelSelectCamera(GameObj):
        def __init__(self):
            super().__init__()
            self.moving_to = None
            self.always_think = True
            self.index = 0
            self.custombutton = None

        def manifested(self):
            global _attempts
            _attempts = 0

            get_game().get_cam().target = Vector2(0, 0)
            self.custombutton = get_game().find_by_tag("customlevels_button")

        def get_tag(self):
            return "cam_holder"

        def _move_input(self, lvls):
            if self.index < len(lvls)-1 and Input.right_pressed():
                self.moving_to = get_game().get_cam().target.x + 1_500
                self.index += 1
            elif self.index > 0 and Input.left_pressed():
                self.index -= 1
                self.moving_to = get_game().get_cam().target.x - 1_500

        def logic(self):
            if self.moving_to is None:
                if self.custombutton.is_toggled():
                    if len(self.custombutton.levels) != 0:
                        self._move_input(self.custombutton.levels)
                else:
                    self._move_input(LevelSelectScreen.LEVELS)
            else:
                cam = get_game().get_cam()

                if abs(self.moving_to - cam.target.x) < 1_000:
                    cam.target.x = self.moving_to
                    self.moving_to = None
                elif self.moving_to < cam.target.x:
                    cam.target.x -= 100
                elif self.moving_to+10_000 > cam.target.x:
                    cam.target.x += 100

    class EditorCheckBox(UI.Button):
        WIDTH = 100
        HEIGHT = 100
        CIRCLE_RAD = 35

        def __init__(self):
            super().__init__(Vector2(), Vector2(LevelSelectScreen.EditorCheckBox.WIDTH, LevelSelectScreen.EditorCheckBox.HEIGHT))
            self.checked = False
            self.always_think = True
        
        def get_tag(self):
            return "editor_check"

        def is_toggled(self):
            return self.checked
        
        def logic(self):
            super().logic()
            self.position = VecMath.add(get_game().get_cam().target, Vector2(-400, 210))
            self.area.position = clone_vec(self.position)
        
        def apply(self):
            self.checked = not self.checked

        def is_ui_element(self):
            return False

        def draw(self):
            pos = VecMath.floor_i(self.position)
            draw_rectangle_rounded(Rectangle(pos.x, pos.y, LevelSelectScreen.EditorCheckBox.WIDTH, LevelSelectScreen.EditorCheckBox.HEIGHT), 0.5, 50, DARKGRAY)

            if self.checked:
                draw_circle(pos.x+LevelSelectScreen.EditorCheckBox.WIDTH//2, pos.y+LevelSelectScreen.EditorCheckBox.HEIGHT//2, LevelSelectScreen.EditorCheckBox.CIRCLE_RAD, GREEN)

            draw_text("Open in Editor", pos.x+110, pos.y+35, 34, BLACK)

    class LevelButton(UI.Button):
        WIDTH = 1_000
        HEIGHT = 500

        def __init__(self, pos, lvl, color):
            super().__init__(pos, Vector2(LevelSelectScreen.LevelButton.WIDTH, LevelSelectScreen.LevelButton.HEIGHT))
            self.level = lvl
            self.color = color
        
        def apply(self):
            desired_level = self.level
            if get_game().find_by_tag("editor_check").is_toggled():
                desired_level = EditorLevel(self.level)
            get_game().get_cam().target = Vector2(0, 0)
            get_game().defer(lambda: get_game().set_level(desired_level))

        def is_ui_element(self):
            return False

        def draw(self):
            pos = VecMath.floor_i(self.position)
            draw_rectangle_rounded(Rectangle(pos.x, pos.y, LevelSelectScreen.LevelButton.WIDTH, LevelSelectScreen.LevelButton.HEIGHT), 0.5, 50, self.color)

            draw_text(self.level.name, pos.x+500-(measure_text(self.level.name, 54)//2), pos.y+200, 54, WHITE)

    class CustomLevels(UI.Button):
        WIDTH = 200
        HEIGHT = 100

        def __init__(self):
            super().__init__(Vector2(), Vector2(LevelSelectScreen.CustomLevels.WIDTH, LevelSelectScreen.CustomLevels.HEIGHT))
            self.toggled = False
            self.text = "Custom Levels"
            self.levels = []
            self.always_think = True
        
        def is_toggled(self):
            return self.toggled

        def get_tag(self):
            return "customlevels_button"

        def find_custom_level_files(self):
            total_files = []
            for root, dirs, files in os.walk("./custom_levels"):
                for file in files:
                    if os.path.splitext(file)[1] == ".level": # splittext()[1] is the file extension
                        path = os.path.join(root, file)
                        total_files.append(path)
            
            return total_files

        def load_custom_level_buttons(self):
            self.levels.clear()
            files = self.find_custom_level_files()
            print("loading", files)

            x = -500
            for i in files:
                level = Level.from_file(i)
                self.levels.append(level)

                button = LevelSelectScreen.LevelButton(Vector2(x, 700), level, RED)
                button.get_tag = lambda: "custom_level_button"

                x += 1_500
                get_game().make([button])

        def apply(self):
            self.toggled = not self.toggled
            if self.toggled:
                self.text = "Normal Levels"
                get_game().get_cam().target.x = 0
                get_game().get_cam().target.y = 1_000
                
                self.load_custom_level_buttons()
            else:
                get_game().get_cam().target.x = 0
                get_game().get_cam().target.y = 0
                self.text = "Custom Levels"
                for i in get_game().find_many_by_tag("custom_level_button"):
                    get_game().destroy([i])
            
            cam_holder = get_game().find_by_tag("cam_holder")
            cam_holder.index = 0
        
        def logic(self):
            super().logic()
            self.position = VecMath.add(get_game().get_cam().target, Vector2(400, 210))
            self.area.position = clone_vec(self.position)

        def is_ui_element(self):
            return False

        def draw(self):
            pos = VecMath.floor_i(self.position)
            draw_rectangle_rounded(Rectangle(pos.x, pos.y, LevelSelectScreen.CustomLevels.WIDTH, LevelSelectScreen.CustomLevels.HEIGHT), 0.5, 50, DARKGRAY)

            draw_text(self.text, pos.x+210-(measure_text(self.text, 54)//2), pos.y+35, 24, WHITE)


    def __init__(self):
        super().__init__("Level Select Screen", LevelSelectScreen.level_data)
    
    @staticmethod
    def get_level_buttons():
        buttons = []
        x = -500
        for level in LevelSelectScreen.LEVELS:
            buttons.append(LevelSelectScreen.LevelButton(Vector2(x, -300), level, DARKGRAY))
            x += 1_500
        return buttons
    
    @staticmethod
    def level_data():
        objs = [LevelSelectScreen.LevelSelectCamera(), LevelSelectScreen.EditorCheckBox(), LevelSelectScreen.CustomLevels()]

        objs += LevelSelectScreen.get_level_buttons()
        
        return objs

class BackgroundLoader:
    ID_MAP = [
        None, 
        "textures/backgrounds/ocean_sunrise.png"
    ]

    CACHED = {}

    @staticmethod
    def path_from_id(id):
        return BackgroundLoader.ID_MAP[id]
    
    @staticmethod
    def backgrounds():
        return len(BackgroundLoader.ID_MAP)
    
    @staticmethod
    def get_sprite_cache(background):
        if background.sprite_path in BackgroundLoader.CACHED:
            return BackgroundLoader.CACHED[background.sprite_path]
        
        if len(BackgroundLoader.CACHED) > 5:
            k = BackgroundLoader.CACHED.keys()[0]
            sprite = BackgroundLoader.CACHED[k]
            unload_texture(sprite)
            BackgroundLoader.CACHED.remove(k)
            print("released a background in cache")

        sprite = background.get_sprite()
        BackgroundLoader.CACHED[background.sprite_path] = sprite
        return sprite
    
    @staticmethod
    def clear_cache():
        for k,v in BackgroundLoader.CACHED.items():
            print(f"unloading '{k}'")
            unload_texture(v)
        BackgroundLoader.CACHED.clear()

class Background(GameObj):
    def __repr__(self):
        return f"Background('{self.sprite_path}', {self.centerx}, {self.tint}, Vector2({self.stretch.x}, {self.stretch.y}), {self.parallax_speed}, {self.fade})"

    def clone(self):
        return Background(self.sprite_path, self.centerx, self.tint, self.stretch, self.parallax_speed, self.fade)

    def __init__(self, sprite_path, centerx=0, tint = WHITE, stretch=Vector2(1,1), parallax_speed = 0, fade=False):
        super().__init__()
        self.always_think = True
        self.sprite_path = sprite_path
        self.parallax_speed = parallax_speed
        self.sprite = None
        self.tint = tint
        self.stretch = stretch
        self.centerx = centerx
        self.moved = False
        self.fade = fade
        self.start_time = get_time()
    
    def manifested(self):
        self.start_time = get_time()
    
    def get_sprite(self):
        if self.sprite is None:
            with RaylibImage(self.sprite_path) as image:
                image_resize_nn(image, int(image.width * self.stretch.x), int(image.height * self.stretch.y))
                self.sprite = load_texture_from_image(image)

        return self.sprite

    def cache_sprite(self):
        return BackgroundLoader.get_sprite_cache(self)
    
    def unload(self):
        if self.sprite is not None:
            unload_texture(self.sprite)
            self.sprite = None

    def destroyed(self):
        self.unload()

    def draw(self):
        cam = get_game().get_cam()
        offset = Vector2Subtract(cam.target, cam.offset)
        offset.x -= (cam.target.x + self.centerx) * self.parallax_speed

        sprite = self.cache_sprite()

        if self.fade:
            desired = int((get_time() - self.start_time) * 200)
            if desired >= 256:
                desired = 255
            tint = Color(*self.tint[:3], desired)
        else:
            tint = self.tint
            
        draw_texture_ex(sprite, offset, 0, 1, tint)
        draw_texture_ex(sprite, Vector2(offset.x + sprite.width, offset.y), 0, 1, tint)
        draw_texture_ex(sprite, Vector2(offset.x + (sprite.width*2), offset.y), 0, 1, tint)
        draw_texture_ex(sprite, Vector2(offset.x + (sprite.width*3), offset.y), 0, 1, tint)


win_inited = False
def main():
    global game
    global win_inited

    game = Game()
    set_config_flags(ConfigFlags.FLAG_WINDOW_RESIZABLE)
    
    win_inited = True
    init_window(screen_width, screen_height, "Geometry Splash")
    set_target_fps(60)
    set_exit_key(-1)


    logo = load_image("textures/Geometry_Splash_Logo.png")
    set_window_icon(logo)
    
    cam = Camera2D(Vector2(screen_mid[0], screen_mid[1]), Vector2(0, 0), 0, 1)
    game.camera = cam

    game.set_level(LevelSelectScreen()) # SET LEVEL

    clear_window_state(ConfigFlags.FLAG_WINDOW_UNFOCUSED)

    fullscreened = False

    last_frame = get_time()
    delta = 1 / 60
    while not window_should_close() and not game.should_end:
        if is_key_pressed(KeyboardKey(0).KEY_F11):
            if fullscreened:
                clear_window_state(ConfigFlags.FLAG_WINDOW_UNDECORATED)
                set_window_size(screen_width, screen_height)
                set_window_position(screen_width//4, screen_height//4)
            else:
                set_window_position(0, 0)
                set_window_size(get_monitor_width(get_current_monitor()), get_monitor_height(get_current_monitor()))
                set_window_state(ConfigFlags.FLAG_WINDOW_UNDECORATED)
            fullscreened = not fullscreened


        visible_threshold = 500
        visible = []
        for i in game.game_objects:
            if i.always_think:
                if isinstance(i, Background):
                    game.background = i
                else:
                    visible.append(i)
                continue
            if i.position.x + visible_threshold >= cam.target.x - (screen_width/2):
                if cam.target.x + (screen_width/2) >= i.position.x - visible_threshold:
                    visible.append(i)
        
        # Logic
        if game.background is not None:
            game.background.logic()
            
        for i in visible:
            i.logic()
        
        desired_zoom = get_screen_width() / screen_width

        game.camera.zoom = desired_zoom
        game.camera.offset = Vector2(get_screen_width()//2, get_screen_height()//2)

        # Drawing
        begin_drawing()
        clear_background(Color(200, 200, 200))
        
        begin_mode_2d(cam)
        if game.background is not None:
            game.background.predraw()
            game.background.draw()
            game.background.postdraw()
        
        player = game.get_player()

        if (freeze_loc := get_game().frozen_cam) is not None:
            cam.target = VecMath.lerp(clone_vec(cam.target), clone_vec(freeze_loc), 0.3)

        desired_cam_y_locked = False
        if (freeze_y := get_game().frozen_y_cam) is not None:
            desired_cam_y = lerp(cam.target.y, freeze_y, 0.3)
            desired_cam_y_locked = True

        if freeze_loc is None and player is not None:
            if not desired_cam_y_locked:
                desired_cam_y = lerp(cam.target.y, 0, 0.15)

                if not player.halted and player.position.y < -200:
                    desired_cam_y = lerp(cam.target.y, player.position.y+200, 0.15)

            desired_cam_x = lerp(cam.target.x, player.position.x+200, 0.15)

            if player.halted:
                desired_cam_x = lerp(cam.target.x, get_game().find_by_tag("Win").position.x - 400, 0.3)
            cam.target = Vector2(desired_cam_x, desired_cam_y)

        uis = set()
        ground = None
        lvlman = None
        for i in visible:
            if i.get_tag() == "Ground": # yeah yeah i know i'm being inconsistant
                ground = i
                continue
            if type(i) == EditorLevelManager:
                lvlman = i
                continue
            if i.is_ui_element():
                uis.add(i)
            else:
                i.predraw()
                i.draw()
                i.postdraw()

        if ground is not None: # Why? so it renders ontop of everything
            ground.predraw()
            ground.draw()
            ground.postdraw()

        if lvlman is not None:
            lvlman.predraw()
            lvlman.draw()
            lvlman.postdraw()

        
        game._call_deferred()
        
        end_mode_2d()

        for i in uis:
            i.ui_draw()
        
        if player is not None:
            win = game.find_by_tag("Win")
            if win is not None:
                distance = abs(win.position.x - player.position.x)
                percent = 100 - (distance / (win.position.x + 400)) * 100 # I added 400 cause the player starts -400 units back.
                
                text = f"{round(percent, 1)}%"
                draw_rectangle(get_screen_width()//2 - 170, 10, int(percent)*3, 20, BLUE)
                draw_rectangle_lines(get_screen_width()//2 - 170, 10, 300, 20, DARKBLUE)

                draw_text(text, get_screen_width()//2 + 150, 10, 24, BLACK)

        end_drawing()
        
        delta = get_time() - last_frame
        last_frame = get_time()
    
    close_window()
    win_inited = False

    game.reset()
    BackgroundLoader.clear_cache()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback 
        if win_inited:
            close_window()
        
        sys.stderr.write("EXCEPTION HAS OCCURRED\n")
        traceback.print_exc()

        input("Press enter to conclude program.")
    
