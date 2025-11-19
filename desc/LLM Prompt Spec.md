# LLM Prompt Spec – Defaults & Detail Decisions

Dieses Dokument ergänzt **Problemstellung** und **Architektur**, sodass eine andere LLM damit **direkt lauffähige Lösungen implementieren** kann – ohne zu viel raten zu müssen.

Ziel: Du kannst diese Spezifikation + die Architektur-Beschreibung einfach an ein anderes LLM geben und erwarten, dass es dir sinnvollen Code (Python + PySide6) erzeugt.

---

## 1. Parameter-Defaults & sinnvolle Wertebereiche

Die folgenden Bereiche und Defaults orientieren sich an gängigen Praktiken für Noise/FBM/Rendering.

### 1.1 Simplex Noise / FBM / Ridge

**Alle Werte sind Vorschläge, an denen sich die Implementierung orientieren soll.**

#### Scale (frequency)

* `scale_x`: **Default** `1.5`, sinnvoller Bereich: `0.1` – `8.0`
* `scale_y`: **Default** `0.3` (für horizontale Dune-Streifen), Bereich: `0.05` – `4.0`

Interpretation:

* Kleinere Werte → größere, weichere Strukturen.
* Größere Werte → feinere, detailreiche Strukturen.

#### Octaves (FBM)

* `octaves`: **Default** `5`
* Bereich: `1` – `8`

Mehr Octaves → mehr Detail, aber höhere Rechenzeit.

#### Persistence

* `persistence`: **Default** `0.5`
* Bereich: `0.3` – `0.8`

Bestimmt, wie stark höhere Octaves (feinere Details) gewichtet werden.

#### Lacunarity

* `lacunarity`: **Default** `2.0`
* Bereich: `1.8` – `3.0`

Bestimmt die Frequenzsteigerung pro Octave.

#### Ridge Power

* `ridge_power`: **Default** `2.0`
* Bereich: `1.0` – `4.0`

Wird typischerweise in der Form `(1 - abs(noise)) ** ridge_power` verwendet:

* 1.0 → weicher, weniger harte Grate
* 3–4 → sehr scharfe Dünenkämme

#### Height Power (global shaping)

* `height_power`: **Default** `1.7`
* Bereich: `1.0` – `3.0`

Wird auf die gesamte Heightmap angewendet (`height ** height_power`):

* > 1 → verstärkt Höhen/Spitzen, drückt mittlere Werte runter → mehr Kontrast

#### Amplitude (Layer-Gewichtung)

* `amplitude`: **Default** `1.0` für `BASE`, `0.4` für `DETAIL`, `0.5` für `WARP`
* Bereich: `0.0` – `2.0`

Wird verwendet, um die jeweiligen Layer zueinander zu gewichten.

#### Seeds

* `seed_global`: Default `42`
* Layer-spezifische Seeds: Default `seed_global + layer_index`

Eine spätere LLM sollte Seeds explizit in die Konfiguration aufnehmen, damit Ergebnisse reproduzierbar sind.

---

### 1.2 Domain Warping

Für **Warp-Layer** (LayerType = `"warp"`):

* `scale_x`: **Default** `0.2` (niedrige Frequenz)
* `scale_y`: **Default** `0.05`
* `octaves`: **Default** `2`
* `amplitude`: **Default** `0.5` (wie stark die Koordinaten verzerrt werden)

Koordinatenverschiebung z.B.:

```python
wx = warp_noise(x * scale_x, y * scale_y)
wy = warp_noise((x + 1000) * scale_x, (y + 1000) * scale_y)

x_prime = x + wx * amplitude
y_prime = y + wy * amplitude
```

---

### 1.3 Lighting Defaults

**Licht kommt standardmäßig von oben links**, leicht erhöht.

* `light_azimuth_deg`: **Default** `45.0` (0° = rechts, 90° = oben – kann frei definiert werden, aber bitte konsistent)
* `light_elevation_deg`: **Default** `60.0`
* `intensity`: **Default** `0.8`, Bereich `0.2` – `1.0`

Konvertierung in einen Lichtvektor (Beispiel-Logik für die Implementierung):

```python
import math

az = math.radians(light_azimuth_deg)
el = math.radians(light_elevation_deg)

lx = math.cos(el) * math.cos(az)
ly = math.cos(el) * math.sin(az)
lz = math.sin(el)

light_vec = (lx, ly, lz)
```

