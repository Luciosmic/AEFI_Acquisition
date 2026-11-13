"""The operator's path, as main.py composes it: the Objets mesurés panel and a
selector wired by the real wiring function, the presenter, service and
repository created in a scope that returns, garbage collected, then clicks."""

import gc
from datetime import datetime, timezone
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from application.measured_object_registry.measured_object_service.measured_object_service import MeasuredObjectService
from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.measured_object_registry.fake.fake_measured_object_repository import FakeMeasuredObjectRepository
from interface.presenters.measured_object_presenter import MeasuredObjectPresenter
from interface.shell.dashboard_wiring import wire_measured_objects
from interface.widgets.measured_object_selector.measured_object_selector import MeasuredObjectSelector
from interface.widgets.panels.measured_object_registry_panel import MeasuredObjectRegistryPanel

HEXAGONE = MeasuredObject(measured_object_id=uuid4(), name="hexagone_metallique", registered_at=datetime.now(timezone.utc))


def _compose(selector, panel, repository) -> None:
    """Like main.py: presenter, service and bus are locals of a function that returns."""
    event_bus = InMemoryEventBus()
    presenter = MeasuredObjectPresenter(MeasuredObjectService(repository, event_bus), event_bus)
    wire_measured_objects((selector,), panel, presenter)


def _composed(typed="", confirmed=True):
    QApplication.instance() or QApplication([])
    repository = FakeMeasuredObjectRepository([HEXAGONE])
    selector = MeasuredObjectSelector()
    panel = MeasuredObjectRegistryPanel(ask_name=lambda *_: typed, confirm_delete=lambda _name: confirmed)
    _compose(selector, panel, repository)
    gc.collect()
    return repository, selector, panel


def _select_first(panel):
    item = panel.list_widget.item(0)
    panel.list_widget.setCurrentItem(item)
    item.setSelected(True)


def test_a_rename_click_reaches_the_registry_and_every_list():
    repository, selector, panel = _composed(typed="cylindre_base_hexagonale_metallique")
    selector.activated.emit(selector.findData(str(HEXAGONE.measured_object_id)))
    _select_first(panel)

    QTest.mouseClick(panel.rename_button, Qt.MouseButton.LeftButton)

    assert [o.name for o in repository.measured_objects] == ["cylindre_base_hexagonale_metallique"]
    assert repository.measured_objects[0].measured_object_id == HEXAGONE.measured_object_id
    assert panel.list_widget.item(0).text() == "cylindre_base_hexagonale_metallique"
    assert selector.current_measured_object().name == "cylindre_base_hexagonale_metallique"  # same choice, new name
    assert panel.status_label.text() == "Nom enregistré : cylindre_base_hexagonale_metallique"


def test_a_confirmed_delete_click_empties_the_registry_and_every_list():
    repository, selector, panel = _composed(confirmed=True)
    selector.activated.emit(selector.findData(str(HEXAGONE.measured_object_id)))
    _select_first(panel)

    QTest.mouseClick(panel.delete_button, Qt.MouseButton.LeftButton)

    assert repository.measured_objects == []
    assert panel.list_widget.count() == 0
    assert selector.current_measured_object() is None
    assert panel.status_label.text() == "Supprimé du registre : hexagone_metallique"


def test_a_new_object_from_the_panel_appears_in_the_selectors():
    repository, selector, panel = _composed(typed="plaque")

    QTest.mouseClick(panel.add_button, Qt.MouseButton.LeftButton)

    assert sorted(o.name for o in repository.measured_objects) == ["hexagone_metallique", "plaque"]
    assert selector.findText("plaque") >= 0
    assert panel.status_label.text() == "Enregistré : plaque"
