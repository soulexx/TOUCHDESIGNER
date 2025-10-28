# S2L Audio-to-Eos Setup Instructions

## Status: ✅ WORKING

Der DMX-zu-Audio-zu-Eos Flow funktioniert jetzt!

## Setup für automatischen Betrieb

### 1. Frame Tick Execute DAT konfigurieren

Der `/project1/io/frame_tick` DAT muss als **Execute DAT** konfiguriert sein:

1. Gehe zu `/project1/io/frame_tick`
2. Im Parameter-Panel, unter **DAT Execute**:
   - **Frame Start**: `onFrameStart(me)`
   - Oder verwende die GUI und aktiviere "Frame Start"

### 2. Audio Params Exec konfigurieren

Der `/project1/src/s2l_manager/audio_params_exec` DAT sollte automatisch laufen:

1. Gehe zu `/project1/src/s2l_manager/audio_params_exec`
2. Im Parameter-Panel, unter **DAT Execute**:
   - **Table Change**: `onTableChange(me)`
   - Das triggert automatisch wenn die `values` Tabelle sich ändert

### 3. Audio EOS Exec konfigurieren

Der `/project1/src/s2l_manager/audio_eos_exec` DAT muss jedes Frame laufen:

1. Gehe zu `/project1/src/s2l_manager/audio_eos_exec`
2. Im Parameter-Panel, unter **DAT Execute**:
   - **Frame Start**: `onFrameStart(me)`

### 4. Module neu laden (einmalig nach Code-Änderungen)

Führe einmalig aus, um alle Module neu zu laden:

```python
import sys
import importlib

# Reload sacn_dispatch
sacn_path = 'C:/_DEV/TOUCHDESIGNER/io'
if sacn_path not in sys.path:
    sys.path.insert(0, sacn_path)
import sacn_dispatch
importlib.reload(sacn_dispatch)

# Reload dispatcher
manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)
import dispatcher
importlib.reload(dispatcher)

print("✅ All modules reloaded!")
```

## Workflow

Wenn alles korrekt konfiguriert ist:

1. **Eos** → DMX Universe 16 → **TouchDesigner** (`/project1/io/EOS_Universe_016`)
2. **frame_tick** (jedes Frame) → `sacn_dispatch.handle_universe()` → `dispatcher.update_from_dmx()`
3. **dispatcher** schreibt DMX-Werte in `values` Tabelle
4. **audio_params_exec** (bei Änderung) → baut `audio_params_table` aus `values`
5. **audio_eos_exec** (jedes Frame) → liest Audio + Parameter → sendet OSC zu Eos

## Testen

### Test 1: DMX kommt an

```python
uni16 = op('/project1/io/EOS_Universe_016')
print(f"Channel 11 (Sensitivity): {uni16[10].eval()}")
print(f"Channel 12 (Threshold): {uni16[11].eval()}")
```

### Test 2: Values Tabelle wird gefüllt

Ändere in Eos einen Wert (z.B. Sensitivity). Im Textport solltest du sehen:
```
[s2l_manager] S2L_UNIT_1:Sensitivity -> <wert>
```

Prüfe die Tabelle:
```python
values = op('/project1/src/s2l_manager/values')
print(f"Rows: {values.numRows}")
# Sollte > 100 sein (alle 10 Units mit je 13 Parametern)
```

### Test 3: Audio Params Tabelle aktualisiert

```python
audio_params = op('/project1/src/s2l_manager/audio_params_table')
for i in range(audio_params.numRows):
    print(' | '.join([audio_params[i, j].val for j in range(audio_params.numCols)]))
# Sollte S2L_UNIT_1 mit deinen Eos-Werten zeigen
```

### Test 4: OSC wird gesendet

Öffne Textport (Alt+T) und beobachte:
```
[audio_eos_mapper] Sending to Sub 11: 0.42
[audio_eos_mapper] Sending to Sub 12: 0.78
...
```

## Submaster Mapping

Diese Audio-Channels werden zu diesen Eos Submasters gemappt:

| Audio Channel      | Eos Submaster |
|--------------------|---------------|
| low                | 11            |
| mid                | 12            |
| high               | 13            |
| kick               | 14            |
| snare              | 15            |
| rythm              | 16            |
| smsd               | 17            |
| fmsd               | 18            |
| spectralCentroid   | 19            |

## DMX Patch in Eos

Universe 16, S2L_UNIT_1 startet bei Channel 1:

| Channel | Parameter     | Funktion                               |
|---------|---------------|----------------------------------------|
| 1-2     | Submaster     | 16-bit Submaster-Nummer (0-65535)      |
| 3-4     | Cuelist       | 16-bit Cuelist-Nummer                  |
| 5-6     | StartCue      | 16-bit Start-Cue                       |
| 7-8     | EndCue        | 16-bit End-Cue                         |
| 9       | Mode          | 0=Sub, 1=Cue                           |
| 10      | (reserved)    | -                                      |
| 11      | Sensitivity   | 0-255 (Gain/Verstärkung)               |
| 12      | Threshold     | 0-255 (Schwellwert)                    |
| 13      | LowCut_Hz     | 0-255                                  |
| 14      | HighCut_Hz    | 0-255                                  |
| 15      | Lag_ms        | 0-255                                  |
| 16      | MinHold_s     | 0-255                                  |
| 17      | FX_Select     | 0-255                                  |
| 18      | FX_Auto       | 0-255                                  |
| 19      | (reserved)    | -                                      |

Nächste Unit (S2L_UNIT_2) startet bei Channel 21, usw.

## Troubleshooting

### Keine Logs im Textport

- Prüfe ob `frame_tick` als Execute DAT konfiguriert ist
- Prüfe ob Module geladen sind (siehe "Module neu laden")

### Values Tabelle bleibt leer

- Prüfe ob DMX ankommt (Test 1)
- Reload Module

### Audio Params Tabelle bleibt leer

- Prüfe ob `values` Tabelle gefüllt ist
- Reload `audio_params_exec` DAT

### Sensitivity/Threshold haben keinen Effekt

- Prüfe `audio_params_table` - sollte deine Werte enthalten
- Prüfe `audio_eos_mapper.py` - sollte Werte korrekt anwenden
