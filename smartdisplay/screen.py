from i75 import I75

class Screen:
    def __init__(self, i75: I75) -> None:
        self.i75 = i75

    def render(self, frame_time: int) -> bool:
        raise NotImplementedError()
