"""Korrektheits-Kette Punkte 1, 2, 3, 5, 6, 7 (s. PLAN/README): bandwidth/profile gegen unabhängige Neuberechnung, CM/RCM liefern immer eine gültige Permutation (auch bei mehreren Komponenten),
Bandbreite(CM) == Bandbreite(RCM) EXAKT auf jeder Instanz (Satz, kein Band), Stern/Pfad von Hand nachgerechnet, untere Schranke nie verletzt."""

import random

import networkx as nx
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import reverse_cuthill_mckee as scipy_rcm

import band_algorithm as A
import band_constants as C
import band_scenario as S


def _random_instances(n_instances, seed0=1000):
    """Eine bunte Mischung aus allen fünf Instanzarten für die Massentests unten (>= 300 Instanzen für Punkt 1)."""
    rng = random.Random(seed0)
    out = []
    for i in range(n_instances):
        seed = rng.randrange(1_000_000)
        kind = rng.choice(["city", "city_relabel", "ba", "star", "path"])
        if kind == "city":
            inst = S.generate(rng.randint(3, 10), rng.choice([0.0, 0.1, 0.2, 0.3]), rng.choice(["grid", "random"]), seed)
        elif kind == "city_relabel":
            base = S.generate(rng.randint(3, 10), rng.choice([0.0, 0.1, 0.2]), "grid", seed)
            inst = S.random_relabel(base, seed)
        elif kind == "ba":
            m0 = rng.randint(3, 6)
            inst = S.barabasi_albert_instance(rng.randint(m0, 40), rng.randint(1, m0), m0, seed)
        elif kind == "star":
            inst = S.star_instance(rng.randint(3, 30))
        else:
            inst = S.path_instance(rng.randint(2, 30))
        out.append(inst)
    return out


INSTANCES_300 = _random_instances(300)


def _independent_bandwidth(edges, perm):
    """Bandbreite ohne band_algorithm.bandwidth, direkt aus den rohen Kantentripeln (u, v, w) - die unabhängige Gegenprobe für Punkt 1."""
    best = 0
    for u, v, w in edges:
        d = abs(perm[u] - perm[v])
        if d > best:
            best = d
    return best


def _independent_profile(edges, n, perm):
    """Profil ohne band_algorithm.profile, direkt aus den rohen Kantentripeln - die unabhängige Gegenprobe für Punkt 1."""
    best = [None] * n
    for u, v, w in edges:
        for a, b in ((u, v), (v, u)):
            if perm[a] <= perm[b] and (best[b] is None or perm[a] < best[b]):
                best[b] = perm[a]
    return sum(perm[v] - best[v] for v in range(n) if best[v] is not None)


@pytest.mark.parametrize("inst", INSTANCES_300, ids=range(300))
def test_bandwidth_and_profile_match_independent_recomputation(inst):
    adj = A.adjacency(inst.n, inst.edges)
    perm = A.random_permutation(inst.n, inst.seed + 1)
    assert A.bandwidth(adj, perm) == _independent_bandwidth(inst.edges, perm)
    assert A.profile(adj, perm) == _independent_profile(inst.edges, inst.n, perm)


@pytest.mark.parametrize("inst", INSTANCES_300, ids=range(300))
def test_cm_and_rcm_are_always_valid_permutations(inst):
    adj = A.adjacency(inst.n, inst.edges)
    for perm in (A.cuthill_mckee(adj), A.reverse_cuthill_mckee(adj)):
        assert sorted(perm) == list(range(inst.n))


@pytest.mark.parametrize("inst", INSTANCES_300, ids=range(300))
def test_bandwidth_of_cm_equals_bandwidth_of_rcm_exactly(inst):
    """Punkt 3, der zentrale Satz dieses Stücks: Umkehren der Positionsfolge ändert die Bandbreite NIE - Test auf exakte Gleichheit, kein Toleranzband."""
    adj = A.adjacency(inst.n, inst.edges)
    cm = A.cuthill_mckee(adj)
    rcm = A.reverse_cuthill_mckee(adj)
    assert A.bandwidth(adj, cm) == A.bandwidth(adj, rcm)


@pytest.mark.parametrize("inst", INSTANCES_300, ids=range(300))
def test_lower_bound_is_never_violated_by_any_permutation(inst):
    """Punkt 7: die Diameter-Schranke ist ein Satz - JEDE Permutation (auch eine schlechte, zufällige) muss sie erfüllen."""
    adj = A.adjacency(inst.n, inst.edges)
    lb = A.lower_bound_diameter(adj)
    for perm in (list(range(inst.n)), A.random_permutation(inst.n, inst.seed + 2), A.cuthill_mckee(adj), A.reverse_cuthill_mckee(adj)):
        assert A.bandwidth(adj, perm) >= lb


