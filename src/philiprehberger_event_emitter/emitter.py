from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable


Listener = Callable[..., Any]


class EventEmitter:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = {}
        self._once_listeners: set[int] = set()

    def on(self, event: str, listener: Listener) -> Callable[[], None]:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

        def unsubscribe() -> None:
            self.off(event, listener)

        return unsubscribe

    def once(self, event: str, listener: Listener) -> Callable[[], None]:
        self._once_listeners.add(id(listener))
        return self.on(event, listener)

    def off(self, event: str, listener: Listener) -> None:
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
                self._once_listeners.discard(id(listener))
            except ValueError:
                pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        listeners = list(self._listeners.get(event, []))
        for listener in listeners:
            result = listener(*args, **kwargs)
            if inspect.isawaitable(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
            if id(listener) in self._once_listeners:
                self.off(event, listener)

    async def async_emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        listeners = list(self._listeners.get(event, []))
        for listener in listeners:
            result = listener(*args, **kwargs)
            if inspect.isawaitable(result):
                await result
            if id(listener) in self._once_listeners:
                self.off(event, listener)

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))

    def event_names(self) -> list[str]:
        return [k for k, v in self._listeners.items() if v]

    def remove_all_listeners(self, event: str | None = None) -> None:
        if event is None:
            self._listeners.clear()
            self._once_listeners.clear()
        elif event in self._listeners:
            for listener in self._listeners[event]:
                self._once_listeners.discard(id(listener))
            del self._listeners[event]
