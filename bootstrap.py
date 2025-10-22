# bootstrap: einmal beim Projektstart ausführen
import sys, os, importlib

SRC = project.folder + '/src'
if SRC not in sys.path:
    sys.path.append(SRC)

IO = project.folder + '/io'
if IO not in sys.path:
    sys.path.append(IO)


def reload(module_name):
    """Schnell-Reload für ein Modul, z.B. reload('io.router')"""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        __import__(module_name)
    debug("reloaded: " + module_name)


def install_textport_logger():
    """Optional helper to enable the textport logger manually."""
    comp = op("/project1/io/textport_exec")
    if comp and hasattr(comp.module, "install_logger"):
        comp.module.install_logger()
