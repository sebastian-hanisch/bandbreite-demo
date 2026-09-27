# Bandbreite eines Graphen – Cuthill-McKee und Reverse Cuthill-McKee – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-bandbreite-demo.streamlit.app/)**

Elftes Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", ein direktes Kind der Wurzel (Stück 1, [bfs-dfs-demo](https://github.com/sebastian-hanisch/bfs-dfs-demo)): die **Bandbreite** B(π) = max über Kanten (u,v) von |π(u)-π(v)| misst, wie weit die Endpunkte jeder Kante in einer Knotennummerierung π auseinanderliegen – zentral beim Lösen großer dünnbesetzter Gleichungssysteme (FEM, Cholesky-Zerlegung): eine schmale Bandbreite hält alle Nicht-Null-Einträge nah an der Diagonale und macht die Zerlegung viel billiger. Bandbreiten-Minimierung ist NP-vollständig (Papadimitriou 1976) – die Standard-Heuristik **Cuthill-McKee** (1969) ist genau die Breitensuche aus Stück 1, nur mit einer zusätzlichen Gradregel ("Cuthill-McKee = BFS mit Gradregel"). **Reverse Cuthill-McKee** (George 1971) kehrt die fertige Reihenfolge nur um – ein mathematischer Fakt, kein Messwert: die Bandbreite bleibt dabei EXAKT gleich, nur das Profil (die Summe der Zeilenbreiten bis zur Diagonale) kann sich ändern.

