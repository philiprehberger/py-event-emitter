from __future__ import annotations

import asyncio
import inspect
import warnings
from typing import Any, Callable


Listener = Callable[..., Any]
Middleware = Callable[[str, tuple[Any, ...], dict[str, Any]], bool | None]


class EventEmitter:
    def __init__(self, max_listeners: int | None = None) -> None:
        self._listeners: dict[str, list[Listener]] = {}
        self._once_wrappers: dict[int, Listener] = {}
        self._max_listeners = max_listeners
        self._middlewares: list[Middleware] = []

    def use(self, middleware: Middleware) -> Callable[[], None]:
        """Register a middleware function that intercepts every emission.

        The middleware receives ``(event, args, kwargs)`` and can:
        - Return ``None`` or ``True`` to allow the emission to proceed.
        - Return ``False`` to cancel the emission entirely.
        - Mutate *args* / *kwargs* in-place to modify the data seen by listeners.

        Returns an unsubscribe function that removes the middleware.
        """
        self._middlewares.append(middleware)

        def remove() -> None:
            try:
                self._middlewares.remove(middleware)
            except ValueError:
                pass

        return remove

    def _run_middlewares(
        self, event: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> bool:
        """Run all middlewares. Returns ``False`` if any middleware cancels."""
        for mw in list(self._middlewares):
            result = mw(event, args, kwargs)
            if result is False:
                return False
        return True

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

    def prepend(self, event: str, listener: Listener) -> Callable[[], None]:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].insert(0, listener)

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

    def prepend_once(self, event: str, listener: Listener) -> Callable[[], None]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.off(event, wrapper)
            return listener(*args, **kwargs)

        self._once_wrappers[id(wrapper)] = listener
        return self.prepend(event, wrapper)

    def off(self, event: str, listener: Listener) -> None:
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
                self._once_wrappers.pop(id(listener), None)
            except ValueError:
                pass

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        if not self._run_middlewares(event, args, kwargs):
            return
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
        if not self._run_middlewares(event, args, kwargs):
            return
        listeners = list(self._listeners.get(event, []))
        for listener in listeners:
            result = listener(*args, **kwargs)
            if inspect.isawaitable(result):
                await result

    async def wait_for(
        self, event: str, timeout: float | None = None
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Wait for an event to fire and return its arguments.

        Returns a tuple of ``(args, kwargs)`` that were passed to ``emit()``.
        If *timeout* is given (in seconds) and the event does not fire within
        that window, :class:`asyncio.TimeoutError` is raised.
        """
        future: asyncio.Future[tuple[tuple[Any, ...], dict[str, Any]]] = (
            asyncio.get_running_loop().create_future()
        )

        def _wrapper(*args: Any, **kwargs: Any) -> None:
            self.off(event, _wrapper)
            if not future.done():
                future.set_result((args, kwargs))

        self.on(event, _wrapper)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.off(event, _wrapper)
            raise

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))

    def event_names(self) -> list[str]:
        return [k for k, v in self._listeners.items() if v]

    def emit_and_collect(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Fire event listeners and collect their return values.

        Sync only. If any registered listener for ``event`` is a coroutine
        function, raises :class:`TypeError`. Returns a list of return values in
        registration order. Listeners that raise propagate the first exception.
        """
        listeners = list(self._listeners.get(event, []))
        for listener in listeners:
            target = self._once_wrappers.get(id(listener), listener)
            if asyncio.iscoroutinefunction(target) or asyncio.iscoroutinefunction(
                listener
            ):
                raise TypeError(
                    "emit_and_collect requires sync listeners; "
                    "use async_emit_and_collect for async listeners"
                )
        if not self._run_middlewares(event, args, kwargs):
            return []
        # Re-read listeners after middleware (which may have side effects), but
        # use the original list to preserve registration order semantics.
        listeners = list(self._listeners.get(event, []))
        results: list[Any] = []
        for listener in listeners:
            results.append(listener(*args, **kwargs))
        return results

    async def async_emit_and_collect(
        self, event: str, *args: Any, **kwargs: Any
    ) -> list[Any]:
        """Fire all listeners and await coroutine results.

        Collects return values in registration order, awaiting any coroutine
        results from async listeners. Sync listeners run directly.
        """
        if not self._run_middlewares(event, args, kwargs):
            return []
        listeners = list(self._listeners.get(event, []))
        results: list[Any] = []
        for listener in listeners:
            result = listener(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            results.append(result)
        return results

    async def emit_with_timeout(
        self, event: str, timeout: float, *args: Any, **kwargs: Any
    ) -> list[Any]:
        if not self._run_middlewares(event, args, kwargs):
            return []
        listeners = list(self._listeners.get(event, []))
        results: list[Any] = []
        for listener in listeners:
            try:
                result = listener(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await asyncio.wait_for(result, timeout=timeout)
                results.append(result)
            except (asyncio.TimeoutError, TimeoutError):
                continue
        return results

    def remove_all_listeners(self, event: str | None = None) -> None:
        if event is None:
            self._listeners.clear()
            self._once_wrappers.clear()
        elif event in self._listeners:
            for listener in self._listeners[event]:
                self._once_wrappers.pop(id(listener), None)
            del self._listeners[event]
