# EOS Palette Sync - Test Guide

## Vorbereitung

1. **Textport öffnen**: `Alt + T` in TouchDesigner
2. **EOS Verbindung prüfen**: OSC sollte konfiguriert sein

## Test-Befehle für Textport

### 1. Palette Sync aktivieren

```python
# Palette Sync einschalten
op('/project1').store('PALETTE_SYNC_ENABLED', True)
print("Palette Sync ENABLED")
```

### 2. Status prüfen

```python
# Prüfe ob Module geladen sind
try:
    watchdog = mod('/project1/palette_logic/watchdog')
    pump = mod('/project1/palette_logic/pump')
    state = mod('/project1/palette_logic/state')
    handler = mod('/project1/palette_logic/eos_notify_handler')
    print("✅ Alle Module geladen")
except Exception as e:
    print(f"❌ Fehler beim Laden: {e}")
```

### 3. OSC-Verbindung prüfen

```python
# Prüfe OSC Operator
osc_out = op('/project1/io/oscout1')
if osc_out:
    print(f"✅ OSC Out gefunden: {osc_out}")
else:
    print("❌ OSC Out nicht gefunden!")

# Prüfe OSC In
osc_in = op('/project1/io/oscin1_from_eos')
if osc_in:
    print(f"✅ OSC In gefunden: {osc_in.numRows} Zeilen")
else:
    print("❌ OSC In nicht gefunden!")
```

### 4. Manuell Subscribe senden

```python
# Subscribe manuell triggern
base = op('/project1')
watchdog = mod('/project1/palette_logic/watchdog')
watchdog.ensure_subscribed(base)
print("Subscribe-Request gesendet - prüfe Textport für Debug-Output")
```

### 5. Manuell Count-Request senden

```python
# Count-Request für alle Palette-Typen
base = op('/project1')
watchdog = mod('/project1/palette_logic/watchdog')
watchdog.request_all_counts(base)
print("Count-Requests gesendet - prüfe Textport für Antworten")
```

### 6. State anzeigen

```python
# Zeige aktuellen State
state = mod('/project1/palette_logic/state')
st = state.state

print("=== PALETTE SYNC STATE ===")
print(f"Subscribed: {st.subscribed}")
print(f"Last Activity: {absTime.seconds - st.last_activity:.1f}s ago")
print(f"Last Subscribe: {absTime.seconds - st.last_subscribe:.1f}s ago")
print(f"Last Count Request: {absTime.seconds - st.last_count_request:.1f}s ago")
print("\n=== PALETTE COUNTS ===")
for pal_type in ['ip', 'fp', 'cp', 'bp']:
    count = st.counts.get(pal_type, 0)
    queue_len = len(st.queues.get(pal_type, []))
    active = st.active.get(pal_type)
    print(f"{pal_type}: count={count}, queue={queue_len}, active={active}")
```

### 7. Queue-Status anzeigen

```python
# Zeige Queue-Details für Intensity Palettes
state = mod('/project1/palette_logic/state')
st = state.state

print("=== INTENSITY PALETTE QUEUE ===")
queue = st.queues.get('ip', [])
print(f"Queue length: {len(queue)}")
if len(queue) > 0:
    print(f"Next 10 in queue: {list(queue)[:10]}")
    print(f"Active palette: {st.active.get('ip')}")
```

### 8. Palette-Tabelle anzeigen

```python
# Zeige erste 10 Paletten aus Tabelle
table = op('/project1/palette_logic/pal_ip')
if table:
    print("=== INTENSITY PALETTES (erste 10) ===")
    for row in range(min(10, table.numRows)):
        cells = [table[row, col].val for col in range(table.numCols)]
        print(f"Row {row}: {cells}")
else:
    print("❌ Tabelle pal_ip nicht gefunden!")
```

### 9. Manuell einzelne Palette abrufen

```python
# Fordere Palette #1 manuell an (zum Testen)
osc_out = op('/project1/io/oscout1')
if osc_out:
    # Nutze neue korrekte API
    osc_out.sendOSC('/eos/get/ip/1/list/0/1', [])
    print("Request gesendet: /eos/get/ip/1/list/0/1")
    print("Prüfe Textport für Antwort: [palette] DEBUG received list: ...")
else:
    print("❌ OSC Out nicht gefunden!")
```

### 10. Palette Sync deaktivieren

```python
# Palette Sync ausschalten
op('/project1').store('PALETTE_SYNC_ENABLED', False)
print("Palette Sync DISABLED")
```

### 11. OSC-Log live beobachten

