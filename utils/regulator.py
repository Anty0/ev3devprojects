from utils import utils


class RegulatorBase:
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        self.const_p = const_p
        self.const_i = const_i
        self.const_d = const_d
        self.const_target = const_target

        self.getter_p = getter_p
        self.getter_i = getter_i
        self.getter_d = getter_d
        self.getter_target = getter_target

        self.last_error = 0
        self.last_derivative = 0
        self.last_integral = 0

    def reset(self):
        self.last_error = 0
        self.last_integral = 0

    def _get_p(self):
        result = self.getter_p() if self.getter_p is not None else None
        return result if result is not None else self.const_p

    def _get_i(self):
        result = self.getter_i() if self.getter_i is not None else None
        return result if result is not None else self.const_i

    def _get_d(self):
        result = self.getter_d() if self.getter_d is not None else None
        return result if result is not None else self.const_d

    def _get_target(self):
        result = self.getter_target() if self.getter_target is not None else None
        return result if result is not None else self.const_target

    def regulate(self, input_val):
        pass


class ValueRegulator(RegulatorBase):
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        RegulatorBase.__init__(self, const_p, const_i, const_d, const_target,
                               getter_p, getter_i, getter_d, getter_target)

    def regulate(self, input_val):
        target = self._get_target()
        error = target - input_val
        return self.regulate_error(error)

    def regulate_error(self, error):
        integral = float(0.5) * self.last_integral + error
        self.last_integral = integral

        derivative = error - self.last_error
        self.last_error = error
        self.last_derivative = derivative

        return self._get_p() * error + self._get_i() * integral + self._get_d() * derivative


class PercentRegulator(ValueRegulator):
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        ValueRegulator.__init__(self, const_p, const_i, const_d, const_target,
                                getter_p, getter_i, getter_d, getter_target)

    def regulate(self, input_val):
        input_val = utils.crop_r(input_val)
        target = self._get_target()
        max_positive_error = abs(100 - target) * 0.6
        max_negative_error = abs(-target) * 0.6

        error = target - input_val
        max_error = max_negative_error if error < 0 else max_positive_error
        error *= 100 / max_error

        return self.regulate_error(error)
