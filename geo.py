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

class Player(GameObj):
    WIDTH = 50
    HEIGHT = 50

    ROTATE_SPEED = 7

    def __repr__(self):
        return f"Player(Vector2({self.position.x}, {self.position.y}))"

    def clone(self):
        return Player(clone_vec(self.start_pos))
    
    def __init__(self, start_pos = Vector2(-400, 0)):
        super().__init__()
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
    
    def kill(self):
        if self.halted: return

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
    
    def logic(self):
        if self.dead: return
        if self.halted: return
        
        self.velocity.x = 5.5 # horizontal speed
        self._act_on_input()
        
        self._fall()
        if self.wantJump and self.grounded:
            self.position.y -= 5 * self.orientation
            self.grounded = False
            self.velocity.y = -15 * self.orientation
        
        self._update_velocity()
        self.area.position = self.position
        
        
    def _act_on_input(self):
        if Input.jump_down():
           self.wantJump = True
        else:
            self.wantJump = False
        
        if Input.reset_level():
            get_game().reload_level()
    
    def _update_velocity(self):
        self.velocity.y = clamp(self.velocity.y, -20, 20)
        self.position = VecMath.add(self.position, self.velocity)
        
    def _fall(self):
        self.velocity.y += 1 * self.orientation
        
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
        
        if not self.grounded:
            self.rotation -= Player.ROTATE_SPEED * self.orientation
        else:
            self.rotation = 0
        
    
    def draw(self):
        if self.dead: return
        pos = VecMath.floor_i(self.position)
        draw_rectangle(pos.x, pos.y, Player.WIDTH, Player.HEIGHT, BLUE)

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
                self.player.kill()
            if self.player.orientation == 1 and self.player.position.y:
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
                self.player.kill()
    
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
        if self.player.orientation == 1:
            verts = self.player.area.vertices()[2:4]
        else:
            verts = self.player.area.vertices()[:2]

        for i in verts:
            touching = self.area.check_collision_with_point(i)
            ground_threshold = 25
            
            if touching:
                if self.player.orientation == 1:
                    if i.y < self.position.y + ground_threshold:
                        self.player.grounded_y = self.area.position.y + bump
                    else:
                        self.player.kill()
                else:
                    bump = self.area.dimension.y
                    if i.y > (self.position.y + bump) + (ground_threshold * -1):
                        self.player.grounded_y = self.area.position.y + bump
                    else: # hit side of tile
                        self.player.kill()
                
    
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
            TileItem(), SpikeItem(), JumpOrbItem(), 
            GravityOrbItem(), JumpPadItem(), GravityPadItem(), 
            WinWallItem()
        ]
        self.held_item_index = 0

        self.held_item = TileItem()
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

win_inited = False
def main():
    global game
    global win_inited
    
    game = Game()
    game.set_level(EditorLevel()) # SET LEVEL
    
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
    



