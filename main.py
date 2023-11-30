#!/usr/bin/env python3
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

import picographics
from i75 import Colour, I75
try:
    from typing import Optional
except ImportError:
    pass
from io import StringIO
import urequests
import time
import sys

from smartdisplay import BouncingBalls, Clock, Sonos

BACKEND = "127.0.0.1" if I75.is_emulated() else "192.168.1.4"


def get_next_screen(current: str) -> str:
    print("Getting next screen")
    r = urequests.get(f"http://{BACKEND}:6001/next_screen?current={current}")
    try:
        return r.json()
    finally:
        r.close()


BALLS: Optional[BouncingBalls] = None


def get_screen_obj(i75: I75, screen_name: str):
    global BALLS
    print("Next screen", screen_name)
    if screen_name == "sonos":
        return Sonos(BACKEND)
    if screen_name == "balls":
        if BALLS is None:
            BALLS = BouncingBalls(i75)
        return BALLS
    return Clock(i75)


def main():
    i75 = I75(
        display_type=picographics.DISPLAY_INTERSTATE75_64X64,
        rotate=0 if I75.is_emulated() else 90)

    i75.enable_wifi()
    i75.set_time()

    next_ntp = i75.now().hour + 23

    ticks = i75.ticks_ms()
    screen = get_next_screen("first")
    screen_obj = get_screen_obj(i75, screen)
    raise ValueError()
    while True:
        new_ticks = i75.ticks_ms()
        frame_time = i75.ticks_diff(new_ticks, ticks)

        if frame_time < 50:
            i75.sleep_ms(10)
            continue

        ticks = new_ticks
        now = i75.now()

        if screen_obj.render(i75, frame_time):
            if now.hour == next_ntp:
                i75.set_time()
                now = i75.now()
                next_ntp = now.hour + 23

            screen = get_next_screen(screen)
            screen_obj = get_screen_obj(i75, screen)


def main_safe():
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except Exception as e:
            s = StringIO()
            sys.print_exception(e, s)
            urequests.post(f"http://{BACKEND}:6001/error", data=s.getvalue())
            time.sleep_ms(1000)


if __name__ == "__main__":
    main_safe()
