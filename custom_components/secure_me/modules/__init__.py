from __future__ import annotations

"""Secure Me alarm system modules."""
# VERSION = "2.0.1"

from .base import AlarmModule
from .camera import CameraModule
from .climate import ClimateModule
from .lights import LightsModule
from .lock import LockModule
from .siren import SirenModule
from .tts import TTSModule

__all__ = [
    "AlarmModule",
    "CameraModule",
    "ClimateModule",
    "LightsModule",
    "LockModule",
    "SirenModule",
    "TTSModule",
]
