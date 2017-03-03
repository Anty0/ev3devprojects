import math
import time

from ev3dev.auto import LargeMotor, MediumMotor, ColorSensor, InfraredSensor, UltrasonicSensor

RETRIES = 3
LOOPS = 25000

print('Starting response speed test. Every result will be calculated {} times using diameter of {} results times'
      .format(RETRIES, LOOPS))


class TestCase:
    def __init__(self, name, test_method, prepare_method=None):
        self._name = name
        self._test_method = test_method
        self._prepare_method = prepare_method

    @property
    def name(self):
        return self._name

    def skip(self):
        print('-Test({}): Skipped'.format(self.name))

    def start(self):
        print('-Test({}):'.format(self.name))

        if self._prepare_method is not None:
            self._prepare_method()

        for i in range(RETRIES):
            start_time = time.time()
            for j in range(LOOPS):
                self._test_method()
            stop_time = time.time()
            total_time = stop_time - start_time
            print('--Result{}(total={:f}, one={:f})'.format(i, total_time, total_time / LOOPS))


TestCase('empty_loop', lambda: None).start()
print()
TestCase('math(5 + 5)', lambda: 5 + 5).start()
TestCase('math(5 * 5)', lambda: 5 * 5).start()
TestCase('math(5**2)', lambda: 5 ** 2).start()
TestCase('math(pow(5, 2))', lambda: math.pow(5, 2)).start()
TestCase('math(sqrt(2))', lambda: math.sqrt(2)).start()
print()
TestCase('sleep(0.001)', lambda: time.sleep(0.001)).start()
TestCase('sleep(0.002)', lambda: time.sleep(0.002)).start()
print()
motor = LargeMotor()
test = TestCase('large_motor(pos)', lambda: motor.position)
test.start() if motor.connected else test.skip()
if motor.connected: motor.reset()
print()
motor = MediumMotor()
test = TestCase('medium_motor(pos)', lambda: motor.position)
test.start() if motor.connected else test.skip()
if motor.connected: motor.reset()
print()
sensor = ColorSensor()
test = TestCase('color_sensor(ref)', sensor.value, lambda: setattr(sensor, 'mode', ColorSensor.MODE_COL_REFLECT))
test.start() if sensor.connected else test.skip()
test = TestCase('color_sensor(amb)', sensor.value, lambda: setattr(sensor, 'mode', ColorSensor.MODE_COL_AMBIENT))
test.start() if sensor.connected else test.skip()
test = TestCase('color_sensor(col)', sensor.value, lambda: setattr(sensor, 'mode', ColorSensor.MODE_COL_COLOR))
test.start() if sensor.connected else test.skip()
if motor.connected: sensor.mode = ColorSensor.MODE_COL_REFLECT
print()
sensor = InfraredSensor()
test = TestCase('infrared_sensor(prox_dis)', sensor.value, lambda: setattr(sensor, 'mode', InfraredSensor.MODE_IR_PROX))
test.start() if sensor.connected else test.skip()
test = TestCase('infrared_sensor(rem)', sensor.value, lambda: setattr(sensor, 'mode', InfraredSensor.MODE_IR_REMOTE))
test.start() if sensor.connected else test.skip()
if motor.connected: sensor.mode = InfraredSensor.MODE_IR_PROX
print()
sensor = UltrasonicSensor()
test = TestCase('ultrasonic_sensor(dist_cm)', sensor.value,
                lambda: setattr(sensor, 'mode', UltrasonicSensor.MODE_US_DIST_CM))
test.start() if sensor.connected else test.skip()
test = TestCase('ultrasonic_sensor(dist_in)', sensor.value,
                lambda: setattr(sensor, 'mode', UltrasonicSensor.MODE_US_DIST_IN))
test.start() if sensor.connected else test.skip()
test = TestCase('ultrasonic_sensor(listen)', sensor.value,
                lambda: setattr(sensor, 'mode', UltrasonicSensor.MODE_US_LISTEN))
test.start() if sensor.connected else test.skip()
if motor.connected: sensor.mode = UltrasonicSensor.MODE_US_DIST_CM

"""
Last output:

Starting response speed test. Every result will be calculated 3 times using diameter of 25000 results times
-Test(empty_loop): Preparing
--Result0(total=0.945620, one=0.000038)
--Result1(total=0.985297, one=0.000039)
--Result2(total=0.962128, one=0.000038)

-Test(math(5 + 5)):
--Result0(total=0.809097, one=0.000032)
--Result1(total=0.773753, one=0.000031)
--Result2(total=0.774160, one=0.000031)
-Test(math(5 * 5)):
--Result0(total=0.857329, one=0.000034)
--Result1(total=0.828960, one=0.000033)
--Result2(total=0.864314, one=0.000035)
-Test(math(5**2)):
--Result0(total=0.831203, one=0.000033)
--Result1(total=0.798872, one=0.000032)
--Result2(total=0.794394, one=0.000032)
-Test(math(pow(5, 2))):
--Result0(total=4.350266, one=0.000174)
--Result1(total=4.358286, one=0.000174)
--Result2(total=4.395804, one=0.000176)
-Test(math(sqrt(2))):
--Result0(total=4.902943, one=0.000196)
--Result1(total=4.849765, one=0.000194)
--Result2(total=4.964989, one=0.000199)

-Test(sleep(0.001)):
--Result0(total=41.905922, one=0.001676)
--Result1(total=42.249781, one=0.001690)
--Result2(total=41.767830, one=0.001671)
-Test(sleep(0.002)):
--Result0(total=62.664784, one=0.002507)
--Result1(total=62.691573, one=0.002508)
--Result2(total=62.698844, one=0.002508)

-Test(large_motor_pos): Preparing
--Result0(total=39.898236, one=0.001596)
--Result1(total=41.374079, one=0.001655)
--Result2(total=39.715824, one=0.001589)

-Test(medium_motor_pos): Preparing
--Result0(total=39.719231, one=0.001589)
--Result1(total=44.666891, one=0.001787)
--Result2(total=39.638687, one=0.001586)

-Test(color_sensor_ref): Preparing
--Result0(total=63.744713, one=0.002550)
--Result1(total=64.728804, one=0.002589)
--Result2(total=64.077854, one=0.002563)
-Test(color_sensor_amb): Preparing
--Result0(total=66.299081, one=0.002652)
--Result1(total=62.841612, one=0.002514)
--Result2(total=63.113809, one=0.002525)
-Test(color_sensor_col): Preparing
--Result0(total=62.850378, one=0.002514)
--Result1(total=62.381880, one=0.002495)
--Result2(total=66.067342, one=0.002643)

-Test(infrared_sensor_prox_dis): Preparing
--Result0(total=57.337018, one=0.002293)
--Result1(total=57.339429, one=0.002294)
--Result2(total=57.871770, one=0.002315)
-Test(infrared_sensor_rem): Preparing
--Result0(total=63.500449, one=0.002540)
--Result1(total=66.296979, one=0.002652)
--Result2(total=63.454007, one=0.002538)

-Test(ultrasonic_sensor_dist_cm): Skipped
-Test(ultrasonic_sensor_dist_in): Skipped
-Test(ultrasonic_sensor_listen): Skipped
"""
