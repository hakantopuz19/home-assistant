"""I2S audio helpers for ESP32 MicroPython."""

try:
    import machine
except ImportError:
    machine = None


class I2SConfig:
    """Simple wrapper for configuring I2S audio on ESP32."""

    def __init__(self, sck_pin=26, ws_pin=25, sd_pin=33, mode=1, bits=16, rate=16000):
        self.sck_pin = sck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin
        self.mode = mode
        self.bits = bits
        self.rate = rate
        self.i2s = None

    def setup(self):
        if machine is None:
            raise RuntimeError('machine module is not available')
        self.i2s = machine.I2S(
            sck=machine.Pin(self.sck_pin),
            ws=machine.Pin(self.ws_pin),
            sd=machine.Pin(self.sd_pin),
            mode=self.mode,
            bits=self.bits,
            rate=self.rate,
        )
        return self.i2s

    def write(self, data):
        if self.i2s is None:
            self.setup()
        return self.i2s.write(data)

    def read(self, nbytes):
        if self.i2s is None:
            self.setup()
        return self.i2s.read(nbytes)

    def deinit(self):
        if self.i2s is not None:
            try:
                self.i2s.deinit()
            except Exception:
                pass
            self.i2s = None


__all__ = ['I2SConfig']
