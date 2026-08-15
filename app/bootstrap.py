"""Application bootstrap for starting the device and dashboard."""

from app.services.device import boot_device


def main():
    boot_device()
