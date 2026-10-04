"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

import math

SPACING = 1.0                    # Abstand der Kreuzungen im Betriebsnetz-Raster
JITTER = 0.18
SEED_MAX = 999999
DEFAULT_SEED = 35

KINDS = ("city", "city_relabel", "ba", "star", "path")
KIND_LABELS = {
    "city": "Betriebsnetz (natürliche Nummerierung)",
    "city_relabel": "Betriebsnetz zufällig vertauscht",
    "ba": "Skalenfreies Netz (Barabási-Albert)",
    "star": "Stern-Lehrbuch",
    "path": "Pfad-Lehrbuch",
}

# --- Betriebsnetz (wortgleich aus kaskaden-demo/haertung-demo) -----------------------------------------------------------------------------------------
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 3, 14, 7
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4)
DEFAULT_BLOCKED = 0.0

# --- Skalenfreies Netz (Barabási und Albert 1999) ------------------------------------------------------------------------------------------------------
N_BA_MIN, N_BA_MAX, DEFAULT_N_BA = 8, 120, 40
M0_BA_MIN, M0_BA_MAX, DEFAULT_M0_BA = 3, 10, 4
M_BA_MIN, DEFAULT_M_BA = 1, 2

# --- Stern-/Pfad-Lehrbuch (NEU) -------------------------------------------------------------------------------------------------------------------------
N_STAR_MIN, N_STAR_MAX, DEFAULT_N_STAR = 3, 60, 9
N_PATH_MIN, N_PATH_MAX, DEFAULT_N_PATH = 2, 60, 10


def star_optimal_bandwidth(n):
    """Exakte optimale Bandbreite des Sterns K_{1,n-1} (n Knoten insgesamt): der Mittelpunkt wird auf Position m platziert, die übrigen n-1 Positionen 0..n-1 (ohne m) gehen an die Blätter - die am
    weitesten entfernte belegte Position ist entweder 0 oder n-1, und max(m, n-1-m) wird durch m = (n-1)//2 oder m = ceil((n-1)/2) minimiert. Ergebnis: ceil((n-1)/2) - siehe README "Design-
    Entscheidungen" für den Unterschied zur groben Faustformel ⌈n/2⌉ (die beiden Werte stimmen nur für gerades n überein, s. Tests)."""
    n = int(n)
    return math.ceil((n - 1) / 2)


def star_cm_bandwidth(n):
    """GEMESSENER (nicht angenommener) Wert von Cuthill-McKee/Reverse-Cuthill-McKee auf dem Stern K_{1,n-1}, n>=3: exakt n-2, für n>=5 NACHWEISLICH schlechter als das wahre Optimum
    `star_optimal_bandwidth(n)` - der pseudo-periphere Start ist stets ein Blatt, der Mittelpunkt landet dadurch auf Position 1 bzw. n-2 statt in der Mitte (s. README "Befunde", bestätigt
    unabhängig gegen scipy.sparse.csgraph.reverse_cuthill_mckee, dort sogar n-1)."""
    n = int(n)
    if n < 3:
        raise ValueError("nur für n>=3 definiert")
    return n - 2


# --- Vormessung: N_EXACT (Brute-Force-Grenze) -----------------------------------------------------------------------------------------------------------
# Kalibriert in tools/vormessung.py (2026-09-27): exact_bandwidth_bruteforce probiert n! Permutationen durch. Bei n=9 (362880 Permutationen) dauert ein dichter Testfall (Barabasi-Albert, ~2m
# Kanten) rund 1.5-2.5s auf der Entwicklungsmaschine - noch gut mit st.spinner vertretbar, auch mehrfach hintereinander in Tests. n=10 (3.6 Mio. Permutationen) braucht bereits 15-25s und ist fuer
# eine interaktive App/CI zu langsam. N_EXACT=9 ist die gewaehlte Grenze (s. Vormessungs-Ergebnis README).
N_EXACT = 9

# --- Messreihen-Stuetzstellen ---------------------------------------------------------------------------------------------------------------------------
RECOVERY_SIDES = (4, 5, 6, 7, 8, 9, 10)
RECOVERY_SEEDS = (11, 22, 33, 44, 55)

