# VPlayer Quick Start Guide

## 🚀 Automatische Installation (5 Minuten)

### Schritt 1: Projekt öffnen
```bash
# Öffne in TouchDesigner:
c:\_DEV\TOUCHDESIGNER\MIDICRAFT_to_EOS_1.1.toe
```

### Schritt 2: Master Setup ausführen
```python
# In TouchDesigner Textport (Alt+T):
exec(open('c:\\_DEV\\TOUCHDESIGNER\\SETUP_VPLAYER.py').read())

# Warte 1-2 Minuten für automatischen Build
# ✓ Erstellt /project1/media/vplayer
# ✓ Konfiguriert OSC In
# ✓ Integriert LED Feedback
# ✓ Validiert alle Komponenten
```

### Schritt 3: Video laden
1. Navigate: `/project1/media/vplayer/moviefilein1`
2. Parameter `File` → Deine Videodatei wählen
3. Video sollte im Viewer erscheinen

### Schritt 4: Eos OSC konfigurieren
**Auf Eos Konsole:**
- Setup → System → Show Control → OSC
- OSC TX IP: `[Deine TD Computer IP]`
- OSC TX Port: `7001`
- Enable: `Send Feedback` ✅

**Test:**
```python
# In TD Textport - sollte Eos Messages zeigen:
# Drücke GO auf Eos, dann sollte erscheinen:
# [eos_event] Pending: 1/1
# [eos_event] No marker for 1/1, continuing playback
```

### Schritt 5: MIDI testen (Menu 5)
**Auf MIDICRAFT ENC:**
- Drücke Menu Button 5
- **Fader 1** bewegen → Video Position scrubben
- **Fader 2** bewegen → Geschwindigkeit ändern (0.5x - 2.0x)
- **Fader 3** bewegen → Lautstärke ändern

---

## 🎬 Workflow

### A. Marker aufnehmen (RECORD Mode)

```
1. Menu 5 aktivieren
2. GO Langdruck (~0.7s) → LED blinkt grün (RECORD)
3. Video zu gewünschter Position scrubben (Fader 1)
4. Eos GO drücken → Zeigt Pending Cue (z.B. "1/23")
5. GO kurz drücken → Marker gesetzt!
6. Wiederholen für alle Cues
7. GO Langdruck → Zurück zu FOLLOW (LED solid)
```

**Marker prüfen:**
```python
# In TD Textport:
op('/project1/media/vplayer/markers').numRows
# Zeigt Anzahl Marker (inkl. Header)
```

### B. Performance (FOLLOW Mode)

```
1. Menu 5 aktiv, FOLLOW Mode (LED grün solid)
2. Eos GO drücken
   → Video springt automatisch zu Marker
   → Textport zeigt: [eos_event] JUMP: 1/23 -> 45.2s
3. Fader für Live-Anpassungen nutzen
4. LED zeigt Status:
   - Dunkelgrün = Idle (keine Fahrt)
   - Hellgrün = Fahrt läuft
```

---

## 🔧 Schnelltests

### Test 1: RECORD Blink
```python
op('/project1/media/vplayer/state')['mode'] = 1
# → LED sollte grün blinken (2 Hz)
```

### Test 2: FOLLOW Idle
```python
op('/project1/media/vplayer/state')['mode'] = 0
op('/project1/media/vplayer/eos_state')['progress'] = 0
# → LED sollte dunkelgrün sein
```

### Test 3: FOLLOW Fahrt
```python
op('/project1/media/vplayer/state')['mode'] = 0
op('/project1/media/vplayer/eos_state')['progress'] = 0.5
# → LED sollte hellgrün sein
```

### Test 4: Marker setzen (manuell)
```python
markers = op('/project1/media/vplayer/markers')
markers.appendRow(['1/23', '45.2', 'Cue 1/23'])
# → Neuer Marker in Tabelle
```

### Test 5: OSC Empfang prüfen
```python
oscin = op('/project1/io/oscin_eos')
oscin.par.active  # Sollte 1 sein (aktiv)

# Eos GO drücken, dann Textport checken für:
# [eos_event] messages
```

---

## 📋 Cheat Sheet

