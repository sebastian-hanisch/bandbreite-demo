"""Bandbreite eines Graphen – Cuthill-McKee und Reverse Cuthill-McKee – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Elftes Stück der Graphen-und-Netzwerke-Reihe, ein direktes Kind der Wurzel (BFS und DFS, Stück 1): die Bandbreite B(π) = max über Kanten (u,v) von |π(u)-π(v)| misst, wie weit die Endpunkte jeder
Kante in einer Knotennummerierung π auseinanderliegen - zentral beim Lösen großer dünnbesetzter Gleichungssysteme (FEM, Cholesky-Zerlegung). Cuthill-McKee (1969) ist genau die Breitensuche aus
Stück 1, nur mit einer zusätzlichen Gradregel.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import band_constants as C
import band_evaluation as ev
import band_visualization as viz
from band_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, store_from_widget, sync_query_params, push_to_widget

st.set_page_config(page_title="Bandbreite eines Graphen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analyse(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _recovery_check():
    return ev.recovery_check()


@st.cache_data(show_spinner=False)
def _profile_comparison(seed):
    return ev.profile_comparison(seed=seed)


@st.cache_data(show_spinner=False)
def _size_sweep(kind, sizes, seed, nettype, blocked):
    return ev.size_sweep(kind, sizes, seed, nettype, blocked)


def _german(x):
    return f"{x:,}".replace(",", ".") if isinstance(x, int) else x


def _instance_n(kind, side, n_ba, n_star, n_path):
    if kind in ("city", "city_relabel"):
        return side * side
    if kind == "ba":
        return n_ba
    if kind == "star":
        return n_star
    return n_path


def _sweep_sizes_for(kind):
    return {"city": C.SWEEP_SIDES_CITY, "city_relabel": C.SWEEP_SIDES_CITY, "ba": C.SWEEP_SIZES_BA, "star": C.SWEEP_SIZES_STAR, "path": C.SWEEP_SIZES_PATH}[kind]


st.title("📏 Bandbreite eines Graphen")
st.markdown(
    """
**Elftes Stück der Graphen-und-Netzwerke-Reihe**, ein direktes Kind der Wurzel (BFS und DFS, Stück 1): die **Bandbreite** B(π) = max über Kanten (u,v) von |π(u)-π(v)| misst, wie weit die
Endpunkte jeder Kante in einer Knotennummerierung π auseinanderliegen - zentral beim Lösen großer dünnbesetzter Gleichungssysteme (FEM, Cholesky-Zerlegung): eine schmale Bandbreite hält alle
Nicht-Null-Einträge nah an der Diagonale und macht die Zerlegung viel billiger. Bandbreiten-Minimierung ist NP-vollständig (Papadimitriou 1976) - die Standard-Heuristik **Cuthill-McKee** (1969)
ist genau die Breitensuche aus Stück 1, nur mit einer zusätzlichen Gradregel: **"Cuthill-McKee = BFS mit Gradregel"**. **Reverse Cuthill-McKee** (George 1971) kehrt die fertige Reihenfolge nur
um - ein mathematischer Fakt, kein Messwert: die Bandbreite bleibt dabei EXAKT gleich, nur das Profil (die Summe der Zeilenbreiten bis zur Diagonale) kann sich ändern.
"""
)
st.caption(
    "Kind der Breitensuche (Stück 1 der Graphen-und-Netzwerke-Reihe). Das Betriebsnetz zufällig vertauscht zeigt das dramatischste Vorher-Nachher: dieselben Kanten, aber zufällig umnummeriert - "
    "Cuthill-McKee soll die explodierte Bandbreite wieder auf nahe den ursprünglichen Wert zurückbringen (Schritt 4)."
)

with st.expander("So funktioniert die Messung", expanded=True):
    st.markdown(
        """
1. **Cuthill-McKee** (`cuthill_mckee`): Breitensuche vom pseudo-peripheren Startknoten (George und Liu 1979) aus - beim Abarbeiten eines Knotens werden seine noch unbesuchten Nachbarn nach
   AUFSTEIGENDEM Grad in die Warteschlange gelegt (Gleichstand: kleinster Index). Getrennte Komponenten werden nacheinander bedient.
2. **Reverse Cuthill-McKee** (`reverse_cuthill_mckee`): dieselbe Reihenfolge, nur rückwärts durchnummeriert (Position i → n-1-i). Die Bandbreite bleibt dabei BEWIESEN exakt gleich, nur das
   Profil kann sich ändern.
