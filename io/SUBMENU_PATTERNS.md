# Neue Submenu Blink-Patterns

## Patterns erstellt

Drei neue Patterns für bessere Submenu-Erkennung:

| Pattern | Beschreibung | Timing |
|---------|--------------|--------|
| **submenu1** | 1x kurz aufblitzen | 0.15s flash → 2s Pause |
| **submenu2** | 2x kurz aufblitzen | 0.15s flash → 0.1s → 0.15s flash → 2s Pause |
| **submenu3** | 3x kurz aufblitzen | 0.15s → 0.1s → 0.15s → 0.1s → 0.15s → 2s Pause |

---

## Verwendung im Textport

```python
blink = op('/project1/io/led_blink_manager').module

# Submenu 1 (1x Blink)
blink.start('btn/4', 'submenu1', color='blue', priority=10)

# Submenu 2 (2x Blink)
blink.start('btn/4', 'submenu2', color='blue', priority=10)

# Submenu 3 (3x Blink)
blink.start('btn/4', 'submenu3', color='blue', priority=10)

# Stoppen
blink.stop('btn/4')
```

---

## Integration in menu_engine.py

Die Submenu-Konfiguration wurde automatisch angepasst:

```python
_SUBMENU_CONFIG = {
    4: [
        {"key": "form", "label": "submenu 4.1 form", "blink": "submenu1"},      # 1x blink
        {"key": "image", "label": "submenu 4.2 image", "blink": "submenu2"},    # 2x blink
        {"key": "shutter", "label": "submenu 4.3 shutter", "blink": "submenu3"}, # 3x blink
    ],
}
```

**Jetzt:**
- Submenu 4.1 (form) → 1x kurz aufblitzen
- Submenu 4.2 (image) → 2x kurz aufblitzen
- Submenu 4.3 (shutter) → 3x kurz aufblitzen

---

## Testen

### Im Textport testen:

```python
# Menu 4 aktivieren
menu = op('/project1/layers/menus/menu_engine').module
menu._set_active(4)
menu.apply_menu_leds(4)

# Durchschalten und beobachten
menu._advance_submenu(4)  # → submenu1 (1x blink)
menu.apply_menu_leds(4)

menu._advance_submenu(4)  # → submenu2 (2x blink)
menu.apply_menu_leds(4)

menu._advance_submenu(4)  # → submenu3 (3x blink)
menu.apply_menu_leds(4)
```

### Oder direkt Pattern testen:

```python
blink = op('/project1/io/led_blink_manager').module

print("Test submenu1 (1x)...")
blink.start('btn/4', 'submenu1', color='blue', priority=10)
# Warten 5 Sekunden - Sie sollten alle 2 Sekunden 1x kurz aufblitzen sehen
blink.stop('btn/4')

print("Test submenu2 (2x)...")
blink.start('btn/4', 'submenu2', color='blue', priority=10)
# Warten 5 Sekunden - Sie sollten alle 2 Sekunden 2x kurz aufblitzen sehen
blink.stop('btn/4')

print("Test submenu3 (3x)...")
blink.start('btn/4', 'submenu3', color='blue', priority=10)
# Warten 5 Sekunden - Sie sollten alle 2 Sekunden 3x kurz aufblitzen sehen
blink.stop('btn/4')
```

---

## Pattern-Definition (led_blink_patterns.tsv)

```tsv
name	stages
submenu1	[{"state": "press", "duration": 0.15}, {"state": "idle", "duration": 2.0}]
submenu2	[{"state": "press", "duration": 0.15}, {"state": "idle", "duration": 0.1}, {"state": "press", "duration": 0.15}, {"state": "idle", "duration": 2.0}]
submenu3	[{"state": "press", "duration": 0.15}, {"state": "idle", "duration": 0.1}, {"state": "press", "duration": 0.15}, {"state": "idle", "duration": 0.1}, {"state": "press", "duration": 0.15}, {"state": "idle", "duration": 2.0}]
```

---

## Anpassungen möglich

Falls Sie die Timings ändern wollen:

**Kürzere Pause (1 Sekunde statt 2):**
```json
[{"state": "press", "duration": 0.15}, {"state": "idle", "duration": 1.0}]
```

**Längere Blitze (0.2s statt 0.15s):**
```json
[{"state": "press", "duration": 0.2}, {"state": "idle", "duration": 2.0}]
```

**Kürzerer Abstand zwischen Blitzen (0.05s statt 0.1s):**
```json
[{"state": "press", "duration": 0.15}, {"state": "idle", "duration": 0.05}, {"state": "press", "duration": 0.15}, {"state": "idle", "duration": 2.0}]
```

Einfach in `io/led_blink_patterns.tsv` bearbeiten!
