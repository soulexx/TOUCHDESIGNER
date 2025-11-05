# Video Scrubbing Performance Guide

## Current Issue
- 7GB, 2-hour video file causes TouchDesigner to freeze during scrubbing
- Highly compressed codec (H.264/H.265) requires full decode on each frame access

## Best Practice Solutions

### Option 1: HAP Codec (RECOMMENDED for scrubbing)
HAP is designed for real-time playback and scrubbing:

**Pros:**
- Ultra-fast scrubbing (GPU-accelerated)
- Low CPU usage
- Frame-accurate seeking

**Cons:**
- Large file size (50-100GB for 2h video)
- Requires more disk space

**Convert with FFmpeg:**
```bash
# HAP (good quality, large file)
ffmpeg -i input.mp4 -c:v hap output.mov

# HAP Q (higher quality, even larger)
ffmpeg -i input.mp4 -c:v hap -format hap_q output.mov

# HAP Alpha (if you need transparency)
ffmpeg -i input.mp4 -c:v hap -format hap_alpha output.mov
```

### Option 2: Image Sequence
Export video as numbered images:

**Pros:**
- Perfect frame-by-frame access
- No codec decoding overhead
- Easy to edit individual frames

**Cons:**
- Very large disk space
- Many files to manage

**Export with FFmpeg:**
```bash
# PNG sequence (lossless)
ffmpeg -i input.mp4 frames/frame_%06d.png

# JPG sequence (smaller, lossy)
ffmpeg -i input.mp4 -q:v 2 frames/frame_%06d.jpg

# Use in TouchDesigner:
# Set Movie File In TOP to: frames/frame_*.png
```

### Option 3: NotchLC Codec
Good balance between quality and performance:

**Convert with Notch encoder** (requires Notch/Resolume installation)

### Option 4: Reduce Resolution
Quick fix if original is high resolution:

```bash
# 1080p
ffmpeg -i input.mp4 -vf scale=1920:1080 -c:v libx264 -crf 18 -preset slow output.mp4

# 720p
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 -crf 18 -preset slow output.mp4
```

## Temporary Workaround (Keep Current File)

If you can't re-encode now, add smoothing to reduce frame update frequency:

1. Create a Lag CHOP to smooth fader values
2. Only update video every N milliseconds
3. Pre-cache frames in memory (if possible)

## TouchDesigner Settings

### Movie File In TOP Settings:
- **Play Mode**: Specify Index
- **Index**: Set from Python/CHOP
- **Preload**: On (if you have RAM)
- **Preload From**: 0
- **Preload To**: Set to a range you'll scrub (e.g., 0-600 for first minute)

### Performance Tips:
1. **Lower preview resolution** while scrubbing
2. **Use Timeline mode** instead of real-time mode during setup
3. **Enable GPU Direct** if your GPU supports it
4. **Increase Cook Rate** for smoother updates

## Recommended Workflow

For a 2-hour ballet performance:

1. **Main show file**: HAP codec at full resolution
2. **Cue markers**: Use Cue Points in Movie File In TOP
3. **Scrubbing sections**: Pre-rendered image sequences for critical moments
4. **Backup**: Keep original file, use proxy for development

## Code Optimization

Current implementation calls `set_normalized_time()` on every MIDI event.
For heavy files, add throttling:

```python
# In menu_engine.py, add rate limiting:
import time

_last_video_update = 0
_video_update_interval = 0.033  # 30fps max update rate

if path.strip() == '/menu/video/normalized':
    now = time.time()
    if now - _last_video_update >= _video_update_interval:
        vc.set_normalized_time(float(y))
        _last_video_update = now
```

This reduces the update rate to 30fps even if MIDI sends 100+ events/second.
