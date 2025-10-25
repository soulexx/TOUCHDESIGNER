#!/usr/bin/env python3
"""
Auto-Sync Script für TouchDesigner Git Repository.

Dieses Script überwacht automatisch den AKTUELLEN Branch (nicht hardcodiert!)
und synchronisiert nur bei echten Änderungen.

Usage:
    python scripts/auto_sync.py [--interval SEKUNDEN] [--once]
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class GitAutoSync:
    def __init__(self, repo_path: Path, interval: int = 30):
        self.repo_path = repo_path
        self.interval = interval
        self.last_commit = None

    def get_current_branch(self) -> str:
        """Ermittelt den aktuellen Branch-Namen."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Kann Branch nicht ermitteln: {e}")
            return None

    def get_remote_name(self) -> str:
        """Ermittelt den Remote-Namen (meist 'origin')."""
        try:
            result = subprocess.run(
                ["git", "remote"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            remotes = result.stdout.strip().split('\n')
            return remotes[0] if remotes else "origin"
        except subprocess.CalledProcessError:
            return "origin"

    def get_current_commit(self) -> str:
        """Holt den aktuellen Commit-Hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def fetch_updates(self, branch: str) -> bool:
        """Fetcht Updates vom Remote für den aktuellen Branch."""
        remote = self.get_remote_name()
        try:
            subprocess.run(
                ["git", "fetch", remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Fetch fehlgeschlagen: {e.stderr}")
            return False

    def check_for_updates(self, branch: str) -> bool:
        """Prüft ob es neue Commits auf dem Remote gibt."""
        remote = self.get_remote_name()
        try:
            # Hole lokalen Commit
            local = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            # Hole Remote-Commit
            remote_ref = f"{remote}/{branch}"
            remote_commit = subprocess.run(
                ["git", "rev-parse", remote_ref],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            return local != remote_commit
        except subprocess.CalledProcessError:
            return False

    def pull_updates(self, branch: str) -> bool:
        """Pullt Updates vom Remote."""
        remote = self.get_remote_name()
        try:
            result = subprocess.run(
                ["git", "pull", remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return "Already up to date" not in result.stdout
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Pull fehlgeschlagen: {e.stderr}")
            return False

    def sync_once(self) -> bool:
        """Führt einen einzelnen Sync-Vorgang durch."""
        branch = self.get_current_branch()
        if not branch:
            print("[ERROR] Kein gültiger Branch gefunden!")
            return False

        timestamp = datetime.now().strftime("[%H:%M:%S]")

        # Fetch Updates
        if not self.fetch_updates(branch):
            return False

        # Prüfe ob Updates verfügbar
        if not self.check_for_updates(branch):
            # Keine neuen Änderungen - KEIN Spam!
            return False

        # Echte Änderungen gefunden!
        print(f"{timestamp} Neue Änderungen gefunden auf Branch '{branch}'! Synchronisiere...")

        # Pull Updates
        if self.pull_updates(branch):
            print(f"{timestamp} Synchronisiert! Bitte TouchDesigner neu laden.")
            return True
        else:
            print(f"{timestamp} Bereits aktuell.")
            return False

    def run_continuous(self):
        """Läuft kontinuierlich im angegebenen Intervall."""
        print(f"[AUTO-SYNC] Starte Auto-Sync (Intervall: {self.interval}s)")
        print(f"[AUTO-SYNC] Repository: {self.repo_path}")
        print(f"[AUTO-SYNC] Drücke Ctrl+C zum Beenden")
        print("-" * 60)

        try:
            while True:
                self.sync_once()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n[AUTO-SYNC] Gestoppt.")


def main():
    parser = argparse.ArgumentParser(description="Git Auto-Sync für TouchDesigner")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Sync-Intervall in Sekunden (Standard: 30)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Nur einmal synchronisieren, dann beenden"
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Pfad zum Git-Repository"
    )

    args = parser.parse_args()

    # Validiere Repository
    if not (args.repo / ".git").exists():
        print(f"[ERROR] Kein Git-Repository gefunden in: {args.repo}")
        sys.exit(1)

    syncer = GitAutoSync(args.repo, args.interval)

    if args.once:
        # Einmaliger Sync
        syncer.sync_once()
    else:
        # Kontinuierlicher Sync
        syncer.run_continuous()


if __name__ == "__main__":
    main()
