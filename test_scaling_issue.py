#!/usr/bin/env python3
"""Test scaling issue: why does 1 become 255?"""

from src.s2l_unit import dmx_parser, dmx_map

print("=== Test: Skalierungsproblem ===\n")

# Submaster: 16-bit, value_range=(1, 999)
param = dmx_map.parameter_by_name("Submaster")
print(f"Parameter: {param.name}")
print(f"Range: {param.value_range}")
print(f"DMX Slots: {param.dmx_slot_count}\n")

# Test 1: Raw DMX value = 1 (MSB=0, LSB=1)
buffer1 = bytes([0, 1] + [0] * 17)
raw1 = dmx_parser.decode_parameter(buffer1, param, offset=0, scaling=False)
scaled1 = dmx_parser.decode_parameter(buffer1, param, offset=0, scaling=True)
print(f"DMX [MSB=0, LSB=1]:")
print(f"  Raw value: {raw1}")
print(f"  Scaled value: {scaled1}")
print()

# Test 2: Raw DMX value = 255 (MSB=0, LSB=255)
buffer2 = bytes([0, 255] + [0] * 17)
raw2 = dmx_parser.decode_parameter(buffer2, param, offset=0, scaling=False)
scaled2 = dmx_parser.decode_parameter(buffer2, param, offset=0, scaling=True)
print(f"DMX [MSB=0, LSB=255]:")
print(f"  Raw value: {raw2}")
print(f"  Scaled value: {scaled2}")
print()

# Test 3: Was ist wenn wir Wert "1" im Target-Range wollen?
# Target: 1 (im Range 1-999)
# Was sollte der DMX-Wert sein?
target_value = 1
min_val, max_val = param.value_range
span = max_val - min_val  # 998
normalized = (target_value - min_val) / span  # (1-1)/998 = 0
raw_dmx = int(normalized * 65535)
print(f"Um Wert {target_value} zu erreichen (Range {min_val}-{max_val}):")
print(f"  Normalisiert: {normalized}")
print(f"  DMX raw value: {raw_dmx}")
print(f"  DMX MSB: {raw_dmx >> 8}")
print(f"  DMX LSB: {raw_dmx & 0xFF}")
print()

# Test 4: Umgekehrt - was kommt bei DMX=255 raus?
raw_255 = 255
scaled_result = int(min_val + (raw_255 / 65535) * span)
print(f"DMX raw value {raw_255}:")
print(f"  Skaliert zu Target-Range: {scaled_result}")
print(f"  (erwartet: ~{int(1 + (255/65535) * 998)})")
print()

# Test 5: Problem-Szenario - was wenn man denkt man sendet "1" aber es ist ein Byte?
print("=== Problem-Szenario ===")
print("Wenn '1' als DMX-Byte im MSB-Slot landet:")
buffer_problem = bytes([1, 0] + [0] * 17)  # MSB=1, LSB=0
raw_problem = dmx_parser.decode_parameter(buffer_problem, param, offset=0, scaling=False)
scaled_problem = dmx_parser.decode_parameter(buffer_problem, param, offset=0, scaling=True)
print(f"DMX [MSB=1, LSB=0]:")
print(f"  Raw value: {raw_problem} (= 1 << 8)")
print(f"  Scaled value: {scaled_problem}")
print()

# Test 6: Oder vielleicht wird ein Wert falsch als MSB interpretiert?
print("Wenn '1' (als normalisierter 0..1 Wert = 100%) in MSB landet:")
fake_msb = int(1.0 * 255)  # = 255
fake_lsb = int(1.0 * 255)  # = 255
buffer_fake = bytes([fake_msb, fake_lsb] + [0] * 17)
raw_fake = dmx_parser.decode_parameter(buffer_fake, param, offset=0, scaling=False)
scaled_fake = dmx_parser.decode_parameter(buffer_fake, param, offset=0, scaling=True)
print(f"DMX [MSB=255, LSB=255] (= normalized 1.0):")
print(f"  Raw value: {raw_fake}")
print(f"  Scaled value: {scaled_fake}")
