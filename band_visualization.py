"""Plotly-Figuren: 1 Cuthill-McKee-Wellenfront in Aktion (Karte, Schieberegler über die Besuchsreihenfolge, Knotenfärbung nach Grad - die Gradregel sichtbar gemacht), 2 Nicht-Null-Muster
(Streudiagramm der Kantenendpunkte (π(u),π(v)) - das klassische "Band um die Diagonale"-Bild, ein Panel je Nummerierung), 3 Bandbreite gleich/Profil verschieden (Balken über viele Instanzen,
besser/gleich/schlechter für RCM), 4 Wie nah am Optimum? (Bandbreite über die Größe: natürlich/zufällig/CM/RCM gegen exakt und die Diameter-Schranke). Alle Achsen fest (`fixedrange`), Karten
nutzen `scaleanchor` mit autorange und zwei unsichtbaren Eckpunkten (Hauskonvention), jede Referenzlinie bekommt `annotation=dict(bgcolor="white")` (Pflicht-Checkliste dieser Reihe, s. robustheit-
demo/kaskaden-demo)."""

import plotly.graph_objects as go

TEAL, ORANGE, BLUE, RED, PURPLE, GREY, LIGHT, GREEN = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7", "#e8ebee", "#54a24b"


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _corners_trace(xy):
    pad = 0.4
    return go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False)


# --- 1 · Cuthill-McKee in Aktion --------------------------------------------------------------------------------------------------------------------------


def build_cm_wavefront_map(xy, edges, cm_order, degrees, k):
    """Nach den ersten `k` Positionen der Cuthill-McKee-Reihenfolge: bereits platzierte Knoten TEAL (Größe nach Grad - die Gradregel sichtbar), noch unbesuchte GRAU. Kanten zwischen zwei bereits
    platzierten Knoten dick TEAL hervorgehoben (Baumkanten der Wellenfront), alle anderen dünn grau."""
    placed = set(cm_order[:k])
    n = len(xy)
    fig = go.Figure()
    placed_edges = [(u, v) for u, v in edges if u in placed and v in placed]
    other_edges = [(u, v) for u, v in edges if not (u in placed and v in placed)]
    ox, oy = _lines(xy, other_edges)
    fig.add_trace(go.Scatter(x=ox, y=oy, mode="lines", line=dict(color=GREY, width=1.0), opacity=0.5, hoverinfo="skip", showlegend=False, name="Kanten"))
    if placed_edges:
        px_, py_ = _lines(xy, placed_edges)
        fig.add_trace(go.Scatter(x=px_, y=py_, mode="lines", line=dict(color=TEAL, width=2.4), hoverinfo="skip", showlegend=True, name="Beide Enden platziert"))
    unplaced = [v for v in range(n) if v not in placed]
    if unplaced:
        fig.add_trace(go.Scatter(x=[xy[v][0] for v in unplaced], y=[xy[v][1] for v in unplaced], mode="markers", marker=dict(size=6, color=GREY), name="Noch nicht besucht",
                                  hoverinfo="skip"))
    if placed:
        placed_list = [v for v in cm_order[:k]]
        sizes = [7 + 1.6 * degrees[v] for v in placed_list]
        fig.add_trace(go.Scatter(x=[xy[v][0] for v in placed_list], y=[xy[v][1] for v in placed_list], mode="markers", marker=dict(size=sizes, color=TEAL),
                                  text=[f"Position {cm_order.index(v)}, Grad {degrees[v]}" for v in placed_list], hoverinfo="text", name=f"Platziert ({len(placed_list)})"))
    fig.add_trace(_corners_trace(xy))
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=20, b=10), showlegend=True, legend=dict(orientation="h", y=1.08), plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


# --- 2 · Nicht-Null-Muster ---------------------------------------------------------------------------------------------------------------------------------


