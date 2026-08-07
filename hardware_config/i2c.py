"""I2C bus helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class I2CConfig:
    """Thin wrapper around machine.I2C for runtime configuration."""

    def __init__(self, scl_pin=22, sda_pin=21, freq=100000):
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.freq = freq
        self.i2c = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.i2c = machine.I2C(scl=machine.Pin(self.scl_pin), sda=machine.Pin(self.sda_pin), freq=self.freq)
        return self.i2c

    def scan(self):
        if self.i2c is None:
            self.setup()
        return self.i2c.scan()

    def readfrom(self, addr, register, nbytes=1):
        if self.i2c is None:
            self.setup()
        return self.i2c.readfrom_mem(addr, register, nbytes)

    def writeto(self, addr, data):
        if self.i2c is None:
            self.setup()
        return self.i2c.writeto(addr, data)

    def deinit(self):
        if self.i2c is not None:
            try:
                self.i2c.deinit()
            except Exception:
                pass
            self.i2c = None


__all__ = ['I2CConfig']
