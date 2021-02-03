from __future__ import annotations

import asyncio
import inspect
import warnings
from typing import Any, Callable


Listener = Callable[..., Any]


class EventEmitter:
    def __init__(self, max_listeners: int | None = None) -> None:
        self._listeners: dict[str, list[Listener]] = {}
        self._once_wrappers: dict[int, Listener] = {}
        self._max_listeners = max_listeners

    def on(self, event: str, listener: Listener) -> Callable[[], None]:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

        if self._max_listeners is not None:
            count = len(self._listeners[event])
            if count > self._max_listeners:
                warnings.warn(
                    f"Event '{event}' has {count} listeners, "
                    f"exceeding max_listeners={self._max_listeners}. "
                    f"Possible memory leak.",
                    stacklevel=2,
                )

        def unsubscribe() -> None:
            self.off(event, listener)

        return unsubscribe

    def once(self, event: str, listener: Listener) -> Callable[[], None]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.off(event, wrapper)
            return listener(*args, **kwargs)

        self._once_wrappers[id(wrapper)] = listener
        return self.on(event, wrapper)

    def off(self, event: str, listener: Listener) -> None:
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
                self._once_wrappers.pop(id(listener), None)
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
                    result.close()
                    warnings.warn(
                        "Async listener passed to emit() was not awaited. "
                        "Use async_emit() for async listeners.",
                        RuntimeWarning,
                        stacklevel=2,
                    )

    async def async_emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        listeners = list(self._listeners.get(event, []))
        for listener in listeners:
            result = listener(*args, **kwargs)
            if inspect.isawaitable(result):
                await result

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))

    def event_names(self) -> list[str]:
        return [k for k, v in self._listeners.items() if v]

    def remove_all_listeners(self, event: str | None = None) -> None:
        if event is None:
            self._listeners.clear()
            self._once_wrappers.clear()
        elif event in self._listeners:
            for listener in self._listeners[event]:
                self._once_wrappers.pop(id(listener), None)
            del self._listeners[event]
