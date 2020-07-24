import asyncio
import warnings

import pytest
from philiprehberger_event_emitter import EventEmitter


def test_on_and_emit():
    emitter = EventEmitter()
    results = []
    emitter.on("test", lambda x: results.append(x))
    emitter.emit("test", 42)
    assert results == [42]


def test_multiple_listeners():
    emitter = EventEmitter()
    results = []
    emitter.on("evt", lambda: results.append("a"))
    emitter.on("evt", lambda: results.append("b"))
    emitter.emit("evt")
    assert results == ["a", "b"]


def test_off_removes_listener():
    emitter = EventEmitter()
    results = []
    handler = lambda: results.append(1)
    emitter.on("evt", handler)
    emitter.off("evt", handler)
    emitter.emit("evt")
    assert results == []


def test_once_fires_only_once():
    emitter = EventEmitter()
    results = []
    emitter.once("evt", lambda: results.append(1))
    emitter.emit("evt")
    emitter.emit("evt")
    assert results == [1]


def test_unsubscribe_function():
    emitter = EventEmitter()
    results = []
    unsub = emitter.on("evt", lambda: results.append(1))
    unsub()
    emitter.emit("evt")
    assert results == []


def test_listener_count():
    emitter = EventEmitter()
    emitter.on("evt", lambda: None)
    emitter.on("evt", lambda: None)
    assert emitter.listener_count("evt") == 2
    assert emitter.listener_count("other") == 0


def test_event_names():
    emitter = EventEmitter()
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    names = emitter.event_names()
    assert "a" in names
    assert "b" in names


def test_remove_all_listeners_specific():
    emitter = EventEmitter()
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    emitter.remove_all_listeners("a")
    assert emitter.listener_count("a") == 0
    assert emitter.listener_count("b") == 1


def test_remove_all_listeners_all():
    emitter = EventEmitter()
    emitter.on("a", lambda: None)
    emitter.on("b", lambda: None)
    emitter.remove_all_listeners()
    assert emitter.event_names() == []


def test_emit_no_listeners():
    emitter = EventEmitter()
    emitter.emit("nonexistent")  # should not raise


def test_off_nonexistent_listener():
    emitter = EventEmitter()
    emitter.off("evt", lambda: None)  # should not raise


def test_listener_call_order():
    emitter = EventEmitter()
    order = []
    emitter.on("evt", lambda: order.append(1))
    emitter.on("evt", lambda: order.append(2))
    emitter.on("evt", lambda: order.append(3))
    emitter.emit("evt")
    assert order == [1, 2, 3]


def test_emit_passes_args_and_kwargs():
    emitter = EventEmitter()
    captured = {}

    def handler(a, b, key=None):
        captured["a"] = a
        captured["b"] = b
        captured["key"] = key

    emitter.on("evt", handler)
    emitter.emit("evt", 1, 2, key="value")
    assert captured == {"a": 1, "b": 2, "key": "value"}


def test_max_listeners_warning():
    emitter = EventEmitter(max_listeners=2)
    emitter.on("evt", lambda: None)
    emitter.on("evt", lambda: None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        emitter.on("evt", lambda: None)
        assert len(w) == 1
        assert "max_listeners" in str(w[0].message)


def test_max_listeners_none_no_warning():
    emitter = EventEmitter()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for _ in range(100):
            emitter.on("evt", lambda: None)
        assert len(w) == 0


def test_once_passes_args():
    emitter = EventEmitter()
    results = []
    emitter.once("evt", lambda x, y: results.append(x + y))
    emitter.emit("evt", 3, 4)
    assert results == [7]


def test_async_emit():
    async def _run():
        emitter = EventEmitter()
        results = []

        async def handler(x):
            results.append(x)

        emitter.on("evt", handler)
        await emitter.async_emit("evt", 42)
        assert results == [42]

    asyncio.run(_run())


def test_async_emit_mixed_sync_async():
    async def _run():
        emitter = EventEmitter()
        results = []

        def sync_handler(x):
            results.append(f"sync:{x}")

        async def async_handler(x):
            results.append(f"async:{x}")

        emitter.on("evt", sync_handler)
        emitter.on("evt", async_handler)
        await emitter.async_emit("evt", 1)
        assert "sync:1" in results
        assert "async:1" in results

    asyncio.run(_run())


def test_once_with_off():
    emitter = EventEmitter()
    results = []
    unsub = emitter.once("evt", lambda: results.append(1))
    unsub()
    emitter.emit("evt")
    assert results == []


def test_event_names_empty_after_remove():
    emitter = EventEmitter()
    handler = lambda: None
    emitter.on("evt", handler)
    emitter.off("evt", handler)
    assert "evt" not in emitter.event_names()


def test_multiple_once_listeners():
    emitter = EventEmitter()
    results = []
    emitter.once("evt", lambda: results.append("a"))
    emitter.once("evt", lambda: results.append("b"))
    emitter.emit("evt")
    emitter.emit("evt")
    assert results == ["a", "b"]
