# Blink Manager - Kurzanleitung

## Setup (einmalig)

1. **Execute DAT erstellen** in `/project1/io/`:
   - Neues Execute DAT → Name: `led_blink_exec`
   - Code aus `io/led_blink_exec.py` reinkopieren
   - Parameter aktivieren: ✓ **Frame Start** + ✓ **Active**

2. **Fertig!** Blink Manager ist einsatzbereit.

---

## Verwendung (Textport oder Python)

### Blinken starten

```python
blink = op('/project1/io/led_blink_manager').module
blink.start('btn/4', 'slow', color='blue', priority=10)
```

**Parameter:**
- `'btn/4'` = Target (btn/1 bis btn/5)
- `'slow'` = Pattern (slow, fast, pulse)
- `color='blue'` = Farbe (optional)
- `priority=10` = Priorität (höher = wichtiger)

### Blinken stoppen

```python
blink = op('/project1/io/led_blink_manager').module
blink.stop('btn/4')
```

### Alle stoppen

```python
blink = op('/project1/io/led_blink_manager').module
blink.stop_all()
```

---

## Verfügbare Patterns

| Pattern | Beschreibung | Timing |
|---------|-------------|--------|
| `slow` | Langsam | 0.5s press / 0.5s idle |
| `fast` | Schnell | 0.2s press / 0.2s off |
| `pulse` | Puls | 0.1s press / 0.4s idle |

---

## Beispiele

### Einzelner Button

```python
blink = op('/project1/io/led_blink_manager').module

# Langsam blau
blink.start('btn/1', 'slow', color='blue', priority=10)

# Schnell rot
blink.start('btn/2', 'fast', color='red', priority=10)

# Puls grün
blink.start('btn/3', 'pulse', color='green', priority=10)
```

### Prioritäten

```python
blink = op('/project1/io/led_blink_manager').module

# Niedrige Priorität
blink.start('btn/4', 'slow', color='white', priority=5)

# Hohe Priorität überschreibt
blink.start('btn/4', 'fast', color='red', priority=10)  # ← wird verwendet

# Niedrige wird abgelehnt
blink.start('btn/4', 'pulse', color='blue', priority=3)  # ← wird ignoriert
```

### Status abfragen

```python
blink = op('/project1/io/led_blink_manager').module

# Ist btn/4 aktiv?
if blink.is_active('btn/4'):
    print("btn/4 blinkt")

# Alle aktiven anzeigen
print("Aktive:", blink.active_targets())
```

### Base State (Fallback)

```python
blink = op('/project1/io/led_blink_manager').module

# Basis-Status setzen (wenn kein Blink aktiv)
blink.update_base('btn/4', 'idle', 'blue')

# Blink starten (überschreibt Base State)
blink.start('btn/4', 'fast', color='red', priority=10)

# Stoppen mit Restore (kehrt zu Base State zurück)
blink.stop('btn/4', restore=True)  # → btn/4 wird idle blue
```

---

## Integration in eigenen Code

### In menu_engine.py oder anderen Modulen

```python
def my_function():
    # Blink Manager laden
    blink_op = op('/project1/io/led_blink_manager')
    if not blink_op:
        print("Blink Manager nicht gefunden")
        return

    blink = getattr(blink_op, 'module', None)
    if not blink:
        print("Blink Manager Modul nicht verfügbar")
        return

    # Verwenden
    blink.start('btn/4', 'slow', color='blue', priority=10)
```

### Submenu-Integration (wie in menu_engine.py)

```python
# Base State setzen
mod = op('/project1/io/led_blink_manager').module
target = "btn/4"
color = "blue"
base_state = "press"  # oder "idle"

mod.update_base(target, base_state, color)

# Pattern starten (wenn gewünscht)
pattern = "slow"  # oder None
if pattern:
    mod.start(target, pattern, color=color,
              base_state=(base_state, color), priority=10)
else:
    mod.stop(target)
```

---

## Neue Patterns hinzufügen

1. Öffne `io/led_blink_patterns.tsv`
2. Neue Zeile hinzufügen:

```tsv
mypattern    [{"state": "press", "duration": 0.3}, {"state": "idle", "duration": 0.3}]
```

3. Verwenden:

```python
blink = op('/project1/io/led_blink_manager').module
blink.start('btn/4', 'mypattern', color='blue', priority=10)
```

**Pattern-Format:**
- `state`: "press", "idle", oder "off"
- `duration`: Zeit in Sekunden (min. 0.01s)
- `color`: Optional, überschreibt Farbe für diesen Step

---

## Troubleshooting

### "AttributeError: 'NoneType' object has no attribute 'module'"

**Problem:** Operator nicht gefunden

**Lösung:**
```python
# Prüfen
print(op('/project1/io/led_blink_manager'))
```
Falls `None` → Pfad falsch oder DAT fehlt

### Blinkt nicht

**Checkliste:**
1. Execute DAT existiert? `op('/project1/io/led_blink_exec')`
2. Execute DAT aktiv? `exec_dat.par.active == True`
3. Frame Start aktiviert? (Parameter im Execute DAT)
4. Blink aktiv? `blink.is_active('btn/4')`

**Debug:**
```python
# Alle Komponenten prüfen
exec_dat = op('/project1/io/led_blink_exec')
print("Execute DAT:", exec_dat, "Active:", exec_dat.par.active if exec_dat else "N/A")

blink = op('/project1/io/led_blink_manager').module
print("Aktive Blinks:", blink.active_targets())
print("Patterns:", blink.reload_patterns())
```

### Pattern nicht gefunden

```python
# Patterns neu laden
blink = op('/project1/io/led_blink_manager').module
patterns = blink.reload_patterns()
print("Verfügbar:", patterns)
```

---

## Quick Reference (Copy & Paste)

```python
# Setup
blink = op('/project1/io/led_blink_manager').module

# Start
blink.start('btn/4', 'slow', color='blue', priority=10)

# Stop
blink.stop('btn/4')

# Stop All
blink.stop_all()

# Status
print(blink.is_active('btn/4'))
print(blink.active_targets())

# Patterns
print(blink.reload_patterns())
```
