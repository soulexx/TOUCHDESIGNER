# Button Long Press Design Documentation

**WICHTIG**: Diese Dokumentation beschreibt die implementierte Button-Behandlung.
**NICHT ÄNDERN** ohne explizite Anforderung!

## Übersicht

Alle Buttons (btn/*, encPush/*) werden **einheitlich** durch den `button_press()` Filter in `event_filters.py` behandelt.

## Architektur

### 1. Filter-Funktion: `event_filters.py`

**Zwei Press-Modi:**

#### `optimistic` (Default)
- **Press**: Sofortige Ausführung der Short Action
- **Release < 1s**: Nichts (bereits ausgeführt)
- **Release ≥ 1s**: Long Action mit Toggle (0→1→0)
- **Use Case**: Buttons wo schnelle Reaktion wichtig ist

#### `timer`
- **Press**: Nichts (Timer startet)
- **Hold ≥ 1s**: Long Action wird automatisch ausgeführt
- **Release < 1s**: Short Action wird ausgeführt
- **Release ≥ 1s**: Nichts (bereits ausgeführt)
- **Use Case**: Buttons wo Short Press nicht versehentlich bei Long Press triggern darf

**Wichtige Funktionen:**
```python
def check_scheduled_buttons():
    """
    Wird am Anfang von handle_event() aufgerufen.
    Prüft Timer und führt fällige Long Press Aktionen aus.
    """

def button_press(topic, value, press_mode='optimistic'):
    """
    Haupt-Filter für alle Buttons.
    Returns: ('press', value) | ('long_press', toggle_value) | None
    """
```

### 2. Menu Engine: `menu_engine.py`

**Alle Buttons werden einheitlich behandelt:**

1. **Menu Buttons (btn/1-5)**
   - Durchlaufen `button_press()` Filter
   - Short Press: Menu-Wechsel + Action
   - Long Press: Nur Action (kein Menu-Wechsel)

2. **Menu 0 Sub Buttons (btn/11-15)**
   - Durchlaufen `button_press()` Filter
   - Short Press: Submenu-Wechsel + Action
   - Long Press: Nur Long Action

3. **Andere Buttons (btn/21-25, encPush/1-5)**
   - Durchlaufen `button_press()` Filter
   - Short Press: `path_out`
   - Long Press: `path_out_long` mit Toggle

**Wichtig**: `_lookup()` gibt jetzt 4 Werte zurück:
```python
path, scale, path_long, press_mode = _lookup(menu_idx, topic)
```

### 3. Map Configuration: `map_osc.tsv`

**Alle 6 Menüs haben diese Spalten:**
```
topic | device | midi_channel | control_id | path_out | scale | enabled | led_color | path_out_long | press_mode
```

**Spalten-Bedeutung:**
- `path_out`: Short Press Action (oder sofortige Action bei optimistic)
- `path_out_long`: Long Press Action (mit Toggle 0→1→0)
- `press_mode`: `optimistic` (leer = default) oder `timer`

## Konfiguration Pro Button

### Beispiel: Timer Mode (empfohlen für kritische Buttons)

```tsv
encPush/2  midicraft  1  2  /eos/param/gobo/home  1  1  white  /eos/param/gobo/reset  timer
```

**Verhalten:**
- Drücken: Nichts (wartet)
- Halten ≥1s: `/eos/param/gobo/reset` mit Toggle 0→1→0
- Loslassen <1s: `/eos/param/gobo/home`

### Beispiel: Optimistic Mode (default für schnelle Reaktion)

```tsv
btn/21  midicraft  1  26  /eos/key/go  1  1  white  /eos/key/go_back
```

**Verhalten:**
- Drücken: `/eos/key/go` sofort
- Loslassen ≥1s: `/eos/key/go_back` mit Toggle

## Toggle-System

**Long Press Actions nutzen Toggle 0→1→0:**
- Erster Long Press: Sendet `1`
- Zweiter Long Press: Sendet `0`
- Dritter Long Press: Sendet `1`
- etc.

Dies ist nützlich für EOS-Parameter die Toggle-Verhalten brauchen.

## Wichtige Design-Entscheidungen

### ✅ ALLE Buttons durch button_press Filter
- Menu Buttons (1-5) ✅
- Menu 0 Sub Buttons (11-15) ✅
- Normale Buttons (btn/21-25) ✅
- Encoder Push Buttons (encPush/1-5) ✅

**Grund**: Konsistente Behandlung, keine Sonderlocken!

### ✅ Timer-Check am Anfang von handle_event()
```python
def handle_event(topic, value):
    _ensure_active()

    # WICHTIG: Check scheduled buttons FIRST
    scheduled_actions = check_scheduled_buttons()
    for btn_topic, action_type, payload in scheduled_actions:
        # Execute long press actions
```

**Grund**: Timer-basierte Long Press müssen regelmäßig geprüft werden!

### ✅ Press Mode aus Map lesen
```python
path, scale, path_long, press_mode = _lookup(menu_idx, topic)
result = button_press(topic, value, press_mode)
```

**Grund**: Flexibilität - jeder Button kann individuell konfiguriert werden!

## Häufige Fehler (NICHT MACHEN!)

### ❌ Buttons ohne Filter behandeln
```python
# FALSCH:
if t.startswith('btn/'):
    pressed = float(value) >= 0.5
    if pressed:
        send_action()  # Ohne button_press Filter!
```

**Richtig**: Alle Buttons durch `button_press()` Filter!

### ❌ check_scheduled_buttons() vergessen
```python
# FALSCH:
def handle_event(topic, value):
    # Direkt mit Event-Verarbeitung starten
```

**Richtig**: `check_scheduled_buttons()` am Anfang aufrufen!

### ❌ press_mode nicht aus Map lesen
```python
# FALSCH:
result = button_press(topic, value)  # Verwendet nur Default
```

**Richtig**: `press_mode` aus `_lookup()` holen und übergeben!

### ❌ Long Press ohne path_out_long
Wenn `path_out_long` leer ist, macht Long Press nichts!
→ Entweder Spalte füllen oder press_mode weglassen.

## Beispiel-Konfigurationen

### Standard Button (schnell reagierend)
```tsv
btn/21  midicraft  1  26  /eos/key/go  1  1  red
```
- Kein `path_out_long` → kein Long Press
- Kein `press_mode` → optimistic (sofortig)

### Button mit Long Press (Timer Mode)
```tsv
encPush/2  midicraft  1  2  /eos/param/gobo/home  1  1  white  /eos/param/gobo/reset  timer
```
- Short <1s: `/home`
- Long ≥1s: `/reset` mit Toggle

### Menu Button mit Long Press
```tsv
# In beliebigem Menu:
btn/4  midicraft  1  4  (menu action)  1  1  blue  /eos/macro/special  timer
```
- Short: Menu wechseln + normale Action
- Long: Nur `/eos/macro/special` (kein Menu-Wechsel)

## Debugging

**Debug-Flag aktivieren:**
```python
# In event_filters.py (Zeile 27)
BUTTON_DEBUG = True   # False to disable
```

**Debug-Output im TextPort:**

**Optimistic Mode:**
```
[btn optimistic] btn/21 PRESS -> immediate action
[btn optimistic] btn/21 RELEASE after 234ms -> short (already handled)

[btn optimistic] btn/21 PRESS -> immediate action
[btn optimistic] btn/21 RELEASE after 1523ms -> LONG_PRESS toggle=1
```

**Timer Mode:**
```
[btn timer] encPush/2 PRESS -> scheduled (waiting 1000ms)
[btn timer] encPush/2 RELEASE after 345ms -> SHORT_PRESS

[btn timer] encPush/2 PRESS -> scheduled (waiting 1000ms)
[btn timer] encPush/2 LONG_PRESS_TRIGGERED after 1002ms -> toggle=1
[btn timer] encPush/2 RELEASE after 1456ms -> long already executed
```

**Von menu_engine.py:**
```
[scheduled long press] encPush/2 -> /eos/param/gobo_index\speed_2/reset = 1.0
[osc out] /eos/param/gobo_index\speed_2/reset 1.0
```

## Testing

**Test encPush/2 in Menu 0.2:**
1. Menu 0 aktivieren (btn/1 bis 0)
2. Submenu 0.2 wählen (btn/12)
3. encPush/2 testen:
   - Kurz drücken (<1s): OSC `/eos/param/gobo_index\speed_2/home`
   - Lang drücken (≥1s): OSC `/eos/param/gobo_index\speed_2/reset` mit Toggle

**Debug Output in TextPort:**
```
[scheduled long press] encPush/2 -> /eos/param/gobo_index\speed_2/reset = 1.0
[osc out] /eos/param/gobo_index\speed_2/reset 1.0
```

## Code-Stellen

**Haupt-Implementierung:**
- `menus/event_filters.py`: Lines 157-286 (button_press, check_scheduled_buttons)
- `menus/menu_engine.py`: Lines 352-386 (_lookup mit press_mode)
- `menus/menu_engine.py`: Lines 550-568 (check_scheduled_buttons Call)
- `menus/menu_engine.py`: Lines 574-646 (Unified Button Handler)
- `menus/menu_engine.py`: Lines 787-840 (encPush Handler)

**Konfiguration:**
- Alle `menus/menu_*/map_osc.tsv` Dateien (Spalte `press_mode`)

## Changelog

**2025-01-07**: Initial Implementation
- Timer-basierte Long Press hinzugefügt
- Alle Button-Handler vereinheitlicht
- Map-basierte press_mode Konfiguration
- Inkonsistente Button-Behandlung behoben

---

**Bei Fragen oder Änderungen**: Diese Dokumentation ZUERST aktualisieren!
