# Setup-Anleitung: Per-Unit Audio Engine in TouchDesigner

## Schritt-für-Schritt Anleitung

### SCHRITT 1: Prüfe vorhandene Operatoren

Öffne TouchDesigner und prüfe, ob diese Operatoren existieren:

#### 1.1 DMX Input CHOP
- Pfad: `/project1/io/EOS_Universe_016`
- Typ: sACN In CHOP (oder ähnlich)
- **Prüfen:**
  - Rechtsklick auf den Operator → Viewer öffnen (oder `V` drücken)
  - Siehst du 512 Channels?
  - Ändern sich die Werte wenn du in Eos DMX-Werte änderst?

#### 1.2 Values Table
- Pfad: `/project1/src/s2l_manager/values`
- Typ: Table DAT
- **Prüfen:**
  - Doppelklick → Tabelle öffnen
  - Sollte 3 Spalten haben: `instance | parameter | value`
  - Sollte Werte von S2L_UNIT_1 bis S2L_UNIT_10 enthalten

#### 1.3 Audio Analysis CHOP
- Pfad: `/project1/s2l_audio/fixutres/audio_analysis`
- Typ: CHOP (vermutlich Audio Analysis oder Custom)
- **Prüfen:**
  - Viewer öffnen
  - Sollte diese Channels haben:
    - `low` (Bass)
    - `mid` (Mitten)
    - `high` (Höhen)
    - `smsd` (Spectral Mean Standard Deviation)
    - `fmsd` (Flux Mean Standard Deviation)
    - `spectralCentroid`
    - Optional: `kick`, `snare`, `rythm`

#### 1.4 OSC Output
- Pfad: `/project1/io/oscout1`
- Typ: OSC Out DAT
- **Prüfen:**
  - Parameter "Network Address" zeigt auf deine Eos Konsole IP
  - Parameter "Network Port" = 8000 (oder dein Eos OSC Port)
  - Parameter "Active" = On

---

### SCHRITT 2: Erstelle Audio Execute DAT

#### 2.1 DAT erstellen
1. Navigiere zu `/project1/src/s2l_manager/`
2. Drücke `Tab` → Suche "text" → Wähle "Text DAT"
3. Erstelle neuen Text DAT
4. Bennene ihn um: **`audio_exec`**

#### 2.2 Script kopieren
1. Öffne den DAT (Doppelklick)
2. Lösche den Inhalt
3. Kopiere den **kompletten** Inhalt von:
   `C:\_DEV\TOUCHDESIGNER\src\s2l_manager\audio_exec_perunit.py`
4. Füge ihn in den DAT ein
5. Speichern (Ctrl+S)

#### 2.3 DAT als Execute konfigurieren
1. Klicke auf den `audio_exec` DAT (einmal, nicht Doppelklick)
2. Im Parameter-Panel (rechts) gehe zu: **Common Page → DAT**
3. Ändere "DAT Viewer" → **"None"** (damit es ein Python-Script ist)
4. Gehe zu: **Execute Page**
5. Aktiviere diese Checkboxes:
   - ✅ **"Frame Start"** (wichtig!)
   - Alle anderen Checkboxen: OFF

#### 2.4 Pfade prüfen (falls nötig)
Wenn deine Operatoren **andere Pfade** haben, ändere im Script:
```python
# Zeilen 35-37 im audio_exec DAT:
VALUES_TABLE_PATH = "/project1/src/s2l_manager/values"  # Dein Pfad?
AUDIO_CHOP_PATH = "/project1/s2l_audio/fixutres/audio_analysis"  # Dein Pfad?
```

---

### SCHRITT 3: Module neu laden

Öffne das **Textport** (Alt+T oder View → Textport) und führe aus:

```python
# Module neu laden
import sys
import importlib

# Pfade hinzufügen
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_unit')
if 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager' not in sys.path:
    sys.path.insert(0, 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager')

# Audio Engine laden
import audio_engine_perunit
importlib.reload(audio_engine_perunit)

# S2L Unit helpers laden
import s2l_unit as s2l
importlib.reload(s2l)

print("✅ Module geladen!")
```

Erwartete Ausgabe:
```
[audio_engine_perunit] module loaded
✅ Module geladen!
```

---

### SCHRITT 4: DMX Input testen

#### 4.1 Prüfe DMX Values Table

Im Textport:
```python
values = op('/project1/src/s2l_manager/values')
print(f"Values table: {values.numRows} rows, {values.numCols} cols")

# Zeige erste 10 Zeilen
for row in range(min(10, values.numRows)):
    instance = values[row, 0].val
    param = values[row, 1].val
    value = values[row, 2].val
    print(f"{instance} | {param} | {value}")
```

