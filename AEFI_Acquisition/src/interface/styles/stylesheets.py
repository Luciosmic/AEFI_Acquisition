"""
Centralized stylesheets for the application.
"""

# Main Application Theme (Dark Fusion)
APP_STYLESHEET = """
    QToolTip { 
        color: #ffffff; 
        background-color: #2a82da; 
        border: 1px solid white; 
    }
    QGroupBox {
        border: 1px solid #555;
        border-radius: 5px;
        margin-top: 10px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 3px;
        color: #aaa;
    }
    
    /* Fix for Windows Separators and Dock/Tab issues */
    QMainWindow::separator {
        background-color: #2d2d2d;
        width: 4px;
        height: 4px;
    }
    
    QDockWidget {
        color: white;
    }
    
    QDockWidget::title {
        background: #353535;
        padding-left: 5px;
        padding-top: 4px;
        padding-bottom: 4px;
    }
    
    /* Tab Bar styling for Dock Widgets */
    QTabBar::tab {
        background: #2d2d2d;
        color: #cccccc;
        padding: 5px 10px;
        border: 1px solid #444;
        border-bottom: none;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background: #454545;
        color: white;
        border-bottom: 1px solid #454545; /* Blend with container */
    }
    
    QTabBar::tab:hover {
        background: #3a3a3a;
    }
    
    /* Splitter handle color */
    QSplitter::handle {
        background-color: #2d2d2d;
    }
"""

# Qt Advanced Docking System (QtAds) Styles
# This needs to be applied to the CDockManager or specific widgets
# Qt Advanced Docking System (QtAds) Styles
# This needs to be applied to the CDockManager or specific widgets
DOCK_MANAGER_STYLESHEET = """
    ads--CDockWidgetTab, CDockWidgetTab {
        background-color: #404040;
        border: 1px solid #555;
        border-bottom: none;
        color: #FFFFFF;
        padding: 4px 8px;  /* Reduced padding (was 6px 12px) */
        min-height: 22px;  /* Reduced height (was 28px) */
        font-weight: 500;
        font-size: 11px;   /* Slightly smaller font */
    }
    ads--CDockWidgetTab:hover, CDockWidgetTab:hover {
        background-color: #4A4A4A;
    }
    ads--CDockWidgetTab[activeTab="true"], CDockWidgetTab[activeTab="true"] {
        background-color: #2E7D32;
        color: #FFFFFF;
        border: 1px solid #4CAF50;
        border-bottom: none;
        font-weight: 600;
    }
    
    /* Close Button Styling - Make it smaller */
    ads--CDockWidgetTab QPushButton, CDockWidgetTab QPushButton {
        max-width: 12px;
        max-height: 12px;
        qproperty-iconSize: 10px 10px; /* Force smaller icon size */
        padding: 0px;
        margin-left: 4px;
        border: none;
        background: transparent;
        border-radius: 2px;
    }
    ads--CDockWidgetTab QPushButton:hover, CDockWidgetTab QPushButton:hover {
        background-color: rgba(255, 255, 255, 30);
    }
    ads--CDockWidgetTab QPushButton:pressed, CDockWidgetTab QPushButton:pressed {
        background-color: rgba(255, 255, 255, 50);
    }

    ads--CDockAreaWidget, CDockAreaWidget {
        background-color: #2A2A2A;
        border: none;
    }
    ads--CDockAreaTitleBar, CDockAreaTitleBar {
        background-color: #2A2A2A;
        border: none;
        border-bottom: 1px solid #404040;
    }
    ads--CDockAreaTabBar, CDockAreaTabBar {
        background-color: #2A2A2A;
        border: none;
        border-bottom: 1px solid #404040;
    }
    
    /* Splitter styling for QtAds */
    QSplitter::handle {
        background-color: #2d2d2d;
    }
"""
