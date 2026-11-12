import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.services.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO
from interface.widgets.measured_object_selector.measured_object_selector import NEW_MEASURED_OBJECT_LABEL, MeasuredObjectSelector

LUIS = MeasuredObjectDTO(measured_object_id="id-luis", name="Luis Saluden")
MARIE = MeasuredObjectDTO(measured_object_id="id-marie", name="Marie Curie")
_ALIVE = []


def _selector(typed: str = ""):
    QApplication.instance() or QApplication([])
    selector = MeasuredObjectSelector(ask_name=lambda: typed)
    _ALIVE.append(selector)
    selector.set_measured_objects([LUIS])
    return selector


def _choose(selector, label):
    index = selector.findText(label)
    selector.setCurrentIndex(index)
    selector.activated.emit(index)


def test_nobody_is_selected_until_the_measured_object_chooses():
    selector = _selector()
    assert selector.current_measured_object() is None
    assert selector.itemText(selector.count() - 1) == NEW_MEASURED_OBJECT_LABEL


def test_choosing_a_known_measured_object_selects_it():
    selector = _selector()
    _choose(selector, "Luis Saluden")
    assert selector.current_measured_object() == LUIS


def test_new_measured_object_asks_a_name_and_selects_the_registered_one():
    selector = _selector(typed="Marie Curie")
    requested = []
    selector.register_requested.connect(requested.append)

    _choose(selector, NEW_MEASURED_OBJECT_LABEL)
    assert requested == ["Marie Curie"]
    assert selector.current_measured_object() is None  # not selected before the registry answers

    selector.on_measured_object_registered(MARIE, False)
    assert selector.current_measured_object() == MARIE


def test_a_known_spelling_selects_the_existing_measured_object_and_says_so():
    selector = _selector(typed="luis saluden")
    _choose(selector, NEW_MEASURED_OBJECT_LABEL)

    selector.on_measured_object_registered(LUIS, True)

    assert selector.current_measured_object() == LUIS
    assert "Déjà enregistré : Luis Saluden" in selector.statusTip()


def test_cancelled_or_blank_name_registers_nobody():
    selector = _selector(typed="   ")
    requested = []
    selector.register_requested.connect(requested.append)
    _choose(selector, NEW_MEASURED_OBJECT_LABEL)
    assert requested == []
    assert selector.current_measured_object() is None


def test_only_the_requesting_selector_takes_the_registered_measured_object():
    scan, reading = _selector(typed="Marie Curie"), _selector()
    _choose(reading, "Luis Saluden")
    _choose(scan, NEW_MEASURED_OBJECT_LABEL)

    for selector in (scan, reading):  # the presenter broadcasts to every selector
        selector.set_measured_objects([LUIS, MARIE])
        selector.on_measured_object_registered(MARIE, False)

    assert scan.current_measured_object() == MARIE
    assert reading.current_measured_object() == LUIS
