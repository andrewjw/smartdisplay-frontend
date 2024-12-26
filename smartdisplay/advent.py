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

import urequests

from i75 import Date, Colour, I75, Image, render_text, text_boundingbox

FONT = "cg_pixel_3x5_5"


class Advent:
    def __init__(self, i75: I75, backend: str, image: bytearray) -> None:
        self.backend = backend
        self.total_time = 0
        self.rendered = False
        self.opened = 64
        self.image = image
        self.state = 1
        self.image_count = 1

    def render(self, i75: I75, frame_time: int) -> bool:
        day = i75.now().date().day

        if self.rendered:
            if self.state == 1:
                self.state = 2
                return False
            if self.state == 2:
                self.total_time += frame_time
                if self.total_time > 10000:
                    self.total_time = 0
                    self.state = 3
                return False
            if self.state == 3:
                self.total_time += frame_time
                to_open = round(64 - 64 * self.total_time / 5000)
                to_open = max(to_open, self.opened - 5, 0)
                for y in range(64):
                    for x in range(to_open, self.opened):
                        Colour.fromrgb(self.image[(y * 64 + x) * 3],
                                       self.image[(y * 64 + x) * 3 + 1],
                                       self.image[(y * 64 + x) * 3 + 2]
                                       ).set_colour(i75)
                        i75.display.pixel(x, y)
                self.opened = to_open
                i75.display.update()
                if self.opened == 0:
                    self.total_time = 0
                    self.state = 4
                return False
            if self.state == 4 and day < 26:
                self.total_time += frame_time
                return self.total_time >= 15000
            if self.state == 4 and self.image_count == 25:
                self.total_time += frame_time
                return self.total_time >= 15000
            if self.state == 4:
                self.image_count += 1
                try:
                    r = urequests.get(f"http://{self.backend}:6001/image?file=advent/{self.image_count:02d}.png",
                                        stream=True, timeout=10)
                    r.raw.readinto(self.image)
                finally:
                    r.close()
                self.state = 3
                self.opened = 64
                return False
            raise ValueError(f"Invalid state {self.state}")

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

        Colour.fromrgb(0, 0, 255).set_colour(i75)

        if day < 26:
            _, height = text_boundingbox(FONT, str(day), scale=4)
            render_text(i75.display, FONT, 4, 64 - height, str(day), scale=4)

        i75.display.update()

        try:
            image_day = day if day < 26 else 1
            r = urequests.get(f"http://{self.backend}:6001/image?file=advent/{image_day:02d}.png",
                                stream=True, timeout=10)
            r.raw.readinto(self.image)
        finally:
            r.close()

        return False
