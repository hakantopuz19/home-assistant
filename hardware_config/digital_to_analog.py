"""Digital-to-analog conversion helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class DACConfig:
    """Simple wrapper for configuring a DAC pin at runtime."""

    def __init__(self, pin_id=25):
        self.pin_id = pin_id
        self.dac = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.dac = machine.DAC(self.pin_id)
        return self.dac

    def write(self, value):
        if self.dac is None:
            self.setup()
        self.dac.write(value)
        return value

    def deinit(self):
        if self.dac is not None:
            try:
                self.dac.deinit()
            except Exception:
                pass
            self.dac = None


__all__ = ['DACConfig']
