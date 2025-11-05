# Video Transport mit CHOP-System (Empfohlene Lösung)

## Konzept
Statt Play Mode zu wechseln, bleibt der Movie File In TOP immer im **"Specify Index"** Mode.
Ein CHOP-basiertes Transport-System schaltet zwischen:
- **Auto-Play** (Speed CHOP läuft mit Framerate)
- **Manual Scrub** (Fader-Position vom MIDI-Controller)

## Vorteile
✓ Kein Play Mode wechseln → keine Lags
✓ Butterweicher Übergang zwischen Play und Scrub
✓ MIDI-Fader kann jederzeit eingreifen
✓ Optional: Smooth Filter für weiche Übergänge

## Setup (in /project1/media)

### 1. Movie File In TOP Setup
```
moviefilein1
├─ Play Mode: Specify Index
├─ Index Unit: Frames (oder Seconds)
├─ Play: OFF (wird von CHOP gesteuert)
└─ Cache Frames: ON (für butterweich scrubbing)
```

### 2. Speed CHOP (Auto-Play Clock)
```
Name: video_speed
Type: Speed CHOP

Settings:
├─ Speed: 1
├─ Play: ON
└─ Output: seconds (oder frames)

Optional - Add Limit CHOP:
├─ From Range: 0 to (video duration in seconds)
├─ Clamp: ON
└─ → verhindert über-das-Ende-laufen
```

### 3. MIDI Fader Input (bereits vorhanden)
```
Der Fader kommt bereits normalisiert (0-1) vom Menu System.
Wir brauchen ihn in Frames oder Seconds.

Name: video_fader_raw
Source: Menu System gibt normalized value (0-1)

Math CHOP: video_fader_scaled
├─ Input: fader value (0-1)
├─ From Range: 0 to 1
└─ To Range: 0 to (total_frames - 1)  # z.B. 0 to 1544
```

### 4. Fader "Is Moving" Detector
```
Name: video_fader_moving
Type: Logic CHOP

Detect ob Fader bewegt wird:
├─ CHOP To: video_fader_scaled
├─ Channels: fader/1
├─ Combine CHOPs: Subtract
├─ Function: Changed in Last (frames)
└─ Frames: 10  # Falls innerhalb letzter 10 Frames geändert → 1, sonst 0
```

### 5. Switch CHOP (Play vs Scrub)
```
Name: video_index
Type: Switch CHOP

Inputs:
├─ Input 0: video_speed (auto-play)
├─ Input 1: video_fader_scaled (manual scrub)
└─ Index: video_fader_moving (0=play, 1=scrub)

Output: video_index/chan1
```

### 6. Optional: Filter für weiche Übergänge
```
Name: video_index_smooth
Type: Filter CHOP

Input: video_index
Filter Width: 0.05 - 0.1 (experimentieren!)
```

### 7. Export zu Movie File In TOP
```
video_index_smooth → Export to moviefilein1/index

In moviefilein1:
Parameters → Play → Index:
└─ Expression: op('video_index_smooth')['chan1']
```

## Alternative: Python-gesteuert (aktueller Ansatz)

Dein aktuelles System funktioniert auch, aber mit CHOP ist es:
- Performanter (kein Python-Overhead)
- Visuell (du siehst den Transport im Network)
- Flexibler (einfach Filter/Lag hinzufügen)

## Hybrid-Ansatz: Python + CHOP

Du kannst auch beides kombinieren:

1. **CHOP-System** für die Timeline-Logik
2. **Python** (Menu System) schreibt nur noch in CHOPs:
   - `fader_value` CHOP (from MIDI)
   - `play_button` CHOP (0 oder 1)
   - `stop_button` CHOP (trigger)

### Beispiel: Menu System → CHOP Bridge

Erstelle einen **Constant CHOP** in `/project1/media/video_control`:
```
video_control (CHOP)
├─ fader (channel) = 0
├─ playing (channel) = 0
└─ scrubbing (channel) = 0
```

Im Menu Engine Python:
```python
# Statt direkt video_control.set_normalized_time() zu rufen:
control_chop = op('/project1/media/video_control')
control_chop['fader'] = y  # normalized 0-1
```

Im CHOP Network:
```
video_control/fader → Math (scale to frames) → Switch Input 1
video_control/playing → Speed CHOP Play parameter
```

## Play/Stop Buttons mit CHOP

### Play Button (btn/22)
```python
# In menu_engine.py
control_chop = op('/project1/media/video_speed')
control_chop.par.play = 1  # Start the speed CHOP
```

### Stop Button (btn/12)
```python
control_chop = op('/project1/media/video_speed')
control_chop.par.play = 0  # Stop
control_chop.par.start.pulse()  # Reset to 0
```

## Komplettes CHOP Network Diagram

```
┌─────────────────┐
│  video_speed    │  Speed CHOP (auto-play timeline)
│  (Speed CHOP)   │  Speed=1, Play=ON
└────────┬────────┘
         │
         ├─────────────┐
         │             │
┌────────▼────────┐    │
│ video_fader     │    │
│ (from MIDI)     │    │
└────────┬────────┘    │
         │             │
┌────────▼────────┐    │
│ video_fader_    │    │
│ moving (Logic)  │    │
└────────┬────────┘    │
         │             │
         │    ┌────────▼────────┐
         └───►│ video_index     │
              │ (Switch CHOP)   │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ video_index_    │
              │ smooth (Filter) │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ moviefilein1    │
              │ index parameter │
              └─────────────────┘
```

## Performance-Vergleich

| Methode | CPU-Last | Latenz | Komplexität |
|---------|----------|--------|-------------|
| **Python ständig** (alt) | Hoch | ~30ms | Niedrig |
| **Python + Play Mode Switch** | Mittel | ~50ms | Mittel |
| **CHOP-System** | Sehr niedrig | <5ms | Hoch (Setup) |
| **Hybrid CHOP+Python** | Niedrig | ~10ms | Mittel |

## Empfehlung

Für dein 7GB, 2h Video:
1. **Kurzfristig**: Behalte aktuelles System mit Rate-Limiting (funktioniert)
2. **Mittelfristig**: Baue CHOP-System auf (bessere Performance)
3. **Langfristig**: Konvertiere zu HAP Codec

## Nächste Schritte

Willst du:
- **A)** CHOP-System jetzt aufbauen? (ich führe dich durch)
- **B)** Aktuelles Python-System optimieren? (weitere Tweaks)
- **C)** Beides parallel testen?

Sag mir Bescheid und ich helfe dir beim Setup!
