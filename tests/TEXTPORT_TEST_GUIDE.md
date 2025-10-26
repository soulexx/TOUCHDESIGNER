# Blink Manager - Textport Test-Anleitung

## Quick Start - Im TouchDesigner Textport testen

### 1. Blink Manager Zugriff

```python
# Manager-Modul laden
blink = op('/project1/io/led_blink_manager').module

# Patterns anzeigen
patterns = blink.reload_patterns()
print("Verfügbare Patterns:", patterns)
# Erwartet: ['slow', 'fast', 'pulse']
```

### 2. Einfacher Test - Button 4 blinken lassen

```python
# Langsames Blinken starten (slow pattern)
blink.start('btn/4', 'slow', color='blue', priority=10)

# Warten... (Button sollte jetzt blinken: press 0.5s / idle 0.5s)

# Blinken stoppen
blink.stop('btn/4')
```

### 3. Verschiedene Patterns testen

```python
# Fast Pattern (0.2s press / 0.2s off)
blink.start('btn/4', 'fast', color='red', priority=10)
# Warten 3 Sekunden...
blink.stop('btn/4')

# Pulse Pattern (0.1s press / 0.4s idle)
blink.start('btn/4', 'pulse', color='green', priority=10)
# Warten 3 Sekunden...
blink.stop('btn/4')

# Slow Pattern (0.5s press / 0.5s idle)
blink.start('btn/4', 'slow', color='blue', priority=10)
# Warten 3 Sekunden...
blink.stop('btn/4')
```

### 4. Mehrere Buttons gleichzeitig

```python
# Verschiedene Buttons mit verschiedenen Patterns
blink.start('btn/1', 'slow', color='red', priority=10)
blink.start('btn/2', 'fast', color='green', priority=10)
blink.start('btn/3', 'pulse', color='blue', priority=10)

# Aktive Targets anzeigen
active = blink.active_targets()
print("Aktive Blinks:", active)

# Alle stoppen
blink.stop('btn/1')
blink.stop('btn/2')
blink.stop('btn/3')

# Oder alle auf einmal
blink.stop_all(restore=True)
```

### 5. Priority-System testen

```python
# Niedrige Priority
blink.start('btn/4', 'slow', color='white', priority=5)
print("Slow mit priority 5 gestartet")

# Versuch mit niedrigerer Priority (wird abgelehnt)
result = blink.start('btn/4', 'fast', color='red', priority=3)
print("Fast mit priority 3:", "OK" if result else "ABGELEHNT")
# Erwartet: ABGELEHNT

# Höhere Priority überschreibt
result = blink.start('btn/4', 'pulse', color='green', priority=10)
print("Pulse mit priority 10:", "OK" if result else "ABGELEHNT")
# Erwartet: OK (überschreibt slow)

blink.stop('btn/4')
```

### 6. Base State System testen

```python
# Base State setzen (Fallback wenn kein Blink)
blink.update_base('btn/4', 'idle', 'blue')

# Blink starten
blink.start('btn/4', 'fast', color='red', priority=10)
# Button blinkt jetzt rot

# Stoppen mit restore=True (kehrt zu base state zurück)
blink.stop('btn/4', restore=True)
# Button sollte jetzt idle blue sein
```

### 7. Status abfragen

```python
# Prüfen ob ein Target aktiv blinkt
is_blinking = blink.is_active('btn/4')
print("btn/4 blinkt:", is_blinking)

# Alle aktiven Targets
active = blink.active_targets()
print("Alle aktiven Blinks:", active)
```

### 8. Integration mit Menu System testen

```python
# Menu Engine laden
menu = op('/project1/layers/menus/menu_engine').module

# Menu 4 aktivieren (hat Submenu mit Blink)
menu._set_active(4)
menu.apply_menu_leds(4)

# Submenu durchschalten (Button 4 drücken simulieren)
menu._advance_submenu(4)
menu.apply_menu_leds(4)
# Schau ob btn/4 blinkt (je nach Submenu)

# Status anzeigen
active_submenu = menu._active_submenu_entry(4)
print("Aktives Submenu:", active_submenu)
```

## Kompletter Test-Durchlauf

