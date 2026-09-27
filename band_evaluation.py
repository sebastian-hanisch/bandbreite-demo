"""Auswertung: eine einzelne Instanz mit allen fünf Nummerierungen (Schritt 1/2/3-Grundlage, `analyse`), Erholungsgrad des zufällig vertauschten Rasters unter CM/RCM (`recovery_check`,
Korrektheits-Kette Punkt 8), Profil CM gegen RCM über viele verschiedene Instanzen (`profile_comparison`, Punkt 4), Bandbreite/Profil/untere Schranke über die Instanzgröße (`size_sweep`,
Messreihe 1+5) und wie nah CM/RCM/Zufall ans exakte Optimum herankommen (`exact_gap`, Punkt 9, wrappt `size_sweep` auf Größen mit n<=N_EXACT)."""

import random
from dataclasses import dataclass

import band_algorithm as A
import band_constants as C
import band_scenario as S


@dataclass
class Settings:
    kind: str = "city"                    # "city" | "city_relabel" | "ba" | "star" | "path"
    # Betriebsnetz / Betriebsnetz zufaellig vertauscht
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"                 # "grid" | "random"
    # Skalenfreies Netz
    n_ba: int = C.DEFAULT_N_BA
    m_ba: int = C.DEFAULT_M_BA
    m0_ba: int = C.DEFAULT_M0_BA
    # Stern-/Pfad-Lehrbuch
    n_star: int = C.DEFAULT_N_STAR
    n_path: int = C.DEFAULT_N_PATH
    # gemeinsam
    seed: int = C.DEFAULT_SEED


def instance(settings):
    if settings.kind == "city":
        return S.generate(settings.side, settings.blocked, settings.nettype, settings.seed)
    if settings.kind == "city_relabel":
        base = S.generate(settings.side, settings.blocked, settings.nettype, settings.seed)
        return S.random_relabel(base, settings.seed)
    if settings.kind == "ba":
        return S.barabasi_albert_instance(settings.n_ba, settings.m_ba, settings.m0_ba, settings.seed)
    if settings.kind == "star":
        return S.star_instance(settings.n_star)
    if settings.kind == "path":
        return S.path_instance(settings.n_path)
    raise ValueError(f"unbekannte Instanzart {settings.kind}")


# --- Schritt 1/2/3-Grundlage: eine einzelne Instanz mit allen Nummerierungen -----------------------------------------------------------------------------


@dataclass
class Analysis:
    n: int
    m: int
    kind: str
    bw_natural: int
    bw_random: int
    bw_cm: int
    bw_rcm: int
    bw_exact: object              # None, falls n > N_EXACT
    profile_natural: int
    profile_random: int
    profile_cm: int
    profile_rcm: int
    lower_bound: int
    perm_natural: list
    perm_random: list
    perm_cm: list
    perm_rcm: list
    cm_order: list                # order[pos] = Knoten an dieser Position (Cuthill-McKee-Besuchsreihenfolge, fuer die Schritt-fuer-Schritt-Wiedergabe)
    degrees: list                 # Grad je Knoten (fuer die Faerbung der Wellenfront)


def analyse(settings):
    inst = instance(settings)
    adj = A.adjacency(inst.n, inst.edges)
    natural = list(range(inst.n))
    rnd = A.random_permutation(inst.n, settings.seed)
    cm = A.cuthill_mckee(adj)
    rcm = A.reverse_cuthill_mckee(adj)
    exact = A.exact_bandwidth_bruteforce(adj) if inst.n <= C.N_EXACT else None
    lb = A.lower_bound_diameter(adj)
    cm_order = A.cuthill_mckee_order(adj)
    degrees = A.degree_centrality(adj)
    analysis = Analysis(
        n=inst.n, m=inst.m, kind=settings.kind,
        bw_natural=A.bandwidth(adj, natural), bw_random=A.bandwidth(adj, rnd), bw_cm=A.bandwidth(adj, cm), bw_rcm=A.bandwidth(adj, rcm), bw_exact=exact,
        profile_natural=A.profile(adj, natural), profile_random=A.profile(adj, rnd), profile_cm=A.profile(adj, cm), profile_rcm=A.profile(adj, rcm),
        lower_bound=lb, perm_natural=natural, perm_random=rnd, perm_cm=cm, perm_rcm=rcm, cm_order=cm_order, degrees=degrees,
    )
    return inst, adj, analysis


