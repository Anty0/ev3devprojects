import logging
import time

log = logging.getLogger(__name__)


def wait_to_cycle_time(last_time: float, cycle_time: float):
    new_time = time.time()
    sleep_time = cycle_time - (new_time - last_time)
    if sleep_time > 0:
        time.sleep(sleep_time)
    elif sleep_time < -cycle_time * 5:
        log.warning('Cycle is getting late. It\'s late %s seconds. Use bigger cycle time.' % -sleep_time)
    last_time += cycle_time
    return last_time


def crop_m(input_val, min_out=-100, max_out=100):
    return min(max_out, max(min_out, input_val))


def crop_r(input_val, max_r=100):
    return min(max_r, max(-max_r, input_val))
