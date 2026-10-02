import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.services.operator_service.dtos.operator_dto import OperatorDTO
from interface.widgets.operator_selector.operator_selector import NEW_OPERATOR_LABEL, OperatorSelector

LUIS = OperatorDTO(operator_id="id-luis", name="Luis Saluden")
MARIE = OperatorDTO(operator_id="id-marie", name="Marie Curie")
_ALIVE = []


def _selector(typed: str = ""):
    QApplication.instance() or QApplication([])
    selector = OperatorSelector(ask_name=lambda: typed)
    _ALIVE.append(selector)
    selector.set_operators([LUIS])
    return selector


def _choose(selector, label):
    index = selector.findText(label)
    selector.setCurrentIndex(index)
    selector.activated.emit(index)


def test_nobody_is_selected_until_the_operator_chooses():
    selector = _selector()
    assert selector.current_operator() is None
    assert selector.itemText(selector.count() - 1) == NEW_OPERATOR_LABEL


def test_choosing_a_known_operator_selects_it():
    selector = _selector()
    _choose(selector, "Luis Saluden")
    assert selector.current_operator() == LUIS


def test_new_operator_asks_a_name_and_selects_the_registered_one():
    selector = _selector(typed="Marie Curie")
    requested = []
    selector.register_requested.connect(requested.append)

    _choose(selector, NEW_OPERATOR_LABEL)
    assert requested == ["Marie Curie"]
    assert selector.current_operator() is None  # not selected before the registry answers

    selector.on_operator_registered(MARIE, False)
    assert selector.current_operator() == MARIE


def test_a_known_spelling_selects_the_existing_operator_and_says_so():
    selector = _selector(typed="luis saluden")
    _choose(selector, NEW_OPERATOR_LABEL)

    selector.on_operator_registered(LUIS, True)

    assert selector.current_operator() == LUIS
    assert "Déjà enregistré : Luis Saluden" in selector.statusTip()


def test_cancelled_or_blank_name_registers_nobody():
    selector = _selector(typed="   ")
    requested = []
    selector.register_requested.connect(requested.append)
    _choose(selector, NEW_OPERATOR_LABEL)
    assert requested == []
    assert selector.current_operator() is None


def test_only_the_requesting_selector_takes_the_registered_operator():
    scan, reading = _selector(typed="Marie Curie"), _selector()
    _choose(reading, "Luis Saluden")
    _choose(scan, NEW_OPERATOR_LABEL)

    for selector in (scan, reading):  # the presenter broadcasts to every selector
        selector.set_operators([LUIS, MARIE])
        selector.on_operator_registered(MARIE, False)

    assert scan.current_operator() == MARIE
    assert reading.current_operator() == LUIS
