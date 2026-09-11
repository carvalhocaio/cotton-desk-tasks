# ADR 001: Django Tasks (with django-tasks-db) instead of Celery

## Status
Accepted - for learning purposes. See the "Trigger for review" section before using in production.

## Context
`cotton-desk-tasks` needed asynchronous processing for three types of
work: report summarization (latency matters), season reports
(aggregation, can wait), and contract confirmation (needs to wait for the
transaction commit). The options considered were Django 6.0's native
Task Framework (via `django-tasks-db` as the persistence backend) and
Celery.

## Decision
We use the native Tasks Framework, with `django-tasks-db.DatabaseBackend`.

## Reasons
- **The project's goal was to learn the framework itself** - swapping in Celery would defeat the point of the repository.
- **Zero extra infrastructure.** `django-tasks-db` uses the same Postgres database the rest of the application already uses; no need to run Redis/RabbitMQ in parallel. For a small/medium project, that's one fewer operational dependency.
- **Native Django API.** `@task`, `.enqueue()`, `TaskResult` - no third-party decorators, no separate `celery.py`, no broker configuration.

## Known trade-offs (lived in this project, not hypothetical)
- **No built-in scheduling.** Celery has native Celery Beat; here we need an external cron calling a management command (`register_price`). Documented, but it's one more piece to maintain.
- **`django-tasks-db` is a community package**, not part of Django core - the built-in backends (`ImmediateBackend`, `DummyBackend`) are explicitly not recommended for production by the official docs. Celery has decades of production battle-testing; `django-tasks-db` doesn't.
- **`ImmediateBackend` doesn't support `get_result()` by ID** - discovered while separating "the task runs" tests (can use `ImmediateBackend`) from "check status afterward" tests (need to mock the `TaskResult` or, in the real-worker gotcha case, run `DatabaseBackend` with `transaction=True`).
- **Retry, rate limiting, and monitoring** are far more mature in the Celery ecosystem (Flower, retry with configurable backoff). The native Tasks Framework is still recent; fewer ready-made observability tools.

## Trigger for review
If this project (or a successor) goes to real production with significant
task volume, or needs complex recurring scheduling, sophisticated retry,
or Flower-style monitoring - reassess Celery at that point, not before.
Switching backends now, without those real pressures, would be premature
optimization.

---

# ADR 002: PydanticAI + Gemini for structured extraction of confirmations

## Status
Accepted.

## Context
The current phase needed to turn free text (a contract confirmation
received by email, for example) into structured data that could create a
real `Contract`. The options considered were PydanticAI and LangChain
with structured output via `with_structured_output`.

## Decision
We use PydanticAI, with `Agent(output_type=ConfirmationData, ...)` and the
`google:gemini-2.5-flash` model.

## Reasons
- **Schema validation is PydanticAI's central point** - `output_type` is a Pydantic `BaseModel`, and the lib treats schema validation/retry as part of the core, not as a bolted-on feature.
- **`TestModel` + `Agent.override()` make the test deterministic and offline** - no test in the suite needs `GOOGLE_API_KEY` or touches the network.

## Known trade-offs (lived in this project)
- **Eager API key check when the `Agent` is created.** Just *importing* the module without `GOOGLE_API_KEY` in the environment would break the entire suite, even in tests that never call the real API. Solved with `defer_model_check=True`, but it's a gotcha that only surfaced during testing, not prominently documented.
- **Matching failure (a `bale_code` that doesn't exist) is treated as a real task failure** (`Bale.DoesNotExist`), not as a silent retry or fallback. This is intentional — an LLM can hallucinate or get the bale code wrong, and masking that would let the error pass without a trace. The cost is that, in production, every such failure needs human triage (there's no automatic bale code correction yet).
- **`extract_confirmation` shares the `confirmations` queue with `confirm_contract`**, but with lower priority (30 vs. 50) — an LLM call is orders of magnitude slower than a database read. If the volume of AI-driven confirmations grows a lot, this could compete for workers with direct confirmations; at that point, a dedicated queue (`ai-extraction`) would be the next decision to revisit.

## Trigger for review
If the volume of LLM-driven extractions grows enough to genuinely compete
with `confirm_contract` for the `confirmations` queue, split it into its
own queue. If the `Bale.DoesNotExist` rate turns out to be high in
practice, consider a fuzzy-matching step (e.g. suggesting the closest
bale) before failing the task.

---

# ADR 003: Simple polling on the dashboard, instead of WebSocket

## Status
Accepted.

## Context
The dashboard (`/dashboard/`) needs to reflect task state changes
(`READY` -> `RUNNING` -> `SUCCESSFUL`/`FAILED`) without the user reloading
the page. The options considered were periodic `fetch` polling,
Server-Sent Events (SSE), and WebSocket via Django Channels.

## Decision
Polling: the dashboard's JS calls `GET /dashboard/tasks.json` every 1.5s
and reconciles the cards on screen.

## Reasons
- **Zero additional infrastructure.** WebSocket with Channels would require an ASGI server, the `channels` dependency, and a channel layer (usually Redis) - the same kind of operational weight ADR 001 avoided by choosing `django-tasks-db` over Celery. Staying consistent matters: it wouldn't make sense to avoid Redis in the task backend and reintroduce it in the dashboard.
- **The source of truth is already a table.** `DatabaseBackend` writes each task's state to `DBTaskResult`. A poll is literally a `SELECT` - there's no in-memory event to propagate, the data is in the database either way.
- **The project's scope is learning Django Tasks**, not real-time transport. Transport complexity would shift focus away from what the dashboard exists to show.

## Known trade-offs (lived in this project)
- **Transitions shorter than the poll interval are invisible.** We felt this in practice: `summarize_report` finishes in milliseconds, so the `RUNNING` state rarely shows on screen - the card jumps straight from `READY` to `SUCCESSFUL`/`FAILED`. It was only possible to *see* the `RUNNING` state by creating `demo_task` (the `demo` queue), artificially slow and explicitly labeled as such. An event-based transport (SSE/WebSocket) would capture every transition, including instant ones.
- **Constant requests even with an idle dashboard.** One query every 1.5s per open tab, regardless of whether there's work in the queue.
- **Doesn't scale to many simultaneous users.** Each open browser generates a scan of the 50 most recent tasks every cycle. For a local demo dashboard this is irrelevant; for an operational desk dashboard with several operators, it wouldn't be.
- **The `db_worker`'s `--interval` flag affects what you see.** Increasing it makes tasks stay longer in `READY` (visible), but doesn't change the execution duration itself - an empirical finding worth recording for anyone reproducing the demo.
- **The polling endpoint reads a third-party model directly.** `tasks_json` queries `django_tasks_db.models.DBTaskResult`, which is the package's storage model, not a public API - the Tasks Framework exposes `TaskResult` per task id, with no "list the last N across every queue" equivalent. It's the pragmatic choice for a dashboard, but it means a schema change in `django-tasks-db` breaks the view, and the field names (`task_path`, `exception_class_path`, `enqueued_at`) leak into the JSON contract. Worth an adapter function if the dashboard grows.

## Trigger for review
If the dashboard stops being a demo and becomes an operational tool with
several simultaneous users, or if faithfully observing short transitions
becomes necessary, migrate to **SSE before WebSocket** — the flow is
unidirectional (server → browser), so WebSocket's full-duplex capability
would go unused, at a higher infrastructure cost.
