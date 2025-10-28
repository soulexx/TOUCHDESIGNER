# S2L_UNIT Architecture Documentation

## Core Concept

**One Unit = One Submaster = One Audio Profile**

Each S2L_UNIT is a completely independent "virtual device" that:
1. Selects **one** Eos submaster to control
2. Analyzes audio based on its own settings (band, threshold)
3. Applies its own envelope (attack/hold/release)
4. Sends OSC commands to control that specific submaster

## Unit Independence

### Example Setup

```
┌─────────────────────────────────────────────────┐
│ S2L_UNIT_1 (DMX 1-14)                          │
│                                                 │
│ Controls: Submaster 5                          │
│ Audio Profile:                                 │
│  • Band: low (bass)                            │
│  • Threshold: 100 (moderate)                   │
│  • Attack: 20 (fast)                           │
│  • Hold: 50                                    │
│  • Release: 80                                 │
│  • FX_Polarity: normal                         │
│                                                 │
│ Behavior: Sub 5 reacts to bass hits with      │
│           fast attack and moderate decay       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ S2L_UNIT_2 (DMX 15-28)                         │
│                                                 │
│ Controls: Submaster 12                         │
│ Audio Profile:                                 │
│  • Band: high (treble)                         │
│  • Threshold: 150 (less sensitive)             │
│  • Attack: 5 (instant)                         │
│  • Hold: 30 (short)                            │
│  • Release: 200 (long tail)                    │
│  • FX_Polarity: inverted                       │
│                                                 │
│ Behavior: Sub 12 reacts to hi-hats/cymbals    │
│           with instant attack and long decay   │
└─────────────────────────────────────────────────┘
```

### Key Points

- **No interaction between units** - Unit 1 doesn't know Unit 2 exists
- **Independent audio analysis** - Each unit analyzes the same audio input differently
- **Separate envelope states** - Each unit maintains its own attack/hold/release timing
- **Unique OSC output** - Each unit sends commands to its selected submaster only

## Data Flow

```
Audio Input (single source)
    │
    ├──────────────────────────────────────┐
    │                                      │
    ▼                                      ▼
┌─────────────────┐              ┌─────────────────┐
│   S2L_UNIT_1    │              │   S2L_UNIT_2    │
│                 │              │                 │
│ Band: low       │              │ Band: high      │
│ Threshold: 100  │              │ Threshold: 150  │
└────────┬────────┘              └────────┬────────┘
         │                                │
         │ Analyze                        │ Analyze
         │ low freq                       │ high freq
         ▼                                ▼
    ┌────────┐                       ┌────────┐
    │Envelope│                       │Envelope│
    │ A:20   │                       │ A:5    │
    │ H:50   │                       │ H:30   │
    │ R:80   │                       │ R:200  │
    └───┬────┘                       └───┬────┘
        │                                │
        ▼                                ▼
    OSC: /eos/sub/5                  OSC: /eos/sub/12
```

## DMX Configuration Flow

```
Eos Console
    │
    │ sACN Universe 16
    ▼
TouchDesigner DMX Input (EOS_Universe_016)
    │
    │ frame_tick.py (every DMX change)
    ▼
sacn_dispatch.py (decode DMX to values)
    │
    ▼
dispatcher.py (update values table)
    │
    ▼
values table (stores current DMX state)
    │
    ├── S2L_UNIT_1: Submaster=5, Threshold=100, Attack=20, ...
    ├── S2L_UNIT_2: Submaster=12, Threshold=150, Attack=5, ...
    └── S2L_UNIT_3: ...
```

## Audio Engine Processing (Future Implementation)

Each frame, the audio engine should:

```python
# Pseudo-code for audio engine

for each enabled S2L_UNIT:
    # 1. Get unit configuration from values table
    config = get_unit_config(unit_id)
    submaster = config['Submaster']
    threshold = config['Threshold']
    attack = config['Attack']
    hold = config['Hold']
    release = config['Release']
    band = decode_band_mode(config['Band'])
    polarity = decode_fx_polarity(config['FX_Polarity'])

    # 2. Analyze audio for this unit's band
    audio_level = analyze_audio(band)

    # 3. Apply threshold
    if audio_level > threshold:
        triggered = True

    # 4. Apply envelope (attack/hold/release)
    envelope_value = apply_envelope(
        triggered,
        attack_time=attack,
        hold_time=hold,
        release_time=release,
        previous_state=unit_state[unit_id]
    )

    # 5. Apply polarity
    if polarity == "inverted":
        envelope_value = 1.0 - envelope_value

    # 6. Send OSC to Eos
    send_osc(f"/eos/sub/{submaster}", envelope_value)

    # 7. Update unit state for next frame
    unit_state[unit_id] = envelope_value
```

