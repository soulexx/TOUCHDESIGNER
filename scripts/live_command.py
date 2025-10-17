try:
    mod('/project1/palette_logic/subscribe_manager').sync_intensity_palettes(timeout=10)
except Exception as exc:
    print('[sync] failed', exc)