3. **Exakt** (`exact_bandwidth_bruteforce`, nur für sehr kleine Instanzen, n ≤ 9): probiert ALLE n! Permutationen durch - die Referenz, an der Cuthill-McKee/Reverse Cuthill-McKee gemessen werden.
4. **Untere Schranke** (`lower_bound_diameter`): ⌈(n_i-1)/diam_i⌉ je Zusammenhangskomponente - ein Satz, den KEINE Permutation unterschreiten kann, auch keine zufällige.
5. **Gemessen:** Bandbreite/Profil unter natürlicher/zufälliger/Cuthill-McKee/Reverse-Cuthill-McKee-Nummerierung, der Erholungsgrad nach zufälliger Vertauschung, und wie nah Cuthill-McKee/Reverse
   Cuthill-McKee ans exakte Optimum und an die Diameter-Schranke herankommen.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    rows_of_4 = [preset_names[i:i + 4] for i in range(0, len(preset_names), 4)]
    for row in rows_of_4:
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                     help="Betriebsnetz: Raster in natürlicher Nummerierung (schon fast optimal). Zufällig vertauscht: dieselben Kanten, Knoten zufällig umnummeriert (Bandbreite explodiert). "
                          "Skalenfrei: Barabási-Albert, Hubs erzwingen enge Nachbarschaft. Stern/Pfad: von Hand nachrechenbare Lehrbuchfälle.")

    side, blocked, nettype = C.DEFAULT_SIDE, C.DEFAULT_BLOCKED, "grid"
    n_ba, m_ba, m0_ba = C.DEFAULT_N_BA, C.DEFAULT_M_BA, C.DEFAULT_M0_BA
    n_star, n_path = C.DEFAULT_N_STAR, C.DEFAULT_N_PATH

    if kind in ("city", "city_relabel"):
        side = st.slider("Seitenlänge des Rasters", *bounds("side_slider"), value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                          help="Die Instanz hat Seitenlänge² Kreuzungen.")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], key="nettype_widget", on_change=store_from_widget, args=("nettype_select",),
                            index=list(C.NETTYPES).index(ss["nettype_select"]))
        if nettype == "grid":
            blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %",
                                        key="blocked_widget", on_change=store_from_widget, args=("blocked_select",))
        else:
            blocked = 0.0
    elif kind == "ba":
        n_ba = st.slider("Zahl der Knoten n", *bounds("nba_slider"), value=int(ss["nba_slider"]), key="nba_widget", on_change=store_from_widget, args=("nba_slider",))
        m0_ba = st.slider("Kerngröße m0 (Kreis aus m0 Knoten)", *bounds("m0ba_slider"), value=int(ss["m0ba_slider"]), key="m0ba_widget", on_change=store_from_widget, args=("m0ba_slider",))
        if ss["mba_slider"] > m0_ba:
            ss["mba_slider"] = m0_ba
            push_to_widget("mba_slider")
        if C.M_BA_MIN < m0_ba:
            m_ba = st.slider("Neue Kanten je Knoten m (bevorzugte Anbindung)", C.M_BA_MIN, m0_ba, value=int(ss["mba_slider"]), key="mba_widget", on_change=store_from_widget, args=("mba_slider",))
        else:
            m_ba = C.M_BA_MIN                                        # m0 == M_BA_MIN: keine Wahl möglich (min==max würde den Regler zum Absturz bringen)
    elif kind == "star":
        n_star = st.slider("Knotenzahl n (1 Mittelpunkt + n-1 Blätter)", *bounds("nstar_slider"), value=int(ss["nstar_slider"]), key="nstar_widget", on_change=store_from_widget,
                            args=("nstar_slider",), help="Optimale Bandbreite: ⌈(n-1)/2⌉ - von Hand nachrechenbar.")
    else:
        n_path = st.slider("Knotenzahl n", *bounds("npath_slider"), value=int(ss["npath_slider"]), key="npath_widget", on_change=store_from_widget, args=("npath_slider",),
                            help="Die optimale Bandbreite des Pfads ist 1 (natürlich, Cuthill-McKee, Reverse Cuthill-McKee); nur die zufällige Nummerierung ist schlechter.")

    st.markdown("---")
    n_current = _instance_n(kind, side, n_ba, n_star, n_path)
    algo_options = list(C.ALGORITHMS) if n_current <= C.N_EXACT else [a for a in C.ALGORITHMS if a != "exact"]
    if ss["algo_select"] not in algo_options:
        ss["algo_select"] = "cm"
        push_to_widget("algo_select")
    algo = st.radio("Sichtbare Nummerierung (Kopfzeile unten)", options=algo_options, format_func=lambda v: C.ALGORITHM_LABELS[v], key="algo_widget", on_change=store_from_widget,
                     args=("algo_select",), index=algo_options.index(ss["algo_select"]),
                     help="Bandbreite/Profil dieser Nummerierung erscheinen in der Kopfzeile. 'Exakt' ist nur für sehr kleine Instanzen (n≤9) berechenbar.")

    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

