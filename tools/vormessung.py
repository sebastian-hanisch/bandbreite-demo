"""Vormessung (Schritt 5 des Bauplans): wie groß darf N_EXACT sein, damit `exact_bandwidth_bruteforce` (Brute-Force über n! Permutationen) noch interaktiv nutzbar bleibt? Miss die Laufzeit auf
den dichtesten realistischen Testfällen (vollständiger Graph als worst case, Barabási-Albert als realistischer worst case) für n=7..11."""

import itertools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import band_algorithm as A  # noqa: E402
import band_scenario as S  # noqa: E402


def time_it(adj, label, n):
    t0 = time.perf_counter()
    bw = A.exact_bandwidth_bruteforce(adj)
    dt = time.perf_counter() - t0
    print(f"n={n:2d}  {label:24s}  bandbreite={bw:3d}  {dt:7.3f}s  ({len(list(itertools.permutations(range(min(n,1))))) if False else ''}")


for n in range(6, 12):
    edges = [(u, v, 1.0) for u in range(n) for v in range(u + 1, n)]
    adj = A.adjacency(n, edges)
    time_it(adj, "vollstaendiger Graph", n)

for n in range(6, 12):
    m0 = min(4, n)
    m = min(2, m0)
    inst = S.barabasi_albert_instance(n, m, m0, seed=1)
    adj = A.adjacency(inst.n, inst.edges)
    time_it(adj, "Barabasi-Albert", n)

for side in (3, 4):
    inst = S.generate(side, 0.0, "grid", seed=1)
    adj = A.adjacency(inst.n, inst.edges)
    time_it(adj, "Raster", inst.n)
