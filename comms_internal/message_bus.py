"""Message bus for internal software-unit communication.

The message bus stores messages by topic and allows components to publish and
subscribe to them. It is intentionally lightweight and MicroPython-friendly.
"""

try:
    import ucollections as collections
except ImportError:
    import collections


class MessageBus:
    """Very small topic-based message bus implementation."""

    def __init__(self):
        self._topics = collections.defaultdict(list)
        self._messages = []

    def subscribe(self, topic, handler):
        """Register a handler for a topic."""
        self._topics[topic].append(handler)
        return handler

    def unsubscribe(self, topic, handler):
        """Remove a handler from a topic."""
        handlers = self._topics.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)
        if not handlers:
            self._topics.pop(topic, None)

    def publish(self, topic, message):
        """Publish a message to a topic and retain it for inspection."""
        self._messages.append((topic, message))
        handlers = list(self._topics.get(topic, []))
        for handler in handlers:
            try:
                handler(topic, message)
            except Exception:
                pass

    def get_messages(self, topic=None):
        """Return stored messages optionally filtered by topic."""
        if topic is None:
            return list(self._messages)
        return [item for item in self._messages if item[0] == topic]

    def clear(self):
        """Remove all subscriptions and stored messages."""
        self._topics.clear()
        self._messages = []


__all__ = ['MessageBus']
