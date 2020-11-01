from collections import namedtuple
from dataclasses import dataclass


@dataclass
class Marker:
    time: float
    text: str

    # TODO: rm, standardie to just .time
    @property
    def real_time(self):
        return self.time
