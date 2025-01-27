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

import errno
import gc
import picographics
from i75 import Colour, I75
try:
    from typing import Optional
except ImportError:
    pass
from io import StringIO
import machine
import micropython
import urequests
import time
import sys

from secrets import SENTRY_INGEST, SENTRY_KEY, SENTRY_PROJECT_ID
from smartdisplay import Advent, BouncingBalls, Christmas, Clock, \
                         CurrentWeather, HouseTemperature, SentryClient, \
                         Sonos, Trains, Blackout, Solar, WaterGas

BACKEND = "127.0.0.1" if I75.is_emulated() else "192.168.1.207"

SENTRY_CLIENT = SentryClient(SENTRY_INGEST, SENTRY_PROJECT_ID, SENTRY_KEY)


def get_next_screen(current: str) -> str:
    print("Getting next screen")
    try:
        r = urequests.get(f"http://{BACKEND}:6001/next_screen?current={current}", timeout=10)
    except OSError as e:
        if e.errno == errno.ETIMEDOUT:
            return "clock"
        raise
    try:
        return r.json()
    finally:
        r.close()


BALLS: Optional[BouncingBalls] = None

IMAGE = bytearray(64 * 64 * 3)


def get_screen_obj(i75: I75, screen_name: str):
    global BALLS
    print("Next screen", screen_name)
    if screen_name == "blackout":
        return Blackout()
    if screen_name == "sonos":
        return Sonos(BACKEND, IMAGE, False)
    if screen_name == "sonos_quick":
        return Sonos(BACKEND, IMAGE, True)
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
    if screen_name == "current_weather":
        return CurrentWeather(BACKEND, IMAGE)
    if screen_name == "solar":
        return Solar(BACKEND)
    if screen_name == "water_gas":
        return WaterGas(BACKEND)
    if screen_name == "christmas":
        return Christmas(i75)
    if screen_name == "advent":
        return Advent(i75, BACKEND, IMAGE)
    return Clock(i75)


def main() -> None:
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
        except MemoryError as e:
            print(SENTRY_CLIENT.send_exception(e))

            machine.reset()
        except Exception as e:
            print(e)
            print(SENTRY_CLIENT.send_exception(e))

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
