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

import random

from i75 import Date, Colour, I75, Image, render_text, text_boundingbox
from i75.image import SingleColourImage

from .single_bit_buffer import SingleBitBuffer

FONT = "cg_pixel_3x5_5"


class Snowflake:
    def __init__(self, colour: Colour, image: SingleColourImage) -> None:
        self.pos = (random.randint(10, 55), random.randint(0, 60))
        self.move_to = None
        self.colour = colour
        self.image = image

        self._dir = 1 if random.randint(0, 1) == 1 else -1
        self._bounce = random.randint(3, 10)
        self._delay = 0
        self._speed = random.randint(50, 300)

    def update(self,
               frame_time: int) -> None:
        self._delay += frame_time
        if self._delay > self._speed:
            self._delay -= self._speed
            self._bounce -= 1
            if self._bounce < 0:
                self._dir = -self._dir
                self._bounce = 10

            self.move_to = self.pos[0] + self._dir, self.pos[1] + 1

            if self.pos[1] > 64:
                self.move_to = random.randint(10, 55), -self.image.height

    def clean(self, i75: I75, text_buffer: SingleBitBuffer, text_colour: Colour, bg_colour: Colour):
        if self.move_to is None:
            return
        
        for dx in range(0, self.image.width):
            for dy in range(0, self.image.height):
                if self.image._is_pixel(dx, dy):
                    if text_buffer.is_pixel_set(self.pos[0] + dx, self.pos[1] + dy):
                        text_colour.set_colour(i75)
                    else:
                        bg_colour.set_colour(i75)
                    i75.display.pixel(self.pos[0] + dx, self.pos[1] + dy)

    def render(self, i75: I75):
        if self.move_to is not None:
            self.pos = self.move_to
            self.move_to = None

        self.colour.set_colour(i75)
        for dx in range(0, self.image.width):
            for dy in range(0, self.image.height):
                if self.image._is_pixel(dx, dy):
                    i75.display.pixel(self.pos[0] + dx, self.pos[1] + dy)

class Christmas:
    def __init__(self, i75: I75) -> None:
        self.total_time = 0
        self.rendered = False
        self.text_buffer = SingleBitBuffer(64, 64)
        self.red = Colour.fromrgb(255, 50, 50)
        self.white = Colour.fromrgb(255, 255, 255)
        self.black = Colour.fromrgb(0, 0, 0)
        snowflake_image = Image.load(open("images/snowflake.i75", "rb"))
        self.snowflakes = []
        for _ in range(8):
            self.snowflakes.append(Snowflake(self.white, snowflake_image))

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:

            for snowflake in self.snowflakes:
                snowflake.update(frame_time)
                snowflake.clean(i75, self.text_buffer, self.red, self.black)
            for snowflake in self.snowflakes:
                snowflake.render(i75)
        
            i75.display.update()

            return self.total_time > 30000

        self.rendered = True

        self.red.set_colour(i75)

        today = i75.now().date()
        christmas = Date(today.year, 12, 25)

        if today.month == 1:
            y = 10
            width, height = text_boundingbox(FONT, "happy", scale=2)
            number_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75,
                                       number_offset_x,
                                       y,
                                       "happy",
                                       scale=2)
            y += height

            width, height = text_boundingbox(FONT, "new", scale=3)
            sleeps_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75, sleeps_offset_x, y, "new", scale=3)
            y += height

            width, height = text_boundingbox(FONT, "year", scale=2)
            sleeps_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75, sleeps_offset_x, y, "year", scale=2)
        elif today < christmas:
            days_to_go = (christmas - today).days

            y = 10
            width, height = text_boundingbox(FONT, str(days_to_go), scale=5)
            number_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75,
                                       number_offset_x,
                                       y,
                                       str(days_to_go),
                                       scale=5)
            y += height

            text = "sleeps to go" if days_to_go > 1 else "sleep to go"
            width, height = text_boundingbox(FONT, text)
            sleeps_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75, sleeps_offset_x, y, text)
        elif today >= christmas:
            y = 10
            width, height = text_boundingbox(FONT, "merry", scale=2)
            number_offset_x = 32 - int(width / 2)
            self.render_text_to_buffer(i75,
                                       number_offset_x,
                                       y,
                                       "merry",
                                       scale=2)
            y += height

            width, height = text_boundingbox(FONT, "christmas")
            sleeps_offset_x = 32 - int(width / 2)
            render_text(i75.display, FONT, sleeps_offset_x, y, "christmas")

        for snowflake in self.snowflakes:
            snowflake.render(i75)

        i75.display.update()

        return False

    def render_text_to_buffer(self, i75: I75, x: int, y: int, text: str, scale: int=1) -> None:
        render_text(i75.display,
                    FONT,
                    x,
                    y,
                    text,
                    scale=scale)
        
        render_text(self.text_buffer,
                    FONT,
                    x,
                    y,
                    text,
                    scale=scale)
