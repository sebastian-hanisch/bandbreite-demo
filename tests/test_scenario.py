"""Rauchtests der fünf Instanzen: Knoten-/Kantenzahl, Sortierung, Determinismus, Fehlerfälle."""

import pytest

import band_scenario as S


def test_generate_grid_has_expected_edge_count():
    inst = S.generate(side=5, blocked=0.0, nettype="grid", seed=1)
    assert inst.n == 25
    assert inst.m == 2 * 5 * 4              # side*(side-1) horizontale + vertikale Kanten je Richtung
    us = [u for u, v, w in inst.edges]
    vs = [v for u, v, w in inst.edges]
    assert all(u < v for u, v in zip(us, vs))
    assert list(inst.edges) == sorted(inst.edges)


def test_generate_is_deterministic():
    a = S.generate(side=6, blocked=0.2, nettype="grid", seed=7)
    b = S.generate(side=6, blocked=0.2, nettype="grid", seed=7)
    assert a.edges == b.edges
    assert (a.xy == b.xy).all()


def test_generate_random_nettype_same_edge_count_as_grid():
    grid = S.generate(side=6, blocked=0.1, nettype="grid", seed=3)
    rnd = S.generate(side=6, blocked=0.1, nettype="random", seed=3)
    assert rnd.n == grid.n
    assert len(rnd.edges) == len(grid.edges)


def test_generate_rejects_too_small_side():
    with pytest.raises(ValueError):
        S.generate(side=1, seed=1)


def test_random_relabel_preserves_node_and_edge_count_and_degree_sequence():
    base = S.generate(side=5, blocked=0.1, nettype="grid", seed=9)
    relabeled = S.random_relabel(base, seed=9)
    assert relabeled.n == base.n
    assert relabeled.m == base.m
    assert list(relabeled.edges) == sorted(relabeled.edges)
    deg_base = sorted(_degree_sequence(base))
    deg_relabeled = sorted(_degree_sequence(relabeled))
    assert deg_base == deg_relabeled


def test_random_relabel_actually_changes_the_numbering_for_a_nontrivial_graph():
    base = S.generate(side=6, blocked=0.0, nettype="grid", seed=5)
    relabeled = S.random_relabel(base, seed=5)
    assert relabeled.edges != base.edges


def test_random_relabel_is_deterministic():
    base = S.generate(side=5, blocked=0.0, nettype="grid", seed=5)
    a = S.random_relabel(base, seed=5)
    b = S.random_relabel(base, seed=5)
    assert a.edges == b.edges
    assert (a.xy == b.xy).all()


def _degree_sequence(inst):
    deg = [0] * inst.n
    for u, v, w in inst.edges:
        deg[u] += 1
        deg[v] += 1
    return deg


def test_barabasi_albert_has_exact_edge_count():
    inst = S.barabasi_albert_instance(n=30, m=2, m0=4, seed=1)
    assert inst.n == 30
    assert inst.m == 4 + (30 - 4) * 2


def test_barabasi_albert_rejects_bad_parameters():
    with pytest.raises(ValueError):
        S.barabasi_albert_instance(n=30, m=2, m0=2, seed=1)          # m0 < 3
    with pytest.raises(ValueError):
        S.barabasi_albert_instance(n=30, m=5, m0=4, seed=1)          # m > m0


def test_star_instance_edge_count_and_shape():
    inst = S.star_instance(n=8)
    assert inst.n == 8
    assert inst.m == 7
    assert all(u == 0 for u, v, w in inst.edges)
    assert sorted(v for u, v, w in inst.edges) == list(range(1, 8))


def test_star_instance_rejects_too_small_n():
    with pytest.raises(ValueError):
        S.star_instance(n=2)


def test_path_instance_edge_count_and_shape():
    inst = S.path_instance(n=10)
    assert inst.n == 10
    assert inst.m == 9
    assert [(u, v) for u, v, w in inst.edges] == [(i, i + 1) for i in range(9)]


def test_path_instance_rejects_too_small_n():
    with pytest.raises(ValueError):
        S.path_instance(n=1)
