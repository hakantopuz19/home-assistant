"""Event-driven helper primitives for internal component communication."""

from .dispatcher import Dispatcher


class EventDrivenSystem:
    """A small wrapper around Dispatcher for event-based workflows."""

    def __init__(self):
        self.dispatcher = Dispatcher()

    def on(self, event_name, handler):
        """Register a handler for an event."""
        return self.dispatcher.subscribe(event_name, handler)

    def off(self, event_name, handler):
        """Remove a handler for an event."""
        self.dispatcher.unsubscribe(event_name, handler)

    def emit(self, event_name, *args, **kwargs):
        """Emit an event to all subscribers."""
        self.dispatcher.dispatch(event_name, *args, **kwargs)

    def clear(self):
        """Remove all subscriptions."""
        self.dispatcher.clear()


__all__ = ['EventDrivenSystem']