**Erwartete Ausgabe:**
```
Values table: 131 rows, 3 cols
instance | parameter | value
S2L_UNIT_1 | Submaster | 5
S2L_UNIT_1 | Cuelist | 0
S2L_UNIT_1 | StartCue | 0
...
```

#### 4.2 Ändere DMX-Werte in Eos

1. Öffne Eos Konsole
2. Patche S2L_UNIT_1 auf Universe 16, Adresse 1-14
3. Ändere einen Wert, z.B.:
   - **Channel 1/2 (Submaster):** Setze auf 5 (wählt Submaster 5)
   - **Channel 9 (Threshold):** Setze auf 100
   - **Channel 13 (Band):** Setze auf 50 (= "mid")

4. Im Textport prüfen:
```python
# DMX Input triggern
frame_tick = op('/project1/io/frame_tick')
if frame_tick:
    frame_tick.module.onFrameStart(frame_tick)
    print("✅ Frame tick getriggert")

# Values table checken
values = op('/project1/src/s2l_manager/values')
for row in range(1, values.numRows):
    if values[row, 0].val == "S2L_UNIT_1":
        param = values[row, 1].val
        value = values[row, 2].val
        print(f"S2L_UNIT_1 | {param} | {value}")
```

**Solltest du sehen:**
```
S2L_UNIT_1 | Submaster | 5
S2L_UNIT_1 | Band | 50
S2L_UNIT_1 | Threshold | 100
...
```

---

### SCHRITT 5: Audio Analysis testen

#### 5.1 Prüfe Audio CHOP Channels

Im Textport:
```python
audio = op('/project1/s2l_audio/fixutres/audio_analysis')
if audio:
    print(f"Audio CHOP: {audio.numChans} channels")
    for ch in audio.chans():
        print(f"  {ch.name}: {ch[0]:.3f}")
else:
    print("❌ Audio CHOP nicht gefunden!")
```

**Erwartete Ausgabe (mit Musik spielend):**
```
Audio CHOP: 9 channels
  low: 0.234
  mid: 0.456
  high: 0.123
  smsd: 0.678
  fmsd: 0.345
  spectralCentroid: 0.567
  kick: 0.789
  snare: 0.234
  rythm: 0.456
```

Wenn **keine Audio-Werte** (alles 0.000):
- Prüfe Audio Input in TouchDesigner
- Spiele Musik ab
- Prüfe ob Audio Analysis CHOP Audio empfängt

---

### SCHRITT 6: Audio Engine testen

#### 6.1 Config anzeigen

Im Textport:
```python
audio_exec = op('/project1/src/s2l_manager/audio_exec')
audio_exec.module.show_config()
```

**Erwartete Ausgabe:**
```
================================================================================
AUDIO EXEC PER-UNIT CONFIGURATION
================================================================================
Enabled: True
Values table: /project1/src/s2l_manager/values
Audio CHOP: /project1/s2l_audio/fixutres/audio_analysis
Log interval: 300 frames

Operator Status:
  Values table: ✅ Found
    Rows: 131
    Cols: 3
  Audio CHOP: ✅ Found
    Channels: 9
    Samples: 1
    Channel names: ['low', 'mid', 'high', 'smsd', 'fmsd', ...]
  OSC output: ✅ Found
    Type: oscoutDAT

================================================================================
```

Wenn ❌ NOT FOUND:
- Prüfe Pfade im Script
- Prüfe ob Operatoren existieren

#### 6.2 Teste eine einzelne Unit

Im Textport:
```python
audio_exec = op('/project1/src/s2l_manager/audio_exec')
audio_exec.module.test_unit("S2L_UNIT_1")
```

**Erwartete Ausgabe:**
```
[audio_engine_perunit] ✅ S2L_UNIT_1 processed and OSC sent
[audio_engine_perunit] Parameters:
  Submaster: 5
  Cuelist: 0
  StartCue: 0
  EndCue: 0
  Threshold: 100
  Attack: 20
  Hold: 50
  Release: 80
  Band: 50
  FX_Polarity: 0
```

Oder:
```
[audio_engine_perunit] ⚠️  S2L_UNIT_1 processed but no OSC sent
```
(Normal wenn kein Audio oder Threshold zu hoch)

#### 6.3 Teste alle Units

Im Textport:
```python
audio_exec = op('/project1/src/s2l_manager/audio_exec')
audio_exec.module.test_all()
```

**Erwartete Ausgabe:**
```
[test] Processed all units, 3 sent OSC
```

