# Video Player für MIDICRAFT ENC & Eos - Implementierung Komplett

Professioneller Video Player für TouchDesigner mit Eos-Synchronisation und Hardware-Steuerung.

## Status: ✅ Implementierung Abgeschlossen

**Datum:** 2025-01-14
**Version:** 1.0

---

## Was wurde umgesetzt?

### ✅ Code-Änderungen (Automatisch)

1. **[menus/menu_5/map_osc.tsv](menus/menu_5/map_osc.tsv)**
   - Fader 1 (CC 16/48): `/vplayer/scrub` (0-1)
   - Fader 2 (CC 17/49): `/vplayer/speed` (0.5-2.0)
   - Fader 3 (CC 18/50): `/vplayer/volume` (0-1)
   - Button 21: Long press → `/vplayer/mode_toggle`

2. **[menus/menu_engine.py](menus/menu_engine.py)**
   - Neue Funktion: `_handle_vplayer_command(path, value)`
   - Event Routing für `/vplayer/*` Pfade
   - Integration mit bestehender MIDI Pipeline

### ✅ Python Scripts (Bereit zum Kopieren)

**Ordner:** [vplayer_scripts/](vplayer_scripts/)

- **marker_write.py** - Marker setzen in RECORD Mode (GO kurz)
- **marker_delete.py** - Marker löschen in RECORD Mode (BACK kurz)
- **osc_event_handler.py** - OSC Events von Eos empfangen und verarbeiten
- **marker_lookup.py** - Marker-Navigation (Next/Previous/Jump)

### ✅ Dokumentation (Schritt-für-Schritt)

1. **[VPLAYER_BUILD_GUIDE.md](VPLAYER_BUILD_GUIDE.md)** - Haupt-Anleitung
   - TouchDesigner Component-Aufbau
   - CHOP/DAT Netzwerk
   - UI Container
   - Testing Checkliste

2. **[OSC_IN_GUIDE.md](OSC_IN_GUIDE.md)** - OSC Konfiguration
   - Eos OSC Output Setup
   - TouchDesigner OSC In Konfiguration
   - Network Setup & Firewall
   - Troubleshooting

3. **[LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md)** - LED Integration
   - LED State Generator (CHOPs)
   - driver_led.py Integration
   - Blink & Flash Patterns
   - Menu-aware LED Switching

---

## Nächste Schritte (TouchDesigner Arbeit)

### 1. Projekt laden & vorbereiten

```bash
cd c:\_DEV\TOUCHDESIGNER
# Öffne: MIDICRAFT_to_EOS_1.1.toe
```

**Änderungen sind bereits gespeichert:**
- ✅ `menus/menu_5/map_osc.tsv` - MIDI Mappings aktualisiert
- ✅ `menus/menu_engine.py` - Event Handler hinzugefügt

### 2. Component in TouchDesigner bauen

Folge: **[VPLAYER_BUILD_GUIDE.md](VPLAYER_BUILD_GUIDE.md)**

**Geschätzte Zeit:** 2.5-3 Stunden

**Hauptschritte:**
1. Base COMP erstellen (`/project1/media/vplayer`)
2. State CHOPs anlegen (`state`, `eos_state`)
3. Markers Table DAT erstellen
4. Video/Audio Kette aufbauen (Movie File In → Audio Device Out)
5. Fader Integration (Scrub/Speed/Volume)
6. Python Scripts als Text DATs kopieren
7. OSC In Callbacks einrichten
8. LED Feedback integrieren
9. Optional: UI Container bauen

### 3. OSC In konfigurieren

Folge: **[OSC_IN_GUIDE.md](OSC_IN_GUIDE.md)**

**Eos Seite:**
- OSC TX aktivieren (IP: Dein TD Computer, Port: 7001)
- Feedback aktivieren (Cue Lists, Playback)

**TouchDesigner Seite:**
- OSC In DAT Callback hinzufügen → `vplayer/osc_event_handler`
- Netzwerk testen (ping, Firewall)

