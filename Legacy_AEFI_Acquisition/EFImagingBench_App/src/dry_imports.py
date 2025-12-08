#!/usr/bin/env python3
"""
Dry import tester for EFImagingBench_GUI.
Creates minimal stubs for PyQt5 and pyqtgraph to validate Python import paths
without requiring the real GUI libraries.
"""

import sys
import os
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def make_pyqt_stubs():
    # Base PyQt5 package
    pyqt5 = types.ModuleType("PyQt5")
    sys.modules["PyQt5"] = pyqt5

    # QtCore stub
    qtcore = types.ModuleType("PyQt5.QtCore")

    class QObject:
        pass

    def pyqtSignal(*args, **kwargs):
        return object()

    class QThread:
        pass

    class Qt:
        AlignCenter = 0
        DotLine = 1
        SolidLine = 2

    class QTimer:
        pass

    qtcore.QObject = QObject
    qtcore.pyqtSignal = pyqtSignal
    qtcore.QThread = QThread
    qtcore.Qt = Qt
    qtcore.QTimer = QTimer
    sys.modules["PyQt5.QtCore"] = qtcore

    # QtWidgets stub
    qtwidgets = types.ModuleType("PyQt5.QtWidgets")

    class QWidget:
        pass

    class QMainWindow(QWidget):
        pass

    class QApplication:
        def __init__(self, *a, **k):
            pass

        def exec_(self):
            return 0

    class QLayout:
        pass

    class QVBoxLayout(QLayout):
        def __init__(self, *a, **k):
            pass

    class QHBoxLayout(QLayout):
        def __init__(self, *a, **k):
            pass

    class QTabWidget(QWidget):
        pass

    class QStatusBar(QWidget):
        def showMessage(self, *a, **k):
            pass

    class QLabel(QWidget):
        def __init__(self, *a, **k):
            pass

    class QLineEdit(QWidget):
        pass

    class QDoubleSpinBox(QWidget):
        pass

    class QSpinBox(QWidget):
        pass

    class QComboBox(QWidget):
        def addItems(self, *a, **k):
            pass

    class QPushButton(QWidget):
        def setCheckable(self, *a, **k):
            pass

        def setChecked(self, *a, **k):
            pass

        def setStyleSheet(self, *a, **k):
            pass

    class QCheckBox(QWidget):
        def setChecked(self, *a, **k):
            pass

    class QGroupBox(QWidget):
        pass

    class QGridLayout(QLayout):
        pass

    class QMessageBox:
        @staticmethod
        def information(*a, **k):
            pass

        @staticmethod
        def warning(*a, **k):
            pass

        @staticmethod
        def critical(*a, **k):
            pass

    qtwidgets.QWidget = QWidget
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QApplication = QApplication
    qtwidgets.QVBoxLayout = QVBoxLayout
    qtwidgets.QHBoxLayout = QHBoxLayout
    qtwidgets.QTabWidget = QTabWidget
    qtwidgets.QStatusBar = QStatusBar
    qtwidgets.QLabel = QLabel
    qtwidgets.QLineEdit = QLineEdit
    qtwidgets.QDoubleSpinBox = QDoubleSpinBox
    qtwidgets.QSpinBox = QSpinBox
    qtwidgets.QComboBox = QComboBox
    qtwidgets.QPushButton = QPushButton
    qtwidgets.QCheckBox = QCheckBox
    qtwidgets.QGroupBox = QGroupBox
    qtwidgets.QGridLayout = QGridLayout
    qtwidgets.QMessageBox = QMessageBox
    sys.modules["PyQt5.QtWidgets"] = qtwidgets

    # QtGui stub (minimal)
    qtgui = types.ModuleType("PyQt5.QtGui")
    class QFont:
        pass
    qtgui.QFont = QFont
    sys.modules["PyQt5.QtGui"] = qtgui


def make_pyqtgraph_stub():
    pg = types.ModuleType("pyqtgraph")

    class PlotWidget:
        def __init__(self, *a, **k):
            pass

        def setBackground(self, *a, **k):
            pass

        def showGrid(self, *a, **k):
            pass

        def setLabel(self, *a, **k):
            pass

        def addLegend(self, *a, **k):
            pass

        def plot(self, *a, **k):
            class Curve:
                def setData(self, *a, **k):
                    pass

                def setVisible(self, *a, **k):
                    pass
            return Curve()

    def mkPen(*a, **k):
        return object()

    pg.PlotWidget = PlotWidget
    pg.mkPen = mkPen
    sys.modules["pyqtgraph"] = pg


def main():
    print("Setting up stubs for PyQt5 and pyqtgraph...")
    make_pyqt_stubs()
    make_pyqtgraph_stub()

    print("Trying to import EFImagingBench_GUI...")
    try:
        import gui.EFImagingBench_GUI as gui_mod
        print("✓ EFImagingBench_GUI imported successfully")
    except Exception as e:
        print("✗ Import error:", e)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("All imports resolved at Python level (GUI logic not executed).")


if __name__ == "__main__":
    main()



