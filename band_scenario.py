"""Fünf Instanzen dieser Demo. **Betriebsnetz** (Raster/Zufallsgraph, `generate()` wortgleich aus `kas_scenario.py`/`sk_scenario.py` übernommen): in seiner NATÜRLICHEN Nummerierung hat das
Raster schon eine fast optimale Bandbreite (≈ Seitenlänge) - das eigentliche Vehikel ist **Betriebsnetz zufällig vertauscht** (`random_relabel`, NEU): dieselben Kanten, die Knoten aber zufällig
umnummeriert - die Bandbreite explodiert, und Cuthill-McKee/Reverse-Cuthill-McKee sollen sie wieder auf nahe den ursprünglichen Wert bringen (ein direktes, dramatisches Vorher-Nachher).
**Skalenfreies Netz** (Barabási-Albert, wortgleich aus `kas_scenario.py`/`sk_scenario.py` übernommen): Hubs erzwingen enge Nachbarschaft zu vielen Knoten gleichzeitig, ein härterer Testfall.
**Stern-** und **Pfad-Lehrbuch** (NEU, `star_instance(n)`/`path_instance(n)`): der Stern hat eine von Hand nachrechenbare optimale Bandbreite (der Mittelknoten muss "in der Mitte" der
Nummerierung stehen, s. `band_constants.star_optimal_bandwidth` für die genaue Formel), der Pfad hat immer Bandbreite 1 - beide unabhängig vom Algorithmus nachprüfbar.

Knoten sind von 0 bis n-1 durchnummeriert; Kanten (u, v, w) mit u < v, sortiert; w = Länge (nur zur Anzeige, für Bandbreite/Profil ungewichtet)."""

import math
import random
from dataclasses import dataclass

import numpy as np

import band_constants as C


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    edges: tuple                   # ((u, v, w), ...) sortiert
    kind: str = "city"             # "city" | "city_relabel" | "ba" | "star" | "path"
    nettype: str = "grid"          # nur kind in {"city", "city_relabel"}: "grid" | "random"
    side: int = 0                  # nur kind in {"city", "city_relabel"}
    blocked: float = 0.0           # nur kind in {"city", "city_relabel"}
    seed: int = 0
    blocked_edges: tuple = ()      # gesperrte Straßen (u, v), nur zur Anzeige (nur beim Raster)
    m_ba: int = 0                  # nur kind == "ba"
    m0_ba: int = 0                 # nur kind == "ba"
    n_star: int = 0                # nur kind == "star"
    n_path: int = 0                # nur kind == "path"

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.edges)


def make_rng(seed, salt):
    """Zufallsquelle mit fester, plattformunabhängiger Zahlenfolge (Python-`random`, nicht numpy: die Instanzen und alle daraus gezählten Zahlen ändern sich nie mit einer Bibliotheksversion)."""
    return random.Random(int(seed) * 1_000_003 + int(salt))


# --- Betriebsnetz (wortgleiche Kopie aus kas_scenario.py/sk_scenario.py) --------------------------------------------------------------------------------


def grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def block(pairs, share, rng):
    """Sperrt genau `round(share * Zahl der Straßen)` Straßen, zufällig und OHNE Rücksicht auf den Zusammenhang. Gibt (verbleibende, gesperrte) zurück."""
    target = int(round(share * len(pairs)))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    removed = set(order[:target])
    kept = [pairs[j] for j in range(len(pairs)) if j not in removed]
    return kept, [pairs[j] for j in sorted(removed)]