```python
# === VOLLSTÄNDIGER TEST ===
print("=" * 60)
print("BLINK MANAGER LIVE TEST")
print("=" * 60)

# 1. Setup
blink = op('/project1/io/led_blink_manager').module
patterns = blink.reload_patterns()
print(f"✓ Patterns geladen: {patterns}")

# 2. Test Pattern-Start
print("\n--- Test 1: Pattern Start ---")
result = blink.start('btn/4', 'slow', color='blue', priority=10)
print(f"✓ Start slow pattern: {'OK' if result else 'FEHLER'}")

import time
time.sleep(2)  # Warte 2 Sekunden (sollte 4x blinken)

# 3. Test Pattern-Wechsel
print("\n--- Test 2: Pattern Wechsel ---")
result = blink.start('btn/4', 'fast', color='red', priority=15)
print(f"✓ Wechsel zu fast pattern: {'OK' if result else 'FEHLER'}")

time.sleep(2)  # Warte 2 Sekunden

# 4. Test Stop
print("\n--- Test 3: Stop ---")
result = blink.stop('btn/4', restore=True)
print(f"✓ Stop: {'OK' if result else 'FEHLER'}")

# 5. Status
print("\n--- Status ---")
active = blink.active_targets()
print(f"Aktive Blinks: {active}")
print(f"btn/4 aktiv: {blink.is_active('btn/4')}")

print("\n✓ TEST ABGESCHLOSSEN")
```

## Erwartete Ausgabe

```
============================================================
BLINK MANAGER LIVE TEST
============================================================
✓ Patterns geladen: ['slow', 'fast', 'pulse']

--- Test 1: Pattern Start ---
✓ Start slow pattern: OK

--- Test 2: Pattern Wechsel ---
✓ Wechsel zu fast pattern: OK

--- Test 3: Stop ---
✓ Stop: OK

--- Status ---
Aktive Blinks: []
btn/4 aktiv: False

✓ TEST ABGESCHLOSSEN
```

## Troubleshooting

### "AttributeError: 'NoneType' object has no attribute 'module'"

**Problem:** Operator nicht gefunden

**Lösung:**
```python
# Prüfen ob Operator existiert
manager_op = op('/project1/io/led_blink_manager')
print("Manager OP:", manager_op)

# Wenn None -> Pfad prüfen oder DAT erstellen
```

### Blink funktioniert nicht / keine LED-Änderung

**Mögliche Ursachen:**
1. Execute DAT nicht aktiv → Prüfe `/project1/io/led_blink_exec`
2. Driver fehlt → Prüfe `/project1/io/driver_led`
3. LED Const fehlt → Prüfe `/project1/io/led_const`

**Debug:**
```python
# Prüfe alle Komponenten
components = [
    '/project1/io/led_blink_manager',
    '/project1/io/led_blink_exec',
    '/project1/io/driver_led',
    '/project1/io/led_const',
]

for path in components:
    op_obj = op(path)
    print(f"{path}: {'✓ OK' if op_obj else '❌ FEHLT'}")
```

### Pattern wird nicht gefunden

**Prüfen:**
```python
# Pattern-Datei prüfen
patterns_dat = op('/project1/io/led_blink_patterns')
print("Patterns DAT:", patterns_dat)
print("Rows:", patterns_dat.numRows if patterns_dat else "N/A")

# Patterns neu laden
blink = op('/project1/io/led_blink_manager').module
patterns = blink.reload_patterns()
print("Verfügbar:", patterns)
```

## Visueller Test

Um zu sehen ob der Blink Manager läuft:

1. **Textport öffnen** (Alt+T)
2. **Test starten:**
   ```python
   blink = op('/project1/io/led_blink_manager').module
   blink.start('btn/4', 'slow', color='blue', priority=10)
   ```
3. **LED beobachten:** Button 4 sollte alle 0.5s zwischen press und idle wechseln
4. **Stoppen:**
   ```python
   blink.stop('btn/4')
   ```

## Pattern-Referenz

| Pattern | Press-Zeit | Idle/Off-Zeit | Gesamt-Zyklus |
|---------|-----------|---------------|---------------|
| slow    | 0.5s      | 0.5s (idle)   | 1.0s          |
| fast    | 0.2s      | 0.2s (off)    | 0.4s          |
| pulse   | 0.1s      | 0.4s (idle)   | 0.5s          |
