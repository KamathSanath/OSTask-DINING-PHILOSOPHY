"""Dining Philosophers, 4 philosophers, semaphores.

fork[i] (1 each): one semaphore per fork.
room (3): at most N-1 philosophers compete for forks, so a circular wait is impossible (no deadlock).
"""
import argparse, random, sys, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))
from sim_html import Recorder, RWGuard, ForkGuard, write_html, print_trace

N = 4


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
    forks = [threading.Semaphore(1) for _ in range(N)]
    room = threading.Semaphore(N - 1)
    meals = [0] * N

    def philosopher(i):
        name, left, right = names[i], i, (i + 1) % N      # fork i sits between P(i) and P(i+1)
        for _ in range(a.meals):
            time.sleep(random.uniform(0, 2 * a.delay))    # thinking
            rec.emit(name, "Hungry", "wait(room)")
            room.acquire()
            rec.emit(name, "Acquiring Forks", f"wait(fork F{left + 1})")
            forks[left].acquire()
            rec.emit(name, "Acquiring Forks", f"holds F{left + 1}", take=[left])
            time.sleep(a.delay / 4)                       # makes contention visible
            forks[right].acquire()
            rec.emit(name, "Acquiring Forks", f"holds F{right + 1}", take=[right])
            guard.enter(i)
            rec.emit(name, "Eating", "has both forks")
            time.sleep(random.uniform(a.delay, 2 * a.delay))
            guard.leave(i)
            meals[i] += 1
            rec.emit(name, "Releasing Forks", "puts both forks down", drop=[left, right])
            forks[left].release()
            forks[right].release()
            room.release()
            rec.emit(name, "Thinking", "signal(room)")
        rec.emit(name, "Finished", "all meals eaten")

    threads = [threading.Thread(target=philosopher, args=(i,)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()

    print_trace(rec)
    print(f"Meals per philosopher {meals}, neighbour-overlap violations {guard.violations}")
    write_html(ROOT / "generated_html" / "dining_philosophers_semaphore.html",
               "Dining Philosophers (Semaphores)", "4 fork semaphores + room semaphore (N-1)", rec, "dp")


if __name__ == "__main__":
    main()
