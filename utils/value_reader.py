import time
from threading import Thread, Event

from ev3dev.auto import Sensor


class ValueReader(Thread):
    def __init__(self, sensor: Sensor):
        super().__init__(daemon=True)
        self._change_event = Event()
        self._run = True
        self._paused = False
        self._pause = 0
        self._sensor = sensor
        self._num_values = 0
        self._values = []
        self._reads = 1
        self.reload()
        self.start()

    def reload(self):
        self._num_values = self._sensor.num_values
        self._values = [0 in range(self._num_values)]

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
        else:
            if self._paused:
                self._values[n] = self._sensor.value(n)
            self._reads += 1
            self._change_event.set()
        return self._values[n]

    @property
    def num_values(self):
        return self.num_values

    def values(self, force_new=False):
        if force_new:
            for n in range(self._num_values):
                self._values[n] = self._sensor.value(n)
        else:
            if self._paused:
                for n in range(self._num_values):
                    self._values[n] = self._sensor.value(n)
            self._reads += 1
            self._change_event.set()
        return self._values.copy()

    def run(self):
        while self._run:
            if self._pause or not self._reads:
                self._paused = True
                self._change_event.clear()
                while self._pause or not self._reads and self._run:
                    self._change_event.wait()
                    self._change_event.clear()
                self._paused = False

            for n in range(self._num_values):
                self._values[n] = self._sensor.value(n)

            if self._reads > 5:
                self._reads = 5
            else:
                self._reads -= 1
            time.sleep(0.01)

    def pause(self):
        self._pause += 1
        self._change_event.set()

    def wait_to_pause(self):
        while not self._paused:
            time.sleep(0.025)

    def resume(self):
        self._pause -= 1
        self._change_event.set()

    def stop(self):
        self._run = False
