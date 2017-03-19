from .utils import crop_r


class RegulatorBase:
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        self._const_p = const_p
        self._const_i = const_i
        self._const_d = const_d
        self._const_target = const_target

        self._getter_p = getter_p
        self._getter_i = getter_i
        self._getter_d = getter_d
        self._getter_target = getter_target

        self.loop_count = 0
        self.last_error = 0
        self.last_derivative = 0
        self.last_integral = 0

    def reset(self):
        self.loop_count = 0
        self.last_error = 0
        self.last_derivative = 0
        self.last_integral = 0

    def get_p(self) -> float:
        result = self._getter_p() if self._getter_p is not None else None
        return result if result is not None else self._const_p

    def get_i(self) -> float:
        result = self._getter_i() if self._getter_i is not None else None
        return result if result is not None else self._const_i

    def get_d(self) -> float:
        result = self._getter_d() if self._getter_d is not None else None
        return result if result is not None else self._const_d

    def get_target(self) -> float:
        result = self._getter_target() if self._getter_target is not None else None
        return result if result is not None else self._const_target

    def regulate(self, input_val) -> float:
        self.loop_count += 1
        return 0


class ValueRegulator(RegulatorBase):
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        RegulatorBase.__init__(self, const_p, const_i, const_d, const_target,
                               getter_p, getter_i, getter_d, getter_target)

    def regulate(self, input_val) -> float:
        RegulatorBase.regulate(self, input_val)

        target = self.get_target()
        error = target - input_val
        return self.regulate_error(error)

    def regulate_error(self, error) -> float:
        integral = float(0.5) * self.last_integral + error
        self.last_integral = integral

        derivative = error - self.last_error
        self.last_error = error
        self.last_derivative = derivative

        return self.get_p() * error + self.get_i() * integral + self.get_d() * derivative


class PercentRegulator(ValueRegulator):
    def __init__(self, const_p=None, const_i=None, const_d=None, const_target=None,
                 getter_p=None, getter_i=None, getter_d=None, getter_target=None):
        ValueRegulator.__init__(self, const_p, const_i, const_d, const_target,
                                getter_p, getter_i, getter_d, getter_target)

    def regulate(self, input_val) -> float:
        RegulatorBase.regulate(self, input_val)

        input_val = crop_r(input_val)
        target = self.get_target()
        max_positive_error = abs(100 - target) * 0.6
        max_negative_error = abs(-target) * 0.6

        error = target - input_val
        max_error = max_negative_error if error < 0 else max_positive_error
        error *= 100 / max_error

        return self.regulate_error(error)
