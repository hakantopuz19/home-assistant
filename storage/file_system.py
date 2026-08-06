"""Filesystem helpers for MicroPython on ESP32.

This module provides simple helpers to initialize a storage directory
and convenience functions to read/write JSON and text files safely.

The helpers intentionally avoid assumptions about underlying block
devices or partitions and operate at the VFS layer (``uos``/``os``).
"""

try:
	import uos as os
except Exception:
	import os

try:
	import ujson as json
except Exception:
	import json


def exists(path: str) -> bool:
	"""Return True if a path exists in the VFS."""
	try:
		os.stat(path)
		return True
	except Exception:
		return False


def ensure_dir(path: str) -> None:
	"""Create directory `path` (including parents) if it doesn't exist."""
	if exists(path):
		return
	parts = [p for p in path.split('/') if p]
	cur = '/' if path.startswith('/') else ''
	for p in parts:
		cur = cur + p if cur == '/' or cur == '' else cur + '/' + p
		if not exists(cur):
			try:
				os.mkdir(cur)
			except Exception:
				# Best-effort: if concurrent or race condition, ignore
				if not exists(cur):
					raise


def init_storage(base: str = '/storage', subdirs=None) -> str:
	"""Initialize a storage root directory and optional subdirectories.

	Returns the absolute path to the storage root.
	"""
	if subdirs is None:
		subdirs = ['configs', 'logs', 'data']

	ensure_dir(base)
	for d in subdirs:
		ensure_dir(base.rstrip('/') + '/' + d)
	return base


def write_text(path: str, text: str, encoding: str = 'utf-8') -> None:
	"""Atomically write `text` to `path`.

	Implementation writes to a temporary file then renames it.
	"""
	tmp = path + '.tmp'
	with open(tmp, 'w', encoding=encoding) as f:
		f.write(text)
	try:
		os.remove(path)
	except Exception:
		pass
	os.rename(tmp, path)


def read_text(path: str, encoding: str = 'utf-8') -> str:
	"""Read and return text from `path`. Raises on error."""
	with open(path, 'r', encoding=encoding) as f:
		return f.read()


def save_json(path: str, obj) -> None:
	"""Serialize `obj` to JSON and atomically save to `path`."""
	text = json.dumps(obj)
	write_text(path, text)


def load_json(path: str, default=None):
	"""Load JSON from `path`. Return `default` if file missing or parse fails."""
	try:
		text = read_text(path)
		return json.loads(text)
	except Exception:
		return default


def list_dir(path: str) -> list:
	"""Return a list of directory entries for `path`."""
	try:
		return os.listdir(path)
	except Exception:
		return []


def append_log(path: str, line: str) -> None:
	"""Append a line to a text log file (adds newline)."""
	with open(path, 'a') as f:
		if not line.endswith('\r\n'):
			line = line + '\r\n'
		f.write(line)


__all__ = [
	'exists',
	'ensure_dir',
	'init_storage',
	'write_text',
	'read_text',
	'save_json',
	'load_json',
	'list_dir',
	'append_log',
]

