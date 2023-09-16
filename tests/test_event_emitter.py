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


def test_emit_warns_on_async_listener():
    emitter = EventEmitter()

    async def async_handler():
        pass

    emitter.on("evt", async_handler)
    with pytest.warns(RuntimeWarning, match="async_emit"):
        emitter.emit("evt")


# --- Middleware / Interceptor tests ---


def test_middleware_allows_emission():
    emitter = EventEmitter()
    results = []
    log = []

    def mw(event, args, kwargs):
        log.append(event)
        return True

    emitter.use(mw)
    emitter.on("evt", lambda x: results.append(x))
    emitter.emit("evt", 1)
    assert results == [1]
    assert log == ["evt"]


def test_middleware_cancels_emission():
    emitter = EventEmitter()
    results = []

    def block(event, args, kwargs):
        return False

    emitter.use(block)
    emitter.on("evt", lambda: results.append(1))
    emitter.emit("evt")
    assert results == []


def test_middleware_selective_cancel():
    emitter = EventEmitter()
    results = []

    def mw(event, args, kwargs):
        if event == "blocked":
            return False
        return True

    emitter.use(mw)
    emitter.on("allowed", lambda: results.append("a"))
    emitter.on("blocked", lambda: results.append("b"))
    emitter.emit("allowed")
    emitter.emit("blocked")
    assert results == ["a"]


def test_middleware_remove():
    emitter = EventEmitter()
    results = []
    call_count = []

    def mw(event, args, kwargs):
        call_count.append(1)
        return True

    remove = emitter.use(mw)
    emitter.on("evt", lambda: results.append(1))
    emitter.emit("evt")
    assert len(call_count) == 1

    remove()
    emitter.emit("evt")
    assert len(call_count) == 1  # middleware not called again


def test_middleware_chain_short_circuits():
    emitter = EventEmitter()
    calls = []

    def mw1(event, args, kwargs):
        calls.append("mw1")
        return False

    def mw2(event, args, kwargs):
        calls.append("mw2")
        return True

    emitter.use(mw1)
    emitter.use(mw2)
    emitter.on("evt", lambda: None)
    emitter.emit("evt")
    assert calls == ["mw1"]  # mw2 never called


def test_middleware_none_return_allows():
    emitter = EventEmitter()
    results = []

    def mw(event, args, kwargs):
        pass  # returns None implicitly

    emitter.use(mw)
    emitter.on("evt", lambda: results.append(1))
    emitter.emit("evt")
    assert results == [1]


def test_middleware_with_async_emit():
    async def _run():
        emitter = EventEmitter()
        results = []

        def block(event, args, kwargs):
            return False

        emitter.use(block)

        async def handler():
            results.append(1)

        emitter.on("evt", handler)
        await emitter.async_emit("evt")
        assert results == []

    asyncio.run(_run())


def test_middleware_with_emit_with_timeout():
    async def _run():
        emitter = EventEmitter()

        def block(event, args, kwargs):
            return False

        emitter.use(block)
        emitter.on("evt", lambda: "value")
        results = await emitter.emit_with_timeout("evt", timeout=1.0)
        assert results == []

    asyncio.run(_run())


# --- wait_for tests ---


def test_wait_for_resolves():
    async def _run():
        emitter = EventEmitter()

        async def delayed():
            await asyncio.sleep(0.01)
            emitter.emit("done", "result", key="val")

        asyncio.create_task(delayed())
        args, kwargs = await emitter.wait_for("done", timeout=2.0)
        assert args == ("result",)
        assert kwargs == {"key": "val"}

    asyncio.run(_run())


def test_wait_for_timeout():
    async def _run():
        emitter = EventEmitter()
        with pytest.raises(asyncio.TimeoutError):
            await emitter.wait_for("never", timeout=0.05)

    asyncio.run(_run())


def test_wait_for_no_timeout():
    async def _run():
        emitter = EventEmitter()

        async def delayed():
            await asyncio.sleep(0.01)
            emitter.emit("done", 42)

        asyncio.create_task(delayed())
        args, kwargs = await emitter.wait_for("done", timeout=2.0)
        assert args == (42,)

    asyncio.run(_run())


def test_wait_for_cleans_up_on_timeout():
    async def _run():
        emitter = EventEmitter()
        with pytest.raises(asyncio.TimeoutError):
            await emitter.wait_for("evt", timeout=0.05)
        # The once listener should have been cleaned up
        assert emitter.listener_count("evt") == 0

    asyncio.run(_run())


def test_wait_for_only_fires_once():
    async def _run():
        emitter = EventEmitter()

        async def delayed():
            await asyncio.sleep(0.01)
            emitter.emit("evt", "first")
            emitter.emit("evt", "second")

        asyncio.create_task(delayed())
        args, _ = await emitter.wait_for("evt", timeout=2.0)
        assert args == ("first",)

    asyncio.run(_run())


# --- Prepend tests ---


def test_prepend_fires_first():
    emitter = EventEmitter()
    order = []
    emitter.on("evt", lambda: order.append("second"))
    emitter.prepend("evt", lambda: order.append("first"))
    emitter.emit("evt")
    assert order == ["first", "second"]


def test_prepend_once():
    emitter = EventEmitter()
    order = []
    emitter.on("evt", lambda: order.append("regular"))
    emitter.prepend_once("evt", lambda: order.append("once-first"))
    emitter.emit("evt")
    emitter.emit("evt")
    assert order == ["once-first", "regular", "regular"]


# --- emit_with_timeout tests ---


def test_emit_with_timeout_returns_results():
    async def _run():
        emitter = EventEmitter()
        emitter.on("evt", lambda: "sync-result")
        results = await emitter.emit_with_timeout("evt", timeout=1.0)
        assert results == ["sync-result"]

    asyncio.run(_run())


def test_emit_with_timeout_skips_slow():
    async def _run():
        emitter = EventEmitter()

        async def slow():
            await asyncio.sleep(10)
            return "slow"

        emitter.on("evt", slow)
        emitter.on("evt", lambda: "fast")
        results = await emitter.emit_with_timeout("evt", timeout=0.05)
        assert results == ["fast"]

    asyncio.run(_run())
