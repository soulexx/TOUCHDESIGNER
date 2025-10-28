# Audio-to-Eos Mapping System

Dieses System verbindet Audio-Analyse mit Eos Submasters über OSC. Audio-Werte werden durch S2L-Parameter (aus DMX Universe 16) gesteuert und als `Sub <n> At <level>` Commands zu Eos gesendet.

## Komponenten

### 1. `audio_eos_mapper.py` - Core Mapping Logic

Hauptfunktionen:
- `process_audio_to_subs()` - Verarbeitet alle Audio-Kanäle → Submasters
- `map_audio_channel_to_sub()` - Einzelner Kanal → Submaster
- `send_submaster_level(sub, level)` - Direkter OSC-Send zu Eos
- `send_cue_go(cuelist, cue)` - Optional: Cue-Trigger

### 2. `audio_eos_exec.py` - Execute Script

Frame-by-frame Processing Script für TouchDesigner Execute DAT.

## Setup in TouchDesigner

### Schritt 1: Execute DAT erstellen

1. Erstelle ein neues **Execute DAT** in `/project1/s2l_audio/` oder neben deinem Audio-Setup
2. Name: `audio_eos_exec`
3. Parameter → **DAT Execute** → Text: `text.py`
4. Setze den Text-Inhalt auf: `execfile('C:/_DEV/TOUCHDESIGNER/src/s2l_manager/audio_eos_exec.py')`

   ODER importiere direkt:
   ```python
   import sys
   sys.path.append('C:/_DEV/TOUCHDESIGNER/src/s2l_manager')
   import audio_eos_exec
   ```

5. **Callbacks aktivieren**:
   - ☑ Frame Start
   - Execute in: `Python`

### Schritt 2: Operator-Pfade anpassen

In `audio_eos_exec.py` (Zeile ~38-39), passe die Pfade an:

```python
audio_analysis = op('../../s2l_audio/fixtures/audio_analysis')  # Dein CHOP
audio_params = op('../audio_params_table')  # S2L Params Table
```

Ersetze mit den korrekten relativen Pfaden zu:
- Deinem `audio_analysis` CHOP (der low, mid, high, kick, snare, etc. ausgibt)
- Der `audio_params_table` DAT (aus `audio_params_exec.py`)

### Schritt 3: Submaster-Mapping konfigurieren

In `audio_eos_exec.py` (Zeile ~19-28), definiere welche Audio-Kanäle auf welche Eos-Submasters gehen:

```python
SUBMASTER_MAPPING = {
    'low': 11,      # Bass → Sub 11
    'mid': 12,      # Mids → Sub 12
    'high': 13,     # Highs → Sub 13
    'kick': 14,     # Kick → Sub 14
    'snare': 15,    # Snare → Sub 15
    'rhythm': 16,   # Rhythm → Sub 16
}
```

**Wichtig**: Diese Submaster müssen in deiner Eos-Show existieren!

### Schritt 4: OSC-Output prüfen

Stelle sicher, dass `/project1/io/oscout1` korrekt zu Eos verbunden ist:
- Protocol: **OSC**
- Network Address: IP deiner Eos-Konsole (z.B. `192.168.1.100`)
- Network Port: `3032` (Standard Eos OSC-Port)

## Eos Configuration

### Submasters erstellen

1. In Eos: `Sub <n> Enter` für jeden Submaster (z.B. Sub 11-16)
2. Optional: Label die Submasters (z.B. "Audio Bass", "Audio Kick")
3. Optional: Füge die Subs zu einem Cue hinzu oder nutze sie als Override

### OSC-Settings in Eos

1. Setup → System Settings → Show Control → OSC
2. ☑ Enable OSC RX (Receive)
3. RX Port: `3032` (muss mit TouchDesigner überein stimmen)
4. ☑ Enable OSC TX (optional, für Feedback)

## Workflow

```
Audio Device In
    ↓
Audio Analysis (Low/Mid/High/Kick/etc.)
    ↓
DMX Universe 16 → S2L Parameters (Sensitivity, Threshold, Filter, Lag)
    ↓
audio_eos_mapper.py (Processing)
    ↓
OSC → /eos/sub/<n> <level>
    ↓
Eos Submasters
```

## Testing

### Test 1: Single Channel (Textport)

```python
# Im TouchDesigner Textport:
op('/project1/s2l_audio/audio_eos_exec').module.test_single_channel('kick', 14)
```

Das sendet den `kick` Kanal einmalig zu Submaster 14.

### Test 2: All Mappings (Textport)

```python
op('/project1/s2l_audio/audio_eos_exec').module.test_all_mappings()
```

Führt eine Iteration aller Mappings aus.

### Test 3: Enable/Disable Runtime

In `audio_eos_exec.py` (Zeile ~32):
```python
ENABLE_MAPPING = True  # False = deaktiviert
```

## S2L Parameter Einfluss

Die DMX-Parameter aus Universe 16 beeinflussen das Audio-Mapping:

