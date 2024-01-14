from i75 import I75, Image, render_text, text_boundingbox, wrap_text
import urequests

FONT = "cg_pixel_3x5_5"

TRAIN_HOME_FILE = "images/train_home.i75"
TRAIN_TO_LONDON_FILE = "images/train_to_london.i75"

class Trains:
    def __init__(self, backend: str, departures: bool) -> None:
        self.departures = departures
        r = urequests.get(f"http://{backend}:6001/trains_{'to' if departures else 'from'}_london")
        try:
            data = r.json()
        finally:
            r.close()
        self.msg = data["msg"]
        self.trains = data["trains"]
        self.rendered = False
        self.total_time = 0

    def render(self, i75: I75, frame_time: int) -> bool:
        self.total_time += frame_time

        if self.rendered:
            return self.total_time > 30000

        img = Image.load(open(TRAIN_TO_LONDON_FILE if self.departures else TRAIN_HOME_FILE, "rb"))
        img.render(i75.display, 0, 0)

        white = i75.display.create_pen(240, 240, 240)
        red = i75.display.create_pen(240, 0, 0)
        green = i75.display.create_pen(0, 240, 0)
        i75.display.set_pen(white)

        i, y = 0, 8

        if self.msg is not None and len(self.msg) > 0:
            self.msg = wrap_text(FONT, self.msg, 62)
            _, height = text_boundingbox(FONT, self.msg)
            render_text(i75.display, FONT, 1, y, self.msg)
            y += height

        while i < len(self.trains):
            text = self.trains[i]["scheduled"] + " " + self.trains[i]["destination"]
            _, height = text_boundingbox(FONT, text)

            if y + height > 64:
                break

            render_text(i75.display, FONT, 1, y, text)

            y += height

            if "platform" in self.trains[i] and self.trains[i]["platform"] is not None:
                platform = "Pltfm " + self.trains[i]["platform"]
                render_text(i75.display, FONT, 1, y, platform)

            width, height = text_boundingbox(FONT, self.trains[i]["eta"])
            i75.display.set_pen(red if self.trains[i]["is_late"] else green)
            render_text(i75.display, FONT, 63 - width, y, self.trains[i]["eta"])
            i75.display.set_pen(white)

            y += height

            if "message" in self.trains[i] and self.trains[i]["message"] is not None:
                width, height = text_boundingbox(FONT, self.trains[i]["message"])
                render_text(i75.display, FONT, 1, y, self.trains[i]["message"])
                y += height

            i += 1

        i75.display.update()
        self.rendered = True

        return False
