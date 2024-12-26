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

from i75 import I75, ThreeColourImage, render_text, text_boundingbox

FONT = "cg_pixel_3x5_5"

LIGHT_GAP = 4


class WaterGas:
    def __init__(self, backend: str) -> None:
        self.rendered = False
        self.total_time = 0

        r = urequests.get(f"http://{backend}:6001/water_gas", timeout=10)
        try:
            self.data = r.json()
        finally:
            r.close()

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        white = i75.display.create_pen(255, 255, 255)

        i75.display.set_pen(white)

        render_text(i75.display,
                    FONT,
                    10,
                    6,
                    "Water")

        render_text(i75.display,
                    FONT,
                    10,
                    14,
                    f"{self.data['water_day']:0.0f}L")

        render_text(i75.display,
                    FONT,
                    10,
                    22,
                    f"£{self.data['water_cost']:0.2f}")

        render_text(i75.display,
                    FONT,
                    33,
                    37,
                    "Gas")

        width, _ = text_boundingbox(FONT, f"{self.data['gas_day']:0.2f}m")
        render_text(i75.display,
                    FONT,
                    33,
                    45,
                    f"{self.data['gas_day']:0.2f}m")
        
        render_text(i75.display,
                    FONT,
                    33 + width,
                    43,
                    "3")

        render_text(i75.display,
                    FONT,
                    33,
                    53,
                    f"£{self.data['gas_cost']:0.2f}")

        ThreeColourImage.render_from_file(open("images/tap.i75", "rb"), i75.display, 35, 5)

        ThreeColourImage.render_from_file(open("images/flame.i75", "rb"), i75.display, 5, 35)

        i75.display.update()
        self.rendered = True

        return False
