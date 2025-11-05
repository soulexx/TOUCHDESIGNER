# Setup Execute DAT für Video Play
# Dieses Skript erstellt ein selbst-triggerndes Execute DAT

media = op('/project1/media')

# Lösche time_play_exec (CHOP Execute funktioniert nicht)
old_exec = op('/project1/media/time_play_exec')
if old_exec:
    old_exec.destroy()
    print("[OK] Removed old CHOP Execute")

# Erstelle normales Execute DAT
video_exec = op('/project1/media/video_exec')
if not video_exec:
    video_exec = media.create(textDAT, 'video_exec')
    video_exec.par.extension = 'py'
    print(f"[OK] Created {video_exec.path}")

# Schreibe Frame-Update Code
code = '''# Video Play Execute - runs every frame

def onFrameEnd(frame):
    """Called every frame - increment time_play if playing"""
    try:
        transport = op('/project1/media/transport_control')
        constant1 = op('/project1/media/constant1')
        time_play = op('/project1/media/time_play')

        if not (transport and constant1 and time_play):
            return

        # Check if playing
        playing = transport['playing'].eval()
        vel = constant1['vel'].eval()

        if playing > 0.5 and vel > 0.5:
            # Increment time (assume 60fps)
            current = time_play['seconds'].eval()
            time_play.par.value0 = current + (1.0 / 60.0)

    except:
        pass
'''

video_exec.text = code
print(f"[OK] Code written to video_exec")

# Jetzt müssen wir dieses Execute DAT mit einem op() Parameter verknüpfen
# Am einfachsten: Erstelle ein Timer DAT das das Skript aufruft

timer_exec = op('/project1/media/timer_exec')
if not timer_exec:
    timer_exec = media.create(timerCHOP, 'timer_exec')
    print(f"[OK] Created timer_exec")

# Konfiguriere Timer - läuft kontinuierlich
timer_exec.par.initialize = True
timer_exec.par.start = True
timer_exec.par.length = 0.1  # 100ms
timer_exec.par.lengthunits = 'seconds'
timer_exec.par.cycle = True

print(f"\n[INFO] Timer läuft, aber wir brauchen noch DAT Execute!")
print(f"[INFO] Erstelle stattdessen einen einfacheren Ansatz...")

# EINFACHER: Verwende run() im Textport
print(f"\n[ALTERNATIVE] Führe aus:")
print(f"  run('op(\\'/project1/media/video_exec\\').module.onFrameEnd(me.time.frame)', delayFrames=1, delayRef=op('/'), group='video_play')")

print("\n[SUCCESS] Setup complete!")
print("\nJETZT: Kopiere den CHOP Execute Code in die TouchDesigner UI:")
print("1. Rechtsklick auf null_exec -> 'Edit CHOP Execute...'")
print("2. Kopiere den Code aus media/time_play_exec.py")
