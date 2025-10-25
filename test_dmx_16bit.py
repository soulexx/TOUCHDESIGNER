#!/usr/bin/env python3
"""Test DMX 16-bit conversion problem"""

from src.s2l_unit import dmx_parser, dmx_map

# Test 1: DMX decode mit rohen Bytes
print("=== Test 1: DMX Parser (korrekt) ===")
# Submaster = 1 in 16-bit DMX (slots 1-2)
# MSB=0, LSB=1 sollte 1 ergeben
buffer_test1 = bytes([0, 1] + [0] * 17)  # 19 slots total
result = dmx_parser.decode_parameter(
    buffer_test1,
    dmx_map.parameter_by_name("Submaster"),
    offset=0,
    scaling=False  # ohne Skalierung, raw value
)
print(f"DMX bytes [MSB=0, LSB=1] -> {result} (erwartet: 1)")

# MSB=1, LSB=0 sollte 256 ergeben
buffer_test2 = bytes([1, 0] + [0] * 17)
result2 = dmx_parser.decode_parameter(
    buffer_test2,
    dmx_map.parameter_by_name("Submaster"),
    offset=0,
    scaling=False
)
print(f"DMX bytes [MSB=1, LSB=0] -> {result2} (erwartet: 256)")

# MSB=0, LSB=255 sollte 255 ergeben
buffer_test3 = bytes([0, 255] + [0] * 17)
result3 = dmx_parser.decode_parameter(
    buffer_test3,
    dmx_map.parameter_by_name("Submaster"),
    offset=0,
    scaling=False
)
print(f"DMX bytes [MSB=0, LSB=255] -> {result3} (erwartet: 255)")

print("\n=== Test 2: MIDI Fader Logik (für Vergleich) ===")
from menus import event_filters

# Wenn wir 1/65535 als normalisierten Wert (0..1) senden wollen
normalized = 1.0 / 65535.0
print(f"Normalisiert 1/65535 = {normalized}")

# Simuliere MSB
msb_val = int(normalized * 127.0)  # MIDI 7-bit
print(f"MIDI MSB (x * 127): {msb_val}")

# Simuliere LSB
lsb_val = int(normalized * 127.0)  # MIDI 7-bit
print(f"MIDI LSB (x * 127): {lsb_val}")

# Kombiniert (MIDI 14-bit)
midi_combined = ((msb_val << 7) | lsb_val)
print(f"MIDI Combined (MSB<<7 | LSB): {midi_combined} von max 16383")

print("\n=== Test 3: Problem-Szenario ===")
# Was passiert wenn jemand 1 im DMX-Byte-Format sendet,
# aber es wird als normalisierter MIDI-Wert (1.0 = max) interpretiert?
if True:
    print("Szenario: Wert 1 wird als normalisierter Wert 1.0 interpretiert")
    msb = int(1.0 * 127.0)  # = 127
    lsb = int(1.0 * 127.0)  # = 127
    midi_result = ((msb << 7) | lsb)
    print(f"  MIDI MSB=127, LSB=127 -> {midi_result} (max 16383)")
    dmx_result = (127 << 8) | 127
    print(f"  Als DMX: MSB=127, LSB=127 -> {dmx_result}")

print("\n=== Test 4: Umgekehrtes Problem ===")
print("Szenario: DMX-Byte 1 wird mit MIDI-Logik verarbeitet")
# Wenn DMX Byte-Wert 1 durch MIDI-Shift geht
dmx_byte = 1
wrong_shift = (dmx_byte << 7)  # MIDI shift statt << 8
print(f"  DMX Byte {dmx_byte} mit MIDI shift (<<7): {wrong_shift}")
print(f"  Korrekt wäre DMX shift (<<8): {dmx_byte << 8}")