### MIDI Mapping (Menu 5)
| Control | MIDI | Funktion |
|---------|------|----------|
| Fader 1 | CC 16/48 | Scrub (0-1) |
| Fader 2 | CC 17/49 | Speed (0.5-2.0x) |
| Fader 3 | CC 18/50 | Volume (0-1) |
| Button 21 (GO) | Note 26 | Eos GO (kurz) / Mode Toggle (lang) |
| Button 11 (STOP) | Note 21 | Eos STOP |

### Modi
| Mode | LED | GO kurz | BACK kurz | GO lang |
|------|-----|---------|-----------|---------|
| FOLLOW (0) | Solid grün | Eos GO (Video Jump) | Eos BACK | → RECORD |
| RECORD (1) | Blink grün | Marker setzen | Marker löschen | → FOLLOW |

### OSC Paths (von Eos)
```
/eos/out/active/cue/<list>/<cue>   → Video Jump
/eos/out/pending/cue/<list>/<cue>  → RECORD Target
/eos/out/active/cue (Float)        → Progress (LED)
```

### Wichtige Operators
```
/project1/media/vplayer/state          → mode, speed, volume
/project1/media/vplayer/eos_state      → active_cue, pending_cue, progress
/project1/media/vplayer/markers        → Marker Tabelle
/project1/media/vplayer/moviefilein1   → Video TOP
/project1/media/vplayer/led_go_out     → LED Wert (Button 21)
```

---

## 🐛 Troubleshooting

### Problem: Fader reagieren nicht
**Lösung:**
```python
# Prüfe aktives Menu
op('/project1').fetch('ACTIVE_MENU')
# Sollte 5 sein

# Falls nicht, auf MIDICRAFT ENC Button 5 drücken
```

### Problem: Video springt nicht bei Eos GO
**Checkliste:**
1. Marker für diese Cue existiert? → `/project1/media/vplayer/markers` prüfen
2. FOLLOW Mode aktiv? → `state['mode']` sollte 0 sein
3. OSC empfängt? → Textport für `[eos_event]` Messages prüfen
4. Netzwerk OK? → `ping [Eos IP]` in CMD

**Debug:**
```python
# Manuell OSC Event simulieren
handler = op('/project1/media/vplayer/osc_event_handler')
handler.module.on_active_cue_change(1, 23)  # List 1, Cue 23
```

### Problem: LED blinkt nicht in RECORD
```python
# Prüfe LED Output
op('/project1/media/vplayer/led_go_out')['btn_21'].eval()
# Sollte zwischen 0 und 100 wechseln

# Prüfe Blink LFO
op('/project1/media/vplayer/led_blink_lfo')[0].eval()
# Sollte zwischen -1 und 1 oszillieren
```

### Problem: Kein Audio
```python
# Prüfe Audio Device
audioout = op('/project1/media/vplayer/audiodeviceout1')
audioout.par.device  # Sollte valides Audio Device zeigen

# Prüfe Volume
audioout.par.volume.eval()  # Sollte > 0 sein
```

---

## 📚 Weiterführende Docs

- **[VPLAYER_README.md](VPLAYER_README.md)** - Vollständige Übersicht
- **[VPLAYER_BUILD_GUIDE.md](VPLAYER_BUILD_GUIDE.md)** - Detaillierte Build-Anleitung
- **[OSC_IN_GUIDE.md](OSC_IN_GUIDE.md)** - OSC Konfiguration
- **[LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md)** - LED Integration

---

## 🆘 Support

**Validation erneut laufen lassen:**
```python
exec(open('c:\\_DEV\\TOUCHDESIGNER\\validate_vplayer.py').read())
```

**Einzelne Setup-Schritte wiederholen:**
```python
# Nur VPlayer neu bauen
exec(open('c:\\_DEV\\TOUCHDESIGNER\\build_vplayer.py').read())

# Nur OSC In neu konfigurieren
exec(open('c:\\_DEV\\TOUCHDESIGNER\\setup_osc_in.py').read())

# Nur LED neu integrieren
exec(open('c:\\_DEV\\TOUCHDESIGNER\\setup_led_integration.py').read())
```

---

**Version:** 1.0
**Author:** Claude Code Agent
**Datum:** 2025-01-14
