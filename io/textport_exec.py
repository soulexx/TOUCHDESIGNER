# me - Execute DAT

import sys
from pathlib import Path

BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
	sys.path.insert(0, str(SRC_PATH))

from td_helpers.textport_tap import TextportLogger

LOGGER = TextportLogger(BASE_PATH / "logs" / "textport.log", max_lines=400)


def onStart():
	LOGGER.install()
	print("[textport_exec] logger installed onStart")


def onCreate():
	LOGGER.install()
	print("[textport_exec] logger installed onCreate")


def onExit():
	LOGGER.uninstall()
	print("[textport_exec] logger uninstalled onExit")
