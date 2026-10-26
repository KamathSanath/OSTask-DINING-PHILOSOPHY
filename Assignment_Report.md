# Operating Systems Programming Assignment Report
**Synchronization with Semaphores and Monitors (Python) and Program-Generated HTML Simulations**

Name: <your name> | USN: <your USN> | Repository: <GitHub URL> | Submitted to: <faculty name>

## 1. Objective
Two classic problems, Readers-Writers and Dining Philosophers (four philosophers), are implemented twice each:
once with semaphores and once with a monitor (a lock plus a condition variable). Each program logs its own state
changes and turns that log into a browser simulation. The aim is to show how mutual exclusion is obtained and how
deadlock and starvation are handled.

## 2. Readers-Writers with semaphores
The shared resource is one integer. Two semaphores, both starting at 1, control access. `mutex` guards the counter
`read_count`; `wrt` gives exclusive access to the data. The first reader to arrive waits on `wrt`, which keeps writers
out, and the last reader to leave signals it. Writers wait on `wrt` directly. Many readers can therefore read together,
while a writer is always alone. Readers are favoured, so a writer may wait a long time if readers keep arriving.

## 3. Readers-Writers with a monitor
A class holds `active_readers`, `writing` and `waiting_writers` behind one condition object. `start_read` waits while a
writer is active or queued; `start_write` waits while anyone is active. `end_read` and `end_write` call `notify_all`.
Because queued writers block new readers, this version avoids writer starvation.

## 4. Dining Philosophers with semaphores
Four fork semaphores start at 1, and a `room` semaphore starts at 3. A philosopher must enter the room, then pick up the
left fork, then the right one. At most three philosophers hold forks at once, so at least one can always obtain a second
fork. That removes the circular wait and prevents deadlock. Fairness of wake-up is left to the runtime, so starvation is
unlikely but not strictly excluded.

## 5. Dining Philosophers with a monitor
A shared state array holds THINKING, HUNGRY or EATING. `take_forks` waits until neither neighbour is EATING, then marks
the caller EATING, all inside the monitor. `put_forks` marks THINKING and calls `notify_all`. Neighbours never eat
together, and the check-and-set is atomic, so deadlock cannot occur. Two neighbours that alternate could in theory
keep a third philosopher hungry.

## 6. How the HTML is produced
`Recorder.emit()` is called by each thread at every state change (Waiting, Reading, Hungry, Eating and so on). It stores
a timestamp, the actor, the new state, a note, a snapshot of all states and fork owners. When the threads finish,
`write_html()` embeds this list as JSON in a page. The page's JavaScript redraws cards (Readers-Writers) or a table with
forks (Philosophers) for the chosen event and offers Start, Pause, Reset, speed and a timeline.

## 7. Execution traces (from real runs, seed 7, delay 0.1)
Readers-Writers (semaphore): W1 waits on `wrt` and starts writing; R2 arrives, becomes first reader and blocks on `wrt`;
R1, W2 and R3 queue; W1 finishes (value 0 -> 1) and releases `wrt`. Result: value 6 of 6 expected, 3 readers at once, 0 violations.

Readers-Writers (monitor): same start; when W1 ends, W2 is granted the monitor first because a writer is queued. Value 6 of 6, 0 violations.

Dining Philosophers (semaphore): P4 and P2 take F4 and F2, then P4 takes F1 and eats. All four philosophers ate 3 times, 0 violations.

Dining Philosophers (monitor): P4 and P2 are granted forks at once (not neighbours); P1 and P3 become hungry and wait. All four ate 3 times, 0 violations.

## 8. Race condition, mutual exclusion, deadlock, starvation
- **Race condition:** writers read the value, pause, then store value+1. Without exclusion two writers would lose updates; the final value equalling writers x rounds shows no update was lost.
- **Mutual exclusion:** `wrt` (or the monitor condition) allows one writer or many readers. A separate checker counts any overlap; it stayed at 0.
- **Deadlock:** prevented by the `room` semaphore (semaphore version) and by the neighbour test (monitor version).
- **Starvation:** possible for writers in the semaphore Readers-Writers; avoided by writer preference in the monitor version.

## 9. Semaphore versus monitor
Semaphores are small low-level counters; correctness depends on every acquire having its release, in the right order.
A monitor keeps the data, the lock and the waiting conditions together, so the logic reads as plain conditions and is
easier to check. The cost is that the programmer must write the wait conditions correctly and use `notify_all`.

## 10. Screenshots
<Insert one screenshot of each page in generated_html/ and of each console run.>

## 11. AI usage summary
Claude (Anthropic) produced the first version of the code and documents from the assignment PDF. I ran all four
programs, read the traces, and <describe your own changes>. Limitation noticed: the semaphore Readers-Writers favours
readers. Full prompt log: `ai_prompts/prompts.md`.

## 12. Declaration
"I declare that I have personally tested and understood the submitted programs. I have disclosed the AI tools and external resources used in developing this assignment. I can explain the synchronization logic, generated HTML simulation, and modifications made to the code. I have not knowingly submitted another student’s work or unacknowledged third-party material as my own."

## 13. References
See `references/references.md`.
