"""Minimal logger storage test for ESP32 (MicroPython).

This script initializes storage and exercises the logger layer.
"""

from storage import init_storage, exists
from logger import StorageLogger, SerialLogger


def main():
    root = init_storage('/storage_test', subdirs=['configs', 'logs', 'data'])

    if exists(root + '/logs/circular.log'):
        try:
            import os
            os.remove(root + '/logs/circular.log')
        except Exception:
            pass

    if exists(root + '/logs/circular.meta.json'):
        try:
            import os
            os.remove(root + '/logs/circular.meta.json')
        except Exception:
            pass

    circ = StorageLogger(storage_root=root, subdir='logs', filename='circular.log')
    circ.write('Boot storage logger test')
    circ.write('Second storage logger line')
    circ.write('Third storage logger line')

    print(' size=', circ.size, 'pos=', circ.pos)
    print(repr(circ.read_tail(512)))

    serial = SerialLogger(prefix='[SYS] ')
    serial.write('Boot message via SerialLogger')
    print('SerialLogger write OK')


if __name__ == '__main__':
    main()