Die Zahl zeigt wie viele Units OSC gesendet haben.

---

### SCHRITT 7: Live-Monitoring aktivieren

#### 7.1 Prüfe ob Execute läuft

Der `audio_exec` DAT sollte jetzt **automatisch jeden Frame** laufen.

Im Textport siehst du alle 5 Sekunden:
```
[audio_exec_perunit] Frame 300: 2 units sent OSC (total: 456)
[audio_exec_perunit] Frame 600: 3 units sent OSC (total: 789)
...
```

Wenn **keine Ausgabe**:
- Prüfe ob "Frame Start" Checkbox aktiv ist (Schritt 2.3)
- Prüfe ob `ENABLE_PROCESSING = True` im Script (Zeile 38)

#### 7.2 Eos OSC Monitor öffnen

1. Auf Eos Konsole: Drücke `[Displays]` → `Show Control`
2. Gehe zu **"Diagnostics"** Tab
3. Aktiviere **"OSC Monitor"**

Du solltest sehen:
```
Received: /eos/sub/5 45.3
Received: /eos/sub/5 46.1
Received: /eos/sub/5 47.8
...
```

Wenn **keine OSC Messages**:
- Prüfe OSC Out DAT Parameter (IP, Port, Active)
- Prüfe Eos OSC Settings (Shell → Settings → Network → OSC)
- Prüfe Firewall

---

### SCHRITT 8: Live-Test mit Musik

#### 8.1 Setup in Eos

Erstelle Testsetup:
```
[Sub] 5 [At] 0 [Enter]
[Sub] 5 [Label] S2L_Unit1_Bass [Enter]
```

#### 8.2 DMX Configuration in Eos

Fixture 1 (S2L_UNIT_1):
- **Channel 1/2 (Submaster):** 5 (steuert Sub 5)
- **Channel 9 (Threshold):** 100 (moderate Schwelle)
- **Channel 10 (Attack):** 20 (schnell)
- **Channel 11 (Hold):** 50
- **Channel 12 (Release):** 80
- **Channel 13 (Band):** 10 (= "low" = Bass)
- **Channel 14 (FX_Polarity):** 0 (normal)

#### 8.3 Musik abspielen

1. Spiele Musik mit Bass ab
2. Beobachte im Eos:
   - **Sub 5** sollte auf Bass-Hits reagieren
   - Level geht hoch bei Bass-Kick
   - Level geht runter nach Release-Time

3. Im TouchDesigner Textport siehst du:
```
[audio_exec_perunit] Frame 300: 1 units sent OSC (total: 45)
```

#### 8.4 Teste verschiedene Bands

Ändere **Channel 13 (Band)** in Eos:
- `10` → "low" (Bass) → Sub reagiert auf Bass
- `60` → "mid" (Mitten) → Sub reagiert auf Vocals/Snare
- `100` → "high" (Höhen) → Sub reagiert auf Hi-Hats/Cymbals
- `150` → "smsd" → Sub reagiert auf spektrale Änderungen
- `220` → "spectralCentroid" → Sub reagiert auf Helligkeit

#### 8.5 Teste Polarity

Ändere **Channel 14 (FX_Polarity)**:
- `0` → Normal: Sub geht HOCH bei Audio
- `200` → Inverted: Sub geht RUNTER bei Audio (Ducking-Effekt)

---

### SCHRITT 9: Mehrere Units gleichzeitig

#### 9.1 Setup in Eos

Erstelle 3 Submasters:
```
[Sub] 10 [Label] Bass_Lights [Enter]
[Sub] 11 [Label] Mid_Lights [Enter]
[Sub] 12 [Label] High_Lights [Enter]
```

#### 9.2 DMX für 3 Units

**Fixture 1 (S2L_UNIT_1) @ DMX 1-14:**
- Channel 1/2: 10 (Sub 10)
- Channel 13: 10 (low/Bass)

**Fixture 2 (S2L_UNIT_2) @ DMX 15-28:**
- Channel 1/2: 11 (Sub 11)
- Channel 13: 60 (mid)

**Fixture 3 (S2L_UNIT_3) @ DMX 29-42:**
- Channel 1/2: 12 (Sub 12)
- Channel 13: 100 (high)

Jetzt sollten **3 Submasters gleichzeitig** auf verschiedene Frequenzen reagieren!

---

## Troubleshooting

### Problem: "Values table NOT FOUND"

**Lösung:**
```python
# Prüfe ob values table existiert
values = op('/project1/src/s2l_manager/values')
if values:
    print(f"✅ Found: {values.path}")
else:
    print("❌ Not found - erstelle neue Table DAT")
    # Pfad anpassen falls nötig
```

