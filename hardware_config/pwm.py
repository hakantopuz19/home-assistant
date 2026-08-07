"""PWM helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class PWMConfig:
    """Simple wrapper to configure and control PWM output."""

    def __init__(self, pin_id, freq=1000, duty=0):
        self.pin_id = pin_id
        self.freq = freq
        self.duty = duty
        self.pwm = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.pwm = machine.PWM(machine.Pin(self.pin_id))
        self.pwm.freq(self.freq)
        self.pwm.duty(self.duty)
        return self.pwm

    def set_duty(self, duty):
        if self.pwm is None:
            self.setup()
        self.duty = duty
        self.pwm.duty(duty)
        return duty

    def set_freq(self, freq):
        if self.pwm is None:
            self.setup()
        self.freq = freq
        self.pwm.freq(freq)
        return freq

    def deinit(self):
        if self.pwm is not None:
            try:
                self.pwm.deinit()
            except Exception:
                pass
            self.pwm = None


__all__ = ['PWMConfig']
