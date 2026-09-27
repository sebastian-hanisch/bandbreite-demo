"""Bandbreite und Profil einer Knotennummerierung, Cuthill-McKee (= BFS mit Gradregel) und Reverse Cuthill-McKee, pseudo-periphere Startknotenwahl (George und Liu 1979), Brute-Force-Referenz und
untere Schranke über den Durchmesser.

**Bandbreite** B(π) = max über Kanten (u,v) von |π(u)-π(v)|, wobei π(v) die Position (0..n-1) von Knoten v in einer Nummerierung ist. **Profil** (envelope) P(π) = Σ_v (π(v) - min{π(u) : u~v,
π(u) ≤ π(v)}) - die Summe der "Zeilenbreiten" bis zur Diagonale, wie sie bei einer Cholesky-Zerlegung tatsächlich mit Nicht-Null-Einträgen gefüllt werden müssten (0, wenn v keinen Nachbarn mit
kleinerer oder gleicher Position hat).

**Cuthill-McKee** (1969, ACM Proc. 24th Nat. Conf., 157-172): identisch zur Breitensuche aus Stück 1, aber beim Abarbeiten eines Knotens werden seine noch unbesuchten Nachbarn nach AUFSTEIGENDEM
Grad in die Warteschlange gelegt (Gleichstand: kleinster Index) - daher "BFS mit Gradregel". **Reverse Cuthill-McKee** (George 1971, Stanford-Dissertation) kehrt die fertige Positionsfolge nur um:
das ist ein mathematischer FAKT, kein Messwert - die Bandbreite bleibt dabei exakt gleich (|π(u)-π(v)| = |(n-1-π(u))-(n-1-π(v))|), nur das Profil kann sich ändern.

**Elementarschritte** (das Aufwandsmaß dieser Reihe, keine Laufzeit): wie in Stück 1 zählt jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante 1 - hier vor allem in
`cuthill_mckee_trace` für die Schritt-für-Schritt-Wiedergabe in der App verwendet."""

import itertools
import math
import random
from collections import deque


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste (Liste von Listen) aus Kanten (u, v, ...); `order` = "fixed" (aufsteigend) oder "shuffled" (je Knoten gemischt, Seed fest) - wortgleiche Kopie aus `bfd_algorithm.py`/
    `cen_algorithm.py`."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def bfs_distances(adj, s):
    """Abstand von s zu jedem erreichbaren Knoten (-1 = unerreichbar). Gibt (dist, Schritte) zurück - wortgleiche Kopie aus `cen_algorithm.py` (Erbe aus Stück 1: BFS und DFS)."""
    n = len(adj)
    dist = [-1] * n
    dist[s] = 0
    queue = deque([s])
    steps = 1
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            steps += 1
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
                steps += 1
    return dist, steps


def degree_centrality(adj):
    """Grad je Knoten (Zahl der Nachbarn) - wortgleiche Kopie aus `cen_algorithm.py`; hier die Grundlage der Cuthill-McKee-Gradregel und der Knotenfärbung in der Wellenfront-Visualisierung."""
    return [len(nbrs) for nbrs in adj]


# --- Bandbreite und Profil --------------------------------------------------------------------------------------------------------------------------------


def bandwidth(adj, perm):
    """max |perm[u]-perm[v]| über alle Kanten (jede Kante wird von beiden Enden aus gesehen - das ändert nur die Zahl der Vergleiche, nicht das Maximum)."""
    b = 0
    for u in range(len(adj)):
        pu = perm[u]
        for v in adj[u]:
            d = pu - perm[v]
            if d < 0:
                d = -d
            if d > b:
                b = d
    return b


def profile(adj, perm):
    """Σ_v (perm[v] - min{perm[u] : u~v, perm[u] ≤ perm[v]}) je Knoten (0, wenn kein solcher Nachbar existiert - z. B. der Knoten an Position 0, oder ein isolierter Knoten)."""
    total = 0
    for v in range(len(adj)):
        pv = perm[v]
        best = None
        for u in adj[v]:
            pu = perm[u]
            if pu <= pv and (best is None or pu < best):
                best = pu
        if best is not None:
            total += pv - best
    return total


