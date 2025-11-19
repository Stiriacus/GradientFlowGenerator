# 1. High-Level Überblick

Ziel:
Eine PySide6-Desktop-App (Linux + Windows), die:

programmatisch „Dune-Backgrounds“ generiert (Simplex + FBM + Ridge + Domain Warping + Lighting),

eine moderne GUI im Stil „Gnome/Arch-Config-Tool“ hat,

volle Kontrolle über:

Farbpaletten & Gradient-Stops,

Noise-Layer & alle relevanten Parameter,

Auflösung & Export.

Große Blöcke:

core/ – Mathe & Rendering (Noise, FBM, Ridge, Domain Warping, Normals, Lighting, Gradient-Mapping).

model/ – Konfigurations-Objekte (Palette, Gradient, Layer, Projekt).

ui/ – PySide6 GUI (Fenster, Panels, Tabs, Previews).

workers/ – Render-Jobs in Hintergrund-Threads mit Zeit-Anzeige.

io/ – Speichern/Laden von Projekten & Paletten (JSON).

--

# 2. Projektstruktur (Dateien & Module)

Vorschlag: