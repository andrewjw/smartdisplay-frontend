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

from i75 import Colour, I75, render_text, text_boundingbox, wrap_text
from micropython import const
import urequests

from .network_screen import NetworkScreen

_FONT = const("cg_pixel_3x5_5")


class Sonos(NetworkScreen):
    def __init__(self, i75: I75, backend: str, image: bytearray) -> None:
        super().__init__(i75)
        self.backend = backend
        self.image = image
        self.rendered = False
        self.total_time = 0
        self.rendered_text = False
        self.track_info = None

    def load(self) -> None:
        r = urequests.get(f"http://{self.backend}:6001/sonos")
        try:
            self.track_info = r.json()
        finally:
            r.close()

        if self.track_info is None or not self.track_info["album_art"]:
            return

        try:
            r = urequests.get(f"http://{self.backend}:6001/sonos/art", stream=True)
            r.raw.readinto(self.image)
        finally:
            r.close()

    def render_art(self, ) -> bool:
        self.rendered = True
        if self.track_info is None or not self.track_info["album_art"]:
            return False

        for y in range(64):
            for x in range(64):
                Colour.fromint32(self.image[(y * 64 + x) * 3] << 24
                                    | self.image[(y * 64 + x) * 3 + 1] << 16
                                    | self.image[(y * 64 + x) * 3 + 2] << 8
                                    | 255).set_colour(self.i75)
                self.i75.display.pixel(x, y)

        self.i75.display.update()

        return False

    def render_track_details(self) -> bool:
        self.rendered_text = True

        y = 64
        if self.track_info is None:
            return False

        def has_param(p: str) -> bool:
            return self.track_info[p] is not None \
                and len(self.track_info[p]) > 0

        has_artist = has_param("artist")
        has_album = has_param("album")
        has_track = has_param("track")
        if has_artist:
            y = self.render_text(y, self.track_info["artist"])
        if has_artist and has_album:
            y = self.render_line(y)
        if has_album:
            y = self.render_text(y, self.track_info["album"])
        if has_track and (has_artist or has_album):
            y = self.render_line(y)
        if has_track:
            y = self.render_text(y, self.track_info["track"])

        self.i75.display.update()

        return False

    def render_text(self, y: int, text: str) -> int:
        text = wrap_text(_FONT, text, 62)
        width, height = text_boundingbox(_FONT, text)

        self.fade_image(y - height - 1, y)

        self.i75.display.set_pen(self.i75.display.create_pen(255, 255, 255))

        render_text(self.i75.display, _FONT, 1, y - height, text)

        return y - height

    def render_line(self, y: int) -> int:
        self.fade_image(y - 3, y)

        self.i75.display.set_pen(self.i75.display.create_pen(100, 100, 100))
        self.i75.display.line(5, y - 2, 64 - 5, y - 2)

        return y - 2

    def fade_image(self, y1: int, y2: int) -> None:
        assert self.image is not None
        for py in range(max(0, y1), min(y2, 64)):
            for px in range(64):
                Colour.fromint32(
                    round(0.5 * self.image[(py * 64 + px) * 3]) << 24
                    | round(0.5 * self.image[(py * 64 + px) * 3 + 1]) << 16
                    | round(0.5 * self.image[(py * 64 + px) * 3 + 2]) << 8
                    | 255).set_colour(self.i75)
                self.i75.display.pixel(px, py)

    def render(self, frame_time: int) -> bool:
        self.total_time += frame_time
        if not self.rendered_text and self.total_time > 10000:
            return self.render_track_details()
        if self.total_time > 30000:
            return True

        if not self.rendered:
            return self.render_art()

        return False
