# STL-UNIT Eos Patch Reference

## DMX Footprint: 14 Channels

### Universe 16 - 10 Units Configuration

| Unit | DMX Start | DMX End | Status |
|------|-----------|---------|--------|
| S2L_UNIT_1 | 1 | 14 | ✅ Enabled |
| S2L_UNIT_2 | 15 | 28 | ✅ Enabled |
| S2L_UNIT_3 | 29 | 42 | ✅ Enabled |
| S2L_UNIT_4 | 43 | 56 | ✅ Enabled |
| S2L_UNIT_5 | 57 | 70 | ✅ Enabled |
| S2L_UNIT_6 | 71 | 84 | ✅ Enabled |
| S2L_UNIT_7 | 85 | 98 | ✅ Enabled |
| S2L_UNIT_8 | 99 | 112 | ✅ Enabled |
| S2L_UNIT_9 | 113 | 126 | ✅ Enabled |
| S2L_UNIT_10 | 127 | 140 | ✅ Enabled |

**Available Space:** 372 additional channels (room for 26 more units on universe 16)

---

## Parameter Structure

### 16-bit Selection Parameters (Channels 1-8)

All four parameters work the same way: **selecting an index**, NOT controlling a level.

#### DMX 1-2: Submaster (16-bit)
- **Function:** Which submaster ID is active
- **Range:** 0-999
- **Default:** 0
- **Channel 1:** High Byte (coarse)
- **Channel 2:** Low Byte (fine)
- **Important:** This selects WHICH submaster the unit uses, not the submaster's level!

#### DMX 3-4: Cuelist (16-bit)
- **Function:** Which cuelist/stack to address
- **Range:** 0-999 (0 = none/default)
- **Default:** 0
- **Channel 3:** High Byte
- **Channel 4:** Low Byte

#### DMX 5-6: Start Cue (16-bit)
- **Function:** Start cue number within selected cuelist
- **Range:** 0-999 (0 = none/default)
- **Default:** 0
- **Channel 5:** High Byte
- **Channel 6:** Low Byte

#### DMX 7-8: End Cue (16-bit)
- **Function:** End cue number within selected cuelist
- **Range:** 0-999 (0 = none/default)
- **Default:** 0
- **Channel 7:** High Byte
- **Channel 8:** Low Byte

**Playback Range:** Unit plays/reacts from Start Cue to End Cue in the selected Cuelist.

---

### 8-bit Value/Mode Parameters (Channels 9-14)

These define the audio envelope and analysis behavior.

#### DMX 9: Threshold
- **Function:** Audio trigger threshold
- **Range:** 0-255
- **Default:** 128
- **Behavior:** Lower = more sensitive, Higher = less sensitive

#### DMX 10: Attack
- **Function:** Attack/onset time
- **Range:** 0-255
- **Default:** 64
- **Behavior:** 0 = fast attack, 255 = slow attack

#### DMX 11: Hold
- **Function:** Peak hold time
- **Range:** 0-255
- **Default:** 128
- **Behavior:** How long the peak level is maintained

#### DMX 12: Release
- **Function:** Release/decay time
- **Range:** 0-255
- **Default:** 128
- **Behavior:** 0 = fast release, 255 = slow release

#### DMX 13: Band / Analysis Mode
- **Function:** Frequency band or analysis algorithm selection
- **Range:** 0-255
- **Default:** 0 (low)

**Range Mapping:**
| DMX Range | Mode | Description |
|-----------|------|-------------|
| 0-41 | **low** | Low frequency band |
| 42-84 | **mid** | Mid frequency band |
| 85-127 | **high** | High frequency band |
| 128-169 | **smsd** | Spectral Mean Square Difference |
| 170-212 | **fmsd** | Frequency Mean Square Difference |
| 213-255 | **spectralCentroid** | Spectral centroid analysis |

#### DMX 14: FX Polarity / Mode
- **Function:** Effect polarity toggle
- **Range:** 0-255
- **Default:** 0 (normal)

**Range Mapping:**
| DMX Range | Mode |
|-----------|------|
| 0-127 | **normal** |
| 128-255 | **inverted** |

---

## Example Eos Fixture Patch

### Fixture Profile Setup
1. Create custom fixture profile: "STL_UNIT_14ch"
2. 14 DMX channels
3. Add parameters as listed above

### Patching in Eos
```
Patch 1 Thru 10 Universe 16 @ 1 [Enter]
Profile STL_UNIT_14ch [Enter]
```

This will patch:
- Channel 1 @ Universe 16, Address 1-14
- Channel 2 @ Universe 16, Address 15-28
- Channel 3 @ Universe 16, Address 29-42
- ... and so on

---

## DMX Value Calculation Reference

### 16-bit Parameters (Submaster, Cuelist, Start Cue, End Cue)

To send a 16-bit value (e.g., select Cuelist 123):

```
Value = 123
High Byte (coarse) = Value / 256 = 0
Low Byte (fine) = Value % 256 = 123

DMX 3 (High) = 0
DMX 4 (Low) = 123
```

For larger values (e.g., Cue 500):
```
Value = 500
High Byte = 500 / 256 = 1
Low Byte = 500 % 256 = 244

DMX 5 (High) = 1
DMX 6 (Low) = 244
```

### 8-bit Parameters

Direct DMX value 0-255.

---

## Common Patch Scenarios

### Scenario 1: Simple Audio Trigger
- **Submaster:** 1 (select Sub 1)
- **Cuelist:** 0 (none)
- **Start Cue:** 0
- **End Cue:** 0
- **Threshold:** 100 (moderate sensitivity)
- **Attack:** 20 (fast)
- **Hold:** 50
- **Release:** 80
- **Band:** 42 (mid range)
- **FX Polarity:** 0 (normal)

### Scenario 2: Cuelist Playback with Bass Trigger
- **Submaster:** 0
- **Cuelist:** 5 (List 5)
- **Start Cue:** 1 (Cue 1)
- **End Cue:** 10 (Cue 10)
- **Threshold:** 80
- **Attack:** 10 (very fast)
- **Hold:** 100
- **Release:** 120
- **Band:** 0 (low frequency)
- **FX Polarity:** 0 (normal)

### Scenario 3: Inverted High-Frequency FX
- **Submaster:** 3 (select Sub 3)
- **Cuelist:** 0
- **Start Cue:** 0
- **End Cue:** 0
- **Threshold:** 150 (less sensitive)
- **Attack:** 5 (instant)
- **Hold:** 30 (short)
- **Release:** 200 (long tail)
- **Band:** 100 (high frequency)
- **FX Polarity:** 200 (inverted)

---

## Notes

- **Cuelist logic will be implemented later** - currently only selection is prepared
- All 16-bit parameters use **MSB first** (High byte then Low byte) as per DMX standard
- Band ranges are designed with gaps for future expansion
- FX Polarity is a simple toggle, not a continuous value
- Default values are optimized for general-purpose use
