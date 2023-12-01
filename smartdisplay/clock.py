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

import math
try:
    from typing import Tuple
except ImportError:
    pass
import sys

import picographics

from i75 import DateTime, I75
from i75.tz import EuropeLondon

HOUR_LENGTH = 25
MINUTE_LENGTH = 30
SECOND_LENGTH = 30


def get_center_point(angle) -> Tuple[int, int]:
    if angle < math.pi / 2:
        return (32, 31)
    if angle < math.pi:
        return (32, 32)
    if angle < 2 * math.pi / 3:
        return (31, 32)
    return (31, 31)


# This currently has issues due to the i75 working in single precision
# floats, and Python3 using doubles.
def render_clock_face(i75: I75) -> None:
    for tick in range(12):
        tick_len = 3 if tick in (0, 3, 6, 9) else 3
        angle = 2 * math.pi * tick / 12.0
        cx, cy = get_center_point(angle)
        x1 = math.floor((31 - tick_len) * math.cos(angle) + cx)
        y1 = math.floor((31 - tick_len) * math.sin(angle) + cy)
        x2 = math.floor(31 * math.cos(angle) + cx)
        y2 = math.floor(31 * math.sin(angle) + cy)

        i75.display.line(x1, y1, x2, y2)

    i75.display.line(32, 3, 32, 0)
    i75.display.line(31, 60, 31, 63)
    i75.display.line(0, 31, 3, 31)
    i75.display.line(60, 32, 63, 32)


def render_hand(i75: I75, length: int, percent: float) -> None:
    angle = 2 * math.pi * percent
    cx, cy = get_center_point(angle)
    i75.display.line(cx,
                     cy,
                     math.floor(length * math.sin(angle) + cx),
                     math.floor(length * -math.cos(angle) + cy))


def render_clock(i75: I75,
                 white: picographics.Pen,
                 red: picographics.Pen,
                 now: DateTime,
                 subsecond: int,
                 display_ticks: bool = True) -> None:
    if display_ticks:
        i75.display.set_pen(white)
        render_clock_face(i75)

    i75.display.set_pen(red)

    part_second = subsecond / 1000.0
    render_hand(i75, SECOND_LENGTH, (now.second + part_second) / 60.0)

    i75.display.set_pen(white)

    minute_percent = (now.minute * 60
                      + now.second
                      + part_second) / (60.0 * 60)
    hour_percent = ((now.hour % 12) * (60 * 60)
                    + now.minute * 60
                    + now.second + part_second) / (60.0 * 60 * 12)
    render_hand(i75, MINUTE_LENGTH, minute_percent)
    render_hand(i75, HOUR_LENGTH, hour_percent)


class Clock:
    def __init__(self, i75: I75) -> None:
        self.white = i75.display.create_pen(255, 255, 255)
        self.red = i75.display.create_pen(255, 0, 0)
        self.black = i75.display.create_pen(0, 0, 0)

        self.total_time = 0
        self.old_time = i75.now()
        self.old_subsecond = 0
        self.base_ticks = 0

    def render(self, i75: I75, frame_time: int) -> bool:
        now = i75.now()
        subsecond = i75.ticks_diff(i75.ticks_ms(), self.base_ticks) % 1000

        if now != self.old_time and subsecond > self.old_subsecond \
           and subsecond < 9975:
            self.base_ticks -= 25
        elif now == self.old_time and subsecond < self.old_subsecond:
            self.base_ticks += 25
            subsecond = 999

        now = EuropeLondon.to_localtime(now)

        render_clock(i75,
                     self.black,
                     self.black,
                     self.old_time,
                     self.old_subsecond,
                     False)
        render_clock(i75,
                     self.white,
                     self.red,
                     now,
                     subsecond)

        self.old_time = now
        self.old_subsecond = subsecond

        i75.display.update()

        self.total_time += frame_time
        return self.total_time >= 30000
