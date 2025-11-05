"""
PALETTE SYNC - Korrekte Initialisierung

Führe dieses Script aus, um Palette-Sync zu starten:
    exec(open(r"c:\_DEV\TOUCHDESIGNER\PALETTE_SYNC_START.py").read())
"""

print("\n" + "=" * 70)
print(" " * 20 + "PALETTE SYNC START")
print("=" * 70 + "\n")

# WICHTIG: PALETTE_SYNC_ENABLED ZUERST setzen, BEVOR Requests gesendet werden!
base = op('/project1')
base.store('PALETTE_SYNC_ENABLED', True)
print("1. ✅ PALETTE_SYNC_ENABLED = True\n")

# Lade Module
try:
    watchdog = mod('/project1/palette_logic/watchdog')
    state = mod('/project1/palette_logic/state')
    pump = mod('/project1/palette_logic/pump')
    print("2. ✅ Module geladen\n")
except Exception as e:
    print(f"2. ❌ Fehler: {e}\n")
    exit()

# Reset Timer
st = state.state
st.last_activity = 0.0
st.last_subscribe = 0.0
st.last_count_request = 0.0
print("3. ✅ Timer zurückgesetzt\n")

# Jetzt erst Subscribe und Count-Requests senden
print("4. Sende Subscribe und Count-Requests...\n")
watchdog.ensure_subscribed(base)

# Warte auf Counts
print("5. Warte 3 Sekunden auf Count-Antworten...\n")
import time
time.sleep(3)

# Zeige Ergebnisse
print("=" * 70)
print("ERGEBNISSE:")
print("=" * 70 + "\n")

for ptype in ['ip', 'fp', 'cp', 'bp']:
    count = st.counts.get(ptype, 0)
    queue_len = len(st.queues.get(ptype, []))
    active = st.active.get(ptype)

    if count > 0:
        print(f"✅ {ptype.upper():4s} | Count: {count:4d} | Queue: {queue_len:4d} | Active: {active}")
    else:
        print(f"❌ {ptype.upper():4s} | Count: {count:4d} | KEINE DATEN EMPFANGEN!")

print("\n" + "=" * 70)
print("TABELLEN:")
print("=" * 70 + "\n")

for ptype in ['ip', 'fp', 'cp', 'bp']:
    table = base.op(f"palette_logic/pal_{ptype}")
    if not table:
        print(f"❌ pal_{ptype}: NICHT GEFUNDEN!")
        continue

    rows = table.numRows
    has_data = False

    if rows > 1:
        sample = [table[1, col].val for col in range(min(4, table.numCols))]
        has_data = any(cell.strip() for cell in sample if cell)

    if has_data:
        print(f"✅ pal_{ptype}: {rows:4d} Zeilen | Erste Palette: {sample}")
    elif rows > 1:
        print(f"⏳ pal_{ptype}: {rows:4d} Zeilen | SYNC LÄUFT...")
    else:
        print(f"❌ pal_{ptype}: {rows:4d} Zeilen | Nur Header")

print("\n" + "=" * 70)

# Zusammenfassung
total_count = sum(st.counts.get(p, 0) for p in ['ip', 'fp', 'cp', 'bp'])
total_queue = sum(len(st.queues.get(p, [])) for p in ['ip', 'fp', 'cp', 'bp'])

if total_count == 0:
    print("❌ PROBLEM: Keine Counts empfangen!")
    print("\nPrüfe:")
    print("  1. EOS OSC TX ist aktiviert")
    print("  2. IP/Port-Konfiguration ist korrekt")
    print("  3. Führe erneut aus:")
    print("     exec(open(r'c:\\_DEV\\TOUCHDESIGNER\\PALETTE_SYNC_START.py').read())")
elif total_queue > 0:
    print(f"⏳ SYNC LÄUFT: {total_count} Paletten gefunden, {total_queue} noch in Queue")
    print(f"\nWarte {total_queue * 0.05:.1f}s und prüfe dann die Tabellen!")
    print("\nOder führe erneut aus:")
    print("  exec(open(r'c:\\_DEV\\TOUCHDESIGNER\\PALETTE_SYNC_START.py').read())")
else:
    print(f"✅ SYNC ABGESCHLOSSEN: {total_count} Paletten erfolgreich synchronisiert!")

print("=" * 70 + "\n")
