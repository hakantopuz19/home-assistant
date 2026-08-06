""" storage logger.

Writes log lines into a fixed-size circular file on the VFS and
maintains a small meta JSON with the current write position.

Designed for use on MicroPython (ESP32) with the `storage.file_system`
helpers present in this workspace.
"""

import time

from storage import ensure_dir, exists, save_json, load_json


class StorageLogger:
    """ logger that writes into a fixed-size binary file.

    Parameters
    ----------
    storage_root: str
        Base directory under which logs are kept (e.g. '/storage').
    subdir: str
        Subdirectory under `storage_root` to store the circular file.
    filename: str
        Name of the circular log file.
    meta_filename: str
        Name of the meta JSON file that stores the write pointer.
    max_size: int
        Maximum size in bytes of the circular log file.
    """

    def __init__(self, storage_root='/storage', subdir='logs', filename='circular.log',
                 meta_filename='circular.meta.json', max_size=64 * 1024):
        self.dir = storage_root.rstrip('/') + '/' + subdir
        ensure_dir(self.dir)
        self.path = self.dir + '/' + filename
        self.meta_path = self.dir + '/' + meta_filename
        self.max_size = int(max_size)

        if not exists(self.path):
            # create file filled with zero bytes
            with open(self.path, 'wb') as f:
                f.write(b'\x00' * self.max_size)

        meta = load_json(self.meta_path, default={'pos': 0, 'size': 0})
        self.pos = int(meta.get('pos', 0)) % self.max_size
        self.size = min(int(meta.get('size', 0)), self.max_size)

    def _save_meta(self):
        save_json(self.meta_path, {'pos': self.pos, 'size': self.size})

    def write(self, line: str) -> None:
        """Append a line (text) to the circular file."""
        if not line.endswith('\r\n'):
            line = line + '\r\n'
        data = line.encode('utf-8')
        L = len(data)
        if L > self.max_size:
            raise ValueError('line too long for circular buffer')

        with open(self.path, 'r+b') as f:
            end_space = self.max_size - self.pos
            if L <= end_space:
                f.seek(self.pos)
                f.write(data)
                self.pos = (self.pos + L) % self.max_size
            else:
                f.seek(self.pos)
                f.write(data[:end_space])
                f.seek(0)
                f.write(data[end_space:])
                self.pos = len(data) - end_space

        self.size = min(self.max_size, self.size + L)
        self._save_meta()

    def _read_bytes(self, start: int, length: int) -> bytes:
        """Read `length` bytes from the circular file starting at `start`."""
        if length <= 0:
            return b''

        with open(self.path, 'rb') as f:
            if start + length <= self.max_size:
                f.seek(start)
                data = f.read(length)
            else:
                first_len = self.max_size - start
                f.seek(start)
                chunk1 = f.read(first_len)
                f.seek(0)
                chunk2 = f.read(length - first_len)
                data = chunk1 + chunk2

        if data is None:
            return b''
        if isinstance(data, memoryview):
            data = bytes(data)
        if isinstance(data, bytearray):
            data = bytes(data)
        if not isinstance(data, bytes):
            data = bytes(data)
        return data

    def read_all(self) -> str:
        """Return the log content as a UTF-8 string in chronological order."""
        if self.size == 0:
            return ''

        start = (self.pos - self.size) % self.max_size
        data = self._read_bytes(start, self.size)
        data = data.rstrip(b'\x00')
        try:
            return data.decode('utf-8')
        except Exception:
            return ''

    def read_tail(self, max_bytes=1024) -> str:
        """Return the last `max_bytes` of circular log data."""
        if max_bytes <= 0 or self.size == 0:
            return ''

        read_bytes = min(int(max_bytes), self.size)
        start = (self.pos - read_bytes) % self.max_size
        data = self._read_bytes(start, read_bytes)
        data = data.rstrip(b'\x00')
        if not data:
            return ''
        try:
            return data.decode('utf-8')
        except Exception:
            return ''

    def read_from_start(self) -> str:
        """Read the full current log buffer from oldest entry to newest."""
        return self.read_all()


__all__ = ['StorageLogger']
