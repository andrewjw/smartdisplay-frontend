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

from i75 import I75, render_text, text_boundingbox

FONT = "cg_pixel_3x5_5"

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
    def __init__(self, backend: str) -> None:
        self.rendered = False
        self.total_time = 0

        r = urequests.get(f"http://{backend}:6001/house_temperature")
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        white = i75.display.create_pen(255, 255, 255)
        blue = i75.display.create_pen(0, 0, 255)
        yellow = i75.display.create_pen(255, 255, 0)
        red = i75.display.create_pen(255, 0, 0)

        i75.display.set_pen(white)

        room_widths = {room.index: text_boundingbox(FONT, room.title)[0]
                       for room in ROOMS}
        max_room_widths = max([v for v in room_widths.values()]) + 1

        title_width, font_height = text_boundingbox(FONT, TITLE)
        render_text(i75.display,
                    FONT,
                    math.floor(32 - title_width / 2),
                    1,
                    TITLE)

        max_pre_point = 0
        for room in ROOMS:
            if room.index not in self.data:
                continue
            temp_str = f"{self.data[room.index]:.1f}".split(".")[0]
            temp_width, _ = text_boundingbox(FONT, temp_str)
            if temp_width > max_pre_point:
                max_pre_point = temp_width

        y = font_height + 3
        for room in ROOMS:
            i75.display.set_pen(white)
            render_text(i75.display,
                        FONT,
                        max_room_widths - room_widths[room.index],
                        y,
                        room.title)

            if room.index in self.data:
                temp = self.data[room.index]
                if temp < room.limit[0]:
                    i75.display.set_pen(blue)
                elif temp > room.limit[2]:
                    i75.display.set_pen(red)
                elif temp > room.limit[1]:
                    i75.display.set_pen(yellow)

                temp_str = f"{temp:.1f}"
                pre_point, _ = text_boundingbox(FONT, temp_str.split(".")[0])
            else:
                temp_str = "-"
                pre_point = max_pre_point
            temp_width, _ = text_boundingbox(FONT, temp_str)
            render_text(i75.display,
                        FONT,
                        max_room_widths + (max_pre_point - pre_point),
                        y,
                        temp_str)
            temp_width += (max_pre_point - pre_point)

            for i in range(3):
                i75.display.pixel(max_room_widths + temp_width + i, y)
                i75.display.pixel(max_room_widths + temp_width + 2 - i, y + 2)
                i75.display.pixel(max_room_widths + temp_width, y + i)
                i75.display.pixel(max_room_widths + temp_width + 2, y + 2 - i)

            render_text(i75.display,
                        FONT,
                        max_room_widths + temp_width + 4,
                        y,
                        "C")

            y += font_height + 2

        i75.display.update()
        self.rendered = True

        return False
