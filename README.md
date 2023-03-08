# philiprehberger-event-emitter

[![Tests](https://github.com/philiprehberger/py-event-emitter/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-event-emitter/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-event-emitter.svg)](https://pypi.org/project/philiprehberger-event-emitter/)
[![GitHub release](https://img.shields.io/github/v/release/philiprehberger/py-event-emitter)](https://github.com/philiprehberger/py-event-emitter/releases)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-event-emitter)](https://github.com/philiprehberger/py-event-emitter/commits/main)
[![License](https://img.shields.io/github/license/philiprehberger/py-event-emitter)](LICENSE)
[![Bug Reports](https://img.shields.io/github/issues/philiprehberger/py-event-emitter/bug)](https://github.com/philiprehberger/py-event-emitter/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
[![Feature Requests](https://img.shields.io/github/issues/philiprehberger/py-event-emitter/enhancement)](https://github.com/philiprehberger/py-event-emitter/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

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

### Async Listeners

```python
async def async_handler(data):
    await save_to_db(data)

emitter.on("data:received", async_handler)

# Use async_emit to await async listeners
await emitter.async_emit("data:received", {"key": "value"})
```

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
| `.emit(event, *args, **kwargs)` | Emit event synchronously |
| `.async_emit(event, *args, **kwargs)` | Emit event, awaiting async listeners |
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

If you find this package useful, consider giving it a star on GitHub — it helps motivate continued maintenance and development.

[![LinkedIn](https://img.shields.io/badge/Philip%20Rehberger-LinkedIn-0A66C2?logo=linkedin)](https://www.linkedin.com/in/philiprehberger)
[![More packages](https://img.shields.io/badge/more-open%20source%20packages-blue)](https://philiprehberger.com/open-source-packages)

## License

[MIT](LICENSE)
