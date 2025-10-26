import os
import sys
import time
import traceback
from pathlib import Path

# TouchDesigner-compatible path resolution
try:
    if 'TOUCHDESIGNER_ROOT' in os.environ:
        BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT'))
    elif 'project' in globals():
        BASE_PATH = Path(project.folder).resolve()  # type: ignore
    else:
        BASE_PATH = Path(__file__).resolve().parent.parent
except Exception:
    BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
SRC_PATH = BASE_PATH / "src"
if str(SRC_PATH) not in sys.path:
	sys.path.insert(0, str(SRC_PATH))

from td_helpers.file_ring_buffer import FileRingBuffer

COMMAND_PATH = BASE_PATH / "scripts" / "live_command.py"
_LOG = FileRingBuffer(
    BASE_PATH / "logs" / "command_runner.log",
    max_lines=200,
    persist=True,
)


def _log(line: str) -> None:
	ts = f"{time.time():.3f}"
	_LOG.append(f"{ts} {line}")


def _run(dat):
	code = dat.text
	if not code.strip():
		return
	_log(f"RUN {COMMAND_PATH.name}")
	ns = {"op": op, "project": op("/project1"), "__name__": "__td_live_command__"}  # type: ignore
	try:
		exec(compile(code, str(COMMAND_PATH), "exec"), ns, ns)
		_log(f"DONE {COMMAND_PATH.name}")
	except Exception:
		err = traceback.format_exc()
		_log(f"ERROR {err.strip()}")
		print("[command_runner] EXC while executing live command:\n", err)
	return


def onDATChange(dat):
	_run(dat)
	return


def onTableChange(dat):
	_run(dat)
	return