### 4. LED Feedback integrieren

Folge: **[LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md)**

**Integration:**
- LED State CHOPs in vplayer erstellen
- Blink Generator (LFO CHOP)
- Verbindung zu `driver_led.py`
- Menu 5 Priority Logic

---

## Architektur-Übersicht

### Kernkonzept

**Video folgt Eos passiv:**
- Kein OSC Output von TouchDesigner in FOLLOW Mode
- Video springt nur bei OSC Events von Eos (wenn Marker existiert)
- RECORD Mode: Marker aufnehmen ohne Eos-Interaktion

### Zwei Modi

**FOLLOW (Default):**
- Eos GO → Video springt zu Marker (falls vorhanden)
- Eos BACK → Video springt zu vorherigem Marker
- LED: Dunkelgrün (Idle) / Hellgrün (Fahrt)
- OSC In aktiv, OSC Out blockiert

**RECORD (GO Langdruck 0.7s):**
- GO kurz → Marker für Pending Cue setzen/ersetzen
- BACK kurz → Marker löschen (Undo)
- LED: Grün blinkend (500ms)
- OSC Events ignoriert

### MIDI Mapping (Menu 5)

| Control | MIDI | Funktion | Range |
|---------|------|----------|-------|
| Fader 1 | CC 16/48 | Scrub Position | 0-1 |
| Fader 2 | CC 17/49 | Playback Speed | 0.5-2.0x |
| Fader 3 | CC 18/50 | Audio Volume | 0-1 |
| Button 21 | Note 26 | Eos GO (kurz) / Mode Toggle (lang) | - |
| Button 11 | Note 21 | Eos STOP | - |

**Hinweis:** Buttons 11 & 21 behalten Eos-Funktionen. Video folgt passiv.

### OSC Paths (Empfangen von Eos)

```
/eos/out/active/cue/<list>/<cue>   → Active Cue Changed (Video Jump)
/eos/out/pending/cue/<list>/<cue>  → Pending Cue (RECORD Target)
/eos/out/active/cue (Float 0-1)    → Progress (LED Idle/Fahrt)
/eos/out/previous/cue/<list>/<cue> → BACK (Optional)
```

### Marker System

**Format:** Table DAT mit Spalten `key | pos_s | label`

**Key Format:** `list/cue` (z.B. `1/23` für Cue List 1, Cue 23)

**Regeln:**
- Ein Marker pro Cue Key
- Ersetzen nur in RECORD Mode (bewusst per GO kurz)
- Lookup in FOLLOW Mode (exakter Match)

---

## Workflow

### Setup (einmalig)

1. ✅ Code-Änderungen bereits committed
2. TouchDesigner Component bauen (siehe BUILD_GUIDE)
3. OSC In konfigurieren (siehe OSC_IN_GUIDE)
4. LED Feedback integrieren (siehe LED_FEEDBACK_GUIDE)
5. Video-Datei laden in `moviefilein1`

### Rehearsal (Marker aufnehmen)

1. Menu 5 aktivieren
2. Video abspielen
3. **GO Langdruck** (~0.7s) → RECORD Mode (LED blinkt grün)
4. Eos GO drücken → Pending Cue wird angezeigt
5. **GO kurz** → Marker an aktueller Position gesetzt
6. Wiederholen für alle Cues
7. **GO Langdruck** → Zurück zu FOLLOW Mode

### Performance (Marker nutzen)

1. Menu 5 aktivieren
2. Video abspielen
3. Eos GO drücken → Video springt automatisch zu Marker
4. Fader 1/2/3 für Scrub/Speed/Volume nutzen
5. LED zeigt Status (Idle/Fahrt)

### Korrektur (Marker ändern)

1. **GO Langdruck** → RECORD Mode
2. Video zur gewünschten Position scrubben (Fader 1)
3. **GO kurz** → Marker überschreiben
4. Oder **BACK kurz** → Marker löschen (Undo)
5. **GO Langdruck** → FOLLOW Mode

---

## Testing Checkliste

