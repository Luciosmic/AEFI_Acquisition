from PySide6.QtWidgets import QPushButton, QHBoxLayout, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from interface.widgets.taskbar.taskbar_widget import TaskbarWidget
from interface.presentation.taskbar_model import TaskbarPresentationModel

class ModernTaskbar(TaskbarWidget):
    """
    Modern implementation of the Taskbar.
    Uses CSS styling, flat design, and animations (conceptually).

    Panels with a `group` are folded into a single button per group, opening a
    QMenu (click to reveal) listing that group's panels — the native, most
    style-stable Qt equivalent of an Android/iOS folder. Ungrouped panels keep
    a standalone button.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout
        self.layout_container = QHBoxLayout(self)
        self.layout_container.setContentsMargins(10, 5, 10, 5)
        self.layout_container.setSpacing(8)
        self.layout_container.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # State tracking for diffing
        self.buttons = {}  # panel_id -> QPushButton (ungrouped panels only)
        self.group_buttons = {}  # group_name -> QPushButton (opens the group's menu)
        self.group_menus = {}  # group_name -> QMenu
        self.panel_actions = {}  # panel_id -> QAction (grouped panels only)
        self.panel_group = {}  # panel_id -> group_name, for teardown

        # Styling
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            ModernTaskbar {
                background-color: #2D2D2D;
                border-top: 1px solid #3E3E3E;
                min-height: 60px;
            }
            QPushButton {
                background-color: transparent;
                color: #AAAAAA;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #383838;
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background-color: #404040;
                color: #4CAF50; /* Green Accent */
                border-bottom: 2px solid #4CAF50;
            }
            QMenu {
                background-color: #2D2D2D;
                color: #DDDDDD;
                border: 1px solid #3E3E3E;
            }
            QMenu::item {
                padding: 6px 20px;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #404040;
                color: #FFFFFF;
            }
        """)

    def render(self, model: TaskbarPresentationModel):
        """
        Syncs the view with the model.
        Highlights all visible/open panels.
        """
        current_ids = set()

        for panel in model.panels:
            current_ids.add(panel.id)
            if panel.group:
                self._render_grouped_panel(panel)
            else:
                self._render_ungrouped_panel(panel)

        self._remove_stale(current_ids)

    def add_action_group(self, group_label: str, actions: list[tuple[str, str]], on_triggered):
        """
        Adds a standalone dropdown button independent of the panel-toggle model —
        for entries that aren't dockable panels (e.g. launching an external process).
        `actions` is a list of (key, label); `on_triggered(key)` fires on click.
        """
        menu = QMenu(self)
        for key, label in actions:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, k=key: on_triggered(k))
            menu.addAction(action)

        btn = QPushButton(f"{group_label}  ▾")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMenu(menu)
        self.layout_container.addWidget(btn)

    def _render_grouped_panel(self, panel):
        group = panel.group

        if group not in self.group_buttons:
            menu = QMenu(self)
            btn = QPushButton(f"{group}  ▾")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMenu(menu)
            self.layout_container.addWidget(btn)
            self.group_buttons[group] = btn
            self.group_menus[group] = menu

        self.panel_group[panel.id] = group

        if panel.id not in self.panel_actions:
            action = QAction(panel.label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, pid=panel.id: self.panel_clicked.emit(pid))
            self.group_menus[group].addAction(action)
            self.panel_actions[panel.id] = action

        action = self.panel_actions[panel.id]
        action.setText(panel.label)
        action.setChecked(panel.is_visible)

        # Highlight the group button when at least one of its panels is open
        group_has_visible = any(
            act.isChecked() for pid, act in self.panel_actions.items()
            if self.panel_group.get(pid) == group
        )
        group_btn = self.group_buttons[group]
        if group_btn.property("active") != group_has_visible:
            group_btn.setProperty("active", group_has_visible)
            group_btn.style().unpolish(group_btn)
            group_btn.style().polish(group_btn)

    def _render_ungrouped_panel(self, panel):
        if panel.id not in self.buttons:
            btn = QPushButton(panel.label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, pid=panel.id: self.panel_clicked.emit(pid))
            self.layout_container.addWidget(btn)
            self.buttons[panel.id] = btn

        btn = self.buttons[panel.id]
        btn.setText(panel.label)

        was_active = btn.property("active")
        is_visible = panel.is_visible
        if was_active != is_visible:
            btn.setProperty("active", is_visible)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _remove_stale(self, current_ids):
        for pid in list(self.buttons.keys()):
            if pid not in current_ids:
                btn = self.buttons.pop(pid)
                self.layout_container.removeWidget(btn)
                btn.deleteLater()

        for pid in list(self.panel_actions.keys()):
            if pid not in current_ids:
                group = self.panel_group.pop(pid, None)
                action = self.panel_actions.pop(pid)
                menu = self.group_menus.get(group)
                if menu:
                    menu.removeAction(action)
                    if not menu.actions():
                        group_btn = self.group_buttons.pop(group)
                        self.layout_container.removeWidget(group_btn)
                        group_btn.deleteLater()
                        del self.group_menus[group]
