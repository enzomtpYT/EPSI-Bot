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
- **Discord Presentation**:
  - Discord interactions must always be acknowledged promptly (use `await interaction.response.defer(ephemeral=...)` when doing network calls or image generation).
  - Provide both Discord rich embeds and generated card images.
  - Support interactive UI components (Buttons, Selects, Pagination) cleanly using Discord UI views.
- **Database & Persistence**:
  - Use SQLAlchemy / SQLModel or Peewee with SQLite fallback and PostgreSQL support.
  - Database access must be asynchronous or cleanly wrapped to never block the asyncio event loop.
- **Error Handling**:
  - Always handle network timeouts, invalid iCal URLs, parsing glitches, and Discord permission issues gracefully with user-friendly messages.

## 4. Testing & Verification
- **Framework**: `pytest` and `pytest-asyncio`.
- All parsing logic, date/time math, timezone handling (Europe/Paris), and database persistence operations must be covered by automated unit tests in `tests/`.
- Run tests via `uv run pytest`.
