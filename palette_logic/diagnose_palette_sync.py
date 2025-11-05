"""
Diagnose-Script für EOS Palette-Sync Probleme.

Führe dieses Script im TouchDesigner Textport aus:
    exec(open(r"c:\_DEV\TOUCHDESIGNER\palette_logic\diagnose_palette_sync.py").read())

Oder in TouchDesigner:
    mod('/project1/palette_logic/diagnose_palette_sync').run_diagnostics()
"""
import time


def run_diagnostics():
    """Führt eine umfassende Diagnose des Palette-Sync-Systems durch."""
    print("\n" + "=" * 60)
    print("EOS PALETTE SYNC DIAGNOSTICS")
    print("=" * 60 + "\n")

    base = op('/project1')
    if not base:
        print("❌ FEHLER: /project1 nicht gefunden!")
        return

    # 1. Check PALETTE_SYNC_ENABLED
    print("1. PALETTE_SYNC_ENABLED Status:")
    enabled = bool(base.fetch("PALETTE_SYNC_ENABLED", False))
    if enabled:
        print(f"   ✅ AKTIVIERT: {enabled}")
    else:
        print(f"   ❌ DEAKTIVIERT: {enabled}")
        print("   → Aktivieren mit: op('/project1').store('PALETTE_SYNC_ENABLED', True)")
    print()

    # 2. Check OSC Operators
    print("2. OSC Operatoren:")
    osc_out = base.op("io/oscout1")
    osc_in = base.op("io/oscin1_from_eos")

    if osc_out:
        print(f"   ✅ oscout1: {osc_out.par.address}:{osc_out.par.port}")
    else:
        print("   ❌ oscout1 nicht gefunden!")

    if osc_in:
        print(f"   ✅ oscin1_from_eos: {osc_in.numRows} Zeilen empfangen")
    else:
        print("   ❌ oscin1_from_eos nicht gefunden!")
    print()

    # 3. Check Modules
    print("3. Module Status:")
    modules_ok = True
    module_names = ['state', 'pump', 'watchdog', 'eos_notify_handler']
    for name in module_names:
        try:
            mod_obj = mod(f'/project1/palette_logic/{name}')
            print(f"   ✅ {name}: geladen")
        except Exception as e:
            print(f"   ❌ {name}: FEHLER - {e}")
            modules_ok = False
    print()

    if not modules_ok:
        print("⚠️  Nicht alle Module konnten geladen werden!")
        return

    # 4. Check State
    print("4. Palette State:")
    try:
        state_mod = mod('/project1/palette_logic/state')
        st = state_mod.state

        now = time.perf_counter()
        print(f"   Subscribed: {st.subscribed}")
        print(f"   Last Activity: {now - st.last_activity:.1f}s ago")
        print(f"   Last Subscribe: {now - st.last_subscribe:.1f}s ago")
        print(f"   Last Count Request: {now - st.last_count_request:.1f}s ago")
    except Exception as e:
        print(f"   ❌ FEHLER beim State-Check: {e}")
    print()

    # 5. Check Counts & Queues
    print("5. Palette Counts & Queues:")
    try:
        for ptype in ['ip', 'fp', 'cp', 'bp']:
            count = st.counts.get(ptype, 0)
            queue = st.queues.get(ptype, [])
            active = st.active.get(ptype)
            queue_len = len(queue)

            status = "✅" if count > 0 else "⚠️ "
            print(f"   {status} {ptype}: count={count}, queue={queue_len}, active={active}")

            if queue_len > 0:
                print(f"      Queue preview: {list(queue)[:5]}{'...' if queue_len > 5 else ''}")
    except Exception as e:
        print(f"   ❌ FEHLER: {e}")
    print()

    # 6. Check Tables
    print("6. Palette Tabellen:")
    try:
        for ptype in ['ip', 'fp', 'cp', 'bp']:
            table = base.op(f"palette_logic/pal_{ptype}")
            if table:
                rows = table.numRows
                cols = table.numCols
                status = "✅" if rows > 1 else "⚠️ "
                print(f"   {status} pal_{ptype}: {rows} rows x {cols} cols")

                if rows > 1:
                    # Show first data row
                    row_data = [table[1, col].val for col in range(min(6, cols))]
                    print(f"      Row 1: {row_data}")
            else:
                print(f"   ❌ pal_{ptype}: NICHT GEFUNDEN!")
    except Exception as e:
        print(f"   ❌ FEHLER: {e}")
    print()

    # 7. Check OSC Callbacks
    print("7. OSC Callbacks:")
    try:
        osc_cb = base.op("io/osc_in_callbacks")
        if osc_cb:
            print(f"   ✅ osc_in_callbacks gefunden")
        else:
            print(f"   ❌ osc_in_callbacks nicht gefunden!")

        oscin1_cb = base.op("io/oscin1_callbacks")
        if oscin1_cb:
            print(f"   ✅ oscin1_callbacks gefunden")
        else:
            print(f"   ❌ oscin1_callbacks nicht gefunden!")
    except Exception as e:
        print(f"   ❌ FEHLER: {e}")
    print()

    # 8. Check last OSC messages
    print("8. Letzte OSC Nachrichten (von EOS):")
    try:
        if osc_in and osc_in.numRows > 0:
            start = max(0, osc_in.numRows - 10)
            for i in range(start, osc_in.numRows):
                row = [osc_in[i, col].val for col in range(min(3, osc_in.numCols))]
                print(f"   {i}: {row}")
        else:
            print("   ⚠️  Keine OSC Nachrichten empfangen")
    except Exception as e:
        print(f"   ❌ FEHLER: {e}")
    print()

    # 9. Recommendations
    print("=" * 60)
    print("EMPFEHLUNGEN:")
    print("=" * 60)

    if not enabled:
        print("1. ❌ Palette Sync ist DEAKTIVIERT!")
        print("   Aktiviere mit: op('/project1').store('PALETTE_SYNC_ENABLED', True)")

    if st.counts.get('ip', 0) == 0:
        print("2. ⚠️  Keine Paletten-Counts empfangen!")
        print("   Manuell anfordern:")
        print("   watchdog = mod('/project1/palette_logic/watchdog')")
        print("   watchdog.request_all_counts(op('/project1'))")

    table_ip = base.op("palette_logic/pal_ip")
    if table_ip and table_ip.numRows <= 1:
        print("3. ⚠️  Palette-Tabellen sind leer!")
        print("   Mögliche Ursachen:")
        print("   - EOS sendet keine Antworten (prüfe EOS OSC-Konfiguration)")
        print("   - OSC-Callback-Handler funktioniert nicht")
        print("   - Falsche OSC-API wird verwendet")

    print("\n" + "=" * 60)
    print("Diagnose abgeschlossen!")
    print("=" * 60 + "\n")


