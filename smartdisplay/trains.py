from i75 import Colour, I75, SingleColourImage, ScreenManager, render_text, text_boundingbox, wrap_text
from i75.screens.indexed_colour_screen import IndexedColourScreen
from i75.screens.layers import Layers
from i75.screens.single_bit_screen import SingleBitScreen
from i75.screens.offset import Offset
from i75.screens.horizontal_scrolling_screen import HorizontalScrollingScreen
from i75.screens.vertical_scrolling_screen import VerticalScrollingScreen

import urequests

from .font import FONT

TRAIN_HOME_FILE = "images/train_home.i75"
TRAIN_TO_LONDON_FILE = "images/train_to_london.i75"


class Trains:
    def __init__(self, backend: str, manager: ScreenManager, departures: bool) -> None:
        self.departures = departures
        r = urequests.get(f"http://{backend}:6001/trains_"
                          + f"{'to' if departures else 'from'}_london", timeout=10)
        try:
            data = r.json()
        finally:
            r.close()

        self.screen = IndexedColourScreen(64, 64, {
            0: Colour.fromrgb(0, 0, 0),  # Black
            1: Colour.fromrgb(240, 240, 240),  # White
            2: Colour.fromrgb(0, 240, 0),  # Green
            3: Colour.fromrgb(240, 0, 0),  # Red
        })
        self.layers = Layers(Colour.fromrgb(0, 0, 0), [self.screen])
        manager.set_screen(self.layers)

        self.msg = data["msg"]
        self.trains = data["trains"]
        self.rendered = False
        self.total_time = 0

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        img = SingleColourImage.load(open(TRAIN_TO_LONDON_FILE if self.departures
                                     else TRAIN_HOME_FILE, "rb"))
        self.layers.add_layer(img)

        white = 1
        red = 3
        green = 2

        i, y = 0, 8

        if self.msg is not None and len(self.msg) > 0:
            self.msg = wrap_text(FONT, self.msg, 64)
            _, height = text_boundingbox(FONT, self.msg)
            msg_screen = SingleBitScreen(64, height, Colour.fromrgb(240, 240, 240))
            render_text(msg_screen, FONT, 0, 0, self.msg, white)
            scroller = VerticalScrollingScreen(
                64, 19, msg_screen, height,
                initial_pause=10000,
                scroll_duration=10000,
                final_pause=10000)
            self.layers.add_layer(Offset(0, y, scroller))
        
            y += 18

        while i < len(self.trains):
            text = self.trains[i]["scheduled"] + " " + \
                   self.trains[i]["destination"]
            width, height = text_boundingbox(FONT, text)

            if y + height > 64:
                break

            if width >= 64:
                text = self.trains[i]["scheduled"] + " "
                sched_width, height = text_boundingbox(FONT, text)
                render_text(self.screen, FONT, 1, y, text, white)

                dest_width, height = text_boundingbox(FONT,
                                                     self.trains[i]["destination"])
                dest_screen = SingleBitScreen(dest_width, height, Colour.fromrgb(240, 240, 240))
                render_text(dest_screen, FONT, 0, 0,
                            self.trains[i]["destination"], white)
                scroller = HorizontalScrollingScreen(
                    64 - sched_width,
                    height,
                    dest_screen,
                    dest_width,
                    initial_pause=10000,
                    scroll_duration=10000,
                    final_pause=10000)
                self.layers.add_layer(Offset(sched_width, y, scroller))
            else:
                render_text(self.screen, FONT, 1, y, text, white)

            y += height - 1

            if "platform" in self.trains[i] and \
               self.trains[i]["platform"] is not None:
                platform = "Pltfm " + self.trains[i]["platform"]
                render_text(self.screen, FONT, 1, y, platform, white)

            width, height = text_boundingbox(FONT, self.trains[i]["eta"])
            render_text(self.screen,
                        FONT,
                        63 - width,
                        y,
                        self.trains[i]["eta"],
                        red if self.trains[i]["is_late"] else green)

            y += height - 1

            if "message" in self.trains[i] \
               and self.trains[i]["message"] is not None:
                width, height = text_boundingbox(FONT,
                                                 self.trains[i]["message"])
                if width >= 64:
                    message_screen = SingleBitScreen(
                        width, height, Colour.fromrgb(240, 240, 240))
                    render_text(message_screen, FONT, 0, 0,
                                self.trains[i]["message"], white)
                    scroller = HorizontalScrollingScreen(
                        64, height, message_screen, width,
                        initial_pause=10000,
                        scroll_duration=10000,
                        final_pause=10000)
                    self.layers.add_layer(Offset(0, y, scroller))
                else:
                    render_text(self.screen, FONT, 1, y, self.trains[i]["message"], white)
                y += height - 1

            i += 1

        self.rendered = True

        return False
