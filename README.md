# OS Synchronization Assignment

**Name:** <your name>  **USN:** <your USN>  **Course:** Operating Systems

Classic synchronization problems in Python, each with a semaphore and a monitor version.
Every program records its own execution events and writes a replayable HTML simulation.

| Problem | Semaphore | Monitor |
|---|---|---|
| Readers-Writers | `readers_writers/semaphore/rw_semaphore.py` | `readers_writers/monitor/rw_monitor.py` |
| Dining Philosophers (4) | `dining_philosophers/semaphore/dp_semaphore.py` | `dining_philosophers/monitor/dp_monitor.py` |

## Requirements
Python 3.8+ only. No external libraries. No build step.

## Run (generates the HTML)
```
python readers_writers/semaphore/rw_semaphore.py
python readers_writers/monitor/rw_monitor.py
python dining_philosophers/semaphore/dp_semaphore.py
python dining_philosophers/monitor/dp_monitor.py
```
Options: `--readers N --writers N --rounds N` (readers-writers), `--meals N` (philosophers),
`--delay SECONDS`, `--seed N` (repeatable run).

## View
Open any file in `generated_html/` in a browser. Use Start / Pause / Reset, the speed slider and the timeline.

## How it works
`common/sim_html.py` holds a thread-safe `Recorder`. Each thread calls `emit()` on every state change.
After all threads finish, the event list is embedded as JSON in an HTML page whose JavaScript replays it.
Nothing is scripted: change the thread counts or delays and the trace changes.
Each run also prints a self-check (final value, maximum concurrent readers, rule violations = 0).

## Known limitations
- Semaphore Readers-Writers favours readers, so writers can starve under constant reading.
- Python's `threading` does not guarantee fair wake-up order, so starvation cannot be fully excluded in the philosophers.
- Log order can differ slightly from true order for events within the same millisecond.

## AI tools and references
See `ai_prompts/prompts.md` and `references/references.md`.
