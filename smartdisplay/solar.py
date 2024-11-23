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

FONT = "cg_pixel_3x5_5"

LIGHT_GAP = 4


class Solar:
    def __init__(self, backend: str) -> None:
        self.rendered = False
        self.frame_time = 0
        self.total_time = 0
        self.offset = 0

        r = urequests.get(f"http://{backend}:6001/solar")
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            self.frame_time += frame_time
            if self.frame_time > 200:
                self.frame_time = self.frame_time % 200
                self.offset = (self.offset + 1) % LIGHT_GAP
                self.render_lines(i75)
                i75.display.update()
            return self.total_time > 30000

        white = i75.display.create_pen(255, 255, 255)
        yellow = i75.display.create_pen(255, 255, 0)
        red = i75.display.create_pen(255, 0, 0)
        green = i75.display.create_pen(0, 255, 0)
        grey = i75.display.create_pen(180, 180, 180)
        battery_green = i75.display.create_pen(168, 230, 29)

        i75.display.set_pen(white)

        if self.data['battery_change'] > 500:
            battery_change_colour = green
        elif self.data['battery_change'] > 100:
            battery_change_colour = yellow
        elif self.data['battery_change'] > -100:
            battery_change_colour = white
        else:
            battery_change_colour = red
        if abs(self.data['battery_change']) > 1000:
            battery_change = f"{self.data['battery_change']/1000:0.1f}kw"
        else:
            battery_change = f"{self.data['battery_change']:0.0f}w"

        pv_power_colour = white if self.data['pv_power'] < 100 else (
            green if self.data['pv_power'] > 1000 else yellow
        )
        if self.data['pv_power'] > 1.0:
            pv_power = f"{self.data['pv_power']:0.1f}kw"
        else:
            pv_power = f"{self.data['pv_power']*1000:0.0f}w"

        if self.data['pv_generation'] > 1.0:
            pv_generation = f"{self.data['pv_generation']:0.1f}kwh"
        else:
            pv_generation = f"{self.data['pv_generation']*1000:0.0f}wh"

        current_power_colour = red if self.data['current_power'] > 250 else (
            green if self.data['current_power'] < 250 else white
        )
        if abs(self.data['current_power']) > 1000:
            current_power = f"{self.data['current_power']/1000:0.1f}kw"
        else:
            current_power = f"{self.data['current_power']:0.0f}w"

        house_load_colour = red if self.data["house_load"] > 1000 else (
            yellow if self.data["house_load"] > 500 else green
        )
        if self.data['house_load'] > 1:
            house_load = f"{self.data['house_load']:0.1f}kw"
        else:
            house_load = f"{self.data['house_load']*1000:0.0f}w"

        prefixes = {}
        max_length = 0
        for prefix in ["House", "Car"]:
            width, font_height = text_boundingbox(FONT, prefix + ":")
            prefixes[prefix] = width
            if width + 1 > max_length:
                max_length = width + 1

        render_text(i75.display,
                    FONT,
                    max_length - prefixes["House"],
                    1,
                    "House:")
        house_wh = f"{self.data['house_wh']/1000:0.1f}kwh"
        house_cost = f"£{self.data['house_cost']:0.2f}"
        car_wh = f"{self.data['car_wh']/1000:0.1f}kwh"
        car_cost = f"£{self.data['car_cost']:0.2f}"
        house_wh_pre_point, _ = text_boundingbox(FONT,
                                                 house_wh.split(".")[0])
        house_cost_pre_point, _ = text_boundingbox(FONT,
                                                   house_cost.split(".")[0])
        car_wh_pre_point, _ = text_boundingbox(FONT,
                                               car_wh.split(".")[0])
        car_cost_pre_point, _ = text_boundingbox(FONT,
                                                 car_cost.split(".")[0])
        max_pre_point = max(house_wh_pre_point,
                            house_cost_pre_point,
                            car_wh_pre_point,
                            car_cost_pre_point)
        render_text(i75.display,
                    FONT,
                    max_length + (max_pre_point - house_wh_pre_point),
                    1,
                    house_wh)
        render_text(i75.display,
                    FONT,
                    max_length + (max_pre_point - house_cost_pre_point),
                    1 + font_height,
                    house_cost)
        render_text(i75.display,
                    FONT,
                    max_length - prefixes["Car"],
                    1 + font_height * 2,
                    f"Car:")
        render_text(i75.display,
                    FONT,
                    max_length + (max_pre_point - car_wh_pre_point),
                    1 + font_height * 2,
                    car_wh)
        render_text(i75.display,
                    FONT,
                    max_length + (max_pre_point - car_cost_pre_point),
                    1 + font_height * 3,
                    car_cost)

        icon = Image.load(open("images/sun_icon.i75", "rb"))
        icon.set_colour(255, 255, 0)
        icon.render(i75.display, 10, font_height * 4)

        i75.display.set_pen(pv_power_colour)
        render_text(i75.display,
                    FONT,
                    20,
                    2 + font_height * 4,
                    pv_power)
        
        pwr_width, _ = text_boundingbox(FONT, current_power)
        gen_width, _ = text_boundingbox(FONT, pv_generation)
        render_text(i75.display,
                    FONT,
                    54 + round(pwr_width / 2.0) - gen_width,
                    2 + font_height * 4,
                    pv_generation)

        i75.display.set_pen(grey)
        i75.display.line(10, 11 + font_height * 5, 15, 11 + font_height * 5)
        i75.display.line(10, 11 + font_height * 5, 10, 19 + font_height * 5)
        i75.display.line(15, 11 + font_height * 5, 15, 19 + font_height * 5)
        i75.display.line(10, 19 + font_height * 5, 15, 19 + font_height * 5)

        i75.display.set_pen(battery_green)
        for i in range(1, 8):
            if self.data['battery'] > i * 14:
                i75.display.line(11,
                                 19 + font_height * 5 - i,
                                 14,
                                 19 + font_height * 5 - i)

        i75.display.set_pen(red if self.data['battery'] < 40 else (
            green if self.data['battery'] > 60 else yellow
        ))
        perc_text = f"{self.data['battery']:0.0f}%"
        perc_width, _ = text_boundingbox(FONT, perc_text)
        charge_width, _ = text_boundingbox(FONT,
                                           battery_change)
        max_width = max(18, perc_width, charge_width)
        render_text(i75.display,
                    FONT,
                    13 - round(perc_width / 2.0),
                    21 + font_height * 5,
                    perc_text)
        i75.display.set_pen(battery_change_colour)
        render_text(i75.display,
                    FONT,
                    13 - round(charge_width / 2.0),
                    21 + font_height * 6,
                    battery_change)

        icon = Image.load(open("images/pylon_icon.i75", "rb"))
        icon.render(i75.display, 50, 11 + font_height * 6)

        text_width, _ = text_boundingbox(FONT, current_power)
        i75.display.set_pen(current_power_colour)
        render_text(i75.display,
                    FONT,
                    54 - round(text_width / 2.0),
                    21 + font_height * 6,
                    current_power)

        icon = Image.load(open("images/house_icon.i75", "rb"))
        icon.render(i75.display, 30, 11 + font_height * 6)

        text_width, _ = text_boundingbox(FONT, house_load)
        i75.display.set_pen(house_load_colour)
        render_text(i75.display,
                    FONT,
                    34 - round(text_width / 2.0),
                    21 + font_height * 6,
                    house_load)

        self.render_lines(i75)

        i75.display.update()
        self.rendered = True

        return False

    def render_lines(self, i75: I75) -> None:
        white = i75.display.create_pen(255, 255, 255)
        light_green = i75.display.create_pen(168, 230, 29)
        dark_green = i75.display.create_pen(80, 110, 14)

        solar_on = self.data['pv_power'] >= 0.1

        # Solar output
        self.vertical(13, 23 + 10, 23 + 12, i75,
                      light_green if solar_on else white,
                      dark_green if solar_on else white, self.offset)
        # Battery output
        if self.data['battery_change'] <= -100:
            self.vertical(13,
                          23 + 16,
                          23 + 14,
                          i75,
                          light_green,
                          dark_green,
                          self.offset)
        elif self.data['battery_change'] >= 100:
            self.vertical(13,
                          23 + 14,
                          23 + 16,
                          i75,
                          light_green,
                          dark_green,
                          self.offset)
        else:
            self.vertical(13,
                          23 + 14,
                          23 + 16,
                          i75,
                          white,
                          white,
                          self.offset)
        # Link to house
        pv_system = self.data['pv_power'] * 1000 - self.data['battery_change']
        if pv_system <= -100:
            self.horizontal(32,
                            13,
                            23 + 13,
                            i75,
                            light_green,
                            dark_green,
                            (self.offset + 0) % LIGHT_GAP)
        elif pv_system >= 100:
            self.horizontal(13,
                            32,
                            23 + 13,
                            i75,
                            light_green,
                            dark_green,
                            (self.offset + 1) % LIGHT_GAP)
        else:
            self.horizontal(13,
                            32,
                            23 + 13,
                            i75,
                            white,
                            white,
                            self.offset)

        if self.data['current_power'] >= 100:
            # Grid up
            self.vertical(53,
                          23 + 20,
                          23 + 13,
                          i75,
                          light_green,
                          dark_green,
                          self.offset)
            # House to grid
            self.horizontal(53,
                            34,
                            23 + 13,
                            i75,
                            light_green,
                            dark_green,
                            (self.offset + 1) % LIGHT_GAP)
        elif self.data['current_power'] <= -100:
            self.vertical(53,
                          23 + 13,
                          23 + 20,
                          i75,
                          light_green,
                          dark_green,
                          (self.offset + 1) % LIGHT_GAP)
            self.horizontal(34,
                            53,
                            23 + 13,
                            i75,
                            light_green,
                            dark_green,
                            self.offset)
        else:
            self.vertical(53,
                          23 + 13,
                          23 + 20,
                          i75,
                          white,
                          white,
                          self.offset)
            self.horizontal(34,
                            53,
                            23 + 13,
                            i75,
                            white,
                            white,
                            self.offset)
        # Down to house
        self.vertical(33,
                      23 + 13,
                      23 + 20,
                      i75,
                      light_green,
                      dark_green,
                      (self.offset + 1) % LIGHT_GAP)

    def horizontal(self,
                   x1: int,
                   x2: int,
                   y1: int,
                   i75: I75,
                   light,
                   dark,
                   offset: int) -> None:
        start = x1
        direction = 1 if x1 < x2 else -1
        for i in range(abs(x2 - x1) + 1):
            i75.display.set_pen(
                light if (i - offset) % LIGHT_GAP == 0 else dark)
            i75.display.pixel(start + direction * i, y1)

    def vertical(self,
                 x1: int,
                 y1: int,
                 y2: int,
                 i75: I75,
                 light,
                 dark,
                 offset: int) -> None:
        start = y1
        direction = 1 if y1 < y2 else -1
        for i in range(abs(y2 - y1) + 1):
            i75.display.set_pen(
                light if (i - offset) % LIGHT_GAP == 0 else dark)
            i75.display.pixel(x1, start + direction * i)