## Use Cases

### Use Case 1: Multi-Band Audio Reactivity
Control different lighting zones based on frequency bands:
- **Unit 1 (Sub 1):** Low band → Bass lights
- **Unit 2 (Sub 2):** Mid band → Vocal lights
- **Unit 3 (Sub 3):** High band → Cymbal lights

### Use Case 2: Layered Timing
Same frequency band, different timing characteristics:
- **Unit 1 (Sub 5):** Fast attack, short release → Punchy strobes
- **Unit 2 (Sub 6):** Slow attack, long release → Smooth washes

### Use Case 3: Inverted Ducking
- **Unit 1 (Sub 10):** Normal polarity → Lights up on beat
- **Unit 2 (Sub 11):** Inverted polarity → Lights dim on beat (ducking effect)

### Use Case 4: Spectral Analysis Mixing
- **Unit 1 (Sub 20):** SMSD analysis → Complex rhythmic patterns
- **Unit 2 (Sub 21):** Spectral Centroid → Brightness-based control

## Implementation Notes

### Values Table Structure
```
instance     | parameter  | value
-------------|------------|-------
S2L_UNIT_1   | Submaster  | 5
S2L_UNIT_1   | Threshold  | 100
S2L_UNIT_1   | Attack     | 20
S2L_UNIT_1   | Hold       | 50
S2L_UNIT_1   | Release    | 80
S2L_UNIT_1   | Band       | 0
S2L_UNIT_1   | FX_Polarity| 0
S2L_UNIT_2   | Submaster  | 12
S2L_UNIT_2   | Threshold  | 150
...
```

### Band Decoding
Use helper function from dmx_map.py:
```python
import s2l_unit as s2l

raw_band = 100  # DMX value
band_name = s2l.decode_band_mode(raw_band)  # Returns "high"
```

### Polarity Decoding
```python
import s2l_unit as s2l

raw_polarity = 200  # DMX value
polarity = s2l.decode_fx_polarity(raw_polarity)  # Returns "inverted"
```

## Configuration Files

### instances.csv
Defines which units exist and their DMX addresses:
```csv
instance,enabled,universe,start_address
S2L_UNIT_1,true,16,1
S2L_UNIT_2,true,16,15
...
```

### defaults.json
Default values when DMX is not available:
```json
{
  "playback": {
    "submaster": 0,
    "cuelist": 0,
    "start_cue": 0,
    "end_cue": 0
  },
  "audio": {
    "threshold": 128,
    "attack": 64,
    "hold": 128,
    "release": 128,
    "band": 0,
    "fx_polarity": 0
  }
}
```

### dmx_map.py
Defines the 14-channel DMX structure for each unit

## Future: Cuelist Support

When cuelist functionality is added:
- Instead of controlling a submaster level directly
- Unit will trigger cue playback within the selected cuelist range
- Start Cue / End Cue define the playback boundaries
- Audio envelope still applies the same way

Example:
```
S2L_UNIT_3:
  Cuelist: 5
  Start Cue: 10
  End Cue: 20

Audio trigger → Play cues 10-20 in List 5
Envelope controls playback intensity/speed
```

## Performance Considerations

### Real-time Requirements
- DMX updates: Every frame when values change
- Audio analysis: 60fps (or project frame rate)
- Envelope calculation: Per-unit, per-frame
- OSC output: Only when values change (change detection)

### Optimization
- Cache unit configurations (only reload on DMX change)
- Reuse audio analysis when multiple units use same band
- Batch OSC sends per frame
- Use change detection to minimize network traffic

## Summary

✅ **One Unit = One Submaster = One Audio Profile**
✅ **Complete independence** between units
✅ **Scalable** to 36 units per universe
✅ **Flexible** audio reactivity per unit
✅ **Real-time** DMX control from Eos console

This architecture allows for complex, multi-layered audio-reactive lighting with precise control over each element.
