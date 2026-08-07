"""Simple dispatcher for internal software-unit events.

This module provides a lightweight pub/sub dispatcher that allows software
components to register handlers for named events and dispatch messages to them.
"""

try:
    import ucollections as collections
except ImportError:
    import collections


class Dispatcher:
    """A minimal event dispatcher for internal component communication."""

    def __init__(self):
        self._handlers = collections.defaultdict(list)

    def subscribe(self, event_name, handler):
        """Register a handler for a specific event name."""
        self._handlers[event_name].append(handler)
        return handler

    def unsubscribe(self, event_name, handler):
        """Remove a handler from an event name."""
        handlers = self._handlers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
        if not handlers:
            self._handlers.pop(event_name, None)

    def dispatch(self, event_name, *args, **kwargs):
        """Dispatch an event to all registered handlers."""
        handlers = list(self._handlers.get(event_name, []))
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception:
                pass

    def clear(self):
        """Remove all subscriptions."""
        self._handlers.clear()


__all__ = ['Dispatcher']