def random_permutation(n, seed):
    """Eine zufällige Permutation von 0..n-1 (Python-`random`, Hauskonvention `random.Random(seed*1_000_003+salt)`)."""
    rng = random.Random(int(seed) * 1_000_003 + 6421)
    perm = list(range(n))
    rng.shuffle(perm)
    return perm


# --- Untere Schranke über den Durchmesser (Satz) ----------------------------------------------------------------------------------------------------------


def lower_bound_diameter(adj):
    """⌈(n_i-1)/diam_i⌉, maximiert über alle Zusammenhangskomponenten i (Größe n_i, Durchmesser diam_i) - NICHT einfach über den globalen Durchmesser des ganzen (möglicherweise unzusammenhängenden)
    Graphen: innerhalb einer Komponente mit n_i Knoten müssen deren Positionen n_i VERSCHIEDENE Werte aus {0,...,n-1} sein, die also eine Spannweite von mindestens n_i-1 haben (Schubfachprinzip) -
    und die beiden Knoten, die diese Spannweite realisieren, liegen höchstens diam_i Kanten auseinander, also B*diam_i ≥ n_i-1. Der einfachere, komponentenübergreifende Ansatz (globales n und
    globaler Durchmesser) wäre bei unzusammenhängenden Graphen KEINE gültige untere Schranke mehr (Gegenbeispiel: zwei getrennte Kanten, global "Durchmesser" 1 und n=4 ergäben faelschlich
    ⌈3/1⌉=3, obwohl Bandbreite 1 erreichbar ist) - deshalb die Maximierung je Komponente, s. README "Design-Entscheidungen"."""
    n = len(adj)
    if n <= 1:
        return 0
    assigned = [False] * n
    best = 0
    for seed_node in range(n):
        if assigned[seed_node]:
            continue
        seed_dist, _ = bfs_distances(adj, seed_node)
        comp = [v for v in range(n) if seed_dist[v] >= 0]
        for v in comp:
            assigned[v] = True
        if len(comp) <= 1:
            continue
        # Durchmesser der Komponente = groesste Exzentrizitaet UNTER IHREN EIGENEN Knoten (nicht nur die Exzentrizitaet von seed_node, die selbst nur eine UNTERE Schranke des Durchmessers waere
        # und die Schranke unten faelschlich zu GROSS machen wuerde, s. Regressionstest).
        diam_i = 0
        for v in comp:
            dist_v, _ = bfs_distances(adj, v)
            ecc_v = max(dist_v[u] for u in comp)
            if ecc_v > diam_i:
                diam_i = ecc_v
        if diam_i > 0:
            bound_i = math.ceil((len(comp) - 1) / diam_i)
            if bound_i > best:
                best = bound_i
    return best


# --- Pseudo-periphere Startknotenwahl (George und Liu 1979) -----------------------------------------------------------------------------------------------


def pseudo_peripheral(adj, candidates=None):
    """George und Liu (1979, ACM TOMS 5(3), 284-295): BFS von einem Startknoten, unter den am weitesten entfernten Knoten (letzte Ebene) den mit dem kleinsten Grad wählen (Gleichstand: kleinster
    Index), erneut BFS von dort; wiederholen, bis die Exzentrizität nicht mehr wächst. `candidates`, falls gegeben, beschränkt die Wahl auf eine einzelne Zusammenhangskomponente (die
    BFS-Abstände selbst laufen über den ganzen Graphen, bleiben aber innerhalb der Komponente, da keine Kante sie verlässt) - so kann `cuthill_mckee` jede Komponente einzeln bedienen."""
    nodes = list(candidates) if candidates is not None else list(range(len(adj)))
    if len(nodes) == 1:
        return nodes[0]
    start = min(nodes, key=lambda v: (len(adj[v]), v))
    dist, _ = bfs_distances(adj, start)
    ecc = max(dist[v] for v in nodes)
    current = start
    while True:
        last_level = [v for v in nodes if dist[v] == ecc]
        candidate = min(last_level, key=lambda v: (len(adj[v]), v))
        if candidate == current:
            return current
        cdist, _ = bfs_distances(adj, candidate)
        cecc = max(cdist[v] for v in nodes)
        if cecc <= ecc:
            return candidate
        current = candidate
        dist = cdist
        ecc = cecc


# --- Cuthill-McKee und Reverse Cuthill-McKee --------------------------------------------------------------------------------------------------------------


