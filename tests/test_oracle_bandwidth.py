"""Unabhängige Orakel: Bandbreite/Profil aus der permutierten Adjazenzmatrix (numpy), exakte Minimalbandbreite
durch numpy-Vollenumeration aller Permutationen (statt der Demo-Schleife mit frühem Abbruch), Cuthill-McKee
gegen eine eigenständig geschriebene Fassung (Startknoten wie in der Demo) und scipys reverse_cuthill_mckee
(Bandbreite vergleichen, nicht die Reihenfolge; scipy liefert die Reihenfolge, nicht perm[Knoten] = Position)."""

import itertools
import random

import numpy as np
import pytest

import band_algorithm as A
import band_scenario as S


def _graph(rng, n):
    p = rng.choice([0.1, 0.25, 0.5, 0.8])
    edges = [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p]
    if rng.random() < 0.3 and n >= 3:  # Baum
        edges = [(rng.randrange(i), i) for i in range(1, n)]
    return edges


def _adj(n, edges):
    return A.adjacency(n, tuple((u, v, 1.0) for u, v in edges))


def _matrix_bandwidth_profile(n, edges, perm):
    m = np.zeros((n, n), dtype=int)
    for u, v in edges:
        m[perm[u], perm[v]] = m[perm[v], perm[u]] = 1
    bw = prof = 0
    for i in range(n):
        cols = np.nonzero(m[i])[0]
        if len(cols):
            bw = max(bw, int(np.abs(cols - i).max()))
        left = cols[cols <= i]
        if len(left):
            prof += i - int(left.min())
    return bw, prof


def _exact_bandwidth(n, edges):
    if not edges:
        return 0
    e = np.array(edges)
    best = n
    for p in itertools.permutations(range(n)):
        p = np.array(p)
        best = min(best, int(np.abs(p[e[:, 0]] - p[e[:, 1]]).max()))
    return best


def _independent_cm_order(adj):
    n = len(adj)
    seen = [False] * n
    order = []
    deg = [len(a) for a in adj]
    while len(order) < n:
        seed = min(v for v in range(n) if not seen[v])
        comp, stack = {seed}, [seed]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in comp:
                    comp.add(v)
                    stack.append(v)
        comp = sorted(comp)
        start = A.pseudo_peripheral(adj, comp) if len(comp) > 1 else comp[0]
        seen[start] = True
        order.append(start)
        i = len(order) - 1
        while i < len(order):
            u = order[i]
            i += 1
            for v in sorted((x for x in adj[u] if not seen[x]), key=lambda x: (deg[x], x)):
                seen[v] = True
                order.append(v)
    return order


def test_bandwidth_profile_orders_bounds_match_independent_computation():
    rng = random.Random(21)
    for it in range(120):
        n = rng.randint(1, 8)
        edges = _graph(rng, n)
        adj = _adj(n, edges)
        cm = A.cuthill_mckee(adj)
        rcm = A.reverse_cuthill_mckee(adj)
        for perm in (list(range(n)), A.random_permutation(n, it), cm, rcm):
            assert sorted(perm) == list(range(n))
            assert (A.bandwidth(adj, perm), A.profile(adj, perm)) == _matrix_bandwidth_profile(n, edges, perm)
        assert A.bandwidth(adj, cm) == A.bandwidth(adj, rcm)
        assert A.cuthill_mckee_order(adj) == _independent_cm_order(adj)
        exact = _exact_bandwidth(n, edges)
        assert A.exact_bandwidth_bruteforce(adj) == exact
        assert A.lower_bound_diameter(adj) <= exact <= A.bandwidth(adj, cm)


def test_cuthill_mckee_matches_scipy_on_stars_and_is_competitive_on_grids():
    csgraph = pytest.importorskip("scipy.sparse.csgraph")
    sparse = pytest.importorskip("scipy.sparse")

    def scipy_bandwidth(inst):
        rows, cols = [], []
        for u, v, _w in inst.edges:
            rows += [u, v]
            cols += [v, u]
        mat = sparse.csr_matrix(([1] * len(rows), (rows, cols)), shape=(inst.n, inst.n))
        order = csgraph.reverse_cuthill_mckee(mat, symmetric_mode=True)
        perm = [0] * inst.n
        for pos, node in enumerate(order):
            perm[int(node)] = pos
        return A.bandwidth(A.adjacency(inst.n, inst.edges), perm)

    for n in (5, 8, 15):  # beide liefern auf dem Stern n-2 (README)
        inst = S.star_instance(n)
        adj = A.adjacency(inst.n, inst.edges)
        assert A.bandwidth(adj, A.reverse_cuthill_mckee(adj)) == n - 2
        assert scipy_bandwidth(inst) == n - 2
    for side, seed in [(6, 1), (8, 4), (10, 9)]:
        inst = S.random_relabel(S.generate(side=side, blocked=0.1, nettype="grid", seed=seed), seed=seed)
        adj = A.adjacency(inst.n, inst.edges)
        assert A.bandwidth(adj, A.reverse_cuthill_mckee(adj)) <= 2 * scipy_bandwidth(inst)
