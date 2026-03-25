"""
Visualization View
PySide6 GUI implementation.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QLabel, QGroupBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Signal, Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

class VisualisationView(QMainWindow):
    # Signals
    scan_selected_signal = Signal(str)
    step_selected_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEFI Visualization (Restored)")
        self.resize(1600, 900)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # --- Left Panel (Controls) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(400) # Fixed width as in screenshot style
        
        # Data Selection Group
        grp_data = QGroupBox("Data Selection")
        lay_data = QVBoxLayout()
        
        lay_data.addWidget(QLabel("Scan File:"))
        self.list_scans = QListWidget()
        self.list_scans.currentTextChanged.connect(self.scan_selected_signal.emit)
        lay_data.addWidget(self.list_scans)
        
        lay_data.addWidget(QLabel("Processing Step:"))
        self.list_steps = QListWidget()
        self.list_steps.currentTextChanged.connect(self.step_selected_signal.emit)
        lay_data.addWidget(self.list_steps)
        
        grp_data.setLayout(lay_data)
        left_layout.addWidget(grp_data, stretch=3)
        
        # Frame Info Group
        grp_info = QGroupBox("Frame Info")
        lay_info = QVBoxLayout()
        self.lbl_rotation = QLabel("Rotation: N/A")
        self.lbl_ref_point = QLabel("Ref Point: N/A")
        self.lbl_cursor = QLabel("Cursor: Out of axes")
        # High contrast style (Cyan on Dark)
        self.lbl_cursor.setStyleSheet("color: #00FFFF; font-weight: bold; font-size: 10pt;")
        
        lay_info.addWidget(self.lbl_rotation)
        lay_info.addWidget(self.lbl_ref_point)
        lay_info.addWidget(self.lbl_cursor)
        grp_info.setLayout(lay_info)
        left_layout.addWidget(grp_info, stretch=0)
        
        # System Feedback Group
        grp_log = QGroupBox("System Feedback")
        lay_log = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("font-family: Consolas; font-size: 9pt;")
        lay_log.addWidget(self.txt_log)
        grp_log.setLayout(lay_log)
        left_layout.addWidget(grp_log, stretch=1)
        
        main_layout.addWidget(left_panel)
        
        # --- Right Panel (Plot) ---
        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        # Placeholder
        self.plot_layout.addWidget(QLabel("Select a scan and step to visualization"))
        
        main_layout.addWidget(self.plot_container, stretch=1)
        
    # --- Public Methods for Presenter ---
    
    def set_scan_list(self, scans: list):
        self.list_scans.clear()
        self.list_scans.addItems(scans)
        
    def set_step_list(self, steps: list):
        self.list_steps.clear()
        self.list_steps.addItems(steps)
        
    def log_feedback(self, msg: str):
        self.txt_log.append(f">> {msg}")
        
    def set_frame_info(self, rotation: str, ref_point: str):
        self.lbl_rotation.setText(f"Rotation: {rotation}")
        self.lbl_ref_point.setText(f"Ref Point: {ref_point}")
        
    def update_plot(self, fig: Figure):
        # Clear existing
        for i in reversed(range(self.plot_layout.count())):
            widget = self.plot_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add new canvas
        canvas = FigureCanvasQTAgg(fig)
        self.plot_layout.addWidget(canvas)
        
        # Connect mouse event
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def on_mouse_move(self, event):
        """Handle mouse move event to show value under cursor."""
        if event.inaxes:
            x, y = event.xdata, event.ydata
            
            # Find the image in the axes
            # Usually axes.images[0] is the heatmap
            ax = event.inaxes
            if ax.images:
                im = ax.images[0]
                # Get value from array corresponding to x, y
                # This depends on extent and array shape
                # Easier approach: use the array directly if we can map coords
                
                # im.get_cursor_data returns the value at the event position
                # (Newer matplotlib versions)
                try:
                    val = im.get_cursor_data(event)
                    if val is not None and str(val) != 'nan':
                        # Format nicely
                        if isinstance(val, (int, float,  np.number)):
                            self.lbl_cursor.setText(f"Cursor: x={x:.1f}, y={y:.1f} | z={val:.4g}")
                        else:
                             # Should handle masked array
                            self.lbl_cursor.setText(f"Cursor: x={x:.1f}, y={y:.1f} | z={val}")
                    else:
                        self.lbl_cursor.setText(f"Cursor: x={x:.1f}, y={y:.1f} | z=NaN")
                except Exception:
                     self.lbl_cursor.setText(f"Cursor: x={x:.1f}, y={y:.1f}")
            else:
                 self.lbl_cursor.setText(f"Cursor: x={x:.1f}, y={y:.1f}")
        else:
            self.lbl_cursor.setText("Cursor: Out of axes")
