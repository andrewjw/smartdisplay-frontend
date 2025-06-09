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

import math
try:
    from typing import Tuple
except ImportError:
    pass
import urequests

from i75 import Colour, I75, ThreeColourImage, ScreenManager, render_text, text_boundingbox
from i75.screens.layers import Layers
from i75.screens.offset import Offset
from i75.screens.single_bit_screen import SingleBitScreen

from .font import FONT

LIGHT_GAP = 4


class WaterGas:
    def __init__(self, backend: str, manager: ScreenManager) -> None:
        self.rendered = False
        self.total_time = 0

        self.screen = SingleBitScreen(64, 64, Colour.fromrgb(255, 255, 255))
        self.layers = Layers(Colour.fromrgb(0, 0, 0), [self.screen])
        manager.set_screen(self.layers)

        r = urequests.get(f"http://{backend}:6001/water_gas", timeout=10)
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        render_text(self.screen,
                    FONT,
                    10,
                    4,
                    "Water")

        render_text(self.screen,
                    FONT,
                    10,
                    11,
                    f"{self.data['water_day']:0.0f}L")

        render_text(self.screen,
                    FONT,
                    10,
                    18,
                    f"£{self.data['water_cost']:0.2f}")

        render_text(self.screen,
                    FONT,
                    33,
                    33,
                    "Gas")

        width, _ = text_boundingbox(FONT, f"{self.data['gas_day']:0.2f}m")
        render_text(self.screen,
                    FONT,
                    33,
                    41,
                    f"{self.data['gas_day']:0.2f}m")
        
        render_text(self.screen,
                    FONT,
                    33 + width,
                    39,
                    "3")

        render_text(self.screen,
                    FONT,
                    33,
                    49,
                    f"£{self.data['gas_cost']:0.2f}")

        tap = ThreeColourImage.load(open("images/tap.i75", "rb"))

        self.layers.add_layer(Offset(35, 5, tap))

        flame = ThreeColourImage.load(open("images/flame.i75", "rb"))

        self.layers.add_layer(Offset(5, 35, flame))

        self.rendered = True

        return False
