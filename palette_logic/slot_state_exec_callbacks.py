def _update():
    mod('/project1/palette_logic/update_slot_state').update_slot_state()

def onStart():
    _update()
    return

def onTableChange(dat):
    _update()
    return
