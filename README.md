# TOUCHDESIGNER

## Live Command Runner

- Edit `scripts/live_command.py` in VS Code. TouchDesigner reloads the file on save and executes it inside the project (see `io/command_runner_callbacks.py`).
- Set up a `Text DAT` in TouchDesigner that points to the same file (`File` → `c:\_DEV\TOUCHDESIGNER\scripts\live_command.py`) and add a `DAT Execute DAT` to trigger the reload.
- Results and failures are logged to `logs/command_runner.log`; exceptions also appear in the Textport.
- The logging helper prevents duplicate executions when the file content did not change.

## S2L Unit

- Configuration files live in `config/s2l_unit/`. Use `instances.csv` for per-instance data (name, universe, start address, IP) and `defaults.json` for global defaults.
- Python helpers reside in `src/s2l_unit/`. TouchDesigner DATs can call `load_instances()` and `load_defaults()` to pull the latest values.
- The DMX parameter layout is defined once in `src/s2l_unit/dmx_map.py`. Adjust slot order, scaling, or descriptions only there.
- Any TouchDesigner component can simply `import s2l_unit` to access the constants, dataclasses, and loader functions.
