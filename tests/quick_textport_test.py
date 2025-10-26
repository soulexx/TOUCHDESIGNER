"""
QUICK TEXTPORT TEST
Kopiere diesen Code komplett in den TouchDesigner Textport (Alt+T)
"""

# Manager laden
blink = op('/project1/io/led_blink_manager').module

# Test 1: Patterns anzeigen
print("\n=== VERFÜGBARE PATTERNS ===")
patterns = blink.reload_patterns()
print(patterns)

# Test 2: Slow Pattern starten
print("\n=== TEST SLOW PATTERN (btn/4) ===")
print("Starte slow pattern... (beobachte btn/4)")
blink.start('btn/4', 'slow', color='blue', priority=10)
print("✓ Gestartet - Button sollte alle 0.5s blinken (press/idle)")
print("Warte 3 Sekunden...")

import time
time.sleep(3)

print("Stoppe...")
blink.stop('btn/4')
print("✓ Gestoppt")

# Test 3: Fast Pattern
print("\n=== TEST FAST PATTERN (btn/4) ===")
print("Starte fast pattern...")
blink.start('btn/4', 'fast', color='red', priority=10)
print("✓ Gestartet - Button sollte alle 0.2s blinken (press/off)")
print("Warte 3 Sekunden...")

time.sleep(3)

print("Stoppe...")
blink.stop('btn/4')
print("✓ Gestoppt")

# Test 4: Pulse Pattern
print("\n=== TEST PULSE PATTERN (btn/4) ===")
print("Starte pulse pattern...")
blink.start('btn/4', 'pulse', color='green', priority=10)
print("✓ Gestartet - Button sollte kurz aufblitzen (0.1s press / 0.4s idle)")
print("Warte 3 Sekunden...")

time.sleep(3)

print("Stoppe...")
blink.stop('btn/4')
print("✓ Gestoppt")

# Test 5: Status
print("\n=== STATUS ===")
print("Aktive Blinks:", blink.active_targets())
print("btn/4 aktiv:", blink.is_active('btn/4'))

print("\n✓✓✓ ALLE TESTS ABGESCHLOSSEN ✓✓✓")
