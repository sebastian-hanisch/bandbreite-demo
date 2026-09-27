"""Jede in README.md behauptete Zahl wird hier über die echten Auswertungsfunktionen nachgerechnet - Hauskonvention der Reihe (kein Text ohne Test dahinter)."""

import band_algorithm as A
import band_constants as C
import band_evaluation as ev
import band_scenario as S


def test_full_recovery_on_every_tested_grid_relabeling():
    """README „Befunde": Cuthill-McKee UND Reverse Cuthill-McKee erreichen auf JEDER der 35 getesteten (Seitenlänge, Seed)-Kombinationen (Seiten 4..10, 5 Seeds) einen Erholungsgrad von exakt
    1.0 - volle Erholung auf die natürliche Bandbreite, kein einziger Ausreißer."""
    rows = ev.recovery_check(sides=C.RECOVERY_SIDES, seeds=C.RECOVERY_SEEDS)
    assert len(rows) == 35
    assert all(r["recovery_cm"] == 1.0 for r in rows)
    assert all(r["recovery_rcm"] == 1.0 for r in rows)


def test_relabeled_bandwidth_is_dramatically_larger_than_natural():
    """README: die zufällige Vertauschung lässt die Bandbreite auf jeder getesteten Instanz klar über den natürlichen Wert steigen (das dramatische Vorher, das CM danach wieder rückgängig macht)."""
    rows = ev.recovery_check(sides=C.RECOVERY_SIDES, seeds=C.RECOVERY_SEEDS)
    assert all(r["bw_relabeled"] > 2 * r["bw_natural"] for r in rows)


def test_profile_comparison_never_finds_rcm_worse_on_the_default_sample():
    """README: über 200 zufällige Instanzen (Seed 35) ist RCMs Profil in 174 Fällen kleiner, in 26 gleich, in KEINEM Fall größer als CMs Profil - ein einseitiger, aber rein gemessener Befund."""
    rows, summary = ev.profile_comparison(seed=C.DEFAULT_SEED, n_instances=C.PROFILE_COMPARISON_N)
    assert summary == {"better": 174, "equal": 26, "worse": 0, "total": 200}
    assert all(r["bw_cm"] == r["bw_rcm"] for r in rows)


def test_star_cm_matches_n_minus_2_and_diverges_from_optimum_from_n_5():
    """README: Cuthill-McKee erreicht auf dem Stern GENAU n-2 (n>=3), das wahre Optimum ist ceil((n-1)/2) - ab n=5 messbar schlechter."""
    for n in (3, 4, 5, 6, 8, 10, 15, 20, 30):
        inst = S.star_instance(n)
        adj = A.adjacency(inst.n, inst.edges)
        cm_bw = A.bandwidth(adj, A.cuthill_mckee(adj))
        assert cm_bw == n - 2
        if n >= 5:
            assert cm_bw > C.star_optimal_bandwidth(n)


def test_scale_free_gap_to_diameter_bound_widens_with_size():
    """README: auf dem skalenfreien Netz bleibt Cuthill-McKee deutlich über der Diameter-Schranke - der relative Abstand wächst mit n (n=20: Faktor ~1.6, n=80: Faktor >2.5)."""
    rows = ev.size_sweep(kind="ba", sizes=(20, 80), seed=C.DEFAULT_SEED)
    small, large = rows[0], rows[1]
    assert small["bw_cm"] / small["lower_bound"] < large["bw_cm"] / large["lower_bound"]
    assert large["bw_cm"] / large["lower_bound"] > 2.0


def test_grid_cm_matches_the_true_optimum_where_it_can_be_checked_exactly():
    """README: beim kleinsten Raster (Seitenlänge 3, n=9, innerhalb der Brute-Force-Grenze) ist Cuthill-McKee bereits exakt optimal - kein Sicherheitsabstand zur Brute-Force-Referenz."""
    inst = S.generate(3, 0.0, "grid", C.DEFAULT_SEED)
    adj = A.adjacency(inst.n, inst.edges)
    assert A.bandwidth(adj, A.cuthill_mckee(adj)) == A.exact_bandwidth_bruteforce(adj)


def test_lower_bound_component_wise_fix_documented_in_readme():
    """README „Design-Entscheidungen": die naive globale Formel (n, globaler Durchmesser) wäre bei getrennten Komponenten KEINE gültige untere Schranke - Regressionstest für das Gegenbeispiel aus
    dem Modul-Docstring von `lower_bound_diameter`."""
    adj = A.adjacency(4, [(0, 1, 1.0), (2, 3, 1.0)])
    assert A.lower_bound_diameter(adj) == 1
