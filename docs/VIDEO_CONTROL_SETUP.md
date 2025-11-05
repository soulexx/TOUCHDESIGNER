# Video Control Integration

The `video_control` helper wraps a single video TOP (typically a `moviefileinTOP`)
and exposes a small Python API you can call from any DAT script.

## 1. Point the controller at your video TOP

Place (or identify) the TOP that should be controlled, e.g.
`/project1/media/moviefilein1`.  Persist the path once on the project
component – you can run this from the Textport or `scripts/live_command.py`:

```python
project = op("/project1")
project.store("VIDEO_TOP_PATH", "/project1/media/moviefilein1")
```

You can always override the path per-controller later with
`VideoController.set_default_path(path, persist=True)`.

## 2. Drive playback from Python

```python
import video_control

vc = video_control.get_controller()

vc.play()                    # start playback
vc.pause()                   # pause but keep position
vc.stop()                    # pause + reset to frame 0
vc.set_normalized_time(0.5)  # jump to the middle of the clip
info = vc.info()             # -> VideoInfo dataclass (path, frame, rate, etc.)
```

All commands operate on the TOP you configured in step 1.  The helper
automatically resolves a COMP wrapper by selecting the first child with a
`play` parameter, so it also works with simple container-based movie players.

## 3. Hooking up controller menu actions

Once you are happy with the manual API calls, you can route hardware controls.
For example, to map **Menu 5 → Fader 1** to timeline scrubbing:

1. Add a new topic in `menus/menu_5/map_osc.tsv` that emits
   `/menu/video/normalized` (leave the OSC path blank for now).
2. Update `menus/menu_engine.py` so that the handler catches that topic and calls
   `video_control.get_controller().set_normalized_time(value)`.

Buttons in the same menu can call `vc.play()`, `vc.pause()`, or `vc.stop()`
through similar hooks.

This keeps the TouchDesigner OSC dispatching logic in one place while letting
the Python helper handle the actual TOP interaction.
