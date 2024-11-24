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


from i75 import Date, Colour, I75, render_text, text_boundingbox

FONT = "cg_pixel_3x5_5"


class Christmas:
    def __init__(self, i75: I75) -> None:
        self.total_time = 0
        self.rendered = False

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        self.rendered = True

        red = Colour.fromrgb(255, 50, 50)
        red.set_colour(i75)

        today = i75.now().date()
        christmas = Date(today.year, 12, 25)

        if today.month == 11:
            y = 10
            width, height = text_boundingbox(FONT, "happy", scale=2)
            number_offset_x = 32 - int(width / 2)
            render_text(i75.display,
                        FONT,
                        number_offset_x,
                        y,
                        "happy",
                        scale=2)
            y += height

            width, height = text_boundingbox(FONT, "new", scale=3)
            sleeps_offset_x = 32 - int(width / 2)
            render_text(i75.display, FONT, sleeps_offset_x, y, "new", scale=3)
            y += height

            width, height = text_boundingbox(FONT, "year", scale=2)
            sleeps_offset_x = 32 - int(width / 2)
            render_text(i75.display, FONT, sleeps_offset_x, y, "year", scale=2)
        elif today < christmas:
            days_to_go = (christmas - today).days

            y = 10
            width, height = text_boundingbox(FONT, str(days_to_go), scale=5)
            number_offset_x = 32 - int(width / 2)
            render_text(i75.display,
                        FONT,
                        number_offset_x,
                        y,
                        str(days_to_go),
                        scale=5)
            y += height

            width, height = text_boundingbox(FONT, "sleeps to go")
            sleeps_offset_x = 32 - int(width / 2)
            render_text(i75.display, FONT, sleeps_offset_x, y, "sleeps to go")
        elif today >= christmas:
            y = 10
            width, height = text_boundingbox(FONT, "merry", scale=2)
            number_offset_x = 32 - int(width / 2)
            render_text(i75.display,
                        FONT,
                        number_offset_x,
                        y,
                        "merry",
                        scale=2)
            y += height

            width, height = text_boundingbox(FONT, "christmas")
            sleeps_offset_x = 32 - int(width / 2)
            render_text(i75.display, FONT, sleeps_offset_x, y, "christmas")

        i75.display.update()

        return False
