# Changelog

## 0.4.1 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility

## 0.4.0 (2026-03-28)

- Add event middleware/interceptor system via `emitter.use()`
- Add `emitter.wait_for()` async method that returns a Future resolving when the event fires
- Bring package into full compliance with guides

## 0.3.0 (2026-03-27)

- Add `prepend()` to insert listeners at the front of the queue
- Add `prepend_once()` for one-shot prepend listeners
- Add `emit_with_timeout()` for async emission with per-listener timeout
- Add 8 badges, Support section, and issue templates to README
- Add `[tool.pytest.ini_options]` and `[tool.mypy]` to pyproject.toml

## 0.2.3

- Add Development section to README
- Add wheel build target to pyproject.toml

## 0.2.1

- Fix `emit()` to warn instead of silently dropping async listeners

## 0.2.0

- Add `max_listeners` parameter with warning when exceeded
- Fix `once()` to use wrapper approach instead of fragile `id()` tracking
- Add comprehensive test suite (21 tests)
- Add API table to README

## 0.1.1

- Add project URLs to pyproject.toml

## 0.1.0
- Initial release
