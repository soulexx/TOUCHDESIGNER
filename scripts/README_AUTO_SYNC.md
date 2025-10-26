# Auto-Sync Script für TouchDesigner

Intelligentes Git-Sync-Script das **automatisch den aktuellen Branch** überwacht.

## ✨ Features

- ✅ **Automatische Branch-Erkennung** - kein hardcodierter Branch-Name!
- ✅ **Nur bei echten Änderungen** - kein Spam wenn nichts Neues da ist
- ✅ **Konfigurierbares Intervall** - Standard 30 Sekunden
- ✅ **Einmal-Modus** - für manuelles Sync
- ✅ **Sauber abbrechen** mit Ctrl+C

## 🚀 Verwendung

### Einmaliger Sync (empfohlen zum Testen)

```bash
cd /path/to/TOUCHDESIGNER
python scripts/auto_sync.py --once
```

### Kontinuierlicher Sync (alle 30 Sekunden)

```bash
python scripts/auto_sync.py
```

### Eigenes Intervall (z.B. alle 60 Sekunden)

```bash
python scripts/auto_sync.py --interval 60
```

### Im Hintergrund laufen lassen (Linux/Mac)

```bash
nohup python scripts/auto_sync.py &
```

### Im Hintergrund laufen lassen (Windows)

```powershell
Start-Process python -ArgumentList "scripts/auto_sync.py" -WindowStyle Hidden
```

## 🛑 Stoppen

**Vordergrund:** Drücke `Ctrl+C`

**Hintergrund (Linux/Mac):**
```bash
pkill -f auto_sync.py
```

**Hintergrund (Windows):**
Task-Manager → Prozess "python.exe" (mit auto_sync.py) beenden

## 📋 Beispiel-Output

```
[AUTO-SYNC] Starte Auto-Sync (Intervall: 30s)
[AUTO-SYNC] Repository: /home/user/TOUCHDESIGNER
[AUTO-SYNC] Drücke Ctrl+C zum Beenden
------------------------------------------------------------
[23:45:12] Neue Änderungen gefunden auf Branch 'claude/code-review-...'! Synchronisiere...
[23:45:13] Synchronisiert! Bitte TouchDesigner neu laden.
```

**Keine Ausgabe = Keine neuen Änderungen** (kein Spam!)

## ⚙️ TouchDesigner Integration

### Option 1: DAT Execute (empfohlen)

1. Erstelle ein **Execute DAT** in TouchDesigner
2. Füge ein:

```python
import subprocess
import sys

def onFrameStart(frame):
    # Nur alle 30 Sekunden (bei 60fps = 1800 frames)
    if frame % 1800 == 0:
        subprocess.Popen([
            sys.executable,
            "/path/to/TOUCHDESIGNER/scripts/auto_sync.py",
            "--once"
        ])
```

### Option 2: Externes Python

Starte das Script separat in einem Terminal/CMD-Fenster:

```bash
python scripts/auto_sync.py --interval 60
```

## 🔧 Konfiguration

Das Script erkennt automatisch:
- ✅ Aktuellen Branch (z.B. `claude/code-review-...`)
- ✅ Remote-Namen (meist `origin`)
- ✅ Repository-Pfad (automatisch von Script-Ort)

Keine Config-Dateien nötig!

## ❌ Altes Script deaktivieren

Falls das alte Auto-Sync-Script noch läuft:

1. **Finde den Prozess:**
   ```bash
   ps aux | grep git
   ```

2. **Stoppe ihn:**
   ```bash
   kill <PROZESS_ID>
   ```

3. **Suche in TouchDesigner:**
   - Suche nach DATs mit "sync", "git", "pull" im Namen
   - Setze `Active = OFF`

## 📝 Notizen

- Das Script macht **NUR** `git fetch` und `git pull`
- **Keine** lokalen Änderungen werden überschrieben
- Bei Merge-Konflikten stoppt der Pull automatisch
- Log-Ausgaben mit Zeitstempel für Debugging
