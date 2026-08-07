"""Analog-to-digital conversion helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class ADCConfig:
    """Simple wrapper for configuring an ADC pin at runtime."""

    def __init__(self, pin_id=34, atten=3):
        self.pin_id = pin_id
        self.atten = atten
        self.adc = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.adc = machine.ADC(self.pin_id)
        self.adc.atten(self.atten)
        return self.adc

    def read(self):
        if self.adc is None:
            self.setup()
        return self.adc.read()

    def deinit(self):
        if self.adc is not None:
            try:
                self.adc.deinit()
            except Exception:
                pass
            self.adc = None


__all__ = ['ADCConfig']
