"""Hardware configuration helpers for ESP32 peripherals."""

from .analog_to_digital import ADCConfig
from .digital_to_analog import DACConfig
from .input_output import GPIOConfig
from .pwm import PWMConfig
from .i2c import I2CConfig
from .i2s import I2SConfig

__all__ = [
    'ADCConfig',
    'DACConfig',
    'GPIOConfig',
    'PWMConfig',
    'I2CConfig',
    'I2SConfig',
]
