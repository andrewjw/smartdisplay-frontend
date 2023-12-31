#!/usr/bin/env micropython
# smartdisplay-frontend
# Copyright (C) 2023 Andrew Wilkinson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Ball collision code adapted from https://github.com/ekiefl/pooltool/tree/main

import math
import random
try:
    from typing import Tuple, Optional, Union
except ImportError:
    pass
import sys

import picographics

from i75 import I75


class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def unit(self) -> "Vector":
        length = self.length()
        return Vector(self.x / length, self.y / length)

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, other: float) -> "Vector":
        return Vector(self.x * other, self.y * other)

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(self.x - other.x, self.y - other.y)

    def __gt__(self, other: Union[int, "Vector"]) -> bool:
        if isinstance(other, Vector):
            return (self.x ** 2 + self.y ** 2) > (other.x ** 2 + other.y ** 2)
        else:
            return (self.x ** 2 + self.y ** 2) > other ** 2

    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __str__(self) -> str:
        return f"<V {self.x} {self.y}>"


class Matrix:
    def __init__(self) -> None:
        self.values = [[0.0, 0.0], [0.0, 0.0]]

    def dot(self, v: Vector) -> Vector:
        return Vector(self.values[0][0] * v.x + self.values[0][1] * v.y,
                      self.values[1][0] * v.x + self.values[1][1] * v.y)


class Ball:
    def __init__(self,
                 i75: I75,
                 centre: Vector,
                 size: int,
                 motion: Vector) -> None:
        self.colour = i75.display.create_pen(*from_hsv(random.random(),
                                                       1.0,
                                                       1.0))
        self.centre = centre
        self.size = size
        self.motion = motion
        self.growing = size < 5

    def update(self, frame_time: int):
        self.centre = self.centre + self.motion * (frame_time / 1000.0)

        if self.centre.x - self.size <= 0:
            self.motion.x = abs(self.motion.x)
        if self.centre.x + self.size > 63:
            self.motion.x = -abs(self.motion.x)

        if self.centre.y - self.size <= 0:
            self.motion.y = abs(self.motion.y)
        if self.centre.y + self.size > 63:
            self.motion.y = -abs(self.motion.y)

    def collide(self, other: "Ball") -> None:
        distance = self.centre - other.centre
        if distance > (self.size + other.size):
            return

        next = self.centre + self.motion * 0.01
        onext = other.centre + other.motion * 0.01
        if (next - onext) > distance:
            return

        n = (other.centre - self.centre).unit()
        t = coordinate_rotation(n, math.pi / 2)

        v_rel = self.motion - other.motion
        v_mag = v_rel.length()

        beta = angle(v_rel, n)

        self.motion = t * v_mag * math.sin(beta) + other.motion
        other.motion = n * v_mag * math.cos(beta) + other.motion

    def render(self, i75: I75, colour: Optional[picographics.Pen] = None):
        i75.display.set_pen(self.colour if colour is None else colour)
        i75.display.circle(round(self.centre.x),
                           round(self.centre.y),
                           self.size)

    def resize(self):
        if random.random() > 0.2:
            return True
        if self.growing:
            self.size += 1
            self.motion *= 0.9
            if self.size >= 6:
                self.growing = False
        else:
            self.size -= 1
            self.motion *= 1.1
        return self.size > 1


def coordinate_rotation(v: Vector, phi: float) -> Vector:
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    rotation = Matrix()
    rotation.values[0][0] = cos_phi
    rotation.values[0][1] = -sin_phi
    rotation.values[1][0] = sin_phi
    rotation.values[1][1] = cos_phi

    return rotation.dot(v)


def angle(v2: Vector, v1: Vector) -> float:
    ang = math.atan2(v2.y, v2.x) - math.atan2(v1.y, v1.x)

    if ang < 0:
        return 2 * math.pi + ang

    return ang


def from_hsv(h, s, v):
    i = math.floor(h * 6.0)
    f = h * 6.0 - i
    v *= 255.0
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    i = int(i) % 6
    if i == 0:
        return int(v), int(t), int(p)
    if i == 1:
        return int(q), int(v), int(p)
    if i == 2:
        return int(p), int(v), int(t)
    if i == 3:
        return int(p), int(q), int(v)
    if i == 4:
        return int(t), int(p), int(v)
    if i == 5:
        return int(v), int(p), int(q)


def generate_ball(i75: I75, size: int, v: Vector) -> Ball:
    return Ball(i75, v, size, Vector(random.random() * 8,
                                     random.random() * 8))


class BouncingBalls:
    def __init__(self, i75: I75) -> None:
        self.black = i75.display.create_pen(0, 0, 0)

        self.balls = [generate_ball(i75, 1, Vector(10, 20)),
                      generate_ball(i75, 3, Vector(20, 10)),
                      generate_ball(i75, 5, Vector(40, 10))]

        self.fixed_update_time = 100
        self.frame_time = 0
        self.total_time = 0
        self.new_balls_time = 0

    def render(self, i75: I75, frame_time: int) -> bool:
        self.frame_time += frame_time
        self.new_balls_time += frame_time
        self.total_time += frame_time

        if self.frame_time < self.fixed_update_time:
            return False

        while self.frame_time > self.fixed_update_time:
            for ball in self.balls:
                ball.render(i75, self.black)
                ball.update(self.fixed_update_time)

            for i in range(len(self.balls) - 1):
                for j in range(i+1, len(self.balls)):
                    self.balls[i].collide(self.balls[j])

            self.frame_time -= self.fixed_update_time

        for ball in self.balls:
            ball.render(i75)

        while self.new_balls_time > 5000:
            [b.render(i75, self.black) for b in self.balls]
            self.balls = [b for b in self.balls if b.resize()]

            if len(self.balls) < 5 and random.random() < 0.2:
                self.balls.append(
                    generate_ball(i75,
                                  2,
                                  Vector(int(random.random() * 59) + 5,
                                         int(random.random() * 59) + 5)))
            [b.render(i75) for b in self.balls]
            self.new_balls_time -= 5000

        i75.display.update()

        return self.total_time >= 30000

    def reset_timer(self) -> None:
        self.total_time = 0
