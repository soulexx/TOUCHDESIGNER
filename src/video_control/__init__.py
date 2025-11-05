"""Video control helpers for TouchDesigner.

Expose a tiny API that can be imported with ``import video_control``
inside TouchDesigner scripts.  See :mod:`video_control.controller`
for the main entry points.
"""

from .controller import VideoController, get_controller

__all__ = ["VideoController", "get_controller"]
