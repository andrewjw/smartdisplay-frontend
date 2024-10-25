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

from i75 import I75, Image, render_text, text_boundingbox

from .utils import render_image_with_fade

FONT = "cg_pixel_3x5_5"

TITLE = "Weather"

MPH = 2.23694


class CurrentWeather:
    def __init__(self, backend: str, image: bytearray) -> None:
        self.rendered = False
        self.total_time = 0
        self.image = image

        r = urequests.get(f"http://{backend}:6001/current_weather")
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
        green = i75.display.create_pen(0, 255, 0)
        yellow = i75.display.create_pen(255, 255, 0)
        orange = i75.display.create_pen(255, 165, 0)
        red = i75.display.create_pen(255, 0, 0)
        violet = i75.display.create_pen(127, 0, 255)

        if self.data['rain_20m'] >= 0.2:
            image_file = "images/rainy.i75"
        elif self.data['temperature'] > 28:
            image_file = "images/hot.i75"
        elif self.data['temperature'] < 2:
            image_file = "images/cold.i75"
        elif self.data['lux'] < 10:
            image_file = "images/night.i75"
        elif self.data['lux'] < 2500:
            image_file = "images/sunrise.i75"
        elif self.data['lux'] > 50000:
            image_file = "images/sunny.i75"
        else:
            image_file = "images/cloudy.i75"

        img = Image.load_into_buffer(open(image_file, "rb"), self.image)

        render_image_with_fade(i75, img, 2, 0.5)

        i75.display.set_pen(white)
        title_width, font_height = text_boundingbox(FONT, TITLE)
        render_text(i75.display,
                    FONT,
                    math.floor(32 - title_width / 2),
                    3,
                    TITLE)

        y = font_height + 4

        i75.display.set_pen(blue if self.data['temperature'] < 2 else
                            (red if self.data['temperature'] > 28 else
                            (yellow if self.data['temperature'] > 24
                             else white)))

        temp_str = f"{self.data['temperature']:.1f}"
        temp_width, _ = text_boundingbox(FONT, temp_str)
        render_text(i75.display, FONT, 10, y, temp_str)
        temp_width += 10

        for i in range(3):
            i75.display.pixel(temp_width + i, y)
            i75.display.pixel(temp_width + 2 - i, y + 2)
            i75.display.pixel(temp_width, y + i)
            i75.display.pixel(temp_width + 2, y + 2 - i)

        render_text(i75.display,
                    FONT,
                    temp_width + 4,
                    y,
                    "C")

        i75.display.set_pen(white)
        hum_str = f"{self.data['humidity']:.0f}%"
        hum_width, _ = text_boundingbox(FONT, hum_str)
        render_text(i75.display, FONT, 54 - hum_width, y, hum_str)

        y += 1 + font_height

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

        render_text(i75.display,
                    FONT,
                    (max_prefix - rain) + 2,
                    y,
                    "Rain: 24h:")
        render_text(i75.display,
                    FONT,
                    max_prefix + rain_24h + 2 + rain_dot_max - rain_24h_prefix,
                    y,
                    rain_24h_str)
        y += font_height
        render_text(i75.display,
                    FONT,
                    (max_prefix + rain_24h - rain_1h) + 2,
                    y,
                    "1h:")
        render_text(i75.display,
                    FONT,
                    (max_prefix + rain_24h - rain_1h) + 2
                    + rain_1h + rain_dot_max - rain_1h_prefix,
                    y,
                    rain_1h_str)

        y += 1 + font_height
        wind_str = \
            f"Gust: {self.data['gust']*MPH:.0f}mph  {self.data['winddir']}"
        render_text(i75.display, FONT, (max_prefix - gust) + 2, y, wind_str)

        y += font_height
        wind_str = f"Avg: {self.data['wind']*MPH:.0f}mph"
        render_text(i75.display, FONT, (max_prefix - avg) + 2, y, wind_str)

        y += 1 + font_height
        pressure_str = f"{self.data['pressure']:.1f}HPA "
        pressure, _ = text_boundingbox(FONT, pressure_str)
        pressure_start = math.floor(32 - pressure / 2)
        render_text(i75.display, FONT, pressure_start, y, pressure_str)

        if self.data['pressure_change'] == "increasing":
            for iy in range(y, y + 5):
                i75.display.pixel(pressure_start + pressure + 2, iy)
            i75.display.pixel(pressure_start + pressure + 1, y + 1)
            i75.display.pixel(pressure_start + pressure + 3, y + 1)
            i75.display.pixel(pressure_start + pressure, y + 2)
            i75.display.pixel(pressure_start + pressure + 4, y + 2)
        if self.data['pressure_change'] == "decreasing":
            for iy in range(y, y + 5):
                i75.display.pixel(pressure_start + pressure + 2, iy)
            i75.display.pixel(pressure_start + pressure + 1, iy - 1)
            i75.display.pixel(pressure_start + pressure + 3, iy - 1)
            i75.display.pixel(pressure_start + pressure, iy - 2)
            i75.display.pixel(pressure_start + pressure + 4, iy - 2)
        if self.data['pressure_change'] == "level":
            for ix in range(-2, 2):
                i75.display.pixel(pressure_start + pressure + 2 + ix, y + 2)

        y += font_height
        pt_width, _ = text_boundingbox(FONT, self.data['pressure_text'])
        render_text(i75.display,
                    FONT,
                    math.floor(32 - pt_width / 2),
                    y,
                    self.data['pressure_text'])

        y += 1 + font_height
        render_text(i75.display, FONT, (max_prefix - uvi) + 2, y, "UV:")

        if self.data['uv'] <= 2:
            i75.display.set_pen(green)
        elif self.data['uv'] <= 5:
            i75.display.set_pen(yellow)
        elif self.data['uv'] <= 7:
            i75.display.set_pen(orange)
        elif self.data['uv'] <= 10:
            i75.display.set_pen(red)
        else:
            i75.display.set_pen(violet)
        uv_str = f"{self.data['uv']:.0f}"
        render_text(i75.display, FONT, max_prefix + 2, y, uv_str)

        i75.display.update()
        self.rendered = True

        return False