step = st.select_slider("Schritt", options=list(C.STEPS), key="band_step", format_func=lambda s: C.STEPS[s])

sync_query_params({"kind_select": kind, "side_slider": int(side) if kind in ("city", "city_relabel") else int(ss["side_slider"]),
                    "blocked_select": float(blocked) if kind in ("city", "city_relabel") and nettype == "grid" else float(ss["blocked_select"]),
                    "nettype_select": nettype if kind in ("city", "city_relabel") else ss["nettype_select"],
                    "nba_slider": int(n_ba) if kind == "ba" else int(ss["nba_slider"]), "m0ba_slider": int(m0_ba) if kind == "ba" else int(ss["m0ba_slider"]),
                    "mba_slider": int(m_ba) if kind == "ba" else int(ss["mba_slider"]), "nstar_slider": int(n_star) if kind == "star" else int(ss["nstar_slider"]),
                    "npath_slider": int(n_path) if kind == "path" else int(ss["npath_slider"]), "algo_select": algo, "seed_input": int(seed), "band_step": int(step)})

base_settings = dict(kind=kind, side=int(side), blocked=float(blocked), nettype=nettype, n_ba=int(n_ba), m_ba=int(m_ba), m0_ba=int(m0_ba), n_star=int(n_star), n_path=int(n_path), seed=int(seed))
settings = ev.Settings(**base_settings)

with st.spinner("Werte die Instanz aus..."):
    inst, adj, a = _analyse(settings)

perms = {"natural": a.perm_natural, "random": a.perm_random, "cm": a.perm_cm, "rcm": a.perm_rcm}
bws = {"natural": a.bw_natural, "random": a.bw_random, "cm": a.bw_cm, "rcm": a.bw_rcm, "exact": a.bw_exact}
profiles = {"natural": a.profile_natural, "random": a.profile_random, "cm": a.profile_cm, "rcm": a.profile_rcm}

st.markdown("## 🎯 Die Instanz")
edge_pairs = [(u, v) for u, v, _w in inst.edges]
profile_text = f"{profiles[algo]}" if algo in profiles else "n/a (nur Bandbreite)"
st.markdown(f"**{_german(inst.n)} Knoten, {_german(inst.m)} Kanten**. Ausgewählte Nummerierung **{C.ALGORITHM_LABELS[algo]}**: Bandbreite **{bws[algo]}**, Profil **{profile_text}**. "
            f"Diameter-Schranke: **{a.lower_bound}**. Cuthill-McKee-Bandbreite: **{a.bw_cm}** = Reverse-Cuthill-McKee-Bandbreite: **{a.bw_rcm}** (Punkt 3, immer exakt gleich).")

if step == 1:
    n_steps = inst.n
    k = st.slider("Position in der Cuthill-McKee-Reihenfolge", 0, n_steps, value=n_steps, key=f"k_slider_{kind}_{seed}_{side}_{n_ba}_{n_star}_{n_path}_{m_ba}_{m0_ba}",
                   help="0 = noch kein Knoten platziert, Maximum = vollständige Cuthill-McKee-Nummerierung.")
    st.plotly_chart(viz.build_cm_wavefront_map(inst.xy, edge_pairs, a.cm_order, a.degrees, k), width="stretch",
                     key=f"s1_map_{kind}_{seed}_{side}_{nettype}_{blocked}_{n_ba}_{m_ba}_{m0_ba}_{n_star}_{n_path}_{k}")
    st.caption(f"Nach {k} von {n_steps} Positionen der Cuthill-McKee-Reihenfolge (Gradregel: bei jedem abgearbeiteten Knoten werden seine noch unbesuchten Nachbarn nach aufsteigendem Grad in die "
               f"Warteschlange gelegt). Größe der platzierten Knoten ∝ Grad.")