```python
# Zeige letzte 20 OSC-Nachrichten
osc_in = op('/project1/io/oscin1_from_eos')
if osc_in:
    start = max(0, osc_in.numRows - 20)
    print(f"=== LETZTE {osc_in.numRows - start} OSC MESSAGES ===")
    for i in range(start, osc_in.numRows):
        row = [osc_in[i, col].val for col in range(osc_in.numCols)]
        print(f"{i}: {row}")
else:
    print("❌ OSC In nicht gefunden!")
```

## Erwartete Debug-Ausgaben

### Beim Subscribe:
```
[palette] DEBUG sending subscribe (last activity: 5.2s ago)
[palette] subscribe sent
```

### Bei Count-Requests:
```
[palette] DEBUG requesting counts (last request: 10.3s ago)
[palette] count request ip
[palette] count request fp
[palette] count request cp
[palette] count request bp
```

### Bei Count-Antworten:
```
[palette] DEBUG received count: ip=42 | OSC: /eos/out/get/ip/count [42.0]
[palette] DEBUG ip queue initialized: 42 palettes (1-42)
```

### Bei Palette-Requests:
```
[palette] send ip palette #1
[palette] send ip palette #2
...
```

### Bei Palette-Antworten:
```
[palette] DEBUG received list: ip #1 idx=0 uid='abc123' label='Warm'
[palette] DEBUG ip palette #1 ACK (queue: 41 remaining)
```

## Troubleshooting

### Kein Output im Textport?
```python
# Prüfe ob Callbacks aktiv sind
tick_exec = op('/project1/io/tick_exec')
if tick_exec:
    print(f"✅ tick_exec gefunden: {tick_exec}")
    print(f"Active: {tick_exec.par.active}")
else:
    print("❌ tick_exec nicht gefunden!")

osc_callbacks = op('/project1/io/oscin1_callbacks')
if osc_callbacks:
    print(f"✅ OSC callbacks gefunden")
else:
    print("❌ OSC callbacks nicht gefunden!")
```

### Subscribe wird nicht gesendet?
```python
# Force Subscribe
state = mod('/project1/palette_logic/state')
state.state.last_activity = 0.0  # Reset activity timer
state.state.last_subscribe = 0.0  # Reset subscribe timer

base = op('/project1')
watchdog = mod('/project1/palette_logic/watchdog')
watchdog.ensure_subscribed(base)
```

### EOS antwortet nicht?
```python
# Ping EOS
osc_out = op('/project1/io/oscout1')
if osc_out:
    osc_out.sendOSC('/eos/ping', [])
    print("Ping gesendet - prüfe auf /eos/out/ping Antwort")
```

## Vollständiger Test-Durchlauf

```python
# === KOMPLETTER TEST ===
print("=== PALETTE SYNC TEST START ===\n")

# 1. Aktiviere Sync
op('/project1').store('PALETTE_SYNC_ENABLED', True)
print("1. Palette Sync aktiviert\n")

# 2. Lade Module
try:
    watchdog = mod('/project1/palette_logic/watchdog')
    pump = mod('/project1/palette_logic/pump')
    state = mod('/project1/palette_logic/state')
    print("2. Module geladen ✅\n")
except Exception as e:
    print(f"2. Module-Fehler ❌: {e}\n")
    exit()

# 3. Prüfe OSC
osc_out = op('/project1/io/oscout1')
osc_in = op('/project1/io/oscin1_from_eos')
if osc_out and osc_in:
    print(f"3. OSC bereit ✅ (In: {osc_in.numRows} rows)\n")
else:
    print("3. OSC nicht bereit ❌\n")

# 4. Sende Subscribe
base = op('/project1')
watchdog.ensure_subscribed(base)
print("4. Subscribe gesendet - warte 2 Sekunden...\n")

# 5. Warte und prüfe State
import time
time.sleep(2)

st = state.state
print("5. State nach Subscribe:")
print(f"   Subscribed: {st.subscribed}")
print(f"   Counts: ip={st.counts.get('ip', 0)}, fp={st.counts.get('fp', 0)}, cp={st.counts.get('cp', 0)}, bp={st.counts.get('bp', 0)}")
print(f"   Queues: ip={len(st.queues.get('ip', []))}, fp={len(st.queues.get('fp', []))}\n")

# 6. Prüfe Tabelle
table = op('/project1/palette_logic/pal_ip')
if table and table.numRows > 1:
    print(f"6. Tabelle pal_ip: {table.numRows} rows ✅")
    print(f"   Erste Palette: {[table[1, col].val for col in range(min(4, table.numCols))]}\n")
else:
    print("6. Tabelle leer oder nicht gefunden ❌\n")

print("=== TEST ENDE ===")
print("Prüfe Textport-Output für [palette] DEBUG Nachrichten!")
```
