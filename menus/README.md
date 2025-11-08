# Menu System Documentation

## Dateien

- **`event_filters.py`**: Filter für Encoder, Fader und Buttons (Smoothing, Long Press)
- **`menu_engine.py`**: Haupt-Event-Handler und Menu-Logik
- **`menu_0/` bis `menu_5/`**: Menu-Konfigurationen (je `map_osc.tsv`)

## Wichtige Dokumentationen

### 🔴 **[BUTTON_DESIGN.md](./BUTTON_DESIGN.md)** 🔴
**LESEN BEVOR BUTTONS GEÄNDERT WERDEN!**

Beschreibt die Button Long Press Implementierung:
- Wie Buttons behandelt werden (optimistic vs timer mode)
- Einheitliche Button-Handler für ALLE Buttons
- Map-basierte Konfiguration
- Häufige Fehler vermeiden

## Quick Reference

### Button Modi (in map_osc.tsv)

| press_mode | Verhalten | Use Case |
|------------|-----------|----------|
| `optimistic` (default) | Sofort bei Press → Short Action<br>Bei Release ≥1s → Long Action | Schnelle Reaktion wichtig |
| `timer` | Bei Press → Warten<br>Hold ≥1s → Long Action<br>Release <1s → Short Action | Kein versehentlicher Short Press bei Long Press |

### Map Spalten

```
topic | device | midi_channel | control_id | path_out | scale | enabled | led_color | path_out_long | press_mode
```

- **`path_out`**: Short Press oder sofortige Action
- **`path_out_long`**: Long Press Action (Toggle 0→1→0)
- **`press_mode`**: `optimistic` oder `timer` (leer = optimistic)

### Beispiel encPush mit Timer Mode

```tsv
encPush/2  midicraft  1  2  /eos/param/gobo/home  1  1  white  /eos/param/gobo/reset  timer
```

**Resultat:**
- Kurz drücken: `/home`
- Lang halten (≥1s): `/reset` mit Toggle

## Event Flow

```
MIDI Input → handle_event()
           ↓
[check_scheduled_buttons()] ← Timer Long Press Check
           ↓
[Button erkannt] → button_press(topic, value, press_mode)
           ↓                              ↑
     _lookup(menu, topic) ←──────────────┘ (holt press_mode)
           ↓
     ('press', val) → Short Action
           oder
     ('long_press', toggle) → Long Action
```

## Menu Struktur

- **Menu 0**: Pan/Tilt/Zoom/Edge + Gobos (5 Submenus)
- **Menu 1**: Intensity Palettes
- **Menu 2**: Focus Palettes
- **Menu 3**: Color Palettes
- **Menu 4**: Beam Palettes (3 Submenus: Form/Image/Shutter)
- **Menu 5**: Playback/Wheels

## Code-Stellen

### event_filters.py
- `check_scheduled_buttons()`: Timer-Check für Long Press
- `button_press()`: Haupt-Filter für alle Buttons
- `enc_delta()`: Encoder-Filter (Accumulation, Speed Detection)
- `fader_smooth()`: Fader-Filter (14-bit MSB/LSB Kombination)

### menu_engine.py
- `handle_event()`: Haupt-Einstiegspunkt für alle Events
- `_lookup()`: Map-Lookup (gibt path_out, scale, path_out_long, press_mode zurück)
- Button Handler: Lines 574-646 (unified für alle Buttons)
- Encoder Handler: Lines 652-729
- Fader Handler: Lines 732-778
- encPush Handler: Lines 787-840

## Erweiterungen

### Neuen Button hinzufügen

1. Eintrag in `menu_X/map_osc.tsv`:
```tsv
btn/23  midicraft  1  28  /eos/key/new  1  1  red  /eos/key/new_long  timer
```

2. Fertig! (Wird automatisch durch unified handler behandelt)

### Neues Menu hinzufügen

1. Ordner `menu_6/` erstellen
2. `map_osc.tsv` mit Standard-Spalten anlegen
3. In `menu_engine.py`: `_MENU0_SUB_BUTTONS` oder `_SUBMENU_CONFIG` erweitern falls nötig
4. Menu-Color in Map definieren: `__menu_color__  ...  1  <color>`

## Debugging

**Debug-Flags in event_filters.py:**
```python
ENC_DEBUG    = True  # Encoder-Debug-Output
BUTTON_DEBUG = True  # Button-Debug-Output (Default: True)
```

**Button Debug Output (BUTTON_DEBUG=True):**
```
[btn optimistic] btn/21 PRESS -> immediate action
[btn optimistic] btn/21 RELEASE after 234ms -> short (already handled)
[btn optimistic] btn/21 RELEASE after 1523ms -> LONG_PRESS toggle=1

[btn timer] encPush/2 PRESS -> scheduled (waiting 1000ms)
[btn timer] encPush/2 LONG_PRESS_TRIGGERED after 1002ms -> toggle=1
[btn timer] encPush/2 RELEASE after 345ms -> SHORT_PRESS
```

**OSC Output (immer):**
```
[osc out] /eos/param/... <value>
[long press] encPush/2 -> /eos/param/.../reset = 1.0
[scheduled long press] encPush/2 -> ... = 1.0
```

## Wichtig!

⚠️ **Buttons IMMER durch `button_press()` Filter behandeln**
⚠️ **`check_scheduled_buttons()` am Anfang von `handle_event()` aufrufen**
⚠️ **`press_mode` aus `_lookup()` holen und übergeben**

→ Details siehe [BUTTON_DESIGN.md](./BUTTON_DESIGN.md)

---

**Stand**: 2025-01-07
