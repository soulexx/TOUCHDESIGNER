# EOS Palette Sync - Fix und Test-Anleitung

## Problem

Die Paletten-Tabellen (`pal_ip`, `pal_fp`, `pal_cp`, `pal_bp`) blieben leer, obwohl EOS via OSC Paletten-Daten senden sollte.

### Ursache

1. **Falsche OSC API**: Der Code verwendete `/eos/get/{type}/index/{idx}`, aber EOS unterstützt diese API **nicht**.
2. **Korrekte EOS OSC API**: `/eos/get/{type}/{num}/list/0/1` (wobei `{num}` die 1-basierte Paletten-Nummer ist)
3. **Index-Inkonsistenz**: Mischung aus 0-basierten und 1-basierten Indizes

## Durchgeführte Fixes

### 1. [pump.py](palette_logic/pump.py)
- ✅ Umstellung auf 1-basierte Paletten-Nummern (1, 2, 3, ... statt 0, 1, 2, ...)
- ✅ Korrekte OSC API: `/eos/get/{type}/{num}/list/0/1`
- ✅ Parameter-Namen von `index` zu `palette_num` geändert für Klarheit

### 2. [eos_notify_handler.py](palette_logic/eos_notify_handler.py)
- ✅ ACK mit `palette_num` statt `index`
- ✅ Korrekte Zuordnung: Palette #N → Tabellenzeile N
- ✅ Verbesserte Debug-Ausgaben

## Test-Durchführung

### Schritt 1: Diagnose ausführen

Im TouchDesigner Textport (`Alt + T`):

```python
# Lade und führe Diagnose aus
exec(open(r"c:\_DEV\TOUCHDESIGNER\palette_logic\diagnose_palette_sync.py").read())
```

**Erwartete Ausgabe:**
- ✅ Alle Module geladen
- ✅ OSC Out und OSC In gefunden
- Status von PALETTE_SYNC_ENABLED

### Schritt 2: Palette Sync aktivieren

```python
# Aktiviere Palette Sync
op('/project1').store('PALETTE_SYNC_ENABLED', True)
print("✅ Palette Sync aktiviert")
```

### Schritt 3: Subscribe und Count-Request senden

```python
# Lade Module
watchdog = mod('/project1/palette_logic/watchdog')
state = mod('/project1/palette_logic/state')
base = op('/project1')

# Reset Timer für sofortigen Start
state.state.last_activity = 0.0
state.state.last_subscribe = 0.0
state.state.last_count_request = 0.0

# Sende Subscribe und Count-Requests
watchdog.ensure_subscribed(base)
print("✅ Subscribe und Count-Requests gesendet")
```

### Schritt 4: OSC-Antworten prüfen

```python
# Warte 2 Sekunden
import time
time.sleep(2)

# Prüfe State
st = state.state
print("\n=== PALETTE COUNTS ===")
for ptype in ['ip', 'fp', 'cp', 'bp']:
    count = st.counts.get(ptype, 0)
    queue_len = len(st.queues.get(ptype, []))
    active = st.active.get(ptype)
    print(f"{ptype}: count={count}, queue={queue_len}, active={active}")
```

**Erwartete Ausgabe im Textport:**
```
[palette] DEBUG received count: ip=42 | OSC: /eos/out/get/ip/count [42.0]
[palette] DEBUG ip queue initialized: 42 palettes (1-42)
[palette] DEBUG ip sending OSC: /eos/get/ip/1/list/0/1
[palette] send ip palette #1
```

### Schritt 5: Paletten-Tabelle prüfen

```python
# Prüfe ob Paletten in Tabelle sind
table = op('/project1/palette_logic/pal_ip')
if table and table.numRows > 1:
    print(f"\n✅ Tabelle pal_ip: {table.numRows} Zeilen")
    print("\nErste 5 Paletten:")
    for row in range(1, min(6, table.numRows)):
        cells = [table[row, col].val for col in range(min(4, table.numCols))]
        print(f"  Palette #{row}: {cells}")
else:
    print("\n❌ Tabelle leer oder nicht gefunden!")
```

**Erwartete Ausgabe:**
```
✅ Tabelle pal_ip: 43 Zeilen (Header + 42 Paletten)

Erste 5 Paletten:
  Palette #1: ['1', '1', 'abc123', 'Warm']
  Palette #2: ['2', '2', 'def456', 'Cool']
  ...
```

### Schritt 6: Test mit einzelner Palette

Teste manuell eine einzelne Palette-Anfrage:

```python
# Test-Funktion aus diagnose_palette_sync.py
diag = mod('/project1/palette_logic/diagnose_palette_sync')
diag.test_single_palette_request()
```

Dies sendet drei verschiedene OSC-Requests und zeigt, welche funktionieren.

## Erwartete Debug-Ausgaben

### Bei Count-Request:
```
[palette] count request ip
[palette] DEBUG received count: ip=42 | OSC: /eos/out/get/ip/count [42.0]
[palette] DEBUG ip queue initialized: 42 palettes (1-42)
```

### Bei Palette-Request:
```
[palette] DEBUG ip sending OSC: /eos/get/ip/1/list/0/1
[palette] send ip palette #1
```

### Bei Palette-Antwort von EOS:
```
[palette] DEBUG received list: ip palette #1 idx=0 uid='abc123' label='Warm'
[palette] DEBUG ip palette #1 ACK (queue: 41 remaining)
[palette] DEBUG ip sending OSC: /eos/get/ip/2/list/0/1
[palette] send ip palette #2
```

## Troubleshooting

### Problem: Keine Count-Antworten von EOS

