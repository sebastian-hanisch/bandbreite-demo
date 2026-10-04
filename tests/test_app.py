"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanzart, bedingte Regler (Blocked nur bei Raster/grid, m<=m0-Kopplung, „Exakt“ nur bei kleinem n), Permalink-Grenzen,
Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import band_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    state.setdefault("band_step", step)
    state.setdefault("side_slider", 6)
    state.setdefault("nba_slider", 20)
    state.setdefault("nstar_slider", 9)
    state.setdefault("npath_slider", 9)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _click(at, key):
    next(b for b in at.button if b.key == key).click().run()


def test_default_run_shows_the_summary():
    at = _run()
    _ok(at)
    assert {"Knoten", "Kanten"} <= {m.label for m in at.metric}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run(kind_select="city")
    _click(at, f"preset_{name}")
    _ok(at)
    p, ss = C.PRESETS[name], at.session_state
    assert ss["kind_select"] == p["kind"] and ss["band_step"] == p["step"]


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", ["city", "city_relabel", "ba", "star", "path"])
def test_every_step_runs_for_every_kind(step, kind):
    at = _run(step=step, kind_select=kind)
    _ok(at)
    assert at.session_state["band_step"] == step
    assert at.session_state["kind_select"] == kind


def _chart_count(at):
    return len(at.get("plotly_chart"))


def test_step1_shows_the_wavefront_map():
    at = _run(step=1)
    _ok(at)
    assert _chart_count(at) >= 1


def test_step2_shows_three_sparsity_patterns():
    at = _run(step=2, kind_select="star", nstar_slider=8)
    _ok(at)
    assert _chart_count(at) >= 3


def test_step3_shows_profile_comparison_charts():
    at = _run(step=3, kind_select="path", npath_slider=6)
    _ok(at)
    assert _chart_count(at) >= 2


def test_step4_shows_the_optimum_gap_chart():
    at = _run(step=4, kind_select="star", nstar_slider=8)
    _ok(at)
    assert _chart_count(at) >= 1


def test_step4_shows_recovery_chart_only_for_city_kinds():
    at_city = _run(step=4, kind_select="city")
    _ok(at_city)
    assert _chart_count(at_city) >= 2
    at_star = _run(step=4, kind_select="star", nstar_slider=8)
    _ok(at_star)
    assert _chart_count(at_star) == 1


def test_blocked_slider_only_shown_for_grid_nettype():
    at = _run(kind_select="city", nettype_select="grid")
    assert any(w.key == "blocked_widget" for w in at.select_slider)
    at2 = _run(kind_select="city", nettype_select="random")
    assert not any(w.key == "blocked_widget" for w in at2.select_slider)


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    city = _run(kind_select="city")
    assert any(w.key == "side_widget" for w in city.slider) and not any(w.key == "nba_widget" for w in city.slider)
    ba = _run(kind_select="ba")
    assert any(w.key == "nba_widget" for w in ba.slider) and not any(w.key == "side_widget" for w in ba.slider)
    star = _run(kind_select="star")
    assert any(w.key == "nstar_widget" for w in star.slider) and not any(w.key == "npath_widget" for w in star.slider)
    path = _run(kind_select="path")
    assert any(w.key == "npath_widget" for w in path.slider) and not any(w.key == "nstar_widget" for w in path.slider)


def test_ba_m_slider_never_exceeds_m0():
    at = _run(kind_select="ba", m0ba_slider=3, mba_slider=10)
    _ok(at)
    assert at.session_state["mba_slider"] <= 3


def test_exact_algorithm_option_only_offered_for_small_instances():
    exact_label = C.ALGORITHM_LABELS["exact"]
    small = _run(kind_select="city", side_slider=3)      # n=9 <= N_EXACT
    small_radio = next(r for r in small.radio if r.key == "algo_widget")
    assert exact_label in small_radio.options
    big = _run(kind_select="city", side_slider=10)        # n=100 > N_EXACT
    algo_radio = next(r for r in big.radio if r.key == "algo_widget")
    assert exact_label not in algo_radio.options
    assert big.session_state["algo_select"] != "exact"


def test_dice_button_changes_the_seed_and_the_visible_widget():
    at = _run(kind_select="city")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="nope", side="9999", blocked="0.33", nettype="sideways", nba="99999", nstar="99999", npath="99999", algo="up", seed="-4", step="9").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert ss["kind_select"] == "city"
    assert ss["side_slider"] == C.SIDE_MAX
    assert ss["blocked_select"] == C.DEFAULT_BLOCKED
    assert ss["nettype_select"] == "grid"
    assert ss["nba_slider"] == C.N_BA_MAX
    assert ss["nstar_slider"] == C.N_STAR_MAX
    assert ss["npath_slider"] == C.N_PATH_MAX
    assert ss["algo_select"] == "cm"
    assert ss["seed_input"] == 0
    assert ss["band_step"] == 1


def test_permalink_accepts_valid_values_and_writes_them_back():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="ba", nba="30", m0ba="5", mba="2", algo="rcm", seed="7", step="3").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["nba_slider"], ss["m0ba_slider"], ss["algo_select"], ss["seed_input"], ss["band_step"]) == ("ba", 30, 5, "rcm", 7, 3)
    assert at.query_params["seed"] in (["7"], "7") and at.query_params["step"] in (["3"], "3")
    assert ss["nba_widget"] == 30 and ss["seed_widget"] == 7


def test_switching_kind_back_and_forth_keeps_the_stored_values():
    at = _run(kind_select="city", side_slider=9, blocked_select=0.2, seed_input=11)
    at.session_state["kind_select"] = "ba"
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "city"
    at.run()
    _ok(at)
    assert at.session_state["side_widget"] == 9 and at.session_state["blocked_widget"] == 0.2 and at.session_state["seed_widget"] == 11


@pytest.mark.parametrize("kw", [dict(kind_select="city", side_slider=C.SIDE_MIN), dict(kind_select="city", side_slider=C.SIDE_MAX), dict(kind_select="ba", nba_slider=C.N_BA_MIN),
                                 dict(kind_select="star", nstar_slider=C.N_STAR_MIN), dict(kind_select="star", nstar_slider=C.N_STAR_MAX),
                                 dict(kind_select="path", npath_slider=C.N_PATH_MIN), dict(kind_select="path", npath_slider=C.N_PATH_MAX)])
def test_extreme_settings_run_on_step_1_and_4(kw):
    for step in (1, 4):
        _ok(_run(step=step, **kw))


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Cuthill" in m.value and "George" in m.value for e in at.expander for m in e.markdown)