| Parameter | Effekt |
|-----------|--------|
| **Sensitivity** | Gain/Verstärkung (0-100%) - Multiplikator für Audio-Level |
| **Threshold** | Minimum-Pegel (0-100%) - Audio unter diesem Wert wird auf 0 gesetzt |
| **LowCut_Hz** | High-Pass Filter (20-300 Hz) - *Noch nicht implementiert* |
| **HighCut_Hz** | Low-Pass Filter (2k-8k Hz) - *Noch nicht implementiert* |
| **Lag_ms** | Smoothing/Lag (0-500ms) - *TODO: Implementierung* |
| **MinHold_s** | Minimum Hold Time (0-8s) - *TODO: Implementierung* |

Beispiel:
- Bei **Sensitivity = 50%** wird ein Audio-Wert von 0.8 zu 0.4
- Bei **Threshold = 20%** werden alle Werte unter 0.2 auf 0 gesetzt

## Performance

- **MIN_LEVEL_CHANGE**: 1% - OSC wird nur gesendet wenn Level um >1% ändert
- **MIN_SEND_INTERVAL**: 50ms - Max 20 Updates/Sekunde pro Submaster

Diese Werte können in `audio_eos_mapper.py` (Zeile ~18-19) angepasst werden.

## Troubleshooting

### Keine OSC-Nachrichten

1. Prüfe Textport auf `[audio_eos_mapper] OSC → ...` Messages
2. Falls "Cannot find OSC output": Prüfe `/project1/io/oscout1` existiert
3. Prüfe Execute DAT hat ☑ Frame Start aktiviert
4. Prüfe `ENABLE_MAPPING = True` in `audio_eos_exec.py`

### Keine Reaktion in Eos

1. Eos: `About` → Tab `Diagnostics` → schaue auf **RX** Counter (sollte hochzählen)
2. Falls kein RX: Prüfe IP-Adresse und Port in OSC-Settings
3. Falls RX aber keine Submaster-Reaktion: Prüfe Submasters existieren in Eos

### Falsche Audio-Werte

1. Prüfe `audio_analysis` CHOP gibt valide Werte (0-1)
2. Prüfe Operator-Pfade in `audio_eos_exec.py` stimmen
3. Teste mit `test_single_channel()` ob Mapping funktioniert

### Zu viele OSC-Messages

1. Erhöhe `MIN_LEVEL_CHANGE` in `audio_eos_mapper.py` (z.B. 0.05 = 5%)
2. Erhöhe `MIN_SEND_INTERVAL` (z.B. 0.1 = 100ms)

## Erweiterte Nutzung

### Per-Instance S2L Parameters

Aktuell nutzen alle Audio-Kanäle die S2L-Parameter von `S2L_UNIT_1`. Um verschiedene Instances zu nutzen:

```python
# In audio_eos_mapper.py, ändere Zeile ~181:
params = _get_instance_params(audio_params_table_op, 'S2L_UNIT_2')  # Unit 2 statt 1
```

Oder erstelle ein Mapping-Dictionary:
```python
INSTANCE_MAPPING = {
    'low': 'S2L_UNIT_1',
    'mid': 'S2L_UNIT_2',
    'high': 'S2L_UNIT_3',
    # etc.
}
```

### Cue-Trigger auf Audio-Events

In `audio_eos_exec.py`, füge Logik hinzu:

```python
# Beispiel: Trigger Cue bei Kick über Threshold
kick_value = _get_audio_value(audio_analysis, 'kick')
if kick_value and kick_value > 0.7:
    mapper.send_cue_go(cuelist=10, cue=2.5)
```

### Multiple Submaster-Modi

Erstelle verschiedene Mappings und wechsle zwischen ihnen:

```python
MAPPING_BASS_HEAVY = {'low': 11, 'kick': 14}
MAPPING_TREBLE = {'high': 13, 'snare': 15}

current_mode = 'BASS'  # Switch via button/OSC

if current_mode == 'BASS':
    mapper.process_audio_to_subs(audio_analysis, audio_params, MAPPING_BASS_HEAVY)
else:
    mapper.process_audio_to_subs(audio_analysis, audio_params, MAPPING_TREBLE)
```

## Next Steps / TODOs

- [ ] Lag/Smoothing implementieren (Low-Pass Filter auf Level-Changes)
- [ ] MinHold implementieren (Level mindestens X Sekunden halten)
- [ ] LowCut/HighCut Filter in Audio-Chain integrieren
- [ ] UI für Mapping-Configuration (Parameter DAT)
- [ ] Level-Visualisierung (CHOP Feedback)
- [ ] Cue-Trigger auf Beat-Detection
- [ ] Multiple Mapping-Modi mit Mode-Switching

## Files

- [`audio_eos_mapper.py`](audio_eos_mapper.py) - Core Logic
- [`audio_eos_exec.py`](audio_eos_exec.py) - Execute Script
- [`audio_params_exec.py`](audio_params_exec.py) - S2L Parameter Table Builder
- [`dispatcher.py`](dispatcher.py) - DMX → S2L Values

---

**Author**: Claude (Audio-Eos Integration)
**Date**: 2025-10-27
**Project**: TouchDesigner Eos Lighting Control
