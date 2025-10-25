# S2L Fixture DMX Documentation

## Overview

The S2L_UNIT (Sound-to-Light Unit) uses **19 DMX channels** per instance for controlling playback, audio processing, and FX parameters via sACN/DMX.

- **Protocol**: sACN (Streaming ACN) over Ethernet
- **Universe**: Configurable per instance
- **Channels per Instance**: 19
- **16-bit Parameters**: Use MSB (coarse) first, LSB (fine) second
- **Compatible with**: ETC Eos, GrandMA, etc.

---

## DMX Channel Map

### Quick Reference Table

| Channel | Parameter      | Type   | Range        | Default | Description                              |
|---------|----------------|--------|--------------|---------|------------------------------------------|
| 1-2     | Submaster      | 16-bit | 1 - 999      | 1       | Target submaster number                  |
| 3-4     | Cuelist        | 16-bit | 1 - 999      | 1       | Cuelist identifier                       |
| 5-6     | StartCue       | 16-bit | 0 - 999      | 0       | First cue in playback range              |
| 7-8     | EndCue         | 16-bit | 0 - 999      | 0       | Last cue in playback range               |
| 9-10    | Mode           | 16-bit | 0 - 1256     | 0       | Playback mode (0-5=auto, 1001+=bars)     |
| 11      | Sensitivity    | 8-bit  | 0 - 100      | 50      | Audio sensitivity percentage             |
| 12      | Threshold      | 8-bit  | 0 - 100      | 40      | Trigger threshold percentage             |
| 13      | LowCut_Hz      | 8-bit  | 20 - 300     | 120     | Audio low-cut filter (Hz)                |
| 14      | HighCut_Hz     | 8-bit  | 2000 - 8000  | 3500    | Audio high-cut filter (Hz)               |
| 15      | Lag_ms         | 8-bit  | 0 - 500      | 150     | Smoothing/holdback (milliseconds)        |
| 16      | MinHold_s      | 8-bit  | 0 - 8        | 6       | Minimum hold time (seconds)              |
| 17-18   | FX_Select      | 16-bit | 1 - 65535    | 1       | FX preset identifier                     |
| 19      | FX_Auto        | 8-bit  | 0 - 255      | 0       | Auto/beat behavior (0=off, 1=beat, 2-255=auto) |

---

## Parameter Details

### Playback Parameters (Channels 1-10)

#### **Submaster** (Ch 1-2) - 16-bit
- **MSB**: Channel 1 (coarse)
- **LSB**: Channel 2 (fine)
- **Range**: 1 - 999
- **Purpose**: Select target submaster on lighting console

**Example Values:**
- Submaster 1: Ch1=0, Ch2=1
- Submaster 100: Ch1=0, Ch2=100
- Submaster 256: Ch1=1, Ch2=0
- Submaster 999: Ch1=3, Ch2=231

#### **Cuelist** (Ch 3-4) - 16-bit
- **Range**: 1 - 999
- **Purpose**: Select which cuelist to use for playback

#### **StartCue** (Ch 5-6) - 16-bit
- **Range**: 0 - 999
- **Purpose**: Define first cue in playback range
- **Note**: 0 = no restriction

#### **EndCue** (Ch 7-8) - 16-bit
- **Range**: 0 - 999
- **Purpose**: Define last cue in playback range
- **Note**: 0 = no restriction

#### **Mode** (Ch 9-10) - 16-bit
- **Range**: 0 - 1256
- **Values**:
  - `0-5`: Auto modes
  - `1001+`: Bar count modes

---

### Audio Parameters (Channels 11-16)

#### **Sensitivity** (Ch 11) - 8-bit
- **Range**: 0 - 100%
- **Default**: 50%
- **Purpose**: Audio input sensitivity

#### **Threshold** (Ch 12) - 8-bit
- **Range**: 0 - 100%
- **Default**: 40%
- **Purpose**: Trigger threshold for beat detection

#### **LowCut_Hz** (Ch 13) - 8-bit
- **Range**: 20 - 300 Hz
- **Default**: 120 Hz
- **Purpose**: High-pass filter cutoff frequency

#### **HighCut_Hz** (Ch 14) - 8-bit
- **Range**: 2000 - 8000 Hz
- **Default**: 3500 Hz
- **Purpose**: Low-pass filter cutoff frequency

#### **Lag_ms** (Ch 15) - 8-bit
- **Range**: 0 - 500 ms
- **Default**: 150 ms
- **Purpose**: Smoothing/response delay

#### **MinHold_s** (Ch 16) - 8-bit
- **Range**: 0 - 8 seconds
- **Default**: 6 seconds
- **Purpose**: Minimum hold time before next trigger

---

### FX Parameters (Channels 17-19)

#### **FX_Select** (Ch 17-18) - 16-bit
- **MSB**: Channel 17 (coarse)
- **LSB**: Channel 18 (fine)
- **Range**: 1 - 65535
- **Purpose**: Select FX preset

#### **FX_Auto** (Ch 19) - 8-bit
- **Range**: 0 - 255
- **Values**:
  - `0`: Off
  - `1`: Beat-synced
  - `2-255`: Auto modes

---

## ETC Eos Configuration

### Setting up 16-bit Parameters

For 16-bit parameters (Submaster, Cuelist, etc.), configure in Eos:

1. **Patch as 16-bit Parameter**:
   - Use "Coarse/Fine" mode
   - MSB = Coarse (first channel)
   - LSB = Fine (second channel)

2. **Example - Submaster on Ch 1-2**:
   ```
   Patch → S2L_UNIT_1
   Channel 1: Submaster (Coarse)
   Channel 2: Submaster (Fine)
   Mode: 16-bit
   ```

3. **Sending Value "1"**:
   - ✅ **Correct**: Ch1=0, Ch2=1
   - ❌ **Wrong**: Ch1=255 (this is normalized 100%)

---

## Multiple Instances

Each S2L_UNIT instance uses **19 consecutive channels**:

| Instance       | Start Address | Channels   |
|----------------|---------------|------------|
| S2L_UNIT_1     | 1             | 1-19       |
| S2L_UNIT_2     | 20            | 20-38      |
| S2L_UNIT_3     | 39            | 39-57      |
| ...            | ...           | ...        |

**Maximum per universe**: 512 ÷ 19 = **26 instances**

---

## Troubleshooting

### Values appear incorrect (e.g., 1 becomes 255)

**Cause**: ETC Eos sending normalized values instead of DMX values

**Solution**:
- Ensure parameter is patched as "16-bit Coarse/Fine"
- NOT as "Level" or "Intensity" (which sends 0-100%)

### No response from S2L_UNIT

**Check**:
1. Correct universe configured
2. Instance enabled in config
3. Start address matches patch
4. sACN output enabled on console

---

## Technical Notes

- **Byte Order**: MSB first (big-endian)
- **DMX Values**: Direct values, NOT normalized (0-255 for 8-bit, 0-65535 for 16-bit)
- **Update Rate**: Processes every frame (typically 30-60 FPS)
- **Performance**: Optimized with caching, minimal overhead

---

## Configuration Files

- **Parameter Map**: `src/s2l_unit/dmx_map.py`
- **Instances Config**: `config/s2l_unit/instances.tsv`
- **Defaults Config**: `config/s2l_unit/defaults.tsv`

---

*Last Updated: 2025-10-25*
*Generated with Claude Code*