elif step == 2:
    st.markdown("Kantenendpunkte (π(u), π(v)) je Nummerierung - je enger die Punkte an der Diagonale, desto kleiner Bandbreite/Profil (das klassische „Band um die Diagonale“-Bild).")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(viz.build_sparsity_pattern(edge_pairs, a.perm_natural, inst.n, f"Natürlich (Bandbreite {a.bw_natural})", viz.GREY), width="stretch",
                         key=f"s2_natural_{kind}_{seed}_{side}_{nettype}_{blocked}_{n_ba}_{m_ba}_{m0_ba}_{n_star}_{n_path}")
    with c2:
        st.plotly_chart(viz.build_sparsity_pattern(edge_pairs, a.perm_cm, inst.n, f"Cuthill-McKee (Bandbreite {a.bw_cm})", viz.TEAL), width="stretch",
                         key=f"s2_cm_{kind}_{seed}_{side}_{nettype}_{blocked}_{n_ba}_{m_ba}_{m0_ba}_{n_star}_{n_path}")
    with c3:
        st.plotly_chart(viz.build_sparsity_pattern(edge_pairs, a.perm_rcm, inst.n, f"Reverse Cuthill-McKee (Bandbreite {a.bw_rcm})", viz.ORANGE), width="stretch",
                         key=f"s2_rcm_{kind}_{seed}_{side}_{nettype}_{blocked}_{n_ba}_{m_ba}_{m0_ba}_{n_star}_{n_path}")
    st.caption(f"Bandbreite Cuthill-McKee ({a.bw_cm}) und Reverse Cuthill-McKee ({a.bw_rcm}) sind hier - wie auf JEDER Instanz - exakt gleich (mathematischer Fakt, Punkt 3). Profil: "
               f"{a.profile_cm} (CM) gegen {a.profile_rcm} (RCM).")
elif step == 3:
    with st.spinner(f"Vergleiche Profil CM/RCM über {C.PROFILE_COMPARISON_N} zufällige Instanzen..."):
        rows, summary = _profile_comparison(seed)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(viz.build_profile_comparison_bars(summary), width="stretch", key=f"s3_bars_{seed}")
    with c2:
        st.plotly_chart(viz.build_profile_comparison_scatter(rows), width="stretch", key=f"s3_scatter_{seed}")
    n_equal_bw = sum(1 for r in rows if r["bw_cm"] == r["bw_rcm"])
    st.caption(f"Bandbreite(CM) == Bandbreite(RCM) in ALLEN {summary['total']} Instanzen ({n_equal_bw} von {summary['total']}, Punkt 3, Satz). Profil: RCM in {summary['better']} von "
               f"{summary['total']} Instanzen kleiner (besser), in {summary['equal']} gleich, in {summary['worse']} größer (schlechter) - GEMESSEN, nicht als „RCM ist immer besser“ behauptet.")
else:
    sweep_sizes = _sweep_sizes_for(kind)
    with st.spinner("Rechne die Größen-Messreihe (kann bei den größten Instanzen kurz dauern)..."):
        rows = _size_sweep(kind, sweep_sizes, seed, nettype, blocked)
    st.plotly_chart(viz.build_optimum_gap_chart(rows), width="stretch", key=f"s4_gap_{kind}_{seed}_{nettype}_{blocked}")
    exact_rows = [r for r in rows if r["bw_exact"] is not None]
    if exact_rows:
        gaps = ", ".join(f"n={r['n']}: CM/RCM {r['bw_cm']} gegen exakt {r['bw_exact']}" for r in exact_rows)
        st.caption(f"Exakter Vergleich (n ≤ {C.N_EXACT}): {gaps}.")
    else:
        st.caption(f"Keine der Stützstellen dieser Instanzart hat n ≤ {C.N_EXACT} - hier nur der Vergleich gegen die Diameter-Schranke.")
    if kind in ("city", "city_relabel"):
        st.markdown("---")
        with st.spinner("Rechne den Erholungsgrad nach zufälliger Vertauschung..."):
            recovery_rows = _recovery_check()
        st.plotly_chart(viz.build_recovery_chart(recovery_rows), width="stretch", key=f"s4_recovery_{seed}")
        mean_recovery_cm = sum(r["recovery_cm"] for r in recovery_rows) / len(recovery_rows)
        st.caption(f"Mittlerer Erholungsgrad (Cuthill-McKee) über {len(recovery_rows)} zufällig vertauschte Rasterinstanzen: {mean_recovery_cm:.2f} (1.0 = volle Erholung auf die natürliche "
                   f"Bandbreite).")

st.markdown("---")

