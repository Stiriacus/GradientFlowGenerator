# Frost Dune Background Generator – Architektur

## 1. Zielbild

Eine moderne Desktop-App (Python + PySide6), die auf Linux und Windows läuft und programmatisch abstrakte "Dune"-Hintergründe erzeugt – basierend auf Simplex Noise, FBM, Ridge-Formung, Domain Warping, Normals und Lighting.

GUI-Stil: eher modern/minimal wie Gnome/Arch-Konfigurationstools.

---

## 2. High-Level Architektur

### 2.1 Komponenten

* **core/**

  * Implementierung der mathematischen und grafischen Grundlagen:

    * Simplex Noise, FBM, Ridge-Formung, Domain Warping
    * Heightmap-Erzeugung
    * Normalenberechnung & Lighting
    * Gradient-Mapping (Farben & Opazität)

* **model/**

  * Datenmodelle für:

    * Farbpaletten
    * Gradient-Stops & Gradient-Konfiguration
    * Noise-Layer-Konfigurationen
    * Lighting-Konfiguration
    * Projekt-Konfiguration (alles zusammen, speicher-/ladbar)

* **ui/** (PySide6)

  * Hauptfenster & Layout
  * Panels für:

    * Palette & Gradient
    * Noise-Layer-Konfiguration
    * Lighting
    * Export
  * Preview-Bereiche für:

    * Final-Preview (960×540)
    * Noise-Preview (480×270)

* **workers/**

  * Hintergrund-Renderjobs (QThread/QRunnable) mit:

    * Zeit-Anzeige (Elapsed Time, keine ETA)
    * Abbrechen-Funktion

* **io/**

  * Speichern/Laden von Projekten & Paletten im JSON-Format.

---

## 3. Projektstruktur

```text
project_root/
  README.md
  pyproject.toml / requirements.txt

  core/
    noise.py            # Simplex, FBM, Ridge, Domain Warping
    heightmap.py        # Heightmap-Build aus Layern
    lighting.py         # Normals + Licht/Schattierung
    gradient.py         # GradientStops + Farb-/Opacity-Mapping
    renderer.py         # Orchestriert heightmap -> farbiges Bild

  model/
    palette.py          # Farbpaletten & Favoriten
    gradient_model.py   # GradientStop & GradientConfig
    noise_layer.py      # NoiseLayerConfig (Base/Detail/Warp)
    project_config.py   # ProjectConfig mit allem zusammen

  ui/
    main_window.py      # Hauptfenster
    gradient_panel.py   # Gradient-Editor (Stops, Winkel)
    palette_panel.py    # Paletten-Auswahl & -Edit
    noise_panel.py      # Tabs / Editor für Noise-Layer
    lighting_panel.py   # Licht-Parameter
    preview_panel.py    # Final + Noise-Preview
    export_panel.py     # Export-Optionen

  workers/
    render_worker.py    # Hintergrund-Renderer mit Progress-Signalen

  io/
    project_io.py       # Save/Load ProjectConfig (JSON)
    palette_io.py       # Save/Load Palette (JSON)
```

---

## 4. Datenmodell (model/)

### 4.1 Gradient & Palette

**GradientStop** (max. 6 Stops):

* `position: float` (0.0–1.0, automatisch sortiert)
* `color: str` (Hex, z.B. `#0a1628`)
* `opacity: float` (0.0–1.0)

```python
from dataclasses import dataclass
from typing import List

@dataclass
class GradientStop:
    position: float  # 0.0 – 1.0
    color: str       # "#rrggbb"
    opacity: float   # 0.0 – 1.0

@dataclass
class GradientConfig:
    stops: List[GradientStop]
    angle_deg: float  # 0–360°
```

**Palette**:

```python
@dataclass
class Palette:
    name: str
    colors: List[str]  # Hex-Farben
```

Paletten-Favoriten sollen als JSON schnell speicher- und ladbar sein.

---

### 4.2 Noise-Layer & Lighting

**NoiseLayerType** (z.B. Enum oder String):

* `"base"`   – Grund-Heightmap (FBM Ridge)
* `"detail"` – zusätzliche feine Rillen
* `"warp"`   – Domain-Warping-Noise, der die Koordinaten verzerrt

```python
from enum import Enum
from dataclasses import dataclass
from typing import List

class NoiseLayerType(str, Enum):
    BASE = "base"
    DETAIL = "detail"
    WARP = "warp"

@dataclass
class NoiseLayerConfig:
    layer_type: NoiseLayerType
    enabled: bool
    seed: int
    scale_x: float
    scale_y: float
    octaves: int
    persistence: float
    lacunarity: float
    ridge_power: float   # v.a. für BASE/DETAIL relevant
    height_power: float  # optionale zusätzliche Formung
    amplitude: float     # Gewicht im Gesamtsignal
```

**LightingConfig**:

```python
@dataclass
class LightingConfig:
    light_azimuth_deg: float   # 0–360° (Richtung in XY-Ebene)
    light_elevation_deg: float # 0–90° (Winkel über der Fläche)
    intensity: float           # 0–1
```

---

### 4.3 ProjectConfig

Das zentrale Objekt, das alles zusammenhält und speicher-/ladbar ist.

```python
@dataclass
class ProjectConfig:
    palette: Palette
    gradient: GradientConfig
    noise_layers: List[NoiseLayerConfig]
    lighting: LightingConfig

    preview_width: int = 960
    preview_height: int = 540
    noise_preview_width: int = 480
    noise_preview_height: int = 270

    seed_global: int = 42  # optionaler globaler Seed
```

Damit ist ein Setup (Palette, Gradient, Noise-Layer, Licht, Auflösungen, Seeds) als JSON vollständig reproduzierbar.

---

## 5. Render-Pipeline (core/)

### 5.1 Noise (Simplex, FBM, Ridge, Domain Warping)

In `core/noise.py`:

* **Simplex Noise 2D** als Basis.
* **FBM Ridge**:

  * Mehrere Octaves von Simplex-Noise.
  * Pro Oktave: `1 - |noise|` → Ridge-Struktur.
  * Mit `ridge_power` exponentiell geschärft.
  * summiert mit `persistence` und `lacunarity`.
* **Domain Warping**:

  * Ein dedizierter `warp`-Layer modifiziert die Koordinaten:

    * `(x', y') = (x + wx, y + wy)`
    * `wx`, `wy` stammen aus einem niedrig-frequenten Simplex/FBM.

### 5.2 Heightmap-Build (`core/heightmap.py`)

1. Erzeuge ein 2D-Gitter für die Zielauflösung.
2. Wende `warp`-Layer auf die Koordinaten an (Domain Warping).
3. Berechne `BASE`- und `DETAIL`-Layer als FBM-Ridge und addiere sie gewichtet.
4. Normiere die Heightmap nach `[0, 1]` und wende ggf. `height_power` an.

Die **Noise-Preview (480×270)** zeigt z.B. in Tabs:

* Base-Heightmap
* Detail-Heightmap
* finale kombinierte Heightmap

### 5.3 Lighting (`core/lighting.py`)

* Berechne Normals via Finite Differences:

  * `dx = h[x+1] - h[x-1]`
  * `dy = h[y+1] - h[y-1]`
  * Normal ~ `(-dx, -dy, 1)` → normalisieren.
* Wandle `light_azimuth_deg` & `light_elevation_deg` in einen 3D-Lichtvektor um.
* Dot-Produkt `n · light` → `shade` (0–1).
* moduliere optional mit `intensity`.

### 5.4 Gradient Mapping (`core/gradient.py`)

* Berechne für jeden Pixel aus `(x, y)` einen **Gradient-Parameter `t` (0–1)** entlang eines Winkels `angle_deg`.
* Nutze `GradientConfig.stops` (max. 6), um die Farbe per Interpolation zwischen Stops zu bestimmen (inkl. Opacity).
* Kombiniere:

  * `height` (Höhe)
  * `shade` (Licht)
  * `gradient` (Material/Farbe)

Beispiel-Idee:

* `base_color = gradient(t)`
* `brightness_factor` = Funktion aus `height` und `shade`.
* `final_color = base_color * brightness_factor`.

### 5.5 Renderer (`core/renderer.py`)

* Funktion z.B. `render(project_config: ProjectConfig, width: int, height: int) -> Image`.
* Schritte:

  1. Heightmap aus `noise_layers` erzeugen (inkl. Domain Warping).
  2. Lighting berechnen (Normals + Licht).
  3. Gradient-Mapping/Farbgebung mit `gradient` & `palette`.
  4. `PIL.Image` zurückgeben.

Die Renderer-Funktion wird sowohl für die **Preview** als auch für den **Export** genutzt (unterschiedliche Auflösungen).

---

## 6. GUI-Architektur (PySide6, ui/)

### 6.1 Layout

**MainWindow** (z.B. `QMainWindow`):

* **Links**: vertikale Steuerleiste (Tabs oder Seitenleiste):

  * Tab "Global": Palette- und Gradient-Einstellungen.
  * Tab "Noise": Layer-Editor (Base/Detail/Warp), pro Layer ein eigener Bereich.
  * Tab "Lighting": Licht-Richtung und Intensität.
  * Tab "Export": Ausgabeauflösungen & Export-Button.

* **Rechts**:

  * **oben**: Final-Preview (960×540) als `QLabel`/`QGraphicsView` mit Bild.
  * **unten**: Noise-Preview (480×270) mit Tabs (z.B. Base/Detail/Combined).

* **Statusbar**:

  * Text: z.B. `Rendering... 3.2s`
  * ggf. ein Cancel-Button oder Icon (Renderjob abbrechen).

### 6.2 Panels

**GradientPanel** (`gradient_panel.py`):

* Liste/Tabelle für max. 6 Gradient-Stops:

  * Position (Slider + Textfeld 0–1)
  * Farbe (Color-Picker + Hex-Input)
  * Opacity (Slider + Textfeld 0–1)
* Gradient-Winkel (0–360°) als Slider + Textfeld.
* Kleine Vorschau-Leiste (Mini-Gradient) zur visuellen Kontrolle.

**PalettePanel** (`palette_panel.py`):

* Liste der aktiven Farben der Palette.
* Buttons:

  * `+ Color` (Farbe hinzufügen über Color-Picker/Hex)
  * `Remove` (Farbe entfernen)
  * `Save Palette`
  * `Load Palette`

**NoisePanel** (`noise_panel.py`):

* Links: Liste der Noise-Layer (`QListWidget` oder ähnliche Anzeige):

  * Einträge z.B. `Base`, `Detail 1`, `Warp 1`.
  * Ein/Aus-Schalter je Layer.
* Rechts: Detail-Editor für den gewählten Layer:

  * Seed (Textfeld/Spinbox)
  * scale_x, scale_y (Slider + Textfeld)
  * octaves, persistence, lacunarity
  * ridge_power, height_power
  * amplitude

**LightingPanel** (`lighting_panel.py`):

* Azimuth (0–360°) – Slider + Textfeld
* Elevation (0–90°) – Slider + Textfeld
* Intensity (0–1) – Slider + Textfeld

**ExportPanel** (`export_panel.py`):

* Dropdown mit Auflösungs-Presets:

  * 1920×1080 (16:9)
  * 1280×720 (16:9)
  * 1080×1920 (Portrait)
  * 1024×768 (4:3)
* Radiobuttons "Landscape" / "Portrait" (tauscht Breite und Höhe).
* Eingabefelder für Custom Width/Height.
* Export-Button: generiert **PNG** im gewählten Format.

**PreviewPanel** (`preview_panel.py`):

* Anzeige der Final-Preview (960×540).
* Anzeige der Noise-Preview (480×270) mit Unter-Tabs („Base“, „Detail“, „Combined Heightmap“).

---

## 7. Render-Worker & Zeit-Anzeige (workers/)

In `workers/render_worker.py`:

* Worker als `QThread` oder `QRunnable`:

  * erhält eine **Kopie** von `ProjectConfig` + Zielauflösung.
  * führt Rendering im Hintergrund aus.
  * sendet Qt-Signale:

    * `started()`
    * `progress(elapsed_seconds: float)` – optional periodisch
    * `finished(final_image, noise_previews, total_time)`
    * `canceled()`

Im MainWindow:

* Beim Start:

  * Status: "Rendering... 0.0s"
  * `QTimer` zählt `elapsed_time` hoch, solange der Worker läuft.
* Kein ETA, nur **verstrichene Zeit**.
* Cancel-Button:

  * setzt ein Flag im Worker (`should_cancel = True`),
  * Worker prüft dieses Flag während der Berechnung (z.B. pro Zeile/Block).

---

## 8. Speichern & Laden (io/)

**Projekt-Konfiguration** (`project_io.py`):

* `save_project(config: ProjectConfig, path: str)`

  * wandelt Dataclasses in Dict um (`asdict()`),
  * speichert als JSON.

* `load_project(path: str) -> ProjectConfig`

  * liest JSON,
  * baut Projekt-Konfiguration wieder als Dataclasses zusammen.

**Paletten** (`palette_io.py`):

* `save_palette(palette: Palette, path: str)`
* `load_palette(path: str) -> Palette`
* Optional: eine zentrale `palettes.json` mit mehreren Favoriten.

Damit können komplette Setups (inkl. Seed, Winkel, Layern, Gradient, Licht) gespeichert, wieder geladen und exakt reproduziert werden.

---

## 9. Zusammenfassung

* **Ziel**: Eine PySide6-GUI-App, die voll kontrollierbare, programmatische "Dune"-Hintergründe generiert.
* **Rendering** basiert auf:

  * Simplex Noise,
  * Ridge-FBM,
  * Domain Warping,
  * Heightmap + Lighting,
  * Gradient-Mapping mit max. 6 Stops und frei einstellbarem Winkel.
* **GUI** bietet:

  * Kompletten Zugriff auf alle wichtigen Parameter via Slider + Textfelder,
  * Previews in reduzierter Auflösung (960×540 und 480×270),
  * Zeit-Anzeige während des Renderings,
  * Export in PNG mit verschiedenen Auflösungen und Orientierungen,
  * Projekt- und Paletten-Speicherung als JSON.

Diese Architektur dient als solide Basis, um Schritt für Schritt die Implementierung aufzubauen – von den Kern-Funktionen (Noise & Rendering) bis zur vollständigen, modernen Desktop-GUI.
