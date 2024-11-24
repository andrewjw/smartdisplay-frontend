#!/usr/bin/env micropython
# smartdisplay-frontend
# Copyright (C) 2024 Andrew Wilkinson
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


from i75 import Date, Colour, I75, Image, render_text, text_boundingbox

FONT = "cg_pixel_3x5_5"


class Advent:
    def __init__(self, i75: I75, image: bytearray) -> None:
        self.total_time = 0
        self.rendered = False
        self.opened = 64
        self.image = image

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            if self.total_time > 5000 and self.opened > 0:
                to_open = round(64 - 64 * (self.total_time - 5000) / 5000)
                for y in range(64):
                    for x in range(to_open, self.opened):
                        Colour.fromrgb(self.image[(y * 64 + x) * 3],
                                       self.image[(y * 64 + x) * 3 + 1],
                                       self.image[(y * 64 + x) * 3 + 2]
                                       ).set_colour(i75)
                        i75.display.pixel(x, y)
                self.opened = to_open
                i75.display.update()
            return self.total_time > 30000

        self.rendered = True

        Image.load_into_buffer(open("images/christmas_wreath.i75", "rb"),
                               self.image)

        for y in range(64):
            for x in range(64):
                Colour.fromint32(self.image[(y * 64 + x) * 3] << 24
                                 | self.image[(y * 64 + x) * 3 + 1] << 16
                                 | self.image[(y * 64 + x) * 3 + 2] << 8
                                 | 255).set_colour(i75)
                i75.display.pixel(x, y)

        today = i75.now().date()
        today = Date(2024, 12, 2)

        Colour.fromrgb(0, 0, 255).set_colour(i75)

        _, height = text_boundingbox(FONT, str(today.day), scale=4)
        render_text(i75.display, FONT, 4, 64 - height, str(today.day), scale=4)

        i75.display.update()

        Image.load_into_buffer(open(f"images/advent/{today.day:02d}.i75",
                                    "rb"),
                               self.image)

        return False