# --- Punkt 5/6: Stern und Pfad von Hand ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 4, 5, 6, 8, 9])
def test_star_exact_bandwidth_matches_the_closed_form(n):
    """Punkt 5 (Exakt-Teil): die Brute-Force-Referenz trifft die bewiesene optimale Bandbreite ⌈(n-1)/2⌉ exakt."""
    inst = S.star_instance(n)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.exact_bandwidth_bruteforce(adj) == C.star_optimal_bandwidth(n)


@pytest.mark.parametrize("n", [3, 4, 5, 6, 8, 10, 15, 20, 30])
def test_star_cm_and_rcm_bandwidth_matches_the_measured_n_minus_2_pattern(n):
    """Ehrlicher, ÜBERRASCHENDER Befund (Punkt 5, korrigiert gegenüber der Planannahme): Cuthill-McKee erreicht auf dem Stern NICHT das Optimum ⌈(n-1)/2⌉, sondern GENAU n-2 (für n>=3) - der
    pseudo-periphere Start ist immer ein Blatt, der Mittelpunkt landet dadurch auf Position 1 (bzw. n-2 bei RCM), und der gesamte Rest der Blätter muss sich auf die verbleibenden n-2 Positionen
    verteilen. Bestätigt gegen scipy.sparse.csgraph.reverse_cuthill_mckee (liefert dort ebenfalls n-2) - ein bekanntes, hier NACHGEMESSENES Strukturproblem von Cuthill-McKee auf
    Stern-/Hub-dominierten Graphen, s. README "Befunde"."""
    inst = S.star_instance(n)
    adj = A.adjacency(inst.n, inst.edges)
    cm_bw = A.bandwidth(adj, A.cuthill_mckee(adj))
    rcm_bw = A.bandwidth(adj, A.reverse_cuthill_mckee(adj))
    assert cm_bw == n - 2
    assert rcm_bw == n - 2
    if n <= 4:
        assert cm_bw == C.star_optimal_bandwidth(n)          # nur bei sehr kleinen Sternen (n=3,4) zufaellig identisch mit dem Optimum
    else:
        assert cm_bw > C.star_optimal_bandwidth(n)            # ab n=5 messbar schlechter als das Optimum


@pytest.mark.parametrize("n", [3, 5, 8])
def test_star_closed_form_matches_brute_force_directly(n):
    """Gegenprobe der Formel selbst (unabhängig von CM/RCM): stimmt ceil((n-1)/2) mit der echten Brute-Force überein?"""
    inst = S.star_instance(n)
    adj = A.adjacency(inst.n, inst.edges)
    assert C.star_optimal_bandwidth(n) == A.exact_bandwidth_bruteforce(adj)


def test_naive_ceil_n_half_formula_disagrees_with_the_true_optimum_for_odd_n():
    """Ehrlicher Befund: die im Plan grob skizzierte Faustformel ⌈n/2⌉ trifft NICHT für jedes n zu - bei ungeradem n liegt der wahre Wert ceil((n-1)/2) einen darunter. Dieser Test dokumentiert
    den Unterschied bewusst, statt ihn zu verschweigen (s. README "Design-Entscheidungen")."""
    import math
    for n in (3, 5, 7, 9, 15, 21):
        naive = math.ceil(n / 2)
        exact = C.star_optimal_bandwidth(n)
        assert exact == naive - 1


@pytest.mark.parametrize("n", [2, 3, 4, 5, 10, 20, 40])
def test_path_bandwidth_is_always_exactly_one(n):
    inst = S.path_instance(n)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, list(range(n))) == 1
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 1
    assert A.bandwidth(adj, A.reverse_cuthill_mckee(adj)) == 1
    if n <= C.N_EXACT:
        assert A.exact_bandwidth_bruteforce(adj) == 1


# --- Punkt 10: Sonderfälle --------------------------------------------------------------------------------------------------------------------------------


def test_two_nodes_one_edge():
    adj = A.adjacency(2, [(0, 1, 1.0)])
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 1
    assert A.exact_bandwidth_bruteforce(adj) == 1


def test_single_node_no_edges():
    adj = A.adjacency(1, [])
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 0
    assert A.profile(adj, [0]) == 0
    assert A.exact_bandwidth_bruteforce(adj) == 0
    assert A.lower_bound_diameter(adj) == 0