SWEEP_SIDES_CITY = (3, 4, 5, 6, 7, 8, 9, 10, 12, 14)
SWEEP_SIZES_BA = (8, 12, 16, 20, 30, 40, 60, 80)
SWEEP_SIZES_STAR = (4, 6, 8, 10, 14, 20, 30, 45, 60)
SWEEP_SIZES_PATH = (4, 6, 8, 10, 14, 20, 30, 45, 60)

EXACT_GAP_SIDES_CITY = (3, 4)                 # side=3 -> n=9 (== N_EXACT), side=4 -> n=16 (> N_EXACT, nur zur Einordnung)
EXACT_GAP_SIZES_BA = (8, 9)
EXACT_GAP_SIZES_STAR = (3, 5, 7, 9)
EXACT_GAP_SIZES_PATH = (3, 5, 7, 9)

PROFILE_COMPARISON_N = 200

STEPS = {1: "1 · Cuthill-McKee in Aktion", 2: "2 · Nicht-Null-Muster", 3: "3 · Bandbreite gleich, Profil verschieden", 4: "4 · Wie nah am Optimum?"}

ALGORITHMS = ("natural", "random", "cm", "rcm", "exact")
ALGORITHM_LABELS = {"natural": "Natürlich", "random": "Zufällig", "cm": "Cuthill-McKee", "rcm": "Reverse Cuthill-McKee", "exact": "Exakt (Brute-Force)"}

# --- Gemessene Werte (Seed 35, sofern nicht anders angegeben; 2026-09-27, alle Werte über ev.*-Aufrufe nachgerechnet, s. tests/test_claims.py) -----------
# RASTER (side=8, n=64): natuerliche Bandbreite 8 (== Seitenlaenge, Diameter-Schranke 5). Zufaellig vertauscht: Bandbreite explodiert auf 62 - Cuthill-McKee UND Reverse Cuthill-McKee bringen sie
#   auf EXAKT 8 zurueck, den natuerlichen (und, s. exakter Vergleich bei side=3, vermutlich optimalen) Wert - volle Erholung (Erholungsgrad 1.0), gemessen ueber ALLE getesteten Seiten/Seeds
#   (4..10 x 5 Seeds, s. tests/test_evaluation.py), nicht nur diesen einen Fall.
# STERN (n=15): Cuthill-McKee/Reverse-Cuthill-McKee erreichen Bandbreite 13 (= n-2, GEMESSEN, kein Zufall) - das wahre Optimum waere 7 (=ceil(14/2)). Ab n=5 verfehlt Cuthill-McKee das Optimum
#   IMMER (s. tests/test_algorithm_base.py) - ein ueberraschender, ehrlich berichteter Schwachpunkt der Heuristik auf Hub-dominierten Graphen (bestaetigt gegen scipy.sparse.csgraph, dort n-1).
# PFAD (n=15): Bandbreite ist 1, unabhaengig von der gewaehlten Nummerierung.
# SKALENFREI (n=60, m=2, m0=4): natuerliche Bandbreite 56 (die Bau-Reihenfolge selbst ist fast worst-case), Cuthill-McKee bringt sie auf 30 (fast halbiert) - aber die Diameter-Schranke liegt bei
#   nur 12: der Abstand zum Optimum bleibt auf skalenfreien Netzen deutlich groesser als beim Raster (s. README "Befunde").
# KLEINE INSTANZ GEGEN EXAKT (Raster side=3, n=9): natuerlich/Cuthill-McKee/exakt sind alle EXAKT gleich (3) - das Raster ist hier nachweislich schon optimal, bei einer Diameter-Schranke von 2.
# PROFIL CM GEGEN RCM (200 zufaellige Instanzen, Seed 35): Bandbreite in ALLEN 200 exakt gleich (Punkt 3). Profil: RCM in 174 von 200 Faellen kleiner, in 26 gleich, in KEINEM Fall groesser -
#   ein einseitiger, aber rein GEMESSENER (nicht bewiesener) Befund auf diesem Instanzen-Mix.
PRESET_HELP_MEASURED_AT = "2026-09-27"

