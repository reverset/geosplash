
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 13:32:55 2023

@author: Sea bass Rueda
"""

from pyray import *

import math
import random
import sys
import time

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
        return is_key_pressed(KeyboardKey(0).KEY_SPACE) or is_key_pressed(KeyboardKey(0).KEY_UP) or is_mouse_button_pressed(0)
    
    @staticmethod
    def jump_down():
        return is_key_down(KeyboardKey(0).KEY_SPACE) or is_key_down(KeyboardKey(0).KEY_UP) or is_mouse_button_down(0)
    
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
    def floor_i(v1):
        return Vec2i(v1.x, v1.y)
    
    @staticmethod
    def distance(v1, v2):
        x_dist = abs(v1.x - v2.x)
        y_dist = abs(v1.y - v2.y)
        return math.sqrt((x_dist ** 2) + (y_dist ** 2))

    @staticmethod
    def lerp(v1, v2, dt):
        return VecMath.mul(VecMath.add(v1, v2), Vector2(dt, dt))

class Rectangle:
    def __init__(self, position, dimension):
        self.position = position
        self.dimension = dimension
    
    def vertices(self):
        up_left = self.position
        up_right = VecMath.add(self.position, Vector2(self.dimension.x, 0))
        bot_right = VecMath.add(self.position, Vector2(self.dimension.x, self.dimension.y))
        bot_left = VecMath.add(self.position, Vector2(0, self.dimension.y))
        
        return [up_left, up_right, bot_left, bot_right]
    
    def check_collision_with_point(rec, point):
        v = rec.vertices()
        up_left, up_right, bot_left, bot_right = v[0], v[1], v[2], v[3]
        if up_left.x <= point.x <= bot_right.x:
            if up_left.y <= point.y <= bot_left.y:
                return True
        return False
        
        

def clone_vec(vec):
    return Vector2(vec.x, vec.y)

class GameObj:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.area = None # Area should be of type Rectangle
        self.always_think = False
        self.rotation = 0
        self.origin = None
    
    def clone(self):
        raise RuntimeError("Clone not supported for the given GameObj")

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
    
    def postdraw(self):
        rl_pop_matrix()
    
    def draw(self):
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
    
    def reset_rot(self):
        rl_pop_matrix()

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
    
    """
    WARNING ONLY CHECKS IF COLLIDES WITH VERTICES
    """
    def sphere_check(self, pos, radius, ignore = None):
        for i in self.game_objects:
            if i == ignore: continue
            
            if i.area == None: continue
            verts = i.area.vertices()
            if verts == None: continue
        
            for j in verts:
                if VecMath.distance(j, pos) <= radius:
                    return i
        return None
    
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
        self.game_objects = []
    
    def find_by_tag(self, name):
        for i in self.game_objects:
            if i.get_tag() == name:
                return i
        return None

class Level:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    
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
    WIDTH = 50
    HEIGHT = 50
    GRAVITY = 1

    SHIP_WIDTH = 40
    SHIP_HEIGHT = 20
    SHIP_CLIMB_SPEED = 0.7
    SHIP_GRAVITY = 0.3


    ROTATE_SPEED = 7

    def __repr__(self):
        return f"Player(Vector2({self.position.x}, {self.position.y}))"

    def clone(self):
        return Player(clone_vec(self.start_pos))
    
    def set_mode(self, mode):
        if mode not in self.modes:
            raise RuntimeError(f"Attempted to switch to mode '{mode}', which does not exist")
        self.current_mode = mode
        self.rotation = 0

    def __init__(self, start_pos = Vector2(-400, 0)):
        super().__init__()

        self.modes = {
            "square": (self.square_logic, self.square_draw),
            "ship": (self.ship_logic, self.ship_draw)
        }

        self.current_mode = "square"

        self.start_pos = clone_vec(start_pos)
        self.position = start_pos
        self.dead = False
        self.area = Rectangle(
                self.position,
                Vector2(Player.WIDTH, Player.HEIGHT)
            )
        
        self.velocity = Vector2(0, 0)
        
        self.wantJump = False
        self.grounded = False
        self.grounded_y = Ground.ALTITUDE
        self.orientation = 1

        self.halted = False
    
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

    def logic(self):
        if self.dead: return
        if self.halted: return
        
        self.velocity.x = 5.5 # horizontal speed
        self._act_on_input()
        
        self.modes[self.current_mode][0]()
        
        self._update_velocity()
        self.area.position = self.position # ensure that hitbox is adjusted to the visible position, can NOT clone the vector here because of timing & pointers 
        
        
    def _act_on_input(self):
        if Input.jump_down():
           self.wantJump = True
        else:
            self.wantJump = False
        
        if Input.reset_level():
            get_game().reload_level()
    
    @staticmethod
    def _closer(n, options):
        closest = None
        close_value = sys.maxsize
        for i in options:
            if abs(n - i) < close_value:
                closest = i
                close_value = i - n
        return closest
    
    def _square_handle_rotation(self):
        # if not self.grounded:
        #     self.rotation -= Player.ROTATE_SPEED * self.orientation
        #     if self.rotation > 360:
        #         self.rotation = 0
        #     elif self.rotation < -360:
        #         self.rotation = 0
        # else:
        #     close = self._closer(self.rotation, [0, 90, 180, 360, -90, -180, -360])
        #     #print("close =", close, ", rot =", self.rotation)
        #     STEP = 20
        #     if abs(close - self.rotation) < STEP:
        #         self.rotation = close
        #     elif close > self.rotation:
        #         self.rotation += STEP
        #     elif close < self.rotation:
        #         self.rotation -= STEP
        if not self.grounded: # TODO: smoother snap
            self.rotation -= Player.ROTATE_SPEED * self.orientation
        else:
            self.rotation = 0
    
    def _ship_handle_rotation(self):
        self.rotation = -self.velocity.y * 3
    
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
        draw_rectangle(pos.x, pos.y, Player.WIDTH, Player.HEIGHT, BLUE)
    
    def ship_draw(self):
        pos = VecMath.floor_i(self.position)
        pos.x += Player.WIDTH//2
        pos.y += Player.HEIGHT//2

        draw_ellipse(pos.x, pos.y, Player.SHIP_WIDTH, Player.SHIP_HEIGHT, BLUE)

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
        self.area = Rectangle(
            VecMath.sub(self.position, Vector2(5, 30)),
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
            if Rectangle.check_collision_with_point(player_area, vert):
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
        self.area = Rectangle(
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
        else:
            rel_verts = verts[:2]

        for i in verts:
            touching = self.area.check_collision_with_point(i)
            ground_threshold = 25
            
            if touching:
                if i not in rel_verts:
                    self.player.kill("bonked on Tile")
                    break
                if self.player.orientation == 1:
                    if i.y < self.position.y + ground_threshold:
                        self.player.grounded_y = self.area.position.y + bump
                        break
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
    
    def tapped(self):
        pass
    
    def manifested(self):
        self.player = get_game().get_player()
    
    def _center_player(self):
        return Vector2( self.player.position.x + Player.WIDTH*0.5, self.player.position.y + Player.HEIGHT*0.5)
    
    def logic(self):
        if self.already_tapped: return
        if self.player is None: return
        
        if Input.jump_down():
            if VecMath.distance(self._center_player(), self.position) <= self.radius + Player.WIDTH:
                self.already_tapped = True
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
        
        self.area = Rectangle(
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
        
        verts = self.area.vertices()
        
        for i in verts:
            if Rectangle.check_collision_with_point(self.player.area, i):
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
        
        player.position.y -= 1 * player.orientation
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

            timer = TimerObj(5, lambda: get_game().reload_level())
            get_game().make([timer, p])

            p.emit( clone_vec(self.player.position) )
            timer.start()

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
        self.area = Rectangle(
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
            if Rectangle.check_collision_with_point(self.area, i):
                self.apply()
                self.enabled = False
                break
    
    def draw(self):
        p = VecMath.floor_i(self.position)
        draw_rectangle(p.x, p.y, Portal.WIDTH, Portal.HEIGHT, self.color)

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

class Item:
    def __init__(self, name):
        self.name = name

    def supports_rotation(self):
        return False

    def draw_preview(self, where):
        pass
    
    def offset(self, where):
        return VecMath.floor_i(where)

    def origin(self, where):
        return Vector2(0, 0)

    def place(self, where):
        pass

class PlayerSpawnItem(Item):
    def __init__(self):
        super().__init__("PlayerSpawn")
    
    def draw_preview(self, where):
        draw_circle(where.x, where.y, PlayerSpawn.RADIUS, GRAY)
    
    def place(self, where, _rot):
        return PlayerSpawn(where)

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
        super().__init__("JumpOrb")
    
    def place(self, where, _rot):
        return JumpOrb(where)

    def draw_preview(self, where):
        draw_circle(where.x, where.y, Orb.RADIUS, JumpOrb.COLOR)
        draw_circle_lines(where.x, where.y, Orb.RADIUS + 1, JumpOrb.BORDER_COLOR)

class GravityOrbItem(Item):
    def __init__(self):
        super().__init__("GravityOrb")
    
    def place(self, where, _rot):
        return GravityOrb(where)

    def draw_preview(self, where):
        draw_circle(where.x, where.y, Orb.RADIUS, GravityOrb.COLOR)
        draw_circle_lines(where.x, where.y, Orb.RADIUS + 1, GravityOrb.BORDER_COLOR)

class JumpPadItem(Item):
    def __init__(self):
        super().__init__("JumpPad")

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
        super().__init__("GravityPad")

    def offset(self, where):
        w = VecMath.floor_i(where)
        w.x -= Pad.WIDTH // 2
        w.y += 5 # to align with ground
        return w

    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Pad.WIDTH, Pad.HEIGHT, GravityPad.COLOR)
    
    def place(self, where, _rot):
        return GravityPad(where)

class ShipPortalItem(Item):
    def __init__(self):
        super().__init__("ShipPortal")
    
    def place(self, where, _rot):
        return ShipPortal(where)
    
    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, ShipPortal.COLOR)

class SquarePortalItem(Item):
    def __init__(self):
        super().__init__("SquarePortal")
    
    def place(self, where, _rot):
        return SquarePortal(where)
    
    def draw_preview(self, where):
        draw_rectangle(where.x, where.y, Portal.WIDTH, Portal.HEIGHT, SquarePortal.COLOR)



class WinWallItem(Item):
    def __init__(self):
        super().__init__("WinWall")
    
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
    
    def logic(self):
        if is_key_pressed(KeyboardKey(0).KEY_T):
            def get_editor_objs():
                objs = self.editor.get_saved()
                for i in objs[:]:
                    if i.get_tag() == "Player" or i.get_tag() == "Preview":
                        objs.remove(i)
                        
                objs.append(self.editor)
                return objs

            get_game().defer(lambda: get_game().set_level(EditorLevel(get_editor_objs)))

class EditorLevelManager(GameObj):
    ROUND_WIDTH = -1
    CAM_SPEED = 10

    def __init__(self):
        super().__init__()
        self.always_think = True

        self.items = [
            PlayerSpawnItem(), TileItem(), SpikeItem(), JumpOrbItem(),
            GravityOrbItem(), JumpPadItem(), GravityPadItem(),
            ShipPortalItem(), SquarePortalItem(), WinWallItem()
        ]
        self.held_item_index = 0

        self.held_item = self.items[self.held_item_index]
        self.rotation = 0

        self.saved = []
    
    def get_saved(self):
        return [o.clone() for o in self.saved]

    def save_objs(self):
        self.saved.clear()
        for i in get_game().game_objects:
            if type(i) == EditorLevelManager:
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
        if is_key_down(KeyboardKey(0).KEY_D):
            cam.target.x += EditorLevelManager.CAM_SPEED
        elif is_key_down(KeyboardKey(0).KEY_A):
            cam.target.x -= EditorLevelManager.CAM_SPEED
        
        if is_key_down(KeyboardKey(0).KEY_W):
            cam.target.y -= EditorLevelManager.CAM_SPEED
        elif is_key_down(KeyboardKey(0).KEY_S):
            cam.target.y += EditorLevelManager.CAM_SPEED

    @staticmethod
    def get_desired_mouse_pos():
        cam = get_game().get_cam()
        pos = VecMath.sub(get_mouse_position(), VecMath.sub(cam.offset, cam.target))
        pos.x = round(pos.x, EditorLevelManager.ROUND_WIDTH)
        pos.y = round(pos.y, EditorLevelManager.ROUND_WIDTH)
        return pos

    def logic(self):
        self.pick_item()
        self.cam_move()

        if is_key_pressed(KeyboardKey(0).KEY_T):
            objs = [EditorLevelPreview(self), Player()]
            self.save_objs()
            for i in self.saved:
                objs.append(i)
            self.saved = objs

            print("SAVED LEVEL CODE: -=-=-=-=-=")
            print(self.saved)
            print("LEVEL CODE ^^^^^^^-=-=-=-=-=")
            test_level = Level("Preview Level", self.get_saved)
            get_game().defer(lambda: get_game().set_level(test_level))

        pos = EditorLevelManager.get_desired_mouse_pos()
        if self.held_item is not None:
            actual = self.held_item.offset(pos)
            actual.y -= 5

            if is_mouse_button_pressed(0):
                block = self.held_item.place(actual, self.rotation)
                get_game().make([block])
            
            if is_mouse_button_down(1):
                for i in get_game().game_objects:
                    if i.position.x == actual.x and i.position.y == actual.y:
                        get_game().game_objects.remove(i)
                        break
            
            if is_key_pressed(KeyboardKey(0).KEY_R):
                self.rotation += 45
            
            if is_key_pressed(KeyboardKey(0).KEY_P):
                for i in get_game().game_objects[:]:
                    if type(i) == WinWall:
                        get_game().game_objects.remove(i)
                        break

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
                
    
    def draw(self):
        cam = get_game().get_cam()
        cam_pos = VecMath.floor_i(cam.target)
        cam_off = VecMath.floor_i(cam.offset)
        draw_text(f"{cam_pos.x}, {cam_pos.y}", cam_pos.x - cam_off.x, cam_pos.y - cam_off.y, 54, BLACK )

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

class HardLevel(Level):
    def __init__(self):
        super().__init__("HardLevel", HardLevel.level_data)
    
    @staticmethod
    def level_data():
        return [Player(Vector2(-400.0, 0.0)), Ground(), GravityPad(Vector2(-365, 120)), GravityPad(Vector2(-315, 120)), GravityPad(Vector2(-275, -20)), GravityPad(Vector2(-225, -20)), Spike(Vector2(-100.0, 300.0), 0), Tile(Vector2(75.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(100.0, 250.0), 0), Tile(Vector2(315.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(315.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(365.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(415.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(465.0, 200.0), Vector2(50.0, 50.0)), Spike(Vector2(290.0, 300.0), 90), Spike(Vector2(290.0, 260.0), 90), Spike(Vector2(490.0, 200.0), 360), Spike(Vector2(530.0, 200.0), 360), Tile(Vector2(515.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(565.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(565.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(570.0, 200.0), 360), Tile(Vector2(615.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(665.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(715.0, 200.0), Vector2(50.0, 50.0)), Spike(Vector2(740.0, 200.0), 360), Tile(Vector2(765.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(765.0, 200.0), Vector2(50.0, 50.0)), Spike(Vector2(790.0, 150.0), 360), JumpOrb(Vector2(750, 125)), Tile(Vector2(815.0, 100.0), Vector2(50.0, 50.0)), Spike(Vector2(840.0, 100.0), 360), Tile(Vector2(815.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(815.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(815.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(865.0, 50.0), Vector2(50.0, 50.0)), Spike(Vector2(890.0, 50.0), 360), Tile(Vector2(995.0, 50.0), Vector2(50.0, 50.0)), Spike(Vector2(1020.0, 50.0), 360), Tile(Vector2(865.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(1045.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(1095.0, 150.0), Vector2(50.0, 50.0)), Spike(Vector2(1070.0, 100.0), 360), Spike(Vector2(1120.0, 150.0), 360), Tile(Vector2(1145.0, 200.0), Vector2(50.0, 50.0)), Spike(Vector2(1170.0, 200.0), 360), Tile(Vector2(1195.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(1245.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(1295.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(1295.0, 150.0), Vector2(50.0, 50.0)), Spike(Vector2(1370.0, 200.0), 1350), Spike(Vector2(1370.0, 150.0), 1350), Spike(Vector2(1370.0, 100.0), 1350), Spike(Vector2(1370.0, 50.0), 1350), Tile(Vector2(1295.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(1295.0, 50.0), Vector2(50.0, 50.0)), Tile(Vector2(1295.0, 0.0), Vector2(50.0, 50.0)), GravityPad(Vector2(1465, 290)), Tile(Vector2(1295.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1345.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1395.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1445.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1495.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1545.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1595.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1645.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1695.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1745.0, -50.0), Vector2(50.0, 50.0)), Spike(Vector2(1680.0, 50.0), 2340), Spike(Vector2(1710.0, 50.0), 2340), Spike(Vector2(1650.0, 50.0), 2340), Tile(Vector2(1795.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1845.0, -50.0), Vector2(50.0, 50.0)), Spike(Vector2(1880.0, 50.0), 2700), Tile(Vector2(1905.0, -20.0), Vector2(50.0, 50.0)), Spike(Vector2(1930.0, 80.0), 4140), Tile(Vector2(1905.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(1875.0, -50.0), Vector2(50.0, 50.0)), Tile(Vector2(2025.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2075.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2125.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2175.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2225.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2275.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2325.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2375.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2475.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2525.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2575.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2675.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2725.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2775.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2825.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2875.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2925.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(2975.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(3025.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(3075.0, -620.0), Vector2(50.0, 50.0)), Tile(Vector2(3125.0, -620.0), Vector2(50.0, 50.0))]

class ShipLevel(Level):
    def __init__(self):
        super().__init__("ShipLevel", ShipLevel.level_data)
    
    @staticmethod
    def level_data():
        return [Player(Vector2(-400.0, 0.0)), Ground(), Tile(Vector2(-475.0, 110.0), Vector2(50.0, 50.0)), Tile(Vector2(-425.0, 110.0), Vector2(50.0, 50.0)), Tile(Vector2(-375.0, 110.0), Vector2(50.0, 50.0)), Tile(Vector2(-475.0, 160.0), Vector2(50.0, 50.0)), Tile(Vector2(-475.0, 210.0), Vector2(50.0, 50.0)), Tile(Vector2(-475.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(-375.0, 160.0), Vector2(50.0, 50.0)), Tile(Vector2(-375.0, 210.0), Vector2(50.0, 50.0)), Tile(Vector2(-375.0, 250.0), Vector2(50.0, 50.0)), PlayerSpawn(Vector2(-420.0, 55.0)), Tile(Vector2(-285.0, 140.0), Vector2(50.0, 50.0)), Tile(Vector2(-285.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(-285.0, 240.0), Vector2(50.0, 50.0)), Tile(Vector2(-285.0, 260.0), Vector2(50.0, 50.0)), Tile(Vector2(-185.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(-185.0, 230.0), Vector2(50.0, 50.0)), Tile(Vector2(-185.0, 270.0), Vector2(50.0, 50.0)), Tile(Vector2(-85.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(-10.0, 330.0), 0), Spike(Vector2(20.0, 330.0), 0), Spike(Vector2(50.0, 330.0), 0), GravityPad(Vector2(85, 290)), GravityPad(Vector2(125, 100)), GravityPad(Vector2(145, 290)), GravityPad(Vector2(185, 100)), JumpPad(Vector2(265, 290)), Tile(Vector2(385.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(385.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(385.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(485.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(485.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(485.0, 240.0), Vector2(50.0, 50.0)), Tile(Vector2(485.0, 260.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(485.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -90.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -140.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -190.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -240.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -290.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -320.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -370.0), Vector2(50.0, 50.0)), Tile(Vector2(435.0, -380.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -90.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -130.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -180.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -280.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -330.0), Vector2(50.0, 50.0)), Tile(Vector2(535.0, -360.0), Vector2(50.0, 50.0)), Tile(Vector2(565.0, 170.0), Vector2(50.0, 50.0)), Tile(Vector2(565.0, 210.0), Vector2(50.0, 50.0)), Tile(Vector2(565.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(690.0, 250.0), 0), Spike(Vector2(740.0, 250.0), 0), Tile(Vector2(665.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(715.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(890.0, 220.0), 0), Spike(Vector2(890.0, 270.0), 180), Spike(Vector2(940.0, 270.0), 540), Spike(Vector2(940.0, 220.0), 720), JumpOrb(Vector2(820, 185)), JumpOrb(Vector2(1010, 195)), Tile(Vector2(1175.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -110.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -160.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -210.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -260.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -310.0), Vector2(50.0, 50.0)), Tile(Vector2(1175.0, -360.0), Vector2(50.0, 50.0)), ShipPortal(Vector2(1190.0, -15.0)), Tile(Vector2(1175.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(1335.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(1335.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(1335.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -70.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -120.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -170.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -270.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -320.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -370.0), Vector2(50.0, 50.0)), Tile(Vector2(1535.0, -20.0), Vector2(50.0, 50.0)), Spike(Vector2(1560.0, 80.0), 1980), Spike(Vector2(1360.0, 150.0), 2160), Spike(Vector2(1780.0, 110.0), 2160), Tile(Vector2(1755.0, 110.0), Vector2(50.0, 50.0)), Tile(Vector2(1755.0, 160.0), Vector2(50.0, 50.0)), Tile(Vector2(1755.0, 210.0), Vector2(50.0, 50.0)), Tile(Vector2(1755.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -40.0), Vector2(50.0, 50.0)), Spike(Vector2(2010.0, 60.0), 2340), Spike(Vector2(2010.0, 190.0), 2520), Spike(Vector2(2060.0, 190.0), 2520), Spike(Vector2(2110.0, 190.0), 2520), Spike(Vector2(2160.0, 190.0), 2520), Spike(Vector2(2210.0, 190.0), 2520), Spike(Vector2(2060.0, 60.0), 2700), Spike(Vector2(2110.0, 60.0), 2700), Spike(Vector2(2160.0, 60.0), 2700), Tile(Vector2(2035.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(2085.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(2135.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -40.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(2035.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(2085.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(2135.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, 190.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, 240.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, 220.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, 260.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -90.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -130.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -180.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -280.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -320.0), Vector2(50.0, 50.0)), Tile(Vector2(1985.0, -370.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -90.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -130.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -180.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -280.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -330.0), Vector2(50.0, 50.0)), Tile(Vector2(2185.0, -370.0), Vector2(50.0, 50.0)), Tile(Vector2(1225.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1275.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1325.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1365.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1415.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1455.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1495.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1585.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1635.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1685.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1735.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1785.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1835.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1885.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(1935.0, -230.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 250.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 50.0), Vector2(50.0, 50.0)), Spike(Vector2(2550.0, 0.0), 2880), Spike(Vector2(2600.0, 0.0), 2880), Spike(Vector2(2650.0, 0.0), 2880), Tile(Vector2(2475.0, 0.0), Vector2(50.0, 50.0)), Tile(Vector2(2525.0, 0.0), Vector2(50.0, 50.0)), Tile(Vector2(2575.0, 0.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 0.0), Vector2(50.0, 50.0)), Spike(Vector2(2540.0, -120.0), 3060), Spike(Vector2(2580.0, -120.0), 3060), Spike(Vector2(2620.0, -120.0), 3060), Spike(Vector2(2660.0, -120.0), 3060), Tile(Vector2(2475.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2525.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2575.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2635.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, -220.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, -270.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, -320.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, -370.0), Vector2(50.0, 50.0)), Tile(Vector2(2425.0, 0.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 50.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 100.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 150.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 200.0), Vector2(50.0, 50.0)), Tile(Vector2(2625.0, 250.0), Vector2(50.0, 50.0)), Spike(Vector2(2850.0, 70.0), 3240), Spike(Vector2(2900.0, 70.0), 3240), Spike(Vector2(2850.0, 120.0), 3420), Spike(Vector2(2900.0, 120.0), 3420), Spike(Vector2(3050.0, -90.0), 3420), Spike(Vector2(3090.0, -90.0), 3420), Spike(Vector2(3050.0, -140.0), 3600), Spike(Vector2(3090.0, -140.0), 3600), WinWall(Vector2(3700.0, -5.0))]

win_inited = False
def main():
    global game
    global win_inited
    
    game = Game()
    game.set_level(EditorLevel(ShipLevel.level_data)) # SET LEVEL
    
    win_inited = True
    init_window(screen_width, screen_height, "Geometry Splash")
    set_target_fps(60)
    
    cam = Camera2D(Vector2(screen_mid[0], screen_mid[1]), Vector2(0, 0), 0, 1)
    game.camera = cam
    
    last_frame = get_time()
    delta = 1 / 60
    while not window_should_close() and not game.should_end:
        visible_threshold = 500
        visible = []
        for i in game.game_objects:
            if i.always_think:
                visible.append(i)
                continue
            if i.position.x + visible_threshold >= cam.target.x - (screen_width/2):
                if cam.target.x + (screen_width/2) >= i.position.x - visible_threshold:
                    visible.append(i)
                
        # Logic
        for i in visible:
            i.logic()
        
        # Drawing
        begin_drawing()
        clear_background(WHITE)
        
        begin_mode_2d(cam)

        
        player = game.get_player()
        if player is not None:
            desired_cam_y = 0
            if not player.halted and player.position.y < -200:
                # desired_cam_y = ((cam.target.y + player.position.y) * 0.6) + 100
                desired_cam_y = VecMath.lerp(Vector2(cam.target.x, cam.target.y + 200), player.position, 0.5).y

            desired_cam_x = player.position.x
            if player.halted:
                desired_cam_x = cam.target.x
            cam.target = Vector2(desired_cam_x, desired_cam_y)

        ground = None
        for i in visible:
            if i.get_tag() == "Ground":
                ground = i
                continue
            i.predraw()
            i.draw()
            i.postdraw()

        if ground is not None: # Why? so it renders ontop of everything
            ground.predraw()
            ground.draw()
            ground.postdraw()
        
        game._call_deferred()
        
        end_mode_2d()
        end_drawing()
        
        delta = get_time() - last_frame
        last_frame = get_time()
    
    close_window()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if win_inited:
            close_window()
        
        sys.stderr.write("EXCEPTION HAS OCCURRED\n")
        raise e
    
