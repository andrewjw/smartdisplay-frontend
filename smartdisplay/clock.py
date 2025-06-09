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

from i75 import Colour, DateTime, I75, ScreenManager
from i75.graphic_primitives import line
from i75.screens.single_bit_screen import SingleBitScreen
from i75.screens.layers import Layers
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
def render_clock_face(bg: SingleBitScreen) -> None:
    for tick in range(12):
        tick_len = 3 if tick in (0, 3, 6, 9) else 3
        angle = 2 * math.pi * tick / 12.0
        cx, cy = get_center_point(angle)
        x1 = math.floor((31 - tick_len) * math.cos(angle) + cx)
        y1 = math.floor((31 - tick_len) * math.sin(angle) + cy)
        x2 = math.floor(31 * math.cos(angle) + cx)
        y2 = math.floor(31 * math.sin(angle) + cy)

        line(bg, x1, y1, x2, y2)

    line(bg, 32, 3, 32, 0)
    line(bg, 31, 60, 31, 63)
    line(bg, 0, 31, 3, 31)
    line(bg, 60, 32, 63, 32)


def render_hand(screen: SingleBitScreen, length: int, percent: float, set_pixel: bool) -> None:
    angle = 2 * math.pi * percent
    cx, cy = get_center_point(angle)
    line(screen,
         cx,
         cy,
         math.floor(length * math.sin(angle) + cx),
         math.floor(length * -math.cos(angle) + cy),
         set_pixel)


def render_clock(second: SingleBitScreen,
                 minute: SingleBitScreen,
                 hour: SingleBitScreen,
                 now: DateTime,
                 subsecond: int,
                 set_pixel: bool) -> None:
    part_second = subsecond / 1000.0
    render_hand(second, SECOND_LENGTH, (now.second + part_second) / 60.0, set_pixel)


    minute_percent = (now.minute * 60
                      + now.second
                      + part_second) / (60.0 * 60)
    hour_percent = ((now.hour % 12) * (60 * 60)
                    + now.minute * 60
                    + now.second + part_second) / (60.0 * 60 * 12)
    render_hand(minute, MINUTE_LENGTH, minute_percent, set_pixel)
    render_hand(hour, HOUR_LENGTH, hour_percent, set_pixel)


class Clock:
    def __init__(self, i75: I75, manager: ScreenManager) -> None:
        self.bg = SingleBitScreen(64, 64, Colour.fromrgb(255, 255, 255))
        self.second = SingleBitScreen(64, 64, Colour.fromrgb(255, 0, 0))
        self.minute = SingleBitScreen(64, 64, Colour.fromrgb(255, 255, 255))
        self.hour = SingleBitScreen(64, 64, Colour.fromrgb(255, 255, 255))

        manager.set_screen(
            Layers(Colour.fromrgb(0, 0, 0), [self.bg, self.second, self.minute, self.hour]))

        render_clock_face(self.bg)

        self.total_time = 0
        self.old_time = i75.now()
        self.old_subsecond = 0
        self.base_ticks = 0

    def render(self, i75: I75, frame_time: int) -> bool:
        now = EuropeLondon.to_localtime(i75.now())
        subsecond = i75.ticks_diff(i75.ticks_ms(), self.base_ticks) % 1000

        if now != self.old_time and subsecond > self.old_subsecond \
           and subsecond < 9975:
            self.base_ticks -= 25
        elif now == self.old_time and subsecond < self.old_subsecond:
            self.base_ticks += 25
            subsecond = 999

        render_clock(self.second,
                     self.minute,
                     self.hour,
                     self.old_time,
                     self.old_subsecond,
                     False)
        render_clock(self.second,
                     self.minute,
                     self.hour,
                     now,
                     subsecond,
                     True)

        self.old_time = now
        self.old_subsecond = subsecond

        self.total_time += frame_time
        return self.total_time >= 30000