def build_sparsity_pattern(edges, perm, n, title, color=BLUE):
    """Streudiagramm der Kantenendpunkte (π(u),π(v)) UND (π(v),π(u)) (symmetrisch, wie eine Adjazenzmatrix) - je enger die Punkte an der Diagonale, desto kleiner Bandbreite/Profil."""
    xs, ys = [], []
    for u, v in edges:
        pu, pv = perm[u], perm[v]
        xs += [pu, pv]
        ys += [pv, pu]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, n - 1], y=[0, n - 1], mode="lines", line=dict(color=GREY, width=1.0, dash="dot"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(size=4, color=color), hoverinfo="skip", showlegend=False))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white", title=dict(text=title, x=0.02, font=dict(size=13)))
    fig.update_xaxes(title="Position", range=[-0.5, n - 0.5], autorange=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(title="Position", range=[n - 0.5, -0.5], autorange=False, fixedrange=True)          # y-Achse gespiegelt (Zeile 0 oben, wie eine Matrix)
    return fig


# --- 3 · Bandbreite gleich, Profil verschieden -------------------------------------------------------------------------------------------------------------


def build_profile_comparison_scatter(rows):
    """Profil(CM) gegen Profil(RCM), ein Punkt je Instanz - unterhalb der Diagonale = RCM besser, oberhalb = CM besser."""
    xs = [r["profile_cm"] for r in rows]
    ys = [r["profile_rcm"] for r in rows]
    top = max(xs + ys) * 1.05 if xs and ys else 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color=GREY, width=1.2, dash="dot"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(size=6, color=TEAL, opacity=0.65), hoverinfo="skip", showlegend=False))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", title=dict(text="Profil(RCM) gegen Profil(CM) - unter der Diagonale = RCM kleiner", x=0.02,
                       font=dict(size=13)))
    fig.update_xaxes(title="Profil (Cuthill-McKee)", range=[0, top], autorange=False, fixedrange=True)
    fig.update_yaxes(title="Profil (Reverse Cuthill-McKee)", range=[0, top], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


def build_profile_comparison_bars(summary):
    labels = ["RCM besser", "gleich", "RCM schlechter"]
    values = [summary["better"], summary["equal"], summary["worse"]]
    colors = [TEAL, GREY, ORANGE]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors, text=values, textposition="outside"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, plot_bgcolor="white",
                       title=dict(text=f"Profilvergleich über {summary['total']} Instanzen", x=0.02, font=dict(size=13)))
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(title="Zahl der Instanzen", range=[0, max(values) * 1.25 if values else 1], autorange=False, fixedrange=True, gridcolor=LIGHT)
    return fig


# --- 4 · Wie nah am Optimum? -------------------------------------------------------------------------------------------------------------------------------


def build_optimum_gap_chart(rows):
    """Bandbreite über die Instanzgröße: natürlich (grau, gestrichelt), zufällig (hellgrau, gepunktet), CM/RCM (teal/orange, praktisch deckungsgleich, s. Punkt 3), Diameter-Schranke (rot,
    gestrichelt) und - soweit vorhanden - das exakte Optimum (schwarze Punkte)."""
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["bw_natural"] for r in rows], mode="lines+markers", line=dict(color=GREY, width=1.6, dash="dash"), marker=dict(size=5), name="Natürlich"))
    fig.add_trace(go.Scatter(x=ns, y=[r["bw_random"] for r in rows], mode="lines+markers", line=dict(color=LIGHT, width=1.6, dash="dot"), marker=dict(size=5, color=GREY), name="Zufällig"))
    fig.add_trace(go.Scatter(x=ns, y=[r["bw_cm"] for r in rows], mode="lines+markers", line=dict(color=TEAL, width=2.6), marker=dict(size=6), name="Cuthill-McKee"))
    fig.add_trace(go.Scatter(x=ns, y=[r["bw_rcm"] for r in rows], mode="lines+markers", line=dict(color=ORANGE, width=1.6, dash="dashdot"), marker=dict(size=5, symbol="x"),
                              name="Reverse Cuthill-McKee"))
    fig.add_trace(go.Scatter(x=ns, y=[r["lower_bound"] for r in rows], mode="lines+markers", line=dict(color=RED, width=1.8, dash="dot"), marker=dict(size=5), name="Diameter-Schranke"))
    exact_ns = [r["n"] for r in rows if r["bw_exact"] is not None]
    exact_ys = [r["bw_exact"] for r in rows if r["bw_exact"] is not None]
    if exact_ns:
        fig.add_trace(go.Scatter(x=exact_ns, y=exact_ys, mode="markers", marker=dict(size=10, color="black", symbol="diamond"), name="Exakt (Brute-Force)"))
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=1.18), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="Bandbreite", fixedrange=True, gridcolor=LIGHT)
    return fig


def build_recovery_chart(rows):
    """Erholungsgrad (CM, RCM) über die Rastergröße - 1.0 = volle Erholung auf die natürliche Bandbreite, 0.0 = keine Erholung."""
    ns = sorted(set(r["n"] for r in rows))
    mean_cm = [sum(r["recovery_cm"] for r in rows if r["n"] == n) / sum(1 for r in rows if r["n"] == n) for n in ns]
    mean_rcm = [sum(r["recovery_rcm"] for r in rows if r["n"] == n) / sum(1 for r in rows if r["n"] == n) for n in ns]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=mean_cm, mode="lines+markers", line=dict(color=TEAL, width=2.4), marker=dict(size=7), name="Cuthill-McKee"))
    fig.add_trace(go.Scatter(x=ns, y=mean_rcm, mode="lines+markers", line=dict(color=ORANGE, width=1.8, dash="dashdot"), marker=dict(size=6, symbol="x"), name="Reverse Cuthill-McKee"))
    fig.add_hline(y=1.0, line=dict(color=GREY, width=1.2, dash="dot"), annotation_text="volle Erholung", annotation_position="top left", annotation=dict(bgcolor="white"))
    fig.add_hline(y=0.0, line=dict(color=GREY, width=1.0, dash="dot"), annotation_text="keine Erholung", annotation_position="bottom left", annotation=dict(bgcolor="white"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=1.15), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="Erholungsgrad", fixedrange=True, gridcolor=LIGHT)
    return fig
