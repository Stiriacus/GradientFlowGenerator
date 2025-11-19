# Frost Dune Background Generator

## Problemstellung / Ziel des Projekts

Ziel dieses Projekts ist es, **rein programmatisch** – ohne manuelle Designarbeit in Tools wie Figma oder Photoshop – abstrakte, hochwertige Hintergrundbilder zu erzeugen, die an **Sanddünen, weich fallenden Stoff oder geschichtete Felsformationen** erinnern. 

Die Bilder sollen sich besonders als **Website- oder App-Backgrounds** eignen und über eine **interaktive Desktop-Anwendung (Python + PySide6)** generiert werden können.

### 1. Visuelles Ziel

- Monochrome, abstrakte Landschaft (zunächst Graustufen, später auf Farbpaletten wie „Frost“ übertragbar).
- Anmutung von:
  - Sanddünen in der Nacht
  - weich fließendem Stoff
  - geschichtetem Gestein (z.B. Antelope Canyon)
- Minimalistisch, ohne harte grafische Elemente – Fokus auf **Form, Licht und Helligkeit**.

**Farb- und Helligkeitscharakteristik:**

- Weiche, nebelartige Gradients ohne harte Farbkanten.
- Tiefe durch starke Kontraste:
  - Tiefschwarze Schatten in Tälern und oberen Bereichen.
  - Mittelgrau bis fast Weiß auf den Kämmen der Wellen.
- Ruhiger unterer Bereich, der in ein gleichmäßiges Grau (oder später eine ruhige Frost-Farbe) übergeht.

**Form- und Linienstruktur:**

- Organische, fließende Formen statt harter Geometrie.
- Dominante horizontale Bewegung (Wellen laufen von links nach rechts und schwingen sanft).
- Feine, parallele Linien innerhalb der großen Wellen (Sedimentschichten / Stoffstruktur).
- Überlagerte Schichten mit deutlichem Vordergrund/Hintergrund-Eindruck.
- Scharf definierte Oberkanten, weich auslaufende Schatten nach unten.

### 2. Technisches Ziel (System-Perspektive)

Das Projekt soll eine **Python-basierte Desktop-Anwendung** bereitstellen, die:

- eine **moderne GUI (PySide6, Dark Theme)** mit:
  - Farbpaletten-Verwaltung,
  - Gradient-Editor mit bis zu 6 Stops und frei wählbarem Winkel (0–360°),
  - detaillierten Parametern für Noise- und Heightmap-Generierung,
  - Lighting-Parametern (Lichtrichtung, Intensität),
- auf Basis von:
  - Simplex Noise,
  - FBM (mehrere Octaves),
  - Ridge-Formung (`1 - |noise|`),
  - Domain Warping (verzerrte Koordinaten),
  - Heightmap + Normalen + Lighting,
  - Gradient-Mapping,
  vollautomatisch Dünen-ähnliche Hintergrundbilder erzeugt.

Die Anwendung soll:

- eine **Preview** in reduzierter Auflösung (z.B. 960×540) anzeigen,
- zusätzlich eine **Noise-Preview** (z.B. 480×270) zur Visualisierung der Heightmap/Layers bieten,
- Renderzeiten nur als **verstrichene Zeit** anzeigen (ohne ETA),
- und einen **Export** in PNG in vordefinierten und benutzerdefinierten Auflösungen (16:9, 4:3, Landscape/Portrait) ermöglichen.

---

## Kurz zusammengefasst

Das Projekt soll eine **interaktive, reproduzierbare, Python-basierte Lösung** sein, mit der sich:

- **dünenartige, geschichtete, plastische Hintergründe** generieren,
- **komplexe Noise-Setups und Farbräume** präzise steuern,
- und fertige Bilder in typischen Screen-Formaten (Website, Wallpaper, App-Background) exportieren lassen – ohne jegliche manuelle Pixelarbeit.
