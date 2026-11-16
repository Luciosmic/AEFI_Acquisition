"""
upstream_objects - The objects borrowed from the acquisition application, re-exported under one roof.
See upstream_objects_intention.md.
"""

from interface.presentation.carrier_model import CarrierPresentationModel
from interface.presentation.taskbar_model import TaskbarPresentationModel
from interface.presenters.taskbar_presenter import TaskbarPresenter
from interface.widgets.carrier.windows_carrier import WindowsCarrier
from interface.widgets.taskbar.modern_taskbar import ModernTaskbar

__all__ = [
    "CarrierPresentationModel",
    "ModernTaskbar",
    "TaskbarPresentationModel",
    "TaskbarPresenter",
    "WindowsCarrier",
]