**Prüfe:**
1. EOS OSC-Konfiguration:
   - TCP/UDP Port korrekt?
   - OSC TX aktiviert?
   - IP-Adresse korrekt?

2. TouchDesigner OSC In:
   ```python
   osc_in = op('/project1/io/oscin1_from_eos')
   print(f"OSC In Rows: {osc_in.numRows}")
   # Sollte > 0 sein wenn EOS sendet
   ```

### Problem: PALETTE_SYNC_ENABLED ist False

```python
# Aktivieren
op('/project1').store('PALETTE_SYNC_ENABLED', True)
```

### Problem: Module nicht gefunden

Prüfe Pfade in TouchDesigner:
```python
base = op('/project1')
if not base:
    print("❌ /project1 nicht gefunden!")

# Prüfe palette_logic Ordner
pal_logic = op('/project1/palette_logic')
if not pal_logic:
    print("❌ palette_logic nicht gefunden!")
```

### Problem: Paletten kommen an, aber Tabelle bleibt leer

Prüfe `_update_row` Funktion:
```python
handler = mod('/project1/palette_logic/eos_notify_handler')
# Manueller Test
handler._update_row('ip', 1, num='1', uid='test123', label='Test Palette')

# Prüfe Tabelle
table = op('/project1/palette_logic/pal_ip')
print(table[1, 0].val, table[1, 1].val, table[1, 2].val, table[1, 3].val)
# Sollte: 1 1 test123 Test Palette
```

## Automatischer Test-Durchlauf

Vollständiger Test mit allen Schritten:

```python
# === KOMPLETTER TEST ===
print("=== PALETTE SYNC FIX TEST START ===\n")

# 1. Aktiviere Sync
op('/project1').store('PALETTE_SYNC_ENABLED', True)
print("1. ✅ Palette Sync aktiviert\n")

# 2. Lade Module
try:
    watchdog = mod('/project1/palette_logic/watchdog')
    pump = mod('/project1/palette_logic/pump')
    state = mod('/project1/palette_logic/state')
    handler = mod('/project1/palette_logic/eos_notify_handler')
    print("2. ✅ Module geladen\n")
except Exception as e:
    print(f"2. ❌ Module-Fehler: {e}\n")
    # Stop hier
    raise

# 3. Reset Timer
st = state.state
st.last_activity = 0.0
st.last_subscribe = 0.0
st.last_count_request = 0.0
print("3. ✅ Timer zurückgesetzt\n")

# 4. Sende Subscribe
base = op('/project1')
watchdog.ensure_subscribed(base)
print("4. ✅ Subscribe gesendet\n")

# 5. Warte auf Antworten
import time
print("5. ⏳ Warte 3 Sekunden auf EOS-Antworten...\n")
time.sleep(3)

# 6. Prüfe State
print("6. State nach Subscribe:")
for ptype in ['ip', 'fp', 'cp', 'bp']:
    count = st.counts.get(ptype, 0)
    queue_len = len(st.queues.get(ptype, []))
    print(f"   {ptype}: count={count}, queue={queue_len}")
print()

# 7. Prüfe Tabellen
print("7. Paletten-Tabellen:")
for ptype in ['ip', 'fp', 'cp', 'bp']:
    table = base.op(f"palette_logic/pal_{ptype}")
    if table and table.numRows > 1:
        print(f"   ✅ pal_{ptype}: {table.numRows} Zeilen")
        # Zeige erste Palette
        row_data = [table[1, col].val for col in range(min(4, table.numCols))]
        print(f"      Palette #1: {row_data}")
    else:
        print(f"   ⚠️  pal_{ptype}: {table.numRows if table else 0} Zeilen")
print()

print("=== TEST ENDE ===")
print("Prüfe Textport für [palette] DEBUG Nachrichten!")
```

## Nächste Schritte

Falls die Paletten jetzt korrekt geladen werden:

1. **UI Integration**: Die Paletten können jetzt in der UI angezeigt werden
2. **Update-Mechanismus**: Bei Änderungen in EOS automatisch aktualisieren
3. **Performance**: Rate-Limiting ist bereits implementiert (20 Requests/Sekunde max)

## Technische Details

### OSC API Mapping

| EOS Request | EOS Response | Inhalt |
|-------------|--------------|--------|
| `/eos/get/ip/count` | `/eos/out/get/ip/count [42.0]` | Anzahl Paletten |
| `/eos/get/ip/1/list/0/1` | `/eos/out/get/ip/1/list/0/1 [0, uid, label, ...]` | Palette #1 Daten |
| `/eos/get/ip/2/list/0/1` | `/eos/out/get/ip/2/list/0/1 [0, uid, label, ...]` | Palette #2 Daten |

### Datenfluss

1. **Subscribe**: `/eos/subscribe [1]` → EOS aktiviert OSC-Übertragung
2. **Count**: `/eos/get/{type}/count` → EOS sendet Anzahl Paletten
3. **Queue**: System erstellt Queue mit Palette-Nummern (1, 2, 3, ...)
4. **Request**: `/eos/get/{type}/{num}/list/0/1` für jede Palette
5. **Response**: EOS sendet `/eos/out/get/{type}/{num}/list/...` mit Daten
6. **Update**: Handler schreibt Daten in Tabelle (Zeile = Palette-Nummer)
7. **ACK**: Pump erhält ACK und sendet nächste Anfrage

## Kontakt

Bei Problemen prüfe:
- [PALETTE_SYNC_TEST.md](PALETTE_SYNC_TEST.md) - Ursprüngliche Test-Anleitung
- [diagnose_palette_sync.py](palette_logic/diagnose_palette_sync.py) - Diagnose-Tool
- TouchDesigner Textport für Debug-Ausgaben
