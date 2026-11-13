import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO
from interface.widgets.panels.measured_object_registry_panel import MeasuredObjectRegistryPanel

HEXAGONE = MeasuredObjectDTO(measured_object_id="id-hexagone", name="hexagone_metallique")
PLAQUE = MeasuredObjectDTO(measured_object_id="id-plaque", name="plaque")
_ALIVE = []


def _panel(typed: str = "", confirmed: bool = True):
    QApplication.instance() or QApplication([])
    asked = []

    def ask_name(title, label, text):
        asked.append(text)
        return typed

    panel = MeasuredObjectRegistryPanel(ask_name=ask_name, confirm_delete=lambda _name: confirmed)
    panel.asked = asked
    _ALIVE.append(panel)
    panel.set_measured_objects([HEXAGONE, PLAQUE])
    return panel


def _select(panel, name):
    item = panel.list_widget.findItems(name, Qt.MatchFlag.MatchExactly)[0]
    panel.list_widget.setCurrentItem(item)
    item.setSelected(True)


def _record(signal):
    emitted = []
    signal.connect(lambda *args: emitted.append(args))
    return emitted


def test_lists_the_registry_and_needs_a_selection_to_rename_or_delete():
    panel = _panel()
    assert [panel.list_widget.item(i).text() for i in range(panel.list_widget.count())] == ["hexagone_metallique", "plaque"]
    assert not panel.rename_button.isEnabled() and not panel.delete_button.isEnabled()
    _select(panel, "plaque")
    assert panel.rename_button.isEnabled() and panel.delete_button.isEnabled()


def test_rename_proposes_the_current_name_and_asks_by_identity():
    panel = _panel(typed="cylindre_base_hexagonale_metallique")
    emitted = _record(panel.rename_requested)
    _select(panel, "hexagone_metallique")
    panel.rename_button.click()
    assert panel.asked == ["hexagone_metallique"]
    assert emitted == [("id-hexagone", "cylindre_base_hexagonale_metallique")]


def test_a_cancelled_rename_asks_nothing():
    panel = _panel(typed="")
    emitted = _record(panel.rename_requested)
    _select(panel, "plaque")
    panel.rename_button.click()
    assert emitted == []


def test_delete_asks_by_identity_only_once_confirmed():
    refused = _panel(confirmed=False)
    emitted = _record(refused.delete_requested)
    _select(refused, "plaque")
    refused.delete_button.click()
    assert emitted == []

    confirmed = _panel(confirmed=True)
    emitted = _record(confirmed.delete_requested)
    _select(confirmed, "plaque")
    confirmed.delete_button.click()
    assert emitted == [("id-plaque",)]


def test_add_asks_for_a_name():
    panel = _panel(typed="sphère 20 mm")
    emitted = _record(panel.register_requested)
    panel.add_button.click()
    assert emitted == [("sphère 20 mm",)]


def test_the_selection_survives_a_refresh_and_a_deleted_one_is_dropped():
    panel = _panel()
    _select(panel, "plaque")
    panel.set_measured_objects([HEXAGONE, PLAQUE])
    assert panel.selected_measured_object() == PLAQUE
    panel.set_measured_objects([HEXAGONE])
    assert panel.selected_measured_object() is None
    assert not panel.delete_button.isEnabled()


def test_outcomes_are_shown_in_words():
    panel = _panel()
    panel.show_failure("Renommage refusé : un autre objet mesuré s'appelle déjà « plaque »")
    assert "plaque" in panel.status_label.text()
    panel.show_done("Supprimé du registre : plaque")
    assert panel.status_label.text() == "Supprimé du registre : plaque"