Normals kommen z.B. aus:

```python
# height: 2D array
pad = np.pad(height, 1, mode="edge")
dx = pad[1:-1, 2:] - pad[1:-1, :-2]
dy = pad[2:, 1:-1] - pad[:-2, 1:-1]

nx = -dx
ny = -dy
nz = np.ones_like(height)

length = np.sqrt(nx*nx + ny*ny + nz*nz) + 1e-8
nx /= length
ny /= length
nz /= length

shade = np.clip(nx*lx + ny*ly + nz*lz, 0.0, 1.0)
```

**Helligkeitsfaktor** kann dann z.B. sein:

```python
brightness = 0.4 + 0.6 * shade  # 0.4–1.0
```

---

### 1.4 Gradient Defaults

* Maximal **6 Gradient-Stops**.
* Default-Gradient (für Frost/Dune-Style), wenn nichts anderes angegeben:

```jsonc
{
  "angle_deg": 20.0,
  "stops": [
    { "position": 0.0, "color": "#000814", "opacity": 1.0 },
    { "position": 0.3, "color": "#0a1628", "opacity": 1.0 },
    { "position": 0.6, "color": "#1a2e45", "opacity": 1.0 },
    { "position": 1.0, "color": "#caf0f8", "opacity": 1.0 }
  ]
}
```

* Angle-Bereich: `0` – `360`°. Default: `20`°.
* Stops sollen **automatisch nach Position sortiert** werden.

Gradient-Mapping:

* LLM kann `angle_deg` so interpretieren, dass:

  * `angle = 0°`: Gradient läuft von links nach rechts.
  * `90°`: von unten nach oben.
  * etc.
* Normierte Koordinate `t` kann z.B. per Projektion auf die Gradient-Achse berechnet werden.

---

## 2. Bibliotheken & Implementierungs-Entscheidungen

### 2.1 Erlaubte & gewünschte Libraries

Die LLM darf für den **Kern-Renderer** folgende Libraries verwenden:

* `numpy` – für Arrays, Heightmaps, Vektoroperationen
* `Pillow (PIL)` – für Bild-Erzeugung & Export (PNG)
* Simplex Noise:

  * Entweder eine eigene Simplex-Implementierung
  * **oder** eine externe Library wie `opensimplex`

Für die **GUI**:

* **PySide6** als GUI-Framework (modern, Qt-basiert)
* Optional Qt-Styles für Dark-Theme (z.B. via Palette oder Stylesheet)

### 2.2 Bildausgabe

* Standard-Output-Format: **PNG**.
* Export-Auflösungen:

  * 1920×1080 (16:9)
  * 1280×720 (16:9)
  * 1080×1920 (Vertikal, 16:9)
  * 1024×768 (4:3)
  * Custom (frei definierbar)

Preview-Auflösungen:

* Final-Preview: **960×540**
* Noise-Preview: **480×270**

---

## 3. Beispiel-ProjectConfig (JSON)

Diese Beispiel-Konfiguration kann **1:1** als Referenz genutzt werden.
Eine LLM sollte sich an diesem Format orientieren, wenn sie Projekt-Save/Load-Funktionen implementiert.

```json
{
  "palette": {
    "name": "frost",
    "colors": [
      "#000814",
      "#0a1628",
      "#1a2e45",
      "#caf0f8",
      "#64ffda",
      "#4ecdc4"
    ]
  },
  "gradient": {
    "angle_deg": 20.0,
    "stops": [
      { "position": 0.0, "color": "#000814", "opacity": 1.0 },
      { "position": 0.3, "color": "#0a1628", "opacity": 1.0 },
      { "position": 0.6, "color": "#1a2e45", "opacity": 1.0 },
      { "position": 1.0, "color": "#caf0f8", "opacity": 1.0 }
    ]
  },
  "noise_layers": [
    {
      "layer_type": "warp",
      "enabled": true,
      "seed": 42,
      "scale_x": 0.2,
      "scale_y": 0.05,
      "octaves": 2,
      "persistence": 0.5,
      "lacunarity": 2.0,
      "ridge_power": 1.0,
      "height_power": 1.0,
      "amplitude": 0.5
    },
    {
      "layer_type": "base",
      "enabled": true,
      "seed": 43,
      "scale_x": 1.5,
      "scale_y": 0.3,
      "octaves": 5,
      "persistence": 0.5,
      "lacunarity": 2.0,
      "ridge_power": 2.0,
      "height_power": 1.7,
      "amplitude": 1.0
    },
    {
      "layer_type": "detail",
      "enabled": true,
      "seed": 44,
      "scale_x": 6.0,
      "scale_y": 2.0,
      "octaves": 3,
      "persistence": 0.5,
      "lacunarity": 2.0,
      "ridge_power": 2.0,
      "height_power": 1.3,
      "amplitude": 0.4
    }
  ],
  "lighting": {
    "light_azimuth_deg": 45.0,
    "light_elevation_deg": 60.0,
    "intensity": 0.8
  },
  "preview_width": 960,
  "preview_height": 540,
  "noise_preview_width": 480,
  "noise_preview_height": 270,
  "seed_global": 42
}
```

