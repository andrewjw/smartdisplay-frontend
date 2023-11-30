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

from i75 import Colour, I75
import urequests


class Sonos:
    def __init__(self, backend: str) -> None:
        self.backend = backend
        self.rendered = False
        self.total_time = 0

    def render_art(self, i75: I75) -> bool:
        r = urequests.get(f"http://{self.backend}:6001/sonos")
        j = r.json()
        r.close()

        if j["album_art"] is None:
            return True

        for y in range(64):
            for x in range(64):
                Colour.fromint32(j["album_art"][y][x]).set_colour(i75)
                i75.display.pixel(x, y)

        i75.display.update()
        self.rendered = True

        return False

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time
        if self.total_time > 30000:
            return True

        if not self.rendered:
            return self.render_art(i75)

        return False