### Problem: "Audio CHOP NOT FOUND"

**Lösung:**
```python
# Suche Audio CHOP
import find_operators
ops = find_operators.find_all()
print("Audio CHOPs gefunden:")
for op_path in ops.get('audio_analysis', []):
    print(f"  {op_path}")
```

Dann Pfad im Script anpassen (Zeile 36).

### Problem: "Keine OSC Messages in Eos"

**Checkliste:**
1. OSC Out DAT Active? `op('/project1/io/oscout1').par.active.eval()`
2. IP korrekt? `op('/project1/io/oscout1').par.address.eval()`
3. Port korrekt? `op('/project1/io/oscout1').par.port.eval()`
4. Eos OSC aktiviert? (Shell → Settings → Network → OSC RX)
5. Firewall? (Teste mit Ping)

### Problem: "Units senden OSC aber Submaster bewegt sich nicht"

**Checkliste:**
1. Ist der Submaster auf Level 0? (Muss >0 sein)
2. Hat der Submaster Fixtures? (Submaster braucht Inhalt)
3. OSC Command korrekt? (Sollte `/eos/sub/5 <level>` sein)
4. Eos im "Live" Mode? (Nicht Blind)

### Problem: "Envelope reagiert nicht"

**Lösung:**
```python
# Clear envelope states
audio_exec = op('/project1/src/s2l_manager/audio_exec')
audio_exec.module.clear_states()
print("✅ Envelope states cleared")
```

### Problem: "Audio ist 0.0"

**Checkliste:**
1. Musik spielt ab?
2. Audio Input in TouchDesigner aktiv?
3. Audio Analysis CHOP bekommt Audio?
4. Viewer auf Audio CHOP öffnen → siehst du Werte?

---

## Performance Tuning

### Reduziere CPU Last

Im `audio_exec` DAT ändern:

```python
# Zeile 39: Log weniger oft
LOG_INTERVAL = 600  # Alle 10 Sekunden statt 5

# OSC Change Detection in audio_engine_perunit.py:
MIN_LEVEL_CHANGE = 0.02  # 2% statt 1% (weniger OSC Messages)
MIN_SEND_INTERVAL = 0.1  # 100ms statt 50ms (weniger frequent)
```

### Deaktiviere einzelne Units

Setze in Eos DMX Channel 1/2 (Submaster) auf **0**:
- Unit mit Submaster=0 wird übersprungen
- Spart CPU

---

## Nächste Schritte

✅ DMX Input funktioniert
✅ Audio Analysis funktioniert
✅ OSC zu Eos funktioniert
✅ Per-Unit Processing funktioniert

**Jetzt kannst du:**
1. Komplexe Multi-Band Setups bauen
2. Verschiedene Attack/Release-Zeiten pro Unit
3. Inverted Polarity für Ducking-Effekte
4. Spectral Analysis für kreative Effekte

**Später implementieren:**
- Cuelist Trigger (DMX Channel 3-8)
- Beat Detection für Cue Go
- Erweiterte Audio-Filter (LowCut/HighCut)

---

## Quick Reference: Wichtige Textport Commands

```python
# Config anzeigen
op('/project1/src/s2l_manager/audio_exec').module.show_config()

# Eine Unit testen
op('/project1/src/s2l_manager/audio_exec').module.test_unit("S2L_UNIT_1")

# Alle Units testen
op('/project1/src/s2l_manager/audio_exec').module.test_all()

# Envelope States clearen
op('/project1/src/s2l_manager/audio_exec').module.clear_states()

# Module neu laden
op('/project1/src/s2l_manager/audio_exec').module.reload_engine()

# Values table anzeigen
values = op('/project1/src/s2l_manager/values')
for row in range(min(20, values.numRows)):
    print(f"{values[row,0].val} | {values[row,1].val} | {values[row,2].val}")

# Audio Levels anzeigen
audio = op('/project1/s2l_audio/fixutres/audio_analysis')
for ch in audio.chans():
    print(f"{ch.name}: {ch[0]:.3f}")

# DMX triggern
op('/project1/io/frame_tick').module.onFrameStart(op('/project1/io/frame_tick'))
```

---

## Support

Bei Problemen:
1. `show_config()` ausführen → zeigt Status aller Operatoren
2. Textport Output checken → zeigt Fehlermeldungen
3. OSC Monitor in Eos checken → zeigt empfangene Messages
4. DMX Viewer in TouchDesigner öffnen → zeigt DMX Input

**Viel Erfolg!** 🎉
