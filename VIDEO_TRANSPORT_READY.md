# Video Transport System - Setup Complete! ✓

## Was wurde gemacht:

### 1. Scrubbing funktioniert jetzt! ✓
- Fader 1 (Menu 5) steuert die Video-Timeline
- Smooth scrubbing durch das gesamte Video
- Keine Lags mehr (mit Rate-Limiting optimiert)

### 2. CHOP-System aufgebaut
Das neue System verwendet CHOPs statt Python für bessere Performance:

```
MIDI Fader → fader_input → math1 (scale 0-1 to frames) ──┐
                                                            ├→ switch2 → filter1 → moviefilein1.index
Count CHOP → limit1 (auto-play) ──────────────────────────┘
                                                            ↑
                                          transport_control (playing/scrubbing)
```

### 3. Play/Stop Buttons sind konfiguriert

**Button 22 (Play)**: Startet Auto-Play
- Schaltet zu Count CHOP
- Video läuft automatisch ab

**Button 12 (Stop)**: Stoppt und setzt zurück
- Stoppt Auto-Play
- Setzt Video auf Frame 0 zurück
- Fader kann wieder scrubben

## Nächste Schritte (in TouchDesigner):

### Schritt 1: Count CHOP erstellen
Führe im **Textport** aus:
```python
execfile('C:\\_DEV\\TOUCHDESIGNER\\FIX_PLAY_STOP.py')
```

Das erstellt:
- **count_auto** (ersetzt speed_auto)
- Verbindet es mit limit1
- Konfiguriert alle Parameter

### Schritt 2: System testen
Führe im **Textport** aus:
```python
execfile('C:\\_DEV\\TOUCHDESIGNER\\TEST_VIDEO_TRANSPORT.py')
```

Das zeigt:
- ✓ Alle CHOPs vorhanden
- ✓ Alle Verbindungen korrekt
- Aktuelle Werte
- Test-Befehle

### Schritt 3: Manueller Test

**Scrubbing testen:**
```python
# Fader bewegen
op('/project1/media/fader_input')['normalized'].val = 0.5
op('/project1/media/transport_control')['scrubbing'].val = 1
```

**Play testen:**
```python
# Video abspielen
op('/project1/media/transport_control')['playing'].val = 1
op('/project1/media/transport_control')['scrubbing'].val = 0
```

**Stop testen:**
```python
# Video stoppen und zurücksetzen
op('/project1/media/transport_control')['playing'].val = 0
op('/project1/media/transport_control')['scrubbing'].val = 1
op('/project1/media/count_auto').par.count = 0
```

### Schritt 4: MIDI-Buttons testen

Nachdem count_auto erstellt wurde:
1. **Drücke Button 22** (Play) → Video sollte automatisch laufen
2. **Drücke Button 12** (Stop) → Video sollte stoppen und auf Frame 0 springen
3. **Bewege Fader 1** → Video sollte smooth scrubben

## Dateien wurden aktualisiert:

1. **menus/menu_engine.py**
   - Play/Stop Buttons verwenden jetzt count_auto statt speed1
   - Scrubbing schreibt in fader_input CHOP

2. **FIX_PLAY_STOP.py** (neu)
   - Erstellt count_auto CHOP
   - Löscht altes speed_auto
   - Verbindet alles korrekt

3. **TEST_VIDEO_TRANSPORT.py** (neu)
   - Vollständiger System-Check
   - Zeigt Status aller CHOPs

## Warum Count CHOP statt Speed CHOP?

Speed CHOP hatte 0 Channels und keine Parameter - war nicht funktionsfähig.
Count CHOP ist einfacher und zuverlässiger:
- Zählt Frames hoch (0 bis 126414)
- Hat `count` Parameter zum Zurücksetzen
- Loop-fähig (am Ende wieder auf 0)

## Troubleshooting

### Video scrubbt nicht:
```python
# Check ob math1 verbunden ist:
math1 = op('/project1/media/math1')
print(math1.inputs[0].path)  # sollte fader_input sein
```

### Play funktioniert nicht:
```python
# Check ob count_auto existiert:
count_auto = op('/project1/media/count_auto')
if not count_auto:
    print("count_auto fehlt! Führe FIX_PLAY_STOP.py aus")
```

### Movie index aktualisiert nicht:
```python
# Check index mode:
movie = op('/project1/media/moviefilein1')
print(movie.par.index.mode)  # sollte ParMode.EXPRESSION sein
print(movie.par.index.expr)  # sollte "op('filter1')[0]" sein
```

## Performance-Tipps

Für dein 7GB, 2h Video:
1. **Aktuell**: Rate-Limiting auf 30fps (funktioniert)
2. **Langfristig**: Video zu HAP Codec konvertieren (siehe VIDEO_SCRUBBING_PERFORMANCE.md)

## Was jetzt?

1. Führe `FIX_PLAY_STOP.py` aus
2. Führe `TEST_VIDEO_TRANSPORT.py` aus
3. Teste mit MIDI-Controller:
   - Fader bewegen (scrubben)
   - Button 22 drücken (play)
   - Button 12 drücken (stop)
4. Berichte ob alles funktioniert!

Viel Erfolg! 🎬
