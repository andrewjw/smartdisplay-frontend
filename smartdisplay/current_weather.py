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

from i75 import Colour, I75, ThreeColourImage, ScreenManager, render_text, text_boundingbox
from i75.screens.colour_block import ColourBlock
from i75.screens.indexed_colour_screen import IndexedColourScreen
from i75.screens.layers import Layers
from i75.screens.offset import Offset

from .font import FONT
from .utils import render_image_with_fade

TITLE = "Weather"

MPH = 2.23694


class CurrentWeather:
    def __init__(self, backend: str, manager: ScreenManager) -> None:
        self.rendered = False
        self.total_time = 0

        self.layers = Layers(Colour.fromrgb(0, 0, 0), [])

        manager.set_screen(self.layers)

        r = urequests.get(f"http://{backend}:6001/current_weather", timeout=10)
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        text_screen = IndexedColourScreen(64, 64, {
            0: Colour.fromrgba(0, 0, 0, 0),
            1: Colour.fromrgb(255, 255, 255),  # white
            2: Colour.fromrgb(0, 0, 255),  # blue
            3: Colour.fromrgb(0, 255, 0),  # green
            4: Colour.fromrgb(255, 255, 0),  # yellow
            5: Colour.fromrgb(255, 165, 0),  # orange
            6: Colour.fromrgb(255, 0, 0),  # red
            7: Colour.fromrgb(127, 0, 255)  # violet
        })

        white = 1
        blue = 2
        green = 3
        yellow = 4
        orange = 5
        red = 6
        violet = 7

        if self.data['rain_20m'] >= 0.2:
            image = ThreeColourImage.load(open("images/rainy.i75", "rb"))
        elif self.data['temperature'] > 28:
            image = ThreeColourImage.load(open("images/hot.i75", "rb"))
        elif self.data['temperature'] < 2:
            image = ThreeColourImage.load(open("images/cold.i75", "rb"))
        elif self.data['lux'] < 10:
            image = ThreeColourImage.load(open("images/night.i75", "rb"))
        elif self.data['lux'] < 2500:
            image = ThreeColourImage.load(open("images/sunrise.i75", "rb"))
        elif self.data['lux'] > 50000:
            image = ThreeColourImage.load(open("images/sunny.i75", "rb"))
        else:
            image = ThreeColourImage.load(open("images/cloudy.i75", "rb"))

        self.layers.add_layer(image)

        self.layers.add_layer(
            Offset(2, 2, ColourBlock(60, 60, Colour.fromrgba(0, 0, 0, 128)))
        )

        self.layers.add_layer(text_screen)

        title_width, font_height = text_boundingbox(FONT, TITLE)
        render_text(text_screen,
                    FONT,
                    math.floor(32 - title_width / 2),
                    1,
                    TITLE,
                    white)

        y = font_height

        colour = (blue if self.data['temperature'] < 2 else
                  (red if self.data['temperature'] > 28 else
                   (yellow if self.data['temperature'] > 24
                    else white)))

        temp_str = f"{self.data['temperature']:.1f}"
        temp_width, _ = text_boundingbox(FONT, temp_str)
        render_text(text_screen, FONT, 10, y, temp_str, colour)
        temp_width += 10

        for i in range(3):
            text_screen.set_pixel(temp_width + i, y + 1, white)
            text_screen.set_pixel(temp_width + 2 - i, y + 3, white)
            text_screen.set_pixel(temp_width, y + i + 1, white)
            text_screen.set_pixel(temp_width + 2, y + 3 - i, white)

        render_text(text_screen,
                    FONT,
                    temp_width + 4,
                    y,
                    "C",
                    white)

        hum_str = f"{self.data['humidity']:.0f}%"
        hum_width, _ = text_boundingbox(FONT, hum_str)
        render_text(text_screen, FONT, 54 - hum_width, y, hum_str, white)

        y += font_height - 1

        rain, _ = text_boundingbox(FONT, "Rain: ")
        gust, _ = text_boundingbox(FONT, "Gust: ")
        avg, _ = text_boundingbox(FONT, "Avg: ")
        uvi, _ = text_boundingbox(FONT, "UV: ")

        max_prefix = max([rain, gust, avg, uvi]) + 2

        rain_24h, _ = text_boundingbox(FONT, "24h:")
        rain_1h, _ = text_boundingbox(FONT, "1h:")

        rain_24h_str = f"{self.data['rain_24h']:.1f}mm"
        rain_24h_prefix, _ = text_boundingbox(FONT, rain_24h_str.split(".")[0])
        rain_1h_str = f"{self.data['rain_1h']:.1f}mm"
        rain_1h_prefix, _ = text_boundingbox(FONT, rain_1h_str.split(".")[0])

        rain_dot_max = max(rain_24h_prefix, rain_1h_prefix, 5)

        render_text(text_screen,
                    FONT,
                    (max_prefix - rain) + 2,
                    y,
                    "Rain: 24h:",
                    white)
        render_text(text_screen,
                    FONT,
                    max_prefix + rain_24h + 2 + rain_dot_max - rain_24h_prefix,
                    y,
                    rain_24h_str,
                    white)
        y += font_height - 2
        render_text(text_screen,
                    FONT,
                    (max_prefix + rain_24h - rain_1h) + 2,
                    y,
                    "1h:",
                    white)
        render_text(text_screen,
                    FONT,
                    (max_prefix + rain_24h - rain_1h) + 2
                    + rain_1h + rain_dot_max - rain_1h_prefix,
                    y,
                    rain_1h_str,
                    white)

        y += font_height - 2
        wind_str = \
            f"Gust: {self.data['gust']*MPH:.0f}mph  {self.data['winddir']}"
        render_text(text_screen, FONT, (max_prefix - gust) + 2, y, wind_str, white)

        y += font_height - 2
        wind_str = f"Avg: {self.data['wind']*MPH:.0f}mph"
        render_text(text_screen, FONT, (max_prefix - avg) + 2, y, wind_str, white)

        y += font_height - 1
        pressure_str = f"{self.data['pressure']:.1f}hPa "
        pressure, _ = text_boundingbox(FONT, pressure_str)
        pressure_start = math.floor(32 - pressure / 2)
        render_text(text_screen, FONT, pressure_start, y, pressure_str, white)

        if self.data['pressure_change'] == "increasing":
            for iy in range(y, y + 5):
                text_screen.set_pixel(pressure_start + pressure + 2, iy + 2, white)
            text_screen.set_pixel(pressure_start + pressure + 1, y + 3, white)
            text_screen.set_pixel(pressure_start + pressure + 3, y + 3, white)
            text_screen.set_pixel(pressure_start + pressure, y + 4, white)
            text_screen.set_pixel(pressure_start + pressure + 4, y + 4, white)
        if self.data['pressure_change'] == "decreasing":
            for iy in range(y, y + 5):
                text_screen.set_pixel(pressure_start + pressure + 2, iy + 2, white)
            text_screen.set_pixel(pressure_start + pressure + 1, iy + 1, white)
            text_screen.set_pixel(pressure_start + pressure + 3, iy + 1, white)
            text_screen.set_pixel(pressure_start + pressure, iy, white)
            text_screen.set_pixel(pressure_start + pressure + 4, iy, white)
        if self.data['pressure_change'] == "level":
            for ix in range(-2, 2):
                text_screen.set_pixel(pressure_start + pressure + 2 + ix, y + 4, white)

        y += font_height - 1
        pt_width, _ = text_boundingbox(FONT, self.data['pressure_text'])
        render_text(text_screen,
                    FONT,
                    math.floor(32 - pt_width / 2),
                    y,
                    self.data['pressure_text'],
                    white)

        y += font_height - 1
        render_text(text_screen, FONT, (max_prefix - uvi) + 2, y, "UV:", white)

        if self.data['uv'] <= 2:
            colour = green
        elif self.data['uv'] <= 5:
            colour = yellow
        elif self.data['uv'] <= 7:
            colour = orange
        elif self.data['uv'] <= 10:
            colour = red
        else:
            colour = violet
        uv_str = f"{self.data['uv']:.0f}"
        render_text(text_screen, FONT, max_prefix + 2, y, uv_str, colour)

        self.rendered = True

        return False
