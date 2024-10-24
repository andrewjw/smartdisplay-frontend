from i75 import I75, Image


def render_image_with_fade(i75: I75,
                           img: Image,
                           margin: int,
                           fade: float) -> None:
    for y in range(img.height):
        for x in range(img.width):
            if (y < margin or y >= (img.height - margin)) \
               or (x < margin or x >= (img.width - margin)):
                pfade = 1.0
            else:
                pfade = fade
            i75.display.set_pen(i75.display.create_pen(
                int(img.data[3 * (y * img.width + x)] * pfade),
                int(img.data[3 * (y * img.width + x) + 1] * pfade),
                int(img.data[3 * (y * img.width + x) + 2] * pfade),
            ))
            i75.display.pixel(x, y)