### ✅ Code Changes
- [x] `map_osc.tsv` updated
- [x] `menu_engine.py` event handler added
- [x] Python scripts created

### 🔲 TouchDesigner Build (Deine Aufgabe)
- [ ] `/project1/media/vplayer` Base COMP erstellt
- [ ] State CHOPs (`state`, `eos_state`)
- [ ] Markers Table DAT
- [ ] Movie File In + Audio Device Out
- [ ] Fader CHOPs (scrub/speed/volume)
- [ ] OSC Event Handler DAT
- [ ] Marker Write/Delete Scripts

### 🔲 OSC Integration (Deine Aufgabe)
- [ ] Eos OSC TX konfiguriert
- [ ] TouchDesigner OSC In empfängt Messages
- [ ] Textport zeigt `[eos_event]` Messages
- [ ] Video springt bei Eos GO (wenn Marker existiert)

### 🔲 LED Feedback (Deine Aufgabe)
- [ ] LED State CHOP erstellt
- [ ] Blink Generator (LFO)
- [ ] Integration mit `driver_led.py`
- [ ] Hardware LED zeigt korrekte Farbe/Pattern

### 🔲 End-to-End Test
- [ ] RECORD: GO kurz → Marker gesetzt
- [ ] RECORD: BACK kurz → Marker gelöscht
- [ ] FOLLOW: Eos GO → Video Jump
- [ ] Fader 1: Scrub funktioniert (always play)
- [ ] Fader 2: Speed ändert sich (0.5-2.0x)
- [ ] Fader 3: Volume ändert sich (0-1)
- [ ] LED: Blinkt in RECORD, solid in FOLLOW

---

## Troubleshooting

### Video springt nicht bei Eos GO

**Checkliste:**
- [ ] Marker für diese Cue existiert in `markers` Table
- [ ] Mode = 0 (FOLLOW)
- [ ] OSC In empfängt `/eos/out/active/cue` Messages (Textport prüfen)
- [ ] `osc_event_handler` DAT hat kein Python Error

**Debug:**
```python
# Manuell testen:
handler = op('/project1/media/vplayer/osc_event_handler')
handler.module.on_active_cue_change(1, 23)  # Cue 1/23
# Sollte Video springen wenn Marker existiert
```

### Fader reagieren nicht

**Checkliste:**
- [ ] Menu 5 ist aktiv (`op('/project1').fetch('ACTIVE_MENU') == 5`)
- [ ] MIDI Events erreichen `bus_events` (Monitor CHOP)
- [ ] `map_osc.tsv` korrekt geladen (neustart TD?)
- [ ] `menu_engine.py` `_handle_vplayer_command` wird aufgerufen (print statement)

### LED aktualisiert nicht

**Checkliste:**
- [ ] `led_go_out` CHOP hat korrekten Wert
- [ ] `led_const` channel `btn_21` aktualisiert
- [ ] MIDI Out ist aktiv (grünes Flag)
- [ ] MIDICRAFT ENC empfängt MIDI (andere Buttons testen)

**Manueller Test:**
```python
# LED direkt setzen:
drv = op('/project1/io/driver_led')
drv.module.send_led('btn/21', 'press', 'green')
# LED sollte leuchten
```

Siehe vollständiges Troubleshooting in den jeweiligen Guides.

---

## Datei-Übersicht

### Code (Bereits geändert)
```
menus/menu_5/map_osc.tsv      - MIDI Mapping aktualisiert
menus/menu_engine.py           - Event Handler hinzugefügt
```

### Scripts (Zum Kopieren in TD)
```
vplayer_scripts/
├── marker_write.py            - Marker setzen (RECORD GO)
├── marker_delete.py           - Marker löschen (RECORD BACK)
├── osc_event_handler.py       - OSC Events verarbeiten
└── marker_lookup.py           - Marker Navigation
```

### Dokumentation
```
VPLAYER_README.md              - Diese Datei (Übersicht)
VPLAYER_BUILD_GUIDE.md         - TouchDesigner Build Anleitung
OSC_IN_GUIDE.md                - OSC Konfiguration
LED_FEEDBACK_GUIDE.md          - LED Integration
```