def test_single_palette_request():
    """Testet eine einzelne Palette-Anfrage an EOS."""
    print("\n" + "=" * 60)
    print("TEST: Einzelne Palette-Anfrage")
    print("=" * 60 + "\n")

    base = op('/project1')
    osc_out = base.op("io/oscout1")
    osc_in = base.op("io/oscin1_from_eos")

    if not osc_out:
        print("❌ OSC Out nicht gefunden!")
        return

    if not osc_in:
        print("❌ OSC In nicht gefunden!")
        return

    print(f"OSC Out: {osc_out.par.address}:{osc_out.par.port}")
    print(f"OSC In: {osc_in.numRows} Nachrichten bisher\n")

    # Test verschiedene API-Varianten
    print("Sende Test-Anfragen:\n")

    # Variante 1: /eos/get/{type}/count
    print("1. Count-Request: /eos/get/ip/count")
    osc_out.sendOSC("/eos/get/ip/count", [])

    # Variante 2: /eos/get/{type}/index/{index} (aktuelle pump.py)
    print("2. Index-Request (pump.py): /eos/get/ip/index/0")
    osc_out.sendOSC("/eos/get/ip/index/0", [])

    # Variante 3: /eos/get/{type}/{num}/list/{index}/{count} (subscribe_manager.py)
    print("3. List-Request (subscribe_manager.py): /eos/get/ip/1/list/0/1")
    osc_out.sendOSC("/eos/get/ip/1/list/0/1", [])

    print("\n⏳ Warte 2 Sekunden auf Antworten...\n")
    import time
    time.sleep(2)

    print(f"OSC In hat jetzt {osc_in.numRows} Nachrichten")
    print("\nLetzte 5 Nachrichten:")
    start = max(0, osc_in.numRows - 5)
    for i in range(start, osc_in.numRows):
        row_data = [osc_in[i, col].val for col in range(min(3, osc_in.numCols))]
        print(f"   {i}: {row_data}")

    print("\n" + "=" * 60)
    print("Prüfe das Textport auf [palette] DEBUG Ausgaben!")
    print("=" * 60 + "\n")


def enable_palette_sync():
    """Aktiviert Palette Sync und startet die Synchronisation."""
    print("\n" + "=" * 60)
    print("PALETTE SYNC AKTIVIEREN")
    print("=" * 60 + "\n")

    base = op('/project1')
    base.store('PALETTE_SYNC_ENABLED', True)
    print("✅ PALETTE_SYNC_ENABLED = True\n")

    # Reset timers für sofortigen Start
    try:
        state_mod = mod('/project1/palette_logic/state')
        state_mod.state.last_activity = 0.0
        state_mod.state.last_subscribe = 0.0
        state_mod.state.last_count_request = 0.0
        print("✅ Timer zurückgesetzt\n")
    except Exception as e:
        print(f"⚠️  Konnte Timer nicht zurücksetzen: {e}\n")

    # Trigger watchdog
    try:
        watchdog = mod('/project1/palette_logic/watchdog')
        watchdog.ensure_subscribed(base)
        print("✅ Subscribe und Count-Requests gesendet\n")
    except Exception as e:
        print(f"❌ Fehler beim Senden: {e}\n")

    print("=" * 60)
    print("Prüfe das Textport für Debug-Ausgaben!")
    print("=" * 60 + "\n")


# Auto-run if executed directly
if __name__ == "__main__":
    run_diagnostics()