def random_pairs(n, m, rng):
    """`m` verschiedene Kanten zwischen zufälligen verschiedenen Knotenpaaren (einfacher Graph)."""
    max_m = n * (n - 1) // 2
    m = min(m, max_m)
    chosen = set()
    while len(chosen) < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        chosen.add((min(u, v), max(u, v)))
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, blocked=C.DEFAULT_BLOCKED, nettype="grid", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if nettype not in C.NETTYPES:
        raise ValueError(f"unbekannter Netztyp {nettype}")
    side = int(side)
    if side < 2:
        raise ValueError("Seitenlänge mindestens 2")
    n = side * side
    rng = make_rng(seed, 4711)
    xy = np.array([[c * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING, r * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    kept, removed = block(grid_edges(side), float(blocked), rng)
    if nettype == "random":
        rng2 = make_rng(seed, 9173)
        kept = random_pairs(n, len(kept), rng2)
        removed = []
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in kept)
    return Instance(xy, edges, "city", nettype, side, float(blocked), int(seed), tuple(removed))


# --- Betriebsnetz zufällig vertauscht (NEU) -------------------------------------------------------------------------------------------------------------


def random_relabel(inst, seed):
    """Derselbe Graph (dieselben Kanten als ungerichtetes Muster), Knoten zufällig umnummeriert: sigma[alte ID] = neue ID, eine zufällige Permutation. Die (x,y)-Lage folgt der NEUEN Nummerierung
    (dieselbe physische Position, nur der Index ändert sich) - so bleibt die Karte anschaulich lesbar, während die BANDBREITE unter dieser neuen, zufälligen Nummerierung explodiert (dramatisches
    Vorher-Nachher für Cuthill-McKee). Die optimale Bandbreite selbst ist ein Graph-Invariant und ändert sich durch die Umnummerierung NICHT - nur die aktuell vorliegende (natürliche) Nummerierung
    wird schlecht."""
    n = inst.n
    rng = make_rng(seed, 3407)
    sigma = list(range(n))
    rng.shuffle(sigma)
    new_xy = np.zeros_like(inst.xy)
    for old in range(n):
        new_xy[sigma[old]] = inst.xy[old]
    new_edges = []
    for u, v, w in inst.edges:
        a, b = sigma[u], sigma[v]
        new_edges.append((min(a, b), max(a, b), w))
    new_edges.sort()
    return Instance(new_xy, tuple(new_edges), "city_relabel", inst.nettype, inst.side, inst.blocked, int(seed), ())


# --- Skalenfreies Netz (Barabási und Albert 1999, wortgleiche Kopie aus kas_scenario.py/sk_scenario.py) ------------------------------------------------


def barabasi_albert_instance(n, m, m0, seed):
    """Kern: ein Kreis über m0 Knoten (m0 Kanten, jeder Kernknoten Grad 2, von Anfang an zusammenhängend). Jeder weitere Knoten t=m0..n-1 hängt sich mit m Kanten an m verschiedene bereits vorhandene
    Knoten an, gezogen proportional zum aktuellen Grad (bevorzugte Anbindung): eine Liste der Kantenenden (jeder Knoten so oft darin, wie er schon Kanten hat) macht die gewichtete Ziehung effizient -
    ein zufällig gezogenes Element der Liste trifft jeden Knoten mit Wahrscheinlichkeit proportional zu seinem Grad. Exakte Kantenzahl m0+(n-m0)*m."""
    n = int(n)
    m = int(m)
    m0 = int(m0)
    if m0 < 3:
        raise ValueError("m0 muss mindestens 3 sein (Kern ist ein Kreis über m0 Knoten, ein Kreis über 2 Knoten wäre eine Mehrfachkante)")
    if not (1 <= m <= m0):
        raise ValueError(f"m muss zwischen 1 und m0={m0} liegen")
    if n < m0:
        raise ValueError("n muss mindestens m0 sein")
    rng = make_rng(seed, 8117)
    edges = []
    stubs = []
    for i in range(m0):
        j = (i + 1) % m0
        u, v = min(i, j), max(i, j)
        edges.append((u, v))
        stubs.append(u)
        stubs.append(v)
    for new in range(m0, n):
        chosen = set()
        while len(chosen) < m:
            cand = stubs[rng.randrange(len(stubs))]
            if cand != new and cand not in chosen:
                chosen.add(cand)
        for t in sorted(chosen):
            edges.append((t, new))
            stubs.append(t)
            stubs.append(new)
    edges.sort()
    xy = np.zeros((n, 2), dtype=float)
    for i in range(m0):
        ang = 2 * math.pi * i / m0
        xy[i] = [1.6 * math.cos(ang), 1.6 * math.sin(ang)]
    layout_rng = make_rng(seed, 2477)
    for i in range(m0, n):
        ang = 2 * math.pi * layout_rng.random()
        rad = 0.3 + 1.3 * layout_rng.random()
        xy[i] = [rad * math.cos(ang), rad * math.sin(ang)]
    out_edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in edges)
    return Instance(xy, out_edges, "ba", "grid", 0, 0.0, int(seed), (), int(m), int(m0))


# --- Stern-Lehrbuch (NEU) --------------------------------------------------------------------------------------------------------------------------------


def star_instance(n):
    """Stern K_{1,n-1}: Knoten 0 = Mittelpunkt, Knoten 1..n-1 = Blätter, jedes Blatt nur mit dem Mittelpunkt verbunden. Optimale Bandbreite von Hand nachrechenbar (s. `band_constants.
    star_optimal_bandwidth`): der Mittelpunkt muss so nummeriert werden, dass er möglichst "mittig" zwischen den Blattpositionen liegt."""
    n = int(n)
    if n < 3:
        raise ValueError("Stern braucht mindestens 3 Knoten (1 Mittelpunkt + 2 Blätter)")
    xy = np.zeros((n, 2), dtype=float)
    for i in range(1, n):
        ang = 2 * math.pi * (i - 1) / (n - 1)
        xy[i] = [math.cos(ang), math.sin(ang)]
    edges = tuple((0, i, float(np.hypot(*(xy[0] - xy[i])))) for i in range(1, n))
    return Instance(xy, edges, "star", "grid", 0, 0.0, 0, (), 0, 0, int(n), 0)


# --- Pfad-Lehrbuch (NEU) ----------------------------------------------------------------------------------------------------------------------------------


def path_instance(n):
    """Pfad 0-1-2-...-(n-1). Bandbreite ist bei JEDER Permutation, die die natürliche Reihenfolge (oder ihre Umkehrung) verwendet, exakt 1 - der denkbar einfachste Fall."""
    n = int(n)
    if n < 2:
        raise ValueError("Pfad braucht mindestens 2 Knoten")
    xy = np.array([[float(i), 0.0] for i in range(n)], dtype=float)
    edges = tuple((i, i + 1, 1.0) for i in range(n - 1))
    return Instance(xy, edges, "path", "grid", 0, 0.0, 0, (), 0, 0, 0, int(n))