# --- Erholungsgrad nach zufaelliger Vertauschung (Korrektheits-Kette Punkt 8) ----------------------------------------------------------------------------


def recovery_check(sides=C.RECOVERY_SIDES, seeds=C.RECOVERY_SEEDS, blocked=0.0, nettype="grid"):
    """Für jede (Seitenlänge, Seed)-Kombination: natürliches Raster, zufällig vertauscht (Bandbreite explodiert), CM/RCM auf der vertauschten Version. Erholungsgrad =
    (bw_vertauscht - bw_cm) / (bw_vertauscht - bw_natuerlich) - 1.0 = volle Erholung auf den natürlichen Wert, 0.0 = keine Erholung, >1.0 sogar besser als die natürliche Nummerierung selbst
    (GEMESSEN, nicht angenommen - s. README "Befunde" für den tatsächlichen Wert)."""
    rows = []
    for side in sides:
        for seed in seeds:
            base = S.generate(side, blocked, nettype, seed)
            adj_natural = A.adjacency(base.n, base.edges)
            bw_natural = A.bandwidth(adj_natural, list(range(base.n)))
            relabeled = S.random_relabel(base, seed)
            adj_relabeled = A.adjacency(relabeled.n, relabeled.edges)
            bw_relabeled = A.bandwidth(adj_relabeled, list(range(relabeled.n)))
            cm = A.cuthill_mckee(adj_relabeled)
            rcm = A.reverse_cuthill_mckee(adj_relabeled)
            bw_cm = A.bandwidth(adj_relabeled, cm)
            bw_rcm = A.bandwidth(adj_relabeled, rcm)
            denom = bw_relabeled - bw_natural
            recovery_cm = (bw_relabeled - bw_cm) / denom if denom > 0 else 1.0
            recovery_rcm = (bw_relabeled - bw_rcm) / denom if denom > 0 else 1.0
            rows.append({"side": side, "seed": seed, "n": base.n, "bw_natural": bw_natural, "bw_relabeled": bw_relabeled, "bw_cm": bw_cm, "bw_rcm": bw_rcm,
                         "recovery_cm": recovery_cm, "recovery_rcm": recovery_rcm})
    return rows


# --- Profil CM gegen RCM ueber viele verschiedene Instanzen (Korrektheits-Kette Punkt 4) -------------------------------------------------------------------


def profile_comparison(seed=C.DEFAULT_SEED, n_instances=C.PROFILE_COMPARISON_N):
    """Profil(CM) gegen Profil(RCM) auf `n_instances` verschiedenen, zufällig gewählten Instanzen (Betriebsnetz / Betriebsnetz zufällig vertauscht / Skalenfrei, je unterschiedliche Größe/Seed) -
    Anteil besser/gleich/schlechter für RCM GEMESSEN, NICHT als "RCM ist immer besser" behauptet (s. README "Befunde")."""
    rng = random.Random(int(seed) * 1_000_003 + 8837)
    rows = []
    for _ in range(int(n_instances)):
        variant = rng.choice(["city", "city_relabel", "ba"])
        inst_seed = rng.randrange(1_000_000)
        if variant == "city":
            side = rng.randint(C.SIDE_MIN, C.SIDE_MAX)
            inst = S.generate(side, rng.choice(C.BLOCKED_OPTIONS), "grid", inst_seed)
        elif variant == "city_relabel":
            side = rng.randint(C.SIDE_MIN, C.SIDE_MAX)
            base = S.generate(side, rng.choice(C.BLOCKED_OPTIONS), "grid", inst_seed)
            inst = S.random_relabel(base, inst_seed)
        else:
            m0 = rng.randint(C.M0_BA_MIN, C.M0_BA_MAX)
            inst = S.barabasi_albert_instance(rng.randint(m0, C.N_BA_MAX), rng.randint(C.M_BA_MIN, m0), m0, inst_seed)
        adj = A.adjacency(inst.n, inst.edges)
        cm = A.cuthill_mckee(adj)
        rcm = A.reverse_cuthill_mckee(adj)
        rows.append({"variant": variant, "n": inst.n, "bw_cm": A.bandwidth(adj, cm), "bw_rcm": A.bandwidth(adj, rcm), "profile_cm": A.profile(adj, cm), "profile_rcm": A.profile(adj, rcm)})
    better = sum(1 for r in rows if r["profile_rcm"] < r["profile_cm"])
    equal = sum(1 for r in rows if r["profile_rcm"] == r["profile_cm"])
    worse = sum(1 for r in rows if r["profile_rcm"] > r["profile_cm"])
    return rows, {"better": better, "equal": equal, "worse": worse, "total": len(rows)}


