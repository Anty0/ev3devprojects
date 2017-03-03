import time
from threading import Thread

from ev3dev.auto import Sensor


class ValueReader(Thread):
    def __init__(self, sensor: Sensor):
        super().__init__(daemon=True)
        self._run = True
        self._paused = False
        self._pause = 0
        self._sensor = sensor
        self._num_values = 0
        self._values = []
        self.reload()
        self.start()

    def reload(self):
        self._num_values = self._sensor.num_values
        self._values = [0 for n in range(self._num_values)]

    def mode(self, value):
        self.pause()
        self.wait_to_pause()
        try:
            self._sensor.mode = value
        finally:
            self.reload()
            self.resume()

    def value(self, n=0, force_new=False):
        if force_new:
            self._values[n] = self._sensor.value(n)
        return self._values[n]

    @property
    def num_values(self):
        return self.num_values

    def values(self, force_new=False):
        if force_new:
            for n in range(self._num_values):
                self._values[n] = self._sensor.value(n)
        return self._values.copy()

    def run(self):
        while self._run:
            if self._pause:
                self._paused = True
                while self._pause > 0 and self._run:
                    time.sleep(0)
                self._paused = False

            for n in range(self._num_values):
                self._values[n] = self._sensor.value(n)
            time.sleep(0)

    def pause(self):
        self._pause += 1

    def wait_to_pause(self):
        while not self._paused:
            time.sleep(0)

    def resume(self):
        self._pause -= 1

    def stop(self):
        self._run = False
