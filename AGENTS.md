# AI Development Guidelines & Rules

This project follows strict engineering standards. Any AI assistant working on this codebase must adhere to the following rules:

## 1. Code Quality, Formatting & Type Safety
- **Linter & Formatter**: Use **`ruff`** for formatting and linting.
  - Format command: `uv run ruff format .`
  - Lint command: `uv run ruff check . --fix`
  - Target Python version: 3.11+. Line length: 100.
- **Type Checking**: Use **`ty`** (or `mypy`/`pyright`) to verify type soundness.
  - Type-check command: `ty check` or `uv run ty check`
  - All public functions, methods, and classes must contain explicit type annotations.

## 2. Dependency Management & Environment
- **Package Manager**: Use **`uv`**.
  - Install dependencies: `uv sync`
  - Run commands: `uv run <command>` (e.g. `uv run pytest`, `uv run python src/main.py`)
  - Keep `pyproject.toml` and `uv.lock` as the single source of truth for dependencies.
  - Avoid adding system C library dependencies unless strictly necessary.

## 3. Architecture & Separation of Concerns
- **Domain Modeling**: Keep timetable and event data strongly typed (e.g., using `pydantic` or dataclasses).
- **ICS Parsing**: Maintain clean separation between network fetching, raw iCal parsing (`icalendar` / `recurring-ical-events`), and presentation layers.
- **Timezone Handling & Dynamic Scaling**:
  - Events originate in `Europe/Paris`. Always support user target timezones (all standard IANA names).
  - Timezone names with spaces must be normalized (e.g., `"America/New York"` -> `"America/New_York"`).
  - Both image rendering (`render_week_image`) and Web UI timetable grids must dynamically compute hour bounds (`start_hour`/`end_hour`) to support shifted timezones without course clipping or upward squishing.
  - **Grid Bounds Isolation**: Weekly timetable hour bounds calculation must only consider courses falling on the displayed weekdays (Monday to Friday, `0 <= day_offset < 5`). Full-day events (`duration >= 24h` or midnight-to-midnight) and holidays must never distort the hourly grid bounds.
  - **Date Math**: Dates across month and year boundaries must always be calculated using `timedelta(days=...)` rather than arithmetic on `date.day`.
- **Security & SSRF Hardening**:
  - All outbound iCal fetches must go through `SafeResolver` to defeat DNS rebinding (TOCTOU) by re-checking IP addresses at resolution time. Loopback, private (RFC 1918), link-local, and multicast addresses are strictly forbidden.
  - Caches for remote content must be bounded in size (e.g. `cachetools.TTLCache`) and response payloads capped to prevent memory exhaustion (DoS).
  - Untrusted inputs or raw server error details must never be inserted into the DOM via `innerHTML` (use `textContent` or `escapeHtml()`).
- **Schedule Sharing & Privacy**:
  - Schedules can be shared via token or Discord user ID whitelist.
  - When viewing another user's schedule (shared view), **Microsoft Teams links must always be hidden** (`teams_link = None`).
  - For the schedule owner (non-shared view), provide clickable Teams action buttons and clear visual badges.
- **Discord Presentation**:
  - Discord interactions must always be acknowledged promptly (use `await interaction.response.defer(ephemeral=...)` when doing network calls or image generation).
  - Provide both Discord rich embeds and generated card images.
  - Support interactive UI components (Buttons, Selects, Pagination) cleanly using Discord UI views.
- **Database & Persistence**:
  - Use SQLAlchemy / SQLModel with SQLite fallback and PostgreSQL support.
  - Database access must be asynchronous or cleanly wrapped to never block the asyncio event loop.
- **Error Handling**:
  - Always handle network timeouts, invalid iCal URLs, parsing glitches, and Discord permission issues gracefully with user-friendly messages.

## 4. Testing & Verification
- **Framework**: `pytest` and `pytest-asyncio`.
- All parsing logic, date/time math, timezone handling, sharing/privacy rules, security/SSRF protections, and database persistence operations must be covered by automated unit tests in `tests/`.
- Run tests via `uv run pytest`.
- Verify formatting with `uv run ruff check . --fix && uv run ruff format .`.
- Verify types with `uv run ty check` or `uvx ty check`.
- Verify dependencies with `uvx pip-audit`.
