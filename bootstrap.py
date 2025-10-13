# bootstrap: einmal beim Projektstart ausführen
import sys, os, importlib

SRC = project.folder + '/src'
if SRC not in sys.path:
    sys.path.append(SRC)

def reload(module_name):
    """Schnell-Reload für ein Modul, z.B. reload('io.router')"""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        __import__(module_name)
    debug("reloaded: " + module_name)
