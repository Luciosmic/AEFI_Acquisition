from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle, QDockWidget
from PyQt6.QtCore import Qt, QSize

class CustomDockTitleBar(QWidget):
    """
    A custom title bar for QDockWidget that provides:
    - Visible Title
    - Explicit 'Float' (Detach) and 'Close' buttons
    - Tooltips for these buttons to clarify functionality (addressing user confusion).
    """
    def __init__(self, dock_widget: QDockWidget):
        super().__init__(parent=dock_widget)
        self.dock = dock_widget
        
        # Apply dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2E86AB;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #2A9D8F;
            }
        """)
        
        # Main Layout
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(4)
        
        # 1. Title Label
        title = dock_widget.windowTitle()
        self.title_label = QLabel(title)
        # We ensure the label doesn't block mouse events so dragging might still work 
        # (though QDockWidget usually handles dragging on empty space)
        layout.addWidget(self.title_label)
        
        # Spacer to push buttons to right
        layout.addStretch()
        
        # 2. Float/Detach Button
        self.float_btn = QPushButton()
        # Use a standard 'Normal' icon (often looks like two windows or a restore box)
        # This matches the 'two windows' icon the user mentioned.
        self.float_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton))
        self.float_btn.setToolTip("Detach: Open in a separate window")
        self.float_btn.setFixedSize(24, 24)
        self.float_btn.setFlat(True) # Make it blend in
        self.float_btn.clicked.connect(self._toggle_floating)
        layout.addWidget(self.float_btn)

        # 3. Close Button
        self.close_btn = QPushButton()
        # Use standard 'Close' icon (the 'little cross')
        self.close_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.close_btn.setToolTip("Close this tab")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setFlat(True)
        self.close_btn.clicked.connect(self.dock.close)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)

    def _toggle_floating(self):
        """Toggle the floating state of the parent dock."""
        if self.dock.isFloating():
            self.dock.setFloating(False)
        else:
            self.dock.setFloating(True)

    def mouseDoubleClickEvent(self, event):
        """
        Override double-click to Handle Maximize/Restore behavior.
        Default QDockWidget behavior is to toggle floating (dock back), which users find confusing
        when trying to maximize.
        """
        if self.dock.isFloating():
            if self.dock.isMaximized():
                self.dock.showNormal()
            else:
                self.dock.showMaximized()
        else:
            # If docked, double-click can detach (Float) it, which is a useful shortcut
            self.dock.setFloating(True)
            if self.dock.isFloating(): # Check if it succeeded
                self.dock.show() # Ensure visibility

