from abc import ABCMeta
from PySide6.QtCore import QObject


class QABCMeta(type(QObject), ABCMeta):
    """Combined metaclass resolving conflict between QObject (Shiboken) and ABCMeta."""
    pass