def _component_of(adj, seed_node):
    """Alle über Kanten erreichbaren Knoten ab `seed_node` (die ganze Zusammenhangskomponente, in Entdeckungsreihenfolge)."""
    seen = {seed_node}
    order = [seed_node]
    dq = deque([seed_node])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                order.append(v)
                dq.append(v)
    return order


def cuthill_mckee_order(adj, start=None):
    """Liefert die Besuchsreihenfolge (order[i] = an Position i platzierter Knoten) - die eigentliche BFS-mit-Gradregel-Konstruktion, auch für die Schritt-für-Schritt-Wiedergabe der App nutzbar.
    Getrennte Komponenten werden nacheinander abgearbeitet (kleinster noch unbesuchter Index bestimmt die nächste Komponente); `start` gilt nur für die ERSTE Komponente - jede weitere startet
    über `pseudo_peripheral`, beschränkt auf ihre eigenen Knoten."""
    n = len(adj)
    visited = [False] * n
    order = []
    first = True
    while len(order) < n:
        seed_node = next(v for v in range(n) if not visited[v])
        comp = _component_of(adj, seed_node)
        if first and start is not None:
            if start not in comp:
                raise ValueError("start liegt nicht in der ersten (kleinstindizierten) Komponente")
            s = start
        else:
            s = pseudo_peripheral(adj, comp)
        first = False
        visited[s] = True
        order.append(s)
        dq = deque([s])
        while dq:
            u = dq.popleft()
            nbrs = sorted((v for v in adj[u] if not visited[v]), key=lambda v: (len(adj[v]), v))
            for v in nbrs:
                visited[v] = True
                order.append(v)
                dq.append(v)
    return order


def cuthill_mckee(adj, start=None):
    """Cuthill-McKee (1969): Breitensuche, aber die noch unbesuchten Nachbarn eines abgearbeiteten Knotens werden nach AUFSTEIGENDEM Grad in die Warteschlange gelegt (Gleichstand: kleinster
    Index) - identisch zur BFS aus Stück 1, nur mit dieser einen zusätzlichen Regel. `start=None` wählt den Startknoten über `pseudo_peripheral`. Gibt eine Permutation `perm` zurück mit
    `perm[knoten] = position`."""
    order = cuthill_mckee_order(adj, start)
    n = len(order)
    perm = [0] * n
    for pos, node in enumerate(order):
        perm[node] = pos
    return perm


def reverse_cuthill_mckee(adj, start=None):
    """Reverse Cuthill-McKee (George 1971): die Cuthill-McKee-Positionsfolge einfach umgekehrt (perm -> n-1-perm). Mathematischer Fakt: die BANDBREITE bleibt dabei exakt gleich
    (|(n-1-a)-(n-1-b)| = |a-b|) - nur das Profil kann sich ändern (meist zum Kleineren, aber nicht garantiert, s. README "Befunde")."""
    cm = cuthill_mckee(adj, start)
    n = len(cm)
    return [n - 1 - p for p in cm]


# --- Exakte Bandbreite per Brute-Force (nur kleine Instanzen, n <= N_EXACT) ---------------------------------------------------------------------------------


def exact_bandwidth_bruteforce(adj):
    """Probiert ALLE n! Permutationen durch (nur für sehr kleine n sinnvoll, s. `band_constants.N_EXACT`) - die Referenz, an der Cuthill-McKee/Reverse Cuthill-McKee gemessen werden.
    Bandbreitenminimierung ist NP-vollständig (Papadimitriou 1976, Computing 16(3), 263-270), es gibt also keinen bekannten Trick, der hier zuverlässig schneller wäre."""
    n = len(adj)
    if n <= 1:
        return 0
    edges = [(u, v) for u in range(n) for v in adj[u] if u < v]
    if not edges:
        return 0
    best = None
    for perm in itertools.permutations(range(n)):
        b = 0
        for u, v in edges:
            d = perm[u] - perm[v]
            if d < 0:
                d = -d
            if d > b:
                b = d
            if best is not None and b >= best:
                break                                    # kann diese Permutation nicht mehr verbessern - frueher Abbruch (aendert das Ergebnis nicht, nur die Laufzeit)
        if best is None or b < best:
            best = b
    return best
