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
    from typing import Any, Callable, Optional
except ImportError:
    pass
from io import StringIO
import machine
import urequests
import _thread
import time
import sys

from secrets import SENTRY_INGEST, SENTRY_KEY, SENTRY_PROJECT_ID
from smartdisplay import BouncingBalls, Clock, HouseTemperature, \
                         NetworkScreen, \
                         SentryClient, Sonos, Trains, get_exception_str

BACKEND = "127.0.0.1" if I75.is_emulated() else "192.168.1.207"

SENTRY_CLIENT = SentryClient(SENTRY_INGEST, SENTRY_PROJECT_ID, SENTRY_KEY)

IMAGE = bytearray(64 * 64 * 3)

LOCK = _thread.allocate_lock()
SEND: Optional[NetworkScreen] = None
RECEIVE: Optional[NetworkScreen] = None


def get_next_screen(current: str) -> str:
    print("Getting next screen")
    r = urequests.get(f"http://{BACKEND}:6001/next_screen?current={current}")
    try:
        return r.json()
    finally:
        r.close()

def second_thread() -> None:
    global SEND, RECEIVE
    while True:
        with LOCK:
            if SEND is None:
                continue
            v = SEND
            SEND = None

            print("ready to load")
            v.load()
            print("loaded")

            RECEIVE = v

class ScreenManager:
    def __init__(self, i75: I75) -> None:
        self.balls: Optional[BouncingBalls] = None
        self.current = "first"
        self.current_obj = None
        self.loading_next = False
        self.i75 = i75
        self.black = i75.display.create_pen(0, 0, 0)

    def get_screen(self) -> Any:
        global SEND, RECEIVE

        if self.loading_next:
            if LOCK.acquire(0): #blocking=False):
                if RECEIVE is None:
                    LOCK.release()
                    return self.current_obj
                self.current_obj = RECEIVE
                RECEIVE = None
            
                self.clear_screen()
                self.loading_next = False
                return self.current_obj
            else:
                return self.current_obj
        
        self.current = get_next_screen(self.current) if self.current != "first" else "clock"
        next_obj = self.get_screen_obj(self.current)
        if isinstance(next_obj, NetworkScreen):
            self.loading_next = True
            SEND = next_obj
            LOCK.release()
            return self.current_obj

        self.clear_screen()

        self.current_obj = next_obj
        return self.current_obj

    def clear_screen(self) -> None:
        gc.collect()
        log(f"Free memory: {gc.mem_free()}\n")

        self.i75.display.set_pen(self.black)
        self.i75.display.fill(0, 0, 64, 64)

    def get_screen_obj(self, screen_name: str):
        print("Next screen", screen_name)
        if screen_name == "sonos":
            return Sonos(self.i75, BACKEND, IMAGE)
        if screen_name == "balls":
            if self.balls is None:
                self.balls = BouncingBalls(self.i75)
            else:
                self.balls.reset_timer()
            return self.balls
        if screen_name == "trains_to_london":
            return Trains(self.i75, BACKEND, True)
        if screen_name == "trains_home":
            return Trains(self.i75, BACKEND, False)
        if screen_name == "house_temperature":
            return HouseTemperature(self.i75, BACKEND)
        return Clock(self.i75)


def main() -> None:
    i75 = I75(
        display_type=picographics.DISPLAY_INTERSTATE75_64X64,
        rotate=0 if I75.is_emulated() else 90)

    LOCK.acquire()
    _thread.start_new_thread(safe_func, (second_thread, ))

    screen_manager = ScreenManager(i75)

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
    screen_obj = screen_manager.get_screen()

    while True:
        new_ticks = i75.ticks_ms()
        frame_time = i75.ticks_diff(new_ticks, ticks)

        if frame_time < 50:
            i75.sleep_ms(10)
            continue

        ticks = new_ticks
        now = i75.now()

        if screen_obj.render(frame_time):
            if now.hour == next_ntp:
                i75.set_time()
                now = i75.now()
                next_ntp = now.hour + 23

            screen_obj = screen_manager.get_screen()


def safe_func(func: Callable[[], None]) -> None:
    while True:
        try:
            try:
                func()
            except KeyboardInterrupt:
                break
            except MemoryError as e:
                print(SENTRY_CLIENT.send_exception(e))

                machine.reset()
            except Exception as e:
                print(SENTRY_CLIENT.send_exception(e))

                time.sleep_ms(1000)
            except:  # noqa
                log_error("Unknown exception...")
                time.sleep_ms(1000)
        except Exception as e:
            try:
                log_error(get_exception_str(e))
                time.sleep_ms(1000)
            except:  # noqa
                machine.reset()


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
    safe_func(main)
