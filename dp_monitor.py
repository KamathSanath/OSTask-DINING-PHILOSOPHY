"""Dining Philosophers, 4 philosophers, monitor (lock + condition variable).

A philosopher may eat only when neither neighbour is eating, so both forks are free.
The check and the state change happen atomically inside the monitor.
"""
import argparse, random, sys, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))
from sim_html import Recorder, RWGuard, ForkGuard, write_html, print_trace

N = 4


class DiningMonitor:
    def __init__(self, rec):
        self.cond = threading.Condition()
        self.rec = rec
        self.state = ["THINKING"] * N

    def _can_eat(self, i):
        return self.state[(i - 1) % N] != "EATING" and self.state[(i + 1) % N] != "EATING"

    def take_forks(self, i, name):
        with self.cond:
            self.state[i] = "HUNGRY"
            self.rec.emit(name, "Hungry", "asks the monitor for forks")
            while not self._can_eat(i):
                self.cond.wait()
            self.state[i] = "EATING"
            self.rec.emit(name, "Acquiring Forks", "neighbours not eating, takes both",
                          take=[i, (i + 1) % N])
            self.rec.emit(name, "Eating", "has both forks")

    def put_forks(self, i, name):
        with self.cond:
            self.state[i] = "THINKING"
            self.rec.emit(name, "Releasing Forks", "puts both forks down", drop=[i, (i + 1) % N])
            self.rec.emit(name, "Thinking", "notify_all neighbours")
            self.cond.notify_all()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--meals", type=int, default=3)
    p.add_argument("--delay", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    if a.seed is not None:
        random.seed(a.seed)

    names = [f"P{i + 1}" for i in range(N)]
    rec, guard = Recorder(names, "Thinking", N), ForkGuard(N)
    mon, meals = DiningMonitor(rec), [0] * N

    def philosopher(i):
        for _ in range(a.meals):
            time.sleep(random.uniform(0, 2 * a.delay))
            mon.take_forks(i, names[i])
            guard.enter(i)
            time.sleep(random.uniform(a.delay, 2 * a.delay))
            guard.leave(i)
            meals[i] += 1
            mon.put_forks(i, names[i])
        rec.emit(names[i], "Finished", "all meals eaten")

    threads = [threading.Thread(target=philosopher, args=(i,)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()

    print_trace(rec)
    print(f"Meals per philosopher {meals}, neighbour-overlap violations {guard.violations}")
    write_html(ROOT / "generated_html" / "dining_philosophers_monitor.html",
               "Dining Philosophers (Monitor)", "lock + condition variable, neighbour check", rec, "dp")


if __name__ == "__main__":
    main()