Eine LLM sollte:

* dieses Format beim Implementieren von `ProjectConfig` berücksichtigen,
* `save_project` und `load_project` exakt kompatibel dazu bauen,
* Standardwerte aus diesem JSON übernehmen, falls keine Werte gesetzt sind.

---

## 4. GUI-Details (PySide6, Verhalten & Stil)

### 4.1 Stil & Sprache

* **Dark Theme**:

  * GUI soll ein dunkles Theme verwenden (Qt-Palette oder Stylesheet).
* **Sprache**:

  * Alle Labels, Buttons und Texte **auf Englisch**.
* **Layout**:

  * **Sidebar links** mit Navigation (Tabs oder Buttons) für:

    * Global (Palette + Gradient)
    * Noise
    * Lighting
    * Export
  * **Tabs oben** (innerhalb bestimmter Panels) sind erlaubt, z.B. für Noise-Preview oder Layer-Details.

### 4.2 Preview-Verhalten

* Previews sollen **nicht automatisch** bei jedem Slider-Change neu rendern.
* Stattdessen gibt es einen **"Generate"-Button**:

  * Klick → startet einen Renderjob im Hintergrund.
  * Währenddessen wird in der Statusbar die **verstrichene Zeit** angezeigt:

    * z.B. `Rendering… 1.2s` → `Rendering… 5.8s`
  * Keine ETA / keine Vorhersage, wann es fertig ist.

### 4.3 Previews (Größe & Anordnung)

* Final-Preview:

  * Größe: `960×540`
  * Position: **rechts oben** im Hauptfenster.

* Noise-Preview:

  * Größe: `480×270`
  * Position: **unterhalb** der Auswahlmöglichkeiten (z.B. unter Noise-Panel oder zentral unter dem Control-Bereich).
  * Darf Tabs verwenden, z.B.:

    * `Base`
    * `Detail`
    * `Combined Heightmap`

### 4.4 Export

* Export-Panel soll ermöglichen:

  * Auswahl eines Auflösungs-Presets (z.B. Dropdown).
  * Umschalten von `Landscape` / `Portrait`:

    * Implementation: Breite/Höhe tauschen.
  * Eingabe eigener Auflösung (Custom-Width, Custom-Height).
  * Export-Button, der das aktuell angezeigte Setup mit gewünschter Auflösung als **PNG** rendert und speichert.

---

## 5. Wie dieses Dokument mit der Architektur zusammenspielt

Dieses Dokument ist als Ergänzung zu:

* **Problemstellung / Zielbeschreibung (README)**
* **Architektur-Übersicht (Ordnerstruktur, Klassen, Render-Pipeline, GUI-Konzept)**

gedacht.

Eine andere LLM kann mit diesen drei Bausteinen:

1. Das Datenmodell (`ProjectConfig`, `NoiseLayerConfig`, etc.) korrekt definieren.
2. Eine konsistente Render-Pipeline implementieren (Simplex + FBM + Ridge + Domain Warping + Lighting + Gradient Mapping).
3. Eine PySide6-GUI mit:

   * Dark Theme,
   * Sidebar links,
   * Previews in korrekten Größen,
   * Generate-Button + Elapsed-Time-Anzeige,
   * Export als PNG,
   * Save/Load von Projekt-JSON.

Damit ist der Input so vollständig, dass eine LLM **ohne weitere Rückfragen** eine erste, brauchbare Version deines Tools erzeugen kann, die du dann iterativ verfeinern kannst.
