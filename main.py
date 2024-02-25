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

import gc
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

from smartdisplay import BouncingBalls, Clock, HouseTemperature, Sonos, Trains

BACKEND = "127.0.0.1" if I75.is_emulated() else "192.168.1.207"


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
        else:
            BALLS.reset_timer()
        return BALLS
    if screen_name == "trains_to_london":
        return Trains(BACKEND, True)
    if screen_name == "trains_home":
        return Trains(BACKEND, False)
    if screen_name == "house_temperature":
        return HouseTemperature(BACKEND)
    return Clock(i75)


def main():
    i75 = I75(
        display_type=picographics.DISPLAY_INTERSTATE75_64X64,
        rotate=0 if I75.is_emulated() else 90)

    while not i75.enable_wifi():
        time.sleep_ms(1000)

    failure_count: int = 0
    while not i75.set_time():
        if failure_count > 30:
            log_error("Failed to set time.\n")
            failure_count = 0
        failure_count += 1
        time.sleep_ms(1000)

    next_ntp = i75.now().hour + 23

    ticks = i75.ticks_ms()
    screen = get_next_screen("first")
    screen_obj = get_screen_obj(i75, screen)

    black = i75.display.create_pen(0, 0, 0)

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

            gc.collect()
            log(f"Free memory: {gc.mem_free()}\n")

            i75.display.set_pen(black)
            i75.display.fill(0, 0, 64, 64)


def main_safe():
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except MemoryError:
            sys.exit()
        except Exception as e:
            s = StringIO()
            sys.print_exception(e, s)
            s.seek(0)
            log_error(s.read())
            time.sleep_ms(1000)
        except:  # noqa
            log_error("Unknown exception...")
            time.sleep_ms(1000)


def log(msg: str) -> None:
    r = None
    try:
        r = urequests.post(f"http://{BACKEND}:6001/log", data=msg)
    finally:
        if r is not None:
            r.close()


def log_error(error: str) -> None:
    r = None
    try:
        r = urequests.post(f"http://{BACKEND}:6001/error", data=error)
    finally:
        if r is not None:
            r.close()


if __name__ == "__main__":
    main_safe()
