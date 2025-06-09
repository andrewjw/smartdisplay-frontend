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
import urequests

from i75 import Colour, I75, ScreenManager, render_text, text_boundingbox
from i75.screens.indexed_colour_screen import IndexedColourScreen

from .font import FONT

TITLE = "House Temps"


class Room:
    def __init__(self,
                 title: str,
                 index: str,
                 limit: Tuple[int, int, int]) -> None:
        self.title = title
        self.index = index
        self.limit = limit


ROOMS = [
    Room("Main:", "mainbedroom", (19, 23, 25)),
    Room("Alex:", "alexbedroom", (19, 23, 25)),
    Room("Harriet:", "harrietbedroom", (19, 23, 25)),
    Room("Kitchen:", "kitchen", (19, 23, 25)),
    Room("Lounge:", "lounge", (19, 23, 25)),
    Room("Office:", "office", (19, 23, 25)),
    Room("Outside:", "outside", (2, 24, 28)),
]


class HouseTemperature:
    def __init__(self, backend: str, manager: ScreenManager) -> None:
        self.rendered = False
        self.total_time = 0

        colours = {
            0: Colour.fromrgb(0, 0, 0),
            1: Colour.fromrgb(255, 255, 255),
            2: Colour.fromrgb(0, 0, 255),  # Blue
            3: Colour.fromrgb(255, 255, 0),  # Yellow
            4: Colour.fromrgb(255, 0, 0),  # Red
        }
        self.screen = IndexedColourScreen(64, 64, colours)
        manager.set_screen(self.screen)

        r = urequests.get(f"http://{backend}:6001/house_temperature", timeout=10)
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        room_widths = {room.index: text_boundingbox(FONT, room.title.upper())[0]
                       for room in ROOMS}
        max_room_widths = max([v for v in room_widths.values()]) + 1

        title_width, font_height = text_boundingbox(FONT, TITLE.upper())
        render_text(self.screen,
                    FONT,
                    math.floor(32 - title_width / 2),
                    0,
                    TITLE.upper(),
                    1)

        max_pre_point = 0
        for room in ROOMS:
            if room.index not in self.data:
                continue
            temp_str = f"{self.data[room.index]:.1f}".split(".")[0]
            temp_width, _ = text_boundingbox(FONT, temp_str)
            if temp_width > max_pre_point:
                max_pre_point = temp_width

        y = font_height + 1
        for room in ROOMS:
            render_text(self.screen,
                        FONT,
                        max_room_widths - room_widths[room.index],
                        y,
                        room.title.upper(),
                        1)

            colour = 1
            if room.index in self.data:
                temp = self.data[room.index]
                if temp < room.limit[0]:
                    colour = 2  # Blue
                elif temp > room.limit[2]:
                    colour = 4  # Red
                elif temp > room.limit[1]:
                    colour = 3  # Yellow

                temp_str = f"{temp:.1f}"
                pre_point, _ = text_boundingbox(FONT, temp_str.split(".")[0])
            else:
                temp_str = "-"
                pre_point = max_pre_point
            temp_width, _ = text_boundingbox(FONT, temp_str)
            render_text(self.screen,
                        FONT,
                        max_room_widths + (max_pre_point - pre_point),
                        y,
                        temp_str,
                        colour)
            temp_width += (max_pre_point - pre_point)

            for i in range(3):
                self.screen.set_pixel(max_room_widths + temp_width + i, y, colour)
                self.screen.set_pixel(max_room_widths + temp_width + 2 - i, y + 2, colour)
                self.screen.set_pixel(max_room_widths + temp_width, y + i, colour)
                self.screen.set_pixel(max_room_widths + temp_width + 2, y + 2 - i, colour)

            render_text(self.screen,
                        FONT,
                        max_room_widths + temp_width + 4,
                        y,
                        "C",
                        colour)

            y += font_height

        self.rendered = True

        return False
