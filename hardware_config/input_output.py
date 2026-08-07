"""Digital input/output helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class GPIOConfig:
    """Simple wrapper for configuring digital GPIO pins at runtime."""

    def __init__(self, pin_id, mode='out', pull=None, value=None):
        self.pin_id = pin_id
        self.mode = mode
        self.pull = pull
        self.value = value
        self.pin = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.pin = machine.Pin(self.pin_id, mode=self._pin_mode(self.mode))
        if self.pull is not None:
            self.pin.init(pull=self.pull)
        if self.value is not None:
            self.pin.value(self.value)
        return self.pin

    def read(self):
        if self.pin is None:
            self.setup()
        return self.pin.value()

    def write(self, value):
        if self.pin is None:
            self.setup()
        self.pin.value(value)
        return value

    def deinit(self):
        if self.pin is not None:
            try:
                self.pin.deinit()
            except Exception:
                pass
            self.pin = None

    def _pin_mode(self, mode):
        if mode == 'in':
            return machine.Pin.IN
        if mode == 'out':
            return machine.Pin.OUT
        return machine.Pin.OUT


__all__ = ['GPIOConfig']
