"""
Force Palette Sync - Manuelles Sync-Script für EOS Paletten

Führe dieses Script aus, um alle Paletten manuell zu synchronisieren:
    exec(open(r"c:\_DEV\TOUCHDESIGNER\palette_logic\force_palette_sync.py").read())
"""
import time


def force_sync_all_palettes():
    """Erzwingt eine vollständige Synchronisation aller Paletten-Typen."""
    print("\n" + "=" * 60)
    print("FORCE PALETTE SYNC")
    print("=" * 60 + "\n")

    base = op('/project1')
    if not base:
        print("❌ FEHLER: /project1 nicht gefunden!")
        return

    # 1. Aktiviere Palette Sync
    base.store('PALETTE_SYNC_ENABLED', True)
    print("1. ✅ PALETTE_SYNC_ENABLED = True\n")

    # 2. Lade Module
    try:
        state_mod = mod('/project1/palette_logic/state')
        pump_mod = mod('/project1/palette_logic/pump')
        watchdog_mod = mod('/project1/palette_logic/watchdog')
        print("2. ✅ Module geladen\n")
    except Exception as e:
        print(f"2. ❌ Fehler beim Laden: {e}\n")
        return

    # 3. Reset State
    st = state_mod.state
    st.last_activity = 0.0
    st.last_subscribe = 0.0
    st.last_count_request = 0.0
    print("3. ✅ State zurückgesetzt\n")

    # 4. Sende Subscribe
    osc_out = base.op("io/oscout1")
    if not osc_out:
        print("4. ❌ OSC Out nicht gefunden!\n")
        return

    osc_out.sendOSC("/eos/subscribe", [1])
    print("4. ✅ Subscribe gesendet\n")

    # 5. Warte kurz
    time.sleep(0.5)

    # 6. Fordere Counts an
    print("5. Count-Requests senden:")
    for ptype in ['ip', 'fp', 'cp', 'bp']:
        osc_out.sendOSC(f"/eos/get/{ptype}/count", [])
        print(f"   → /eos/get/{ptype}/count")
    print()

    # 7. Warte auf Antworten
    print("6. ⏳ Warte 2 Sekunden auf Count-Antworten...\n")
    time.sleep(2)

    # 8. Prüfe State
    print("7. Empfangene Counts:")
    all_ok = True
    for ptype in ['ip', 'fp', 'cp', 'bp']:
        count = st.counts.get(ptype, 0)
        queue_len = len(st.queues.get(ptype, []))
        active = st.active.get(ptype)

        if count > 0:
            print(f"   ✅ {ptype}: count={count}, queue={queue_len}, active={active}")
        else:
            print(f"   ❌ {ptype}: count={count} (keine Daten empfangen!)")
            all_ok = False
    print()

    if not all_ok:
        print("⚠️  WARNUNG: Nicht alle Count-Antworten empfangen!")
        print("   Mögliche Ursachen:")
        print("   - EOS antwortet nicht (prüfe EOS OSC-Konfiguration)")
        print("   - OSC-Callback-Handler funktioniert nicht")
        print("   - PALETTE_SYNC_ENABLED war noch nicht aktiv\n")

    # 9. Warte auf erste Paletten-Daten
    print("8. ⏳ Warte 3 Sekunden auf Paletten-Daten...\n")
    time.sleep(3)

    # 10. Prüfe Tabellen
    print("9. Paletten-Tabellen Status:")
    for ptype in ['ip', 'fp', 'cp', 'bp']:
        table = base.op(f"palette_logic/pal_{ptype}")
        if not table:
            print(f"   ❌ pal_{ptype}: NICHT GEFUNDEN!")
            continue

        rows = table.numRows
        # Prüfe ob Daten in Row 1 sind (Row 0 ist Header)
        has_data = False
        if rows > 1:
            first_row = [table[1, col].val for col in range(min(6, table.numCols))]
            # Prüfe ob mindestens ein Feld gefüllt ist
            has_data = any(cell.strip() for cell in first_row if cell)

        if has_data:
            print(f"   ✅ pal_{ptype}: {rows} Zeilen (mit Daten)")
            print(f"      Erste Palette: {first_row[:4]}")
        elif rows > 1:
            print(f"   ⚠️  pal_{ptype}: {rows} Zeilen (LEER!)")
        else:
            print(f"   ⚠️  pal_{ptype}: {rows} Zeilen (nur Header)")
    print()

    print("=" * 60)
    print("Sync abgeschlossen!")
    print("=" * 60)
    print("\nPrüfe das Textport für [palette] DEBUG Nachrichten!")
    print("Wenn Paletten immer noch leer sind, prüfe:")
    print("  1. EOS OSC-Konfiguration (TX aktiviert?)")
    print("  2. EOS antwortet auf Requests (siehe OSC In Tabelle)")
    print("  3. Regex-Patterns in eos_notify_handler.py\n")


def check_osc_messages():
    """Zeigt die letzten OSC-Nachrichten von EOS."""
    print("\n" + "=" * 60)
    print("LETZTE OSC-NACHRICHTEN VON EOS")
    print("=" * 60 + "\n")

    osc_in = op('/project1/io/oscin1_from_eos')
    if not osc_in:
        print("❌ oscin1_from_eos nicht gefunden!\n")
        return

    print(f"Gesamt: {osc_in.numRows} Nachrichten empfangen\n")
    print("Letzte 20 Nachrichten:")
    start = max(0, osc_in.numRows - 20)

    for i in range(start, osc_in.numRows):
        row_data = [osc_in[i, col].val for col in range(min(3, osc_in.numCols))]
        address = row_data[1] if len(row_data) > 1 else ""

        # Highlight palette-relevante Nachrichten
        if '/eos/out/get/' in address:
            print(f"   {i}: ⭐ {row_data}")
        else:
            print(f"   {i}: {row_data}")

    print("\n" + "=" * 60 + "\n")


def manually_inject_count(palette_type: str, count: int):
    """Injiziert manuell einen Count-Wert (für Testing)."""
    print(f"\nManuell injiziere Count für {palette_type}: {count}")

    base = op('/project1')
    try:
        pump_mod = mod('/project1/palette_logic/pump')
        pump_mod.attach_base(base)
        pump_mod.queue_counts(base, {palette_type: count})
        print(f"✅ Count {palette_type}={count} injiziert\n")
    except Exception as e:
        print(f"❌ Fehler: {e}\n")


# Auto-run wenn direkt ausgeführt
if __name__ == "__main__":
    force_sync_all_palettes()