# --- Bandbreite/Profil/untere Schranke ueber die Instanzgroesse (Messreihe 1+5) --------------------------------------------------------------------------


def size_sweep(kind="city", sizes=C.SWEEP_SIDES_CITY, seed=C.DEFAULT_SEED, nettype="grid", blocked=C.DEFAULT_BLOCKED):
    """Für jede Größe in `sizes` (bei kind="city"/"city_relabel": Seitenlänge des Rasters; sonst: n direkt): Bandbreite/Profil unter natürlicher/zufälliger/CM/RCM-Nummerierung, die
    Diameter-Schranke, und - falls n<=N_EXACT - das exakte Optimum."""
    rows = []
    for size in sizes:
        if kind == "city":
            inst = S.generate(size, blocked, nettype, seed)
        elif kind == "city_relabel":
            base = S.generate(size, blocked, nettype, seed)
            inst = S.random_relabel(base, seed)
        elif kind == "ba":
            m0 = min(C.DEFAULT_M0_BA, size)
            inst = S.barabasi_albert_instance(size, min(C.DEFAULT_M_BA, m0), m0, seed)
        elif kind == "star":
            inst = S.star_instance(size)
        elif kind == "path":
            inst = S.path_instance(size)
        else:
            raise ValueError(f"unbekannte Instanzart {kind}")
        adj = A.adjacency(inst.n, inst.edges)
        natural = list(range(inst.n))
        rnd = A.random_permutation(inst.n, seed)
        cm = A.cuthill_mckee(adj)
        rcm = A.reverse_cuthill_mckee(adj)
        exact = A.exact_bandwidth_bruteforce(adj) if inst.n <= C.N_EXACT else None
        rows.append({
            "size": size, "n": inst.n, "m": inst.m,
            "bw_natural": A.bandwidth(adj, natural), "bw_random": A.bandwidth(adj, rnd), "bw_cm": A.bandwidth(adj, cm), "bw_rcm": A.bandwidth(adj, rcm),
            "profile_cm": A.profile(adj, cm), "profile_rcm": A.profile(adj, rcm), "lower_bound": A.lower_bound_diameter(adj), "bw_exact": exact,
        })
    return rows


def exact_gap(kind="city", sizes=None, seed=C.DEFAULT_SEED, nettype="grid", blocked=C.DEFAULT_BLOCKED):
    """Wie nah kommen CM/RCM/Zufall ans EXAKTE Optimum heran, auf Instanzen mit n<=N_EXACT (wrappt `size_sweep` und filtert auf die Zeilen, in denen die Brute-Force tatsächlich gelaufen ist)."""
    if sizes is None:
        sizes = {"city": C.EXACT_GAP_SIDES_CITY, "city_relabel": C.EXACT_GAP_SIDES_CITY, "ba": C.EXACT_GAP_SIZES_BA, "star": C.EXACT_GAP_SIZES_STAR, "path": C.EXACT_GAP_SIZES_PATH}[kind]
    rows = size_sweep(kind, sizes, seed, nettype, blocked)
    return [r for r in rows if r["bw_exact"] is not None]
