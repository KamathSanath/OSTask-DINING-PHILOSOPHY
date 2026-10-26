"""Readers-Writers (reader preference) solved with two semaphores.

mutex (1): protects read_count.   wrt (1): exclusive access to the shared data.
Shared resource: shared["value"].  Critical section: reading / writing it.
"""
import argparse, random, sys, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))
from sim_html import Recorder, RWGuard, ForkGuard, write_html, print_trace


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--readers", type=int, default=3)
    p.add_argument("--writers", type=int, default=2)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--delay", type=float, default=0.3, help="base delay in seconds")
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    if a.seed is not None:
        random.seed(a.seed)

    readers = [f"R{i + 1}" for i in range(a.readers)]
    writers = [f"W{i + 1}" for i in range(a.writers)]
    rec, guard = Recorder(readers + writers, "Idle"), RWGuard()
    mutex, wrt = threading.Semaphore(1), threading.Semaphore(1)
    shared = {"value": 0, "read_count": 0}

    def reader(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, 2 * a.delay))
            rec.emit(name, "Waiting", "wait(mutex)")
            mutex.acquire()
            shared["read_count"] += 1
            if shared["read_count"] == 1:           # first reader locks writers out
                rec.emit(name, "Waiting", "first reader: wait(wrt)")
                wrt.acquire()
            mutex.release()
            guard.enter_read()
            rec.emit(name, "Reading", f"reads value={shared['value']} (readers={shared['read_count']})")
            time.sleep(random.uniform(a.delay, 2 * a.delay))
            guard.leave_read()
            rec.emit(name, "Idle", "finished reading")
            mutex.acquire()
            shared["read_count"] -= 1
            if shared["read_count"] == 0:           # last reader lets writers in
                wrt.release()
            mutex.release()
        rec.emit(name, "Finished", "all rounds done")

    def writer(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, 2 * a.delay))
            rec.emit(name, "Waiting", "wait(wrt)")
            wrt.acquire()
            guard.enter_write()
            rec.emit(name, "Writing", "has exclusive access")
            old = shared["value"]
            time.sleep(random.uniform(a.delay, 2 * a.delay))   # widens the race window
            shared["value"] = old + 1
            guard.leave_write()
            rec.emit(name, "Idle", f"wrote value {old} -> {old + 1}")
            wrt.release()
        rec.emit(name, "Finished", "all rounds done")

    threads = [threading.Thread(target=reader, args=(n,)) for n in readers] + \
              [threading.Thread(target=writer, args=(n,)) for n in writers]
    for t in threads: t.start()
    for t in threads: t.join()

    print_trace(rec)
    print(f"Final value {shared['value']} (expected {a.writers * a.rounds}), "
          f"max concurrent readers {guard.max_readers}, violations {guard.violations}")
    write_html(ROOT / "generated_html" / "readers_writers_semaphore.html",
               "Readers-Writers (Semaphores)", "mutex protects read_count, wrt guards the shared data", rec, "rw")


if __name__ == "__main__":
    main()