def test_disconnected_graph_two_components_cm_rcm_still_valid_and_lower_bound_holds():
    edges = [(0, 1, 1.0), (1, 2, 1.0), (3, 4, 1.0), (5, 6, 1.0), (6, 7, 1.0), (7, 8, 1.0)]
    adj = A.adjacency(9, edges)
    cm = A.cuthill_mckee(adj)
    rcm = A.reverse_cuthill_mckee(adj)
    assert sorted(cm) == list(range(9))
    assert sorted(rcm) == list(range(9))
    assert A.bandwidth(adj, cm) == A.bandwidth(adj, rcm)
    lb = A.lower_bound_diameter(adj)
    assert A.bandwidth(adj, cm) >= lb
    assert A.bandwidth(adj, list(range(9))) >= lb


def test_lower_bound_component_wise_formula_is_not_fooled_by_disconnected_graphs():
    """Regressionstest für die im Modul-Docstring erklärte Falle: zwei getrennte Kanten (n=4) - eine naive globale Formel (n, globaler Durchmesser) würde faelschlich 3 behaupten, obwohl
    Bandbreite 1 erreichbar ist. Die komponentenweise Maximierung muss stattdessen höchstens 1 liefern."""
    adj = A.adjacency(4, [(0, 1, 1.0), (2, 3, 1.0)])
    assert A.lower_bound_diameter(adj) == 1
    assert A.bandwidth(adj, [0, 1, 2, 3]) == 1


def test_complete_graph_bandwidth_is_n_minus_1():
    n = 6
    edges = [(u, v, 1.0) for u in range(n) for v in range(u + 1, n)]
    adj = A.adjacency(n, edges)
    assert A.bandwidth(adj, list(range(n))) == n - 1
    assert A.exact_bandwidth_bruteforce(adj) == n - 1
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == n - 1


# --- Determinismus -----------------------------------------------------------------------------------------------------------------------------------------


def test_cuthill_mckee_is_deterministic():
    inst = S.barabasi_albert_instance(40, 2, 4, seed=17)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.cuthill_mckee(adj) == A.cuthill_mckee(adj)


def test_pseudo_peripheral_is_deterministic():
    inst = S.generate(side=8, blocked=0.2, nettype="grid", seed=3)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.pseudo_peripheral(adj) == A.pseudo_peripheral(adj)


# --- Unabhängige Gegenprobe gegen scipy/networkx --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("side,seed", [(6, 1), (8, 4), (10, 9)])
def test_our_rcm_bandwidth_is_competitive_with_scipys_reverse_cuthill_mckee(side, seed):
    """Unabhängige Fremd-Implementierung als Gegenprobe (nicht auf exakte Permutationsgleichheit - unterschiedliche Tie-Break-Regeln führen zu unterschiedlichen, aber gültigen Ergebnissen -
    sondern auf vergleichbare BANDBREITE): scipy.sparse.csgraph.reverse_cuthill_mckee auf demselben (zufällig vertauschten) Graphen darf unsere Bandbreite nicht drastisch schlagen."""
    base = S.generate(side=side, blocked=0.1, nettype="grid", seed=seed)
    inst = S.random_relabel(base, seed=seed)
    adj = A.adjacency(inst.n, inst.edges)
    our_bw = A.bandwidth(adj, A.reverse_cuthill_mckee(adj))

    rows, cols = [], []
    for u, v, w in inst.edges:
        rows += [u, v]
        cols += [v, u]
    mat = csr_matrix(([1] * len(rows), (rows, cols)), shape=(inst.n, inst.n))
    scipy_order = scipy_rcm(mat, symmetric_mode=True)  # scipy liefert die REIHENFOLGE (order[pos] = Knoten), nicht perm[Knoten] = pos
    scipy_perm = [0] * inst.n
    for pos, node in enumerate(scipy_order):
        scipy_perm[int(node)] = pos
    scipy_bw = A.bandwidth(adj, scipy_perm)
    assert our_bw <= 2 * max(scipy_bw, 1)


@pytest.mark.parametrize("side,seed", [(5, 2), (7, 6)])
def test_degree_centrality_matches_networkx(side, seed):
    inst = S.generate(side=side, blocked=0.15, nettype="grid", seed=seed)
    adj = A.adjacency(inst.n, inst.edges)
    g = nx.Graph()
    g.add_nodes_from(range(inst.n))
    g.add_edges_from((u, v) for u, v, w in inst.edges)
    nx_degrees = [g.degree(v) for v in range(inst.n)]
    assert A.degree_centrality(adj) == nx_degrees