**Einordnung in die Reihe:** die Reihe hat zwölf Stücke, dies ist das elfte (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [gebaut: bridges-demo, euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen ─ 8 Robustheit ─ 9 Kaskaden/Ausbr.   [gebaut: centrality-demo, strukturkennzahlen-demo, robustheit-demo, kaskaden-demo]
 │                            └─ 10 Kritische Knoten härten                   [gebaut: haertung-demo]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [gebaut: bandbreite-demo ─ DIESES STÜCK]
```

Ergebnis in Kürze – zwei ehrliche Überraschungen: Auf dem Betriebsnetz-Raster erreicht Cuthill-McKee nach zufälliger Vertauschung in **ALLEN 35 getesteten (Seitenlänge, Seed)-Kombinationen** einen Erholungsgrad von **exakt 1.0** – volle Erholung auf die natürliche (und, soweit exakt überprüfbar, optimale) Bandbreite, kein einziger Ausreißer. Auf dem **Stern-Lehrbuch** dagegen verfehlt Cuthill-McKee das von Hand nachrechenbare Optimum systematisch: ab n=5 GEMESSEN immer bei Bandbreite n-2 statt des wahren Optimums ⌈(n-1)/2⌉ – ein bekanntes, hier nachgemessenes Strukturproblem der Heuristik auf Hub-dominierten Graphen (bestätigt gegen `scipy.sparse.csgraph.reverse_cuthill_mckee`, dort sogar n-1). Auf dem skalenfreien Netz bleibt der Abstand zur Diameter-Schranke deutlich größer als beim Raster und wächst mit der Größe.

## Warum dieses Problem

Beim Lösen großer dünnbesetzter linearer Gleichungssysteme (z. B. aus der Finite-Elemente-Methode) bestimmt die Bandbreite der Koeffizientenmatrix direkt die Kosten einer Cholesky-/LU-Zerlegung: die Nicht-Null-Struktur "füllt sich" bei der Zerlegung nur innerhalb des Bandes auf. Da Bandbreitenminimierung NP-vollständig ist (Papadimitriou 1976), verlässt sich die Praxis seit über 50 Jahren auf die einfache, schnelle Heuristik Cuthill-McKee (1969) – diese Demo zeigt, WARUM sie funktioniert (sie ist buchstäblich Stück 1s Breitensuche mit einer einzigen zusätzlichen Regel), wie gut sie tatsächlich ist (gemessen gegen die exakte Referenz und eine bewiesene untere Schranke), und wo sie messbar versagt (der Stern-Fall).

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese | Ergebnis |
|---|---|
| **H1** Bandbreite/Profil stimmen mit einer komplett unabhängigen Neuberechnung überein. | ✅ Bestätigt auf 300 zufälligen Instanzen (`tests/test_algorithm_base.py`). |
| **H2** Cuthill-McKee und Reverse Cuthill-McKee liefern immer eine gültige Permutation, auch bei mehreren Zusammenhangskomponenten. | ✅ Bestätigt auf 300 zufälligen Instanzen, inklusive eines Sonderfalls mit zwei getrennten Komponenten. |
| **H3** Bandbreite(Cuthill-McKee) == Bandbreite(Reverse Cuthill-McKee) EXAKT auf jeder Instanz. | ✅ Bestätigt als Satz (kein Toleranzband) auf 300 zufälligen Instanzen UND auf 200 weiteren Instanzen des Profilvergleichs. |
| **H4** Reverse Cuthill-McKees Profil ist nie größer als Cuthill-McKees. | ⚠️ **Nur teilweise bestätigt (gemessen, nicht bewiesen):** auf 200 zufälligen Instanzen war RCM in 174 Fällen strikt besser, in 26 Fällen gleich, in KEINEM Fall schlechter – ein einseitiger, aber empirischer Befund, kein Satz. |
| **H5** Der Stern hat eine von Hand nachrechenbare optimale Bandbreite, die Cuthill-McKee erreicht. | ❌ **Teilweise widerlegt:** die exakte optimale Bandbreite ⌈(n-1)/2⌉ stimmt (bestätigt gegen Brute-Force), aber Cuthill-McKee/Reverse Cuthill-McKee erreichen sie NUR bei n=3,4 – ab n=5 liegt die Heuristik GEMESSEN immer bei n-2, deutlich über dem Optimum. |
| **H6** Der Pfad hat immer Bandbreite 1, unabhängig vom Algorithmus. | ✅ Bestätigt für n=2..40, alle vier Nummerierungen. |
| **H7** Die Diameter-Schranke wird von jeder Permutation eingehalten, auch von einer zufälligen. | ✅ Bestätigt auf 300 zufälligen Instanzen – inklusive eines Regressionstests gegen eine naive (falsche) globale Formel, die bei getrennten Komponenten eine ZU GROSSE, damit ungültige Schranke behauptet hätte (s. Design-Entscheidungen). |
| **H8** Zufällige Vertauschung des Rasters wird von Cuthill-McKee wieder vollständig rückgängig gemacht. | ✅ **Bestätigt, stärker als erwartet:** Erholungsgrad exakt 1.0 in ALLEN 35 getesteten Fällen (Seitenlängen 4–10, 5 Seeds je Seite). |
| **H9** Cuthill-McKee/Reverse Cuthill-McKee erreichen nie eine kleinere Bandbreite als das exakte Optimum. | ✅ Bestätigt als Satz auf allen Instanzen mit n ≤ 9 (Raster, skalenfrei, Stern, Pfad). |
| **H10** Sonderfälle (n≤2, unzusammenhängender Graph, vollständiger Graph) laufen ohne Fehler und liefern die erwarteten Randwerte. | ✅ Bestätigt (vollständiger Graph K_n → Bandbreite n-1, zwei Komponenten → gültige Permutation, Diameter-Schranke weiterhin korrekt). |

## Befunde (gemessen, keine Behauptungen)

Seed 35, Standardeinstellungen sofern nicht anders angegeben; alle Zahlen über `band_evaluation`-Funktionen nachgerechnet (`tests/test_presets.py`, `tests/test_claims.py`).

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Bandbreite/Profil stimmen auf 300 Instanzen mit einer unabhängigen Neuberechnung überein; Cuthill-McKee/Reverse-Cuthill-McKee-Bandbreite ist auf JEDER von 500 getesteten Instanzen (300+200) exakt gleich; die Diameter-Schranke wird nie unterschritten; Cuthill-McKee erreicht auf allen n≤9-Instanzen mindestens die exakte Referenz. |
| **Raster (Seitenlänge 8, n=64)** | Natürliche Bandbreite 8 (== Seitenlänge, Diameter-Schranke 5). Zufällig vertauscht: Bandbreite explodiert auf 62 – Cuthill-McKee UND Reverse Cuthill-McKee bringen sie exakt auf 8 zurück. |
| **Erholungsgrad nach zufälliger Vertauschung** | EXAKT 1.0 in allen 35 getesteten (Seitenlänge, Seed)-Kombinationen (Seiten 4–10, je 5 Seeds) – volle Erholung, ausnahmslos. |
| **Kleine Instanz gegen Exakt (Raster, Seitenlänge 3, n=9)** | Natürlich = Cuthill-McKee = Exakt = 3 (Diameter-Schranke 2) – das Raster ist hier bereits nachweislich optimal. |
| **Stern (n=15)** | Cuthill-McKee/Reverse Cuthill-McKee erreichen Bandbreite 13 (= n-2) – das wahre Optimum ist 7 (⌈(n-1)/2⌉). Ab n=5 verfehlt die Heuristik das Optimum IMMER (gemessen für n=5,6,8,10,15,20,30), bestätigt gegen `scipy.sparse.csgraph.reverse_cuthill_mckee` (dort sogar n-1, noch schlechter). Ursache: der pseudo-periphere Start ist stets ein Blatt, wodurch der Mittelpunkt auf Position 1 (bzw. n-2 bei RCM) landet statt in der Mitte. |
| **Pfad (n=15)** | Bandbreite 1, unabhängig von der Nummerierung. |
| **Skalenfreies Netz (n=60, m=2, m0=4)** | Natürliche Bandbreite 56 (die Aufbaureihenfolge selbst ist fast Worst Case), Cuthill-McKee bringt sie auf 30 (fast halbiert) – bleibt aber deutlich über der Diameter-Schranke (12). Der relative Abstand zur Schranke wächst mit n (n=20: Faktor ≈1.6, n=80: Faktor ≈2.6). |
| **Profil Cuthill-McKee gegen Reverse Cuthill-McKee (200 zufällige Instanzen)** | Bandbreite in ALLEN 200 exakt gleich (Satz). Profil: RCM in 174 Fällen kleiner, in 26 gleich, in KEINEM Fall größer – ein einseitiger, aber rein gemessener (nicht bewiesener) Befund auf diesem Instanzen-Mix. |
| **Wie nah an Exakt? (n≤9)** | Raster (n=9): Cuthill-McKee = Exakt = 3. Skalenfrei (n=8): Cuthill-McKee = Exakt = 3. Skalenfrei (n=9): Cuthill-McKee 4 gegen Exakt 3 (ein Schritt daneben). Stern/Pfad: exakte Formel bestätigt für alle getesteten n. |

Presets (8), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Raster natürlich (schon fast optimal) | Bandbreite 8 bei n=64, nah an der Diameter-Schranke |
| Raster zufällig vertauscht (Cuthill-McKee stellt es wieder her) | Bandbreite 8→62→8, volle Erholung |
| Stern von Hand (Cuthill-McKee verfehlt das Optimum) | Bandbreite 13 statt des Optimums 7 bei n=15 |
| Pfad (Bandbreite immer 1) | Bandbreite 1, unabhängig von der Nummerierung |
| Skalenfreies Netz härten | Bandbreite fast halbiert (56→30), aber weit über der Schranke (12) |
| Cuthill-McKee gegen Reverse Cuthill-McKee: Profil-Unterschied | 174 von 200 Instanzen: RCM-Profil kleiner |
| Kleine Instanz gegen das exakte Optimum | Natürlich = Cuthill-McKee = Exakt = 3 bei n=9 |
| Pseudo-periphere Startknotenwahl | Wellenfront-Animation auf dem skalenfreien Netz |

## Modell und Verfahren

- **Betriebsnetz, Skalenfreies Netz** (`band_scenario.py`, wortgleich aus `kas_scenario.py`/`sk_scenario.py`): Raster/Zufallsgraph bzw. Barabási-Albert.
- **Betriebsnetz zufällig vertauscht** (`random_relabel`, NEU): dieselben Kanten, Knoten zufällig umnummeriert (`sigma` als Permutation) – die (x,y)-Lage folgt der neuen Nummerierung, damit die Karte anschaulich bleibt.
- **Stern-/Pfad-Lehrbuch** (`star_instance`/`path_instance`, NEU): Stern K_{1,n-1} bzw. Pfad 0-1-…-(n-1), beide von Hand nachrechenbar.
- **Bandbreite/Profil** (`bandwidth`/`profile`): Bandbreite = max |π(u)-π(v)| über alle Kanten; Profil = Σ_v (π(v) - min{π(u) : u~v, π(u)≤π(v)}).
- **Pseudo-periphere Startknotenwahl** (`pseudo_peripheral`, George und Liu 1979): wiederholte Breitensuche, unter den am weitesten entfernten Knoten den mit dem kleinsten Grad wählen.
- **Cuthill-McKee** (`cuthill_mckee`, 1969): Breitensuche mit Gradregel (unbesuchte Nachbarn nach aufsteigendem Grad in die Warteschlange); Komponenten nacheinander.
- **Reverse Cuthill-McKee** (`reverse_cuthill_mckee`, George 1971): Positionsfolge umgekehrt (π → n-1-π) – Bandbreite dabei beweisbar exakt invariant.
- **Exakte Referenz** (`exact_bandwidth_bruteforce`): alle n! Permutationen, nur für n ≤ 9 (`N_EXACT`).
- **Untere Schranke** (`lower_bound_diameter`): ⌈(n_i-1)/diam_i⌉, maximiert über alle Zusammenhangskomponenten.

## Design-Entscheidungen

- **Diameter-Schranke komponentenweise, nicht global.** Die naheliegende Formel "⌈(n-1)/diam(G)⌉ mit dem globalen Durchmesser" ist bei UNZUSAMMENHÄNGENDEN Graphen keine gültige untere Schranke mehr: zwei getrennte Kanten (n=4, jede Komponente Durchmesser 1) würden ⌈3/1⌉=3 behaupten, obwohl Bandbreite 1 erreichbar ist. Die korrekte Verallgemeinerung maximiert ⌈(n_i-1)/diam_i⌉ über die einzelnen Komponenten (Beweis: die n_i Positionen einer Komponente sind n_i verschiedene ganze Zahlen, ihre Spannweite ist also mindestens n_i-1 – Schubfachprinzip –, und die beiden das realisierenden Knoten liegen höchstens diam_i Kanten auseinander). Dieser Fehler wurde beim Bau tatsächlich gemacht und durch einen Test (Punkt 7 der Korrektheits-Kette) gefunden, s. Grenzen/Bugs unten.
- **Sterns exaktes Optimum ist ⌈(n-1)/2⌉, nicht die grobe Faustformel ⌈n/2⌉.** Beide Formeln stimmen nur bei geradem n überein; bei ungeradem n (z. B. n=15: 7 gegen 8) liefert die grobe Formel einen falschen Wert. `band_constants.star_optimal_bandwidth` verwendet die exakte, gegen Brute-Force geprüfte Formel.
- **"Sichtbare Nummerierung" (Regler) blendet "Exakt" aus, sobald n > N_EXACT=9** – Hauskonvention gegen tote Regler: eine Option, die ohnehin nicht berechenbar wäre, wird nicht erst angeboten und dann stillschweigend zurückgesetzt.
- **`random_relabel`s (x,y)-Lage folgt der neuen Nummerierung** (nicht der alten): die physische Position bleibt dieselbe, nur der Index ändert sich – so bleibt die Karte lesbar, während die Bandbreite unter der (jetzt zufälligen) IDENTITÄTS-Permutation auf dieser neuen Nummerierung explodiert.

## Vormessung (Kalibrierung)

`exact_bandwidth_bruteforce` probiert n! Permutationen durch. Auf der dichtesten realistischen Instanz (vollständiger Graph) dauert n=9 (362.880 Permutationen) rund 0.5s, n=10 (3.628.800 Permutationen) bereits rund 6s – für eine interaktive App und eine schnelle CI zu langsam. **N_EXACT=9** ist die gewählte Grenze (`tools/vormessung.py`); bei den tatsächlich verwendeten (dünneren) Vehikeln liegt die Laufzeit meist deutlich darunter (Sternstruktur mit 8 Kanten bei n=9: 0.11s).

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Cuthill-McKee in Aktion** (Wellenfront-Karte mit Schieberegler über die Besuchsreihenfolge, Knotengröße ∝ Grad) → **Nicht-Null-Muster** (drei Streudiagramme natürlich/Cuthill-McKee/Reverse Cuthill-McKee nebeneinander, das klassische "Band um die Diagonale"-Bild) → **Bandbreite gleich, Profil verschieden** (Balken- und Streudiagramm über 200 zufällige Instanzen) → **Wie nah am Optimum?** (Bandbreite über die Größe: natürlich/zufällig/Cuthill-McKee/Reverse Cuthill-McKee gegen exakt und die Diameter-Schranke; beim Betriebsnetz zusätzlich der Erholungsgrad).
2. **Instanz** (Betriebsnetz / Betriebsnetz zufällig vertauscht / Skalenfreies Netz / Stern-Lehrbuch / Pfad-Lehrbuch), instanzspezifische Größen, sichtbare Nummerierung (bestimmt Bandbreite/Profil in der Kopfzeile), Zufalls-Seed (+🎲); Permalink in der Adresszeile.

## Was nicht funktioniert hat / Grenzen

- **Cuthill-McKee löst das Bandbreitenproblem nicht optimal** (es ist NP-vollständig) – auf dem Stern-Lehrbuch ab n=5 GEMESSEN systematisch daneben (n-2 statt ⌈(n-1)/2⌉), weil der pseudo-periphere Start immer ein Blatt ist und den Mittelpunkt an den Rand statt in die Mitte der Nummerierung drängt.
- **Reverse Cuthill-McKees Profilvorteil ist gemessen, nicht bewiesen** – auf den hier getesteten Instanzen (Raster/vertauschtes Raster/skalenfrei) war es nie schlechter, aber das ist kein allgemeiner Satz.
- **Die Diameter-Schranke ist nicht scharf** – der Abstand zwischen Cuthill-McKee und der Schranke wächst auf dem skalenfreien Netz mit der Größe; ob das exakte Optimum näher an Cuthill-McKee oder an der Schranke liegt, lässt sich jenseits von n=9 nicht mehr direkt nachprüfen.
- **Ein echter Bug wurde beim Bau gefunden und behoben:** die erste Fassung von `lower_bound_diameter` berechnete den Durchmesser einer Komponente fälschlich als die Exzentrizität des zufällig gewählten BFS-Startknotens statt als den echten Komponenten-Durchmesser (Maximum über ALLE Knoten der Komponente) – auf einem Stern mit 24 Knoten ergab das eine UNGÜLTIGE (zu große) untere Schranke von 23 statt der korrekten 12, ein direkter Verstoß gegen den Satz aus Korrektheits-Kette Punkt 7. Der Fehler wurde durch den Massentest über 300 zufällige Instanzen gefunden und ist jetzt durch einen expliziten Regressionstest abgesichert.
- **Synthetische Instanzen.** Betriebsnetz, skalenfreies Netz, Stern und Pfad sind erzeugt, keine echten FEM-Gleichungssysteme.

## Tests

`tests/test_scenario.py` (Rauchtests der fünf Instanzen), `tests/test_algorithm_base.py` (Korrektheits-Kette Punkte 1–3, 5–7, 10: Bandbreite/Profil gegen unabhängige Neuberechnung auf 300 Instanzen, gültige Permutationen, Bandbreite(CM)==Bandbreite(RCM) als Satz, Stern/Pfad von Hand, Diameter-Schranke nie verletzt inklusive Regressionstest gegen die naive Formel, Sonderfälle, Gegenprobe gegen `scipy.sparse.csgraph`/`networkx`), `tests/test_evaluation.py` (Korrektheits-Kette Punkte 4, 8, 9: Profilvergleich gemessen, Erholungsgrad gemessen, Cuthill-McKee/Reverse-Cuthill-McKee ≥ Exakt immer), `tests/test_presets.py` (jede Zahl der Preset-Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (AppTest – Voreinstellung, jedes Preset, jeder Schritt für jede Instanzart, bedingte Regler, "Exakt" nur bei kleinem n, Permalink-Grenzen, Footer).

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `band_algorithm.py` | Bandbreite/Profil, Cuthill-McKee/Reverse Cuthill-McKee, pseudo-periphere Startwahl, Brute-Force, Diameter-Schranke (Bausteine wortgleich aus `bfd_algorithm.py`/`cen_algorithm.py`) |
| `band_scenario.py` | Betriebsnetz, Betriebsnetz zufällig vertauscht, skalenfreies Netz, Stern, Pfad |
| `band_evaluation.py` | Analyse, Erholungsgrad, Profilvergleich, Größen-Sweeps |
| `band_visualization.py` | Plotly-Figuren (Wellenfront-Karte, Nicht-Null-Muster, Profilvergleich, Optimum-Abstand, Erholungsgrad) |
| `band_presets.py`, `band_constants.py` | Permalink, Presets, gemessene Werte |
| `tools/vormessung.py` | Kalibrierung von N_EXACT |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Simuliertes Annealing oder andere Metaheuristiken für die Bandbreitenminimierung selbst (das zwölfte, letzte Stück der Reihe behandelt Bandbreite auf einer strukturierten Zufallsklasse G(n,k,b) und Cliquenüberdeckung – ein eigenständiges Thema). Sparse-Matrix-spezifische Varianten wie King- oder Sloan-Nummerierung (Cuthill-McKee/Reverse Cuthill-McKee sind die historisch wichtigsten und am weitesten verbreiteten Verfahren dieser Familie).

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Cuthill, E., & McKee, J. (1969). *Reducing the bandwidth of sparse symmetric matrices.* Proceedings of the 24th National Conference ACM, 157–172.
- George, A. (1971). *Computer implementation of the finite element method* (Doktorarbeit, Stanford University) – Ursprung von Reverse Cuthill-McKee.
- George, A., & Liu, J. W. H. (1979). *An implementation of a pseudoperipheral node finder.* ACM Transactions on Mathematical Software 5(3), 284–295.
- Papadimitriou, C. H. (1976). *The NP-completeness of the bandwidth minimization problem.* Computing 16(3), 263–270.

Gebaut mit Streamlit, Plotly, NumPy und pandas.
