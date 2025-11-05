"""
TEST PALETTE SYNC - Schnelltest für EOS Paletten-Synchronisation

Einfach im TouchDesigner Textport ausführen:
    exec(open(r"c:\_DEV\TOUCHDESIGNER\TEST_PALETTE_SYNC.py").read())
"""

print("\n" + "=" * 70)
print(" " * 20 + "PALETTE SYNC TEST")
print("=" * 70 + "\n")

# 1. Aktiviere Palette Sync
print("Schritt 1: Aktiviere PALETTE_SYNC_ENABLED...")
base = op('/project1')
base.store('PALETTE_SYNC_ENABLED', True)
print("   ✅ PALETTE_SYNC_ENABLED = True\n")

# 2. Lade Module
print("Schritt 2: Lade Module...")
try:
    watchdog = mod('/project1/palette_logic/watchdog')
    state = mod('/project1/palette_logic/state')
    pump = mod('/project1/palette_logic/pump')
    print("   ✅ Alle Module geladen\n")
except Exception as e:
    print(f"   ❌ FEHLER: {e}\n")
    print("=" * 70 + "\n")
    exit()

# 3. Reset Timer
print("Schritt 3: Reset Timer...")
st = state.state
st.last_activity = 0.0
st.last_subscribe = 0.0
st.last_count_request = 0.0
print("   ✅ Timer zurückgesetzt\n")

# 4. Sende Subscribe und Count-Requests
print("Schritt 4: Sende Subscribe und Count-Requests...")
watchdog.ensure_subscribed(base)
print("   ✅ Requests gesendet\n")

# 5. Warte
print("Schritt 5: Warte 3 Sekunden auf EOS-Antworten...")
import time
time.sleep(3)
print("   ✅ Wartezeit abgelaufen\n")

# 6. Zeige Ergebnisse
print("Schritt 6: Prüfe Ergebnisse\n")
print("=" * 70)
print("COUNTS & QUEUES:")
print("-" * 70)

results = []
for ptype in ['ip', 'fp', 'cp', 'bp']:
    count = st.counts.get(ptype, 0)
    queue_len = len(st.queues.get(ptype, []))
    active = st.active.get(ptype)

    status = "✅" if count > 0 else "❌"
    print(f"{status} {ptype.upper():4s} | Count: {count:3d} | Queue: {queue_len:3d} | Active: {active}")

    results.append((ptype, count, queue_len))

print("\n" + "=" * 70)
print("PALETTEN-TABELLEN:")
print("-" * 70)

for ptype in ['ip', 'fp', 'cp', 'bp']:
    table = base.op(f"palette_logic/pal_{ptype}")
    if not table:
        print(f"❌ pal_{ptype}: NICHT GEFUNDEN!")
        continue

    rows = table.numRows
    # Prüfe ob Row 1 Daten hat
    has_data = False
    sample_data = []

    if rows > 1:
        sample_data = [table[1, col].val for col in range(min(4, table.numCols))]
        has_data = any(cell.strip() for cell in sample_data if cell)

    if has_data:
        print(f"✅ pal_{ptype}: {rows:3d} Zeilen | Palette #1: {sample_data}")
    elif rows > 1:
        print(f"⚠️  pal_{ptype}: {rows:3d} Zeilen | LEER (keine Daten in Row 1)")
    else:
        print(f"❌ pal_{ptype}: {rows:3d} Zeilen | Nur Header")

print("\n" + "=" * 70)
print("ZUSAMMENFASSUNG:")
print("-" * 70)

total_counts = sum(count for _, count, _ in results)
total_queues = sum(queue for _, _, queue in results)

if total_counts == 0:
    print("❌ PROBLEM: Keine Counts empfangen!")
    print("\nMögliche Ursachen:")
    print("  1. EOS antwortet nicht (prüfe EOS OSC TX-Konfiguration)")
    print("  2. OSC-Verbindung unterbrochen")
    print("  3. Falsche IP-Adresse/Port")
    print("\nDebug-Schritte:")
    print("  1. Prüfe oscin1_from_eos Tabelle auf eingehende Nachrichten")
    print("  2. Prüfe Textport auf [palette] DEBUG Ausgaben")
    print("  3. Führe aus: mod('/project1/palette_logic/force_palette_sync').check_osc_messages()")
elif total_queues > 0:
    print(f"⏳ SYNC LÄUFT: {total_counts} Paletten gefunden, {total_queues} in Queue")
    print("\nWarte noch ein paar Sekunden und prüfe dann die Tabellen erneut!")
    print("Führe aus: exec(open(r'c:\\_DEV\\TOUCHDESIGNER\\TEST_PALETTE_SYNC.py').read())")
else:
    print(f"✅ SYNC ABGESCHLOSSEN: {total_counts} Paletten synchronisiert!")

print("\n" + "=" * 70)
print("Prüfe das TouchDesigner Textport für detaillierte Debug-Ausgaben:")
print("  [palette] DEBUG received count: ...")
print("  [palette] DEBUG received list: ...")
print("  [palette] DEBUG ... ACK ...")
print("=" * 70 + "\n")
