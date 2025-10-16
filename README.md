# TOUCHDESIGNER

## Live Command Runner

- Bearbeite `scripts/live_command.py` in VS Code. Beim Speichern lädt TouchDesigner den Inhalt und führt ihn im Projektkontext aus (siehe `io/command_runner_callbacks.py`).  
- Richte in TD einen `Text DAT` ein, der auf dieselbe Datei zeigt (`File` → `c:\_DEV\TOUCHDESIGNER\scripts\live_command.py`) und aktiviere einen `DAT Execute DAT` mit diesem Callback.  
- Ergebnisse und Fehler landen in `logs/command_runner.log`, zusätzlich erscheinen Exceptions im Textport.  
- Komfortfunktion: Der Logger verhindert Doppel-Auslösungen, wenn der Inhalt unverändert bleibt.
