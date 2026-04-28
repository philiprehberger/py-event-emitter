# philiprehberger-event-emitter

[![Tests](https://github.com/philiprehberger/py-event-emitter/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-event-emitter/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-event-emitter.svg)](https://pypi.org/project/philiprehberger-event-emitter/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-event-emitter)](https://github.com/philiprehberger/py-event-emitter/commits/main)

Type-safe event emitter with sync and async listener support.

## Installation

```bash
pip install philiprehberger-event-emitter
```

## Usage

### Basic Events

```python
from philiprehberger_event_emitter import EventEmitter

emitter = EventEmitter()

def on_user_created(user):
    print(f"User created: {user['name']}")

emitter.on("user:created", on_user_created)
emitter.emit("user:created", {"name": "Alice"})
```

### Unsubscribe

```python
# Using the returned unsubscribe function
unsubscribe = emitter.on("event", handler)
unsubscribe()

# Or manually
emitter.off("event", handler)
```

### One-Time Listeners

```python
emitter.once("init", lambda: print("Only fires once"))
emitter.emit("init")  # prints
emitter.emit("init")  # nothing
```

### Prepend Listeners

```python
# Insert listener at the front of the queue (fires before existing listeners)
emitter.on("data", second_handler)
emitter.prepend("data", first_handler)

emitter.emit("data", payload)  # first_handler runs before second_handler

# One-shot version
emitter.prepend_once("data", one_time_first_handler)
```

### Middleware / Interceptors

```python
# Middleware receives (event, args, kwargs) and can modify or cancel emissions
def logging_middleware(event, args, kwargs):
    print(f"Event fired: {event}")
    return True  # allow emission to proceed

def block_middleware(event, args, kwargs):
    if event == "secret":
        return False  # cancel emission
    return True

remove_logger = emitter.use(logging_middleware)
emitter.use(block_middleware)

emitter.emit("hello", "world")   # logged, listeners fire
emitter.emit("secret", "data")   # blocked, no listeners fire

remove_logger()  # remove the logging middleware
```

### Async Listeners

```python
async def async_handler(data):
    await save_to_db(data)

emitter.on("data:received", async_handler)

# Use async_emit to await async listeners
await emitter.async_emit("data:received", {"key": "value"})
```

### Wait for an Event

```python
import asyncio

async def main():
    emitter = EventEmitter()

    # Schedule an emission after a delay
    async def delayed_emit():
        await asyncio.sleep(0.1)
        emitter.emit("ready", "payload")

    asyncio.create_task(delayed_emit())

    # Block until "ready" fires (with optional timeout)
    args, kwargs = await emitter.wait_for("ready", timeout=5.0)
    print(args[0])  # "payload"

asyncio.run(main())
```

### Collect return values

```python
# Sync: collect listener return values in registration order
emitter.on("compute", lambda x: x * 2)
emitter.on("compute", lambda x: x + 100)
results = emitter.emit_and_collect("compute", 5)
print(results)  # [10, 105]

# Async: awaits coroutine listeners and collects mixed sync + async returns
import asyncio

async def main():
    emitter = EventEmitter()

    def sync_handler(x):
        return f"sync:{x}"

    async def async_handler(x):
        return f"async:{x}"

    emitter.on("evt", sync_handler)
    emitter.on("evt", async_handler)
    results = await emitter.async_emit_and_collect("evt", 1)
    print(results)  # ["sync:1", "async:1"]

asyncio.run(main())
```

`emit_and_collect` is sync-only and raises `TypeError` if any registered
listener is a coroutine function — use `async_emit_and_collect` in that case.

### Emit with Timeout

```python
import asyncio

async def slow_handler(data):
    await asyncio.sleep(10)
    return "done"

emitter.on("process", slow_handler)

# Only returns results from listeners that complete within the timeout
results = await emitter.emit_with_timeout("process", timeout=2.0, data="value")
print(results)  # [] (slow_handler timed out)
```

### Max Listeners

```python
# Warn when too many listeners are added (helps detect memory leaks)
emitter = EventEmitter(max_listeners=10)
```

### Management

```python
emitter.listener_count("event")      # number of listeners
emitter.event_names()                 # list of events with listeners
emitter.remove_all_listeners("event") # remove all for one event
emitter.remove_all_listeners()        # remove all listeners
```

## API

| Function / Class | Description |
|---|---|
| `EventEmitter(max_listeners=None)` | Create a new emitter |
| `.on(event, listener)` | Register listener, returns unsubscribe function |
| `.once(event, listener)` | Register one-time listener |
| `.prepend(event, listener)` | Insert listener at front of queue, returns unsubscribe function |
| `.prepend_once(event, listener)` | One-shot prepend listener |
| `.off(event, listener)` | Remove a listener |
| `.use(middleware)` | Register middleware that can modify/cancel emissions, returns remove function |
| `.emit(event, *args, **kwargs)` | Emit event synchronously |
| `.emit_and_collect(event, *args, **kwargs)` | Emit synchronously and return list of listener return values (raises if any listener is async) |
| `.async_emit(event, *args, **kwargs)` | Emit event, awaiting async listeners |
| `.async_emit_and_collect(event, *args, **kwargs)` | Emit, awaiting coroutines, and return list of listener return values |
| `.wait_for(event, timeout=None)` | Async wait for an event, returns `(args, kwargs)` |
| `.emit_with_timeout(event, timeout, *args, **kwargs)` | Emit with per-listener timeout, returns list of results |
| `.listener_count(event)` | Count listeners for an event |
| `.event_names()` | List events with listeners |
| `.remove_all_listeners(event?)` | Remove all or event-specific listeners |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-event-emitter)

🐛 [Report issues](https://github.com/philiprehberger/py-event-emitter/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-event-emitter/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)
