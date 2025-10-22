# me - Execute DAT

import importlib
import sys
from pathlib import Path

BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

_MOD_NAME = "td_helpers.textport_tap"
if _MOD_NAME in sys.modules:
    textport_tap = importlib.reload(sys.modules[_MOD_NAME])
else:
    textport_tap = importlib.import_module(_MOD_NAME)

TextportLogger = textport_tap.TextportLogger

TEXTPORT_MAX_LINES = 500
LOGGER = TextportLogger(
    BASE_PATH / "logs" / "textport.log",
    max_lines=TEXTPORT_MAX_LINES,
)


def install_logger():
    LOGGER.install()


def onStart():
    install_logger()


def onCreate():
    install_logger()


def onExit():
    LOGGER.uninstall()


def onPulse(par):
    install_logger()