### TouchDesigner Component (Zu erstellen)
```
/project1/media/vplayer/       - Base COMP
├── state                      - Constant CHOP (mode, speed, volume, etc.)
├── eos_state                  - Constant CHOP (active/pending cue, progress)
├── markers                    - Table DAT (key, pos_s, label)
├── moviefilein1               - Movie File In TOP
├── null_vid1                  - Null TOP
├── out1                       - Out TOP
├── audiomovie1                - Audio Movie CHOP
├── audiodeviceout1            - Audio Device Out CHOP
├── info_video                 - Info CHOP
├── scrub_input                - Constant CHOP (Fader 1)
├── speed_input                - Constant CHOP (Fader 2)
├── volume_input               - Constant CHOP (Fader 3)
├── scrub_execute              - CHOP Execute DAT
├── osc_event_handler          - Text DAT (Script)
├── marker_write               - Text DAT (Script)
├── marker_delete              - Text DAT (Script)
├── marker_lookup              - Text DAT (Script)
├── led_go_out                 - LED State CHOP
└── container_ui               - Optional UI Container
```

---

## Performance & Optimierung

### Empfohlene Video Codecs
- **HAP** - Beste Performance, GPU-beschleunigt
- **NotchLC** - Sehr gut, transparente Alpha
- **H.264** - Akzeptabel, Standard

### Audio Buffer
- Standard: 512 samples
- Bei Crackling: 1024 oder 2048 samples erhöhen

### CHOP Cook Rate
- LED State: 30 FPS ausreichend
- Video Info: 60 FPS (default)
- State Updates: 60 FPS

### Marker Persistence
Markers speichern zwischen Sessions:
```python
# Save
op('/project1/media/vplayer/markers').save('markers_backup.txt')

# Load on startup
op('/project1/media/vplayer/markers').load('markers_backup.txt')
```

---

## Support & Weiterentwicklung

### Feature-Ideen (Optional)
- Multiple Videos pro Show (filename prefix in marker key)
- Marker Import/Export (CSV, JSON)
- Timeline UI mit Marker-Visualisierung
- Marker Types (Verse/Chorus/Bridge mit verschiedenen LED Farben)
- Auto-Marker (bei jedem Eos GO automatisch aufnehmen)

### Bekannte Einschränkungen
- Keine Parts im Key Format (nur `list/cue`, keine `.part`)
- Ein Marker pro Cue (kein Multiple-Marker pro Cue)
- Eos GO/STOP Buttons in Menu 5 für Video umfunktioniert
- Kein bidirektionales Feedback (TD sendet nichts zurück an Eos)

---

## Credits

**Implementiert von:** Claude Code Agent
**Basierend auf:** Originalspezifikation (User)
**Projekt:** MIDICRAFT ENC → Eos Integration
**Version:** TouchDesigner 2023.11760+
**Datum:** 2025-01-14

---

## Quick Start (Zusammenfassung)

1. ✅ **Code ist bereit** - `map_osc.tsv` und `menu_engine.py` bereits aktualisiert
2. 📖 **Build Guide lesen** - [VPLAYER_BUILD_GUIDE.md](VPLAYER_BUILD_GUIDE.md)
3. 🔧 **Component bauen** - ~2.5 Stunden in TouchDesigner
4. 🌐 **OSC konfigurieren** - [OSC_IN_GUIDE.md](OSC_IN_GUIDE.md)
5. 💡 **LED integrieren** - [LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md)
6. 🎬 **Video laden** - Test mit Beispiel-Video
7. 🎤 **Rehearsal** - Marker in RECORD Mode aufnehmen
8. 🎭 **Performance** - FOLLOW Mode nutzen

**Viel Erfolg bei der Umsetzung!** 🚀

Bei Fragen zu den Guides: Einfach nachfragen oder die Troubleshooting-Abschnitte konsultieren.
