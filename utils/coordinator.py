import time
from threading import Thread

from utils import utils


class Action:
    def actual_progress(self) -> float:
        pass

    def on_start(self):
        pass

    def handle_loop(self, elapsed_time, progress_error):
        pass

    def on_stop(self):
        pass


class Coordinator:
    def __init__(self, actions):
        self._actions = actions
        self._start_time = time.time()

    def on_start(self):
        for action in self._actions:
            action.on_start()

        self._start_time = time.time()

    def handle_loop(self):
        if len(self._actions) == 0:
            return

        actual = []
        for action in self._actions:
            actual.append(action.actual_progress())

        target = []
        for i in range(len(self._actions)):
            total = 0
            count = 0
            for j in range(len(actual)):
                if j == i or actual[j] is None:
                    continue
                total += actual[j]
                count += 1
            target.append(total / count if count != 0 else None)

        elapsed_time = time.time() - self._start_time
        for i in range(len(self._actions)):
            diff = target[i] - actual[i] if target[i] is not None and actual[i] is not None else 0
            self._actions[i].handle_loop(elapsed_time, diff)

    def on_stop(self):
        for action in self._actions:
            action.on_stop()


class ThreadCoordinator(Thread, Coordinator):
    def __init__(self, actions):
        Thread.__init__(self)
        Coordinator.__init__(self, actions)
        self._request_stop = False

    def run(self):
        self.on_start()
        while not self._is_stop_loop():
            self.handle_loop()
        self.on_stop()

    def _is_stop_loop(self):
        return self._request_stop

    def stop(self):
        self._request_stop = True


class CycleThreadCoordinator(ThreadCoordinator):
    def __init__(self, actions, cycle_time=0.01):
        ThreadCoordinator.__init__(self, actions)
        self._cycle_time = cycle_time
        self._last_time = self._start_time

    def on_start(self):
        ThreadCoordinator.on_start(self)
        self._last_time = self._start_time

    def handle_loop(self):
        ThreadCoordinator.handle_loop(self)
        self._last_time = utils.wait_to_cycle_time(self._last_time, self._cycle_time)
