"""Jede Zahl in den Preset-Hilfetexten wird hier gegen die echten Auswertungsfunktionen nachgerechnet (Hauskonvention, wie `haer_presets`/`tests/test_presets.py`)."""

import pytest

import band_algorithm as A
import band_constants as C
import band_evaluation as ev
import band_scenario as S


def test_every_preset_has_help_text():
    for name in C.PRESETS:
        assert name in C.PRESET_HELP and C.PRESET_HELP[name]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_produces_a_valid_instance(name):
    p = C.PRESETS[name]
    settings = ev.Settings(kind=p["kind"], side=p.get("side", C.DEFAULT_SIDE), blocked=p.get("blocked", C.DEFAULT_BLOCKED), nettype=p.get("nettype", "grid"),
                            n_ba=p.get("nba", C.DEFAULT_N_BA), m_ba=p.get("mba", C.DEFAULT_M_BA), m0_ba=p.get("m0ba", C.DEFAULT_M0_BA), n_star=p.get("nstar", C.DEFAULT_N_STAR),
                            n_path=p.get("npath", C.DEFAULT_N_PATH), seed=p["seed"])
    inst, adj, a = ev.analyse(settings)
    assert inst.n > 0
    assert a.bw_cm == a.bw_rcm


def test_raster_natuerlich_preset_numbers():
    inst = S.generate(8, 0.0, "grid", 35)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, list(range(inst.n))) == 8
    assert A.lower_bound_diameter(adj) == 5


def test_raster_zufaellig_vertauscht_preset_numbers():
    base = S.generate(8, 0.0, "grid", 35)
    rel = S.random_relabel(base, 35)
    adj = A.adjacency(rel.n, rel.edges)
    assert A.bandwidth(adj, list(range(rel.n))) == 62
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 8
    assert A.bandwidth(adj, A.reverse_cuthill_mckee(adj)) == 8


def test_stern_preset_numbers():
    inst = S.star_instance(15)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 13 == C.star_cm_bandwidth(15)
    assert C.star_optimal_bandwidth(15) == 7


def test_pfad_preset_numbers():
    inst = S.path_instance(15)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 1


def test_skalenfrei_preset_numbers():
    inst = S.barabasi_albert_instance(60, 2, 4, 35)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, list(range(inst.n))) == 56
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 30
    assert A.lower_bound_diameter(adj) == 12


def test_kleine_instanz_gegen_exakt_preset_numbers():
    inst = S.generate(3, 0.0, "grid", 35)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, list(range(inst.n))) == 3
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == 3
    assert A.exact_bandwidth_bruteforce(adj) == 3
    assert A.lower_bound_diameter(adj) == 2


def test_profil_vergleich_preset_numbers():
    rows, summary = ev.profile_comparison(seed=35, n_instances=C.PROFILE_COMPARISON_N)
    assert summary == {"better": 174, "equal": 26, "worse": 0, "total": 200}
    assert all(r["bw_cm"] == r["bw_rcm"] for r in rows)
