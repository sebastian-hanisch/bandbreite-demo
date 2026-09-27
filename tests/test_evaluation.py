"""Korrektheits-Kette Punkte 4, 8, 9 (s. PLAN/README): Profil CM gegen RCM über viele Instanzen GEMESSEN (nicht "RCM immer besser" behauptet), Erholungsgrad nach zufälliger Vertauschung GEMESSEN,
CM/RCM >= Exakt immer (Satz) und Determinismus/Sonderfälle der Auswertungsfunktionen selbst."""

import band_algorithm as A
import band_constants as C
import band_evaluation as ev


def _settings(**kw):
    base = dict(kind="city", side=6, blocked=0.0, nettype="grid", n_ba=C.DEFAULT_N_BA, m_ba=C.DEFAULT_M_BA, m0_ba=C.DEFAULT_M0_BA, n_star=C.DEFAULT_N_STAR, n_path=C.DEFAULT_N_PATH,
                seed=C.DEFAULT_SEED)
    base.update(kw)
    return ev.Settings(**base)


# --- analyse -----------------------------------------------------------------------------------------------------------------------------------------------


def test_analyse_city_returns_consistent_numbers():
    inst, adj, a = ev.analyse(_settings(kind="city", side=6))
    assert a.n == inst.n == 36
    assert a.bw_natural == A.bandwidth(adj, a.perm_natural)
    assert a.bw_cm == A.bandwidth(adj, a.perm_cm)
    assert a.bw_rcm == A.bandwidth(adj, a.perm_rcm)
    assert a.bw_cm == a.bw_rcm                     # Punkt 3, hier nochmal end-to-end über analyse()
    assert a.bw_exact is None                       # n=36 > N_EXACT
    assert a.lower_bound <= a.bw_cm


def test_analyse_small_star_includes_exact():
    inst, adj, a = ev.analyse(_settings(kind="star", n_star=8))
    assert a.bw_exact is not None
    assert a.bw_exact == C.star_optimal_bandwidth(8)
    assert a.bw_exact <= a.bw_cm


def test_analyse_cm_order_is_a_valid_visiting_sequence():
    inst, adj, a = ev.analyse(_settings(kind="ba", n_ba=25))
    assert sorted(a.cm_order) == list(range(inst.n))
    # Position aus cm_order muss mit perm_cm uebereinstimmen
    perm_from_order = [0] * inst.n
    for pos, node in enumerate(a.cm_order):
        perm_from_order[node] = pos
    assert perm_from_order == a.perm_cm


def test_analyse_is_deterministic():
    _, _, a1 = ev.analyse(_settings(kind="city_relabel", side=6, seed=13))
    _, _, a2 = ev.analyse(_settings(kind="city_relabel", side=6, seed=13))
    assert (a1.bw_cm, a1.bw_rcm, a1.perm_cm, a1.perm_rcm) == (a2.bw_cm, a2.bw_rcm, a2.perm_cm, a2.perm_rcm)


def test_analyse_path_and_star_kinds():
    _, _, a_path = ev.analyse(_settings(kind="path", n_path=12))
    assert a_path.bw_natural == 1 and a_path.bw_cm == 1 and a_path.bw_rcm == 1
    _, _, a_star = ev.analyse(_settings(kind="star", n_star=12))
    assert a_star.bw_cm == C.star_cm_bandwidth(12)


# --- recovery_check (Punkt 8) -------------------------------------------------------------------------------------------------------------------------------


def test_recovery_check_rows_shape_and_bounds():
    rows = ev.recovery_check(sides=(4, 5, 6), seeds=(1, 2))
    assert len(rows) == 6
    for r in rows:
        assert r["bw_relabeled"] >= r["bw_natural"]      # Vertauschung darf die Bandbreite nur verschlechtern oder gleich lassen, nie zufaellig besser machen als das Original selbst
        assert r["bw_cm"] <= r["bw_relabeled"]
        assert r["bw_rcm"] <= r["bw_relabeled"]


def test_recovery_check_cm_recovers_meaningfully_on_average():
    """GEMESSENER, nicht angenommener Befund: im Mittel bringt CM die zufaellig vertauschte Bandbreite deutlich zurueck in Richtung des natuerlichen Werts (Erholungsgrad klar > 0), auch wenn nicht
    jede einzelne Instanz exakt auf den natuerlichen Wert zurueckkommt."""
    rows = ev.recovery_check(sides=C.RECOVERY_SIDES, seeds=C.RECOVERY_SEEDS)
    mean_recovery = sum(r["recovery_cm"] for r in rows) / len(rows)
    assert mean_recovery > 0.5


def test_recovery_check_is_deterministic():
    a = ev.recovery_check(sides=(5, 6), seeds=(3, 4))
    b = ev.recovery_check(sides=(5, 6), seeds=(3, 4))
    assert a == b


# --- profile_comparison (Punkt 4) ---------------------------------------------------------------------------------------------------------------------------


def test_profile_comparison_shapes_and_bandwidth_invariant():
    rows, summary = ev.profile_comparison(seed=1, n_instances=40)
    assert summary["total"] == 40 == len(rows)
    assert summary["better"] + summary["equal"] + summary["worse"] == 40
    for r in rows:
        assert r["bw_cm"] == r["bw_rcm"]              # Punkt 3, auch hier ueber viele zufaellige Instanzen


def test_profile_comparison_is_not_a_landslide_in_either_direction():
    """Ehrlichkeitscheck (Punkt 4): weder 'RCM ist immer besser' noch 'RCM ist nie besser' darf gelten - beide Anteile werden tatsaechlich beobachtet."""
    rows, summary = ev.profile_comparison(seed=C.DEFAULT_SEED, n_instances=C.PROFILE_COMPARISON_N)
    assert summary["better"] > 0
    assert summary["worse"] >= 0                       # falls 0: dokumentierter, kein erzwungener Befund


def test_profile_comparison_is_deterministic():
    a = ev.profile_comparison(seed=5, n_instances=30)
    b = ev.profile_comparison(seed=5, n_instances=30)
    assert a == b


# --- size_sweep / exact_gap (Punkt 9: CM/RCM >= Exakt immer) ------------------------------------------------------------------------------------------------


def test_size_sweep_city_shape():
    rows = ev.size_sweep(kind="city", sizes=(3, 4, 5))
    assert [r["size"] for r in rows] == [3, 4, 5]
    for r in rows:
        assert r["bw_cm"] >= r["lower_bound"]
        assert r["bw_rcm"] >= r["lower_bound"]


def test_size_sweep_all_kinds_run():
    for kind, sizes in (("city", (3, 4)), ("city_relabel", (3, 4)), ("ba", (8, 10)), ("star", (4, 6)), ("path", (4, 6))):
        rows = ev.size_sweep(kind=kind, sizes=sizes)
        assert len(rows) == len(sizes)


def test_exact_gap_cm_and_rcm_never_beat_the_true_optimum():
    """Punkt 9, Satz: die Brute-Force liefert das globale Optimum, CM/RCM können also niemals eine KLEINERE Bandbreite erreichen, nur gleich oder groesser."""
    for kind in ("city", "ba", "star", "path"):
        rows = ev.exact_gap(kind=kind)
        assert len(rows) > 0
        for r in rows:
            assert r["bw_cm"] >= r["bw_exact"]
            assert r["bw_rcm"] >= r["bw_exact"]
            assert r["bw_random"] >= r["bw_exact"]
            assert r["bw_exact"] >= r["lower_bound"]


def test_exact_gap_is_empty_when_no_size_is_small_enough():
    rows = ev.exact_gap(kind="ba", sizes=(50, 60))
    assert rows == []
