# Auto-Sync Script für TouchDesigner
# Läuft im Hintergrund und holt automatisch neue Änderungen

$branch = "claude/debug-dmx-conversion-011CUSwRp8ggwNj6TPricrUc"
$checkInterval = 5  # Sekunden zwischen Checks

Write-Host "=== TouchDesigner Auto-Sync gestartet ===" -ForegroundColor Green
Write-Host "Branch: $branch" -ForegroundColor Cyan
Write-Host "Prüft alle $checkInterval Sekunden auf Änderungen..." -ForegroundColor Cyan
Write-Host "Drücke Ctrl+C zum Beenden`n" -ForegroundColor Yellow

while ($true) {
    try {
        # Hole neueste Commits vom Server
        git fetch origin $branch 2>$null | Out-Null

        # Prüfe ob lokaler Branch hinter remote ist
        $local = git rev-parse HEAD
        $remote = git rev-parse "origin/$branch"

        if ($local -ne $remote) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
            Write-Host "Neue Änderungen gefunden! Synchronisiere..." -ForegroundColor Yellow

            # Pull mit Stash (falls lokale Änderungen)
            git stash push -m "Auto-sync stash" 2>$null | Out-Null
            git pull origin $branch

            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
            Write-Host "✓ Synchronisiert! Bitte TouchDesigner neu laden." -ForegroundColor Green
            Write-Host ""
        }

        Start-Sleep -Seconds $checkInterval

    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Fehler: $_" -ForegroundColor Red
        Start-Sleep -Seconds $checkInterval
    }
}
