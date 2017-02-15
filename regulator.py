class Regulator:
    def __init__(self, const_p=None, const_d=None, const_i=None, const_target=None,
                 getter_p=None, getter_d=None, getter_i=None, getter_target=None):
        self.const_p = const_p
        self.const_d = const_d
        self.const_i = const_i
        self.const_target = const_target

        self.getter_p = getter_p
        self.getter_d = getter_d
        self.getter_i = getter_i
        self.getter_target = getter_target

        self.tmp_error = 0
        self.integral = 0

    def reset(self):
        self.tmp_error = 0
        self.integral = 0

    def get_p(self):
        result = self.getter_p() if self.getter_p is not None else None
        return result if result is not None else self.const_p

    def get_d(self):
        result = self.getter_d() if self.getter_d is not None else None
        return result if result is not None else self.const_d

    def get_i(self):
        result = self.getter_i() if self.getter_i is not None else None
        return result if result is not None else self.const_i

    def get_target(self):
        result = self.getter_target() if self.getter_target is not None else None
        return result if result is not None else self.const_target

    def regulate(self, input_val):
        input_val = min(100, max(-100, input_val))
        target = self.get_target()
        max_positive_error = abs(100 - target) * 0.6
        max_negative_error = abs(-target) * 0.6

        error = target - input_val
        max_error = max_negative_error if error < 0 else max_positive_error
        error *= 100 / max_error

        derivative, self.tmp_error = error - self.tmp_error, error

        integral = float(0.5) * self.integral + error
        self.integral = integral

        return self.get_p() * error + self.get_d() * derivative + self.get_i() * integral
