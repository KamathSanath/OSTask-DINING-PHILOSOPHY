"""Readers-Writers (writer preference) using a monitor: one lock + one condition variable.

Waiting writers block new readers, so writers cannot starve.
"""
import argparse, random, sys, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))
from sim_html import Recorder, RWGuard, ForkGuard, write_html, print_trace


class ReadersWritersMonitor:
    def __init__(self, rec):
        self.cond = threading.Condition()     # lock + condition variable = the monitor
        self.rec = rec
        self.active_readers = 0
        self.writing = False
        self.waiting_writers = 0

    def start_read(self, name):
        with self.cond:
            self.rec.emit(name, "Waiting", "enters monitor, checks start_read condition")
            while self.writing or self.waiting_writers > 0:
                self.cond.wait()
            self.active_readers += 1
            self.rec.emit(name, "Reading", f"start_read granted (readers={self.active_readers})")

    def end_read(self, name):
        with self.cond:
            self.active_readers -= 1
            self.rec.emit(name, "Idle", f"end_read (readers={self.active_readers})")
            if self.active_readers == 0:
                self.cond.notify_all()

    def start_write(self, name):
        with self.cond:
            self.waiting_writers += 1
            self.rec.emit(name, "Waiting", "enters monitor, checks start_write condition")
            while self.writing or self.active_readers > 0:
                self.cond.wait()
            self.waiting_writers -= 1
            self.writing = True
            self.rec.emit(name, "Writing", "start_write granted")

    def end_write(self, name, note):
        with self.cond:
            self.writing = False
            self.rec.emit(name, "Idle", note)
            self.cond.notify_all()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--readers", type=int, default=3)
    p.add_argument("--writers", type=int, default=2)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--delay", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    if a.seed is not None:
        random.seed(a.seed)

    readers = [f"R{i + 1}" for i in range(a.readers)]
    writers = [f"W{i + 1}" for i in range(a.writers)]
    rec, guard = Recorder(readers + writers, "Idle"), RWGuard()
    mon, shared = ReadersWritersMonitor(rec), {"value": 0}

    def reader(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, 2 * a.delay))
            mon.start_read(name)
            guard.enter_read()
            _ = shared["value"]
            time.sleep(random.uniform(a.delay, 2 * a.delay))
            guard.leave_read()
            mon.end_read(name)
        rec.emit(name, "Finished", "all rounds done")

    def writer(name):
        for _ in range(a.rounds):
            time.sleep(random.uniform(0, 2 * a.delay))
            mon.start_write(name)
            guard.enter_write()
            old = shared["value"]
            time.sleep(random.uniform(a.delay, 2 * a.delay))
            shared["value"] = old + 1
            guard.leave_write()
            mon.end_write(name, f"wrote value {old} -> {old + 1}")
        rec.emit(name, "Finished", "all rounds done")

    threads = [threading.Thread(target=reader, args=(n,)) for n in readers] + \
              [threading.Thread(target=writer, args=(n,)) for n in writers]
    for t in threads: t.start()
    for t in threads: t.join()

    print_trace(rec)
    print(f"Final value {shared['value']} (expected {a.writers * a.rounds}), "
          f"max concurrent readers {guard.max_readers}, violations {guard.violations}")
    write_html(ROOT / "generated_html" / "readers_writers_monitor.html",
               "Readers-Writers (Monitor)", "one lock + condition variable, writer preference", rec, "rw")


if __name__ == "__main__":
    main()