st.markdown("## 🎯 Was Cuthill-McKee bringt")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Knoten", _german(inst.n))
r2.metric("Kanten", _german(inst.m))
r3.metric("Bandbreite natürlich → Cuthill-McKee", f"{a.bw_natural} → {a.bw_cm}")
r4.metric("Diameter-Schranke", _german(a.lower_bound))

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Cuthill-McKee findet die optimale Bandbreite** | Falsch im Allgemeinen (Bandbreitenminimierung ist NP-vollständig, Papadimitriou 1976) - auf dem Stern-Lehrbuch GEMESSEN sogar deutlich daneben (Bandbreite n-2 statt des Optimums ⌈(n-1)/2⌉, s. README „Befunde“). | - |
| **Reverse Cuthill-McKee hat immer ein kleineres Profil als Cuthill-McKee** | Nicht garantiert - nur GEMESSEN meist gleich oder kleiner, nie als Satz behauptet (Punkt 4, Schritt 3). | - |
| **Die Diameter-Schranke ist scharf (wird erreicht)** | Nein - sie ist nur eine UNTERE Schranke; der tatsächliche Abstand zum exakten Optimum wächst auf manchen Instanzen (z. B. skalenfrei) mit der Größe (s. Schritt 4). | - |
| **Zufällige Vertauschung macht jede Instanz gleich schwer für Cuthill-McKee** | Nein - auf dem Betriebsnetz-Raster wird die natürliche Bandbreite GEMESSEN fast immer vollständig zurückgewonnen (s. Schritt 4), auf dem skalenfreien Netz nur zu einem Bruchteil. | - |
| **Synthetische Instanzen** | Betriebsnetz, skalenfreies Netz, Stern und Pfad sind erzeugt, keine echten FEM-Gleichungssysteme. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Bandbreite.** $B(\pi) = \max_{(u,v)\in E} |\pi(u)-\pi(v)|$, wobei $\pi:V\to\{0,\dots,n-1\}$ eine bijektive Knotennummerierung ist.

**Profil (envelope).** $P(\pi) = \sum_{v} \big(\pi(v) - \min\{\pi(u) : u\sim v,\ \pi(u)\le \pi(v)\}\big)$ (0, wenn kein solcher Nachbar existiert) - die Summe der "Zeilenbreiten" bis zur
Diagonale, wie sie bei einer Cholesky-Zerlegung tatsächlich mit Nicht-Null-Einträgen gefüllt werden müssten.

**Cuthill-McKee** (Cuthill und McKee 1969, ACM Proc. 24th Nat. Conf., 157-172). Breitensuche vom pseudo-peripheren Startknoten aus; beim Abarbeiten eines Knotens werden seine noch unbesuchten
Nachbarn nach AUFSTEIGENDEM Grad in die Warteschlange gelegt.

**Reverse Cuthill-McKee** (George 1971, Stanford-Dissertation). $\pi_{RCM}(v) = n-1-\pi_{CM}(v)$ - Beweis der Bandbreiten-Invarianz: $|\pi_{RCM}(u)-\pi_{RCM}(v)| = |(n-1-\pi_{CM}(u))-(n-1-\pi_{CM}(v))| = |\pi_{CM}(u)-\pi_{CM}(v)|$.

**Pseudo-periphere Startknotenwahl** (George und Liu 1979, ACM TOMS 5(3), 284-295). BFS von einem Startknoten, unter den am weitesten entfernten Knoten den mit dem kleinsten Grad wählen, erneut
BFS von dort; wiederholen, bis die Exzentrizität nicht mehr wächst.

**Untere Schranke.** Für eine Zusammenhangskomponente mit $n_i$ Knoten und Durchmesser $\mathrm{diam}_i$ gilt $B \ge \lceil (n_i-1)/\mathrm{diam}_i \rceil$: die $n_i$ Positionen dieser Komponente
sind $n_i$ verschiedene ganze Zahlen, ihre Spannweite ist also mindestens $n_i-1$ (Schubfachprinzip), und die beiden Knoten, die diese Spannweite realisieren, liegen höchstens $\mathrm{diam}_i$
Kanten auseinander.

**Bandbreitenminimierung ist NP-vollständig** (Papadimitriou 1976, Computing 16(3), 263-270).

**Literatur.** Cuthill, E., & McKee, J. (1969). *Reducing the bandwidth of sparse symmetric matrices.* Proceedings of the 24th National Conference ACM, 157–172. George, A. (1971). *Computer
implementation of the finite element method* (Doktorarbeit, Stanford University). George, A., & Liu, J. W. H. (1979). *An implementation of a pseudoperipheral node finder.* ACM Transactions on
Mathematical Software 5(3), 284–295. Papadimitriou, C. H. (1976). *The NP-completeness of the bandwidth minimization problem.* Computing 16(3), 263–270.

Implementiert in `band_algorithm.py` (Bandbreite/Profil, Cuthill-McKee/Reverse Cuthill-McKee, pseudo-periphere Startwahl, Brute-Force, Diameter-Schranke), `band_scenario.py` (Instanzen),
`band_evaluation.py` (Analyse, Erholungsgrad, Profilvergleich, Größen-Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html)."
)
