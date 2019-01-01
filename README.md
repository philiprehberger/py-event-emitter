# philiprehberger-event-emitter

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

### Async Listeners

```python
async def async_handler(data):
    await save_to_db(data)

emitter.on("data:received", async_handler)

# Use async_emit to await async listeners
await emitter.async_emit("data:received", {"key": "value"})
```

### Management

```python
emitter.listener_count("event")      # number of listeners
emitter.event_names()                 # list of events with listeners
emitter.remove_all_listeners("event") # remove all for one event
emitter.remove_all_listeners()        # remove all listeners
```

## License

MIT
