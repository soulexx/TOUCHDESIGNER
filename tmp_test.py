from menus import event_filters
print("base", event_filters.fader_smooth("fader/1", 0.0))
print("msb", event_filters.fader_smooth("fader/1/msb", 0.5))
print("lsb", event_filters.fader_smooth("fader/1/lsb", 0.5))
print("lsb2", event_filters.fader_smooth("fader/1/lsb", 0.503))

