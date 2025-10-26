def onFrameStart(frame):
    base = op('/project1')
    if not base:
        return
    if not bool(base.fetch('PALETTE_SYNC_ENABLED', False)):
        # Palette sync disabled; keep DAT quiet.
        return
    try:
        watchdog = mod('/project1/palette_logic/watchdog')
        pump = mod('/project1/palette_logic/pump')
        state = mod('/project1/palette_logic/state')
    except Exception as exc:
        print('[tick_exec] palette modules unavailable:', exc)
        return
    state.attach_base(base)
    # Use project timeline FPS (default 60 if not set)
    fps = max(int(project.cookRate), 1) if hasattr(project, 'cookRate') else 60
    if frame % fps == 0:
        watchdog.ensure_subscribed(base)
    pump_div = max(int(fps / 5), 1)
    if frame % pump_div == 0:
        pump.tick(base)
    return