PRESETS = {
    "Raster natürlich (schon fast optimal)": {"kind": "city", "side": 8, "blocked": 0.0, "nettype": "grid", "algo": "natural", "seed": 35, "step": 2},
    "Raster zufällig vertauscht (Cuthill-McKee stellt es wieder her)": {"kind": "city_relabel", "side": 8, "blocked": 0.0, "nettype": "grid", "algo": "cm", "seed": 35, "step": 4},
    "Stern von Hand (Cuthill-McKee verfehlt das Optimum)": {"kind": "star", "nstar": 15, "algo": "cm", "seed": 35, "step": 2},
    "Pfad (Bandbreite immer 1)": {"kind": "path", "npath": 15, "algo": "cm", "seed": 35, "step": 2},
    "Skalenfreies Netz härten": {"kind": "ba", "nba": 60, "m0ba": 4, "mba": 2, "algo": "cm", "seed": 35, "step": 4},
    "Cuthill-McKee gegen Reverse Cuthill-McKee: Profil-Unterschied": {"kind": "city", "side": 8, "algo": "cm", "seed": 35, "step": 3},
    "Kleine Instanz gegen das exakte Optimum": {"kind": "city", "side": 3, "algo": "exact", "seed": 35, "step": 4},
    "Pseudo-periphere Startknotenwahl": {"kind": "ba", "nba": 40, "m0ba": 4, "mba": 2, "algo": "cm", "seed": 35, "step": 1},
}
PRESET_HELP = {
    "Raster natürlich (schon fast optimal)": "Bandbreite 8 bei Seitenlänge 8 (n=64) - die natürliche Nummerierung liegt schon nah an der Diameter-Schranke (5) und ist bei kleinen Rastern (n=9) "
                                              "nachweislich exakt optimal.",
    "Raster zufällig vertauscht (Cuthill-McKee stellt es wieder her)": "Zufällige Umnummerierung lässt die Bandbreite von 8 auf 62 explodieren - Cuthill-McKee UND Reverse Cuthill-McKee bringen "
                                                                       "sie exakt auf 8 zurück (volle Erholung, gemessen über alle getesteten Rastergrößen/Seeds).",
    "Stern von Hand (Cuthill-McKee verfehlt das Optimum)": "Bei n=15 erreicht Cuthill-McKee Bandbreite 13 (=n-2) - das wahre, von Hand nachrechenbare Optimum ist 7 (⌈(n-1)/2⌉). Ab n=5 verfehlt "
                                                            "die Heuristik das Optimum IMMER, ein gemessener Schwachpunkt auf Hub-dominierten Graphen.",
    "Pfad (Bandbreite immer 1)": "Die einfachste denkbare Instanz: Bandbreite ist 1 bei natürlicher, Cuthill-McKee- und Reverse-Cuthill-McKee-Nummerierung (nur die zufällige Nummerierung ist schlechter: n=15 → 12).",
    "Skalenfreies Netz härten": "Cuthill-McKee halbiert die Bandbreite fast (56→30 bei n=60) - bleibt aber deutlich über der Diameter-Schranke (12), anders als beim Raster.",
    "Cuthill-McKee gegen Reverse Cuthill-McKee: Profil-Unterschied": "Über 200 zufällige Instanzen: Bandbreite(CM)==Bandbreite(RCM) in ALLEN 200 Fällen (Satz) - das Profil ist bei RCM in 174 "
                                                                     "von 200 Fällen kleiner, in 26 gleich, in keinem Fall größer (gemessen, nicht bewiesen).",
    "Kleine Instanz gegen das exakte Optimum": "Bei n=9 (Seitenlänge 3) sind natürlich/Cuthill-McKee/exakt alle identisch (Bandbreite 3) - das Raster ist hier bewiesen schon optimal.",
    "Pseudo-periphere Startknotenwahl": "George und Liu (1979): wiederholte Breitensuche findet einen Startknoten an der Peripherie des skalenfreien Netzes - sichtbar an Schritt 1s "
                                        "Wellenfront-Animation.",
}
