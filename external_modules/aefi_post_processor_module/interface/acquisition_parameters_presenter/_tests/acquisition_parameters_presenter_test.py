"""Le presenter du panneau « Paramètres d'acquisition » avec une vue Fake."""

import os

from ....application.acquisition_catalog_service.dtos.acquisition_status_dto import TO_RECOMPUTE, AcquisitionStatusDTO
from ....application.acquisition_catalog_service.dtos.applied_rotation_dto import AppliedRotationDTO
from ..acquisition_parameters_presenter import AcquisitionParametersPresenter

NAME = "2026-11-13_103000_stepScan_bouteille"


class FakeParametersView:
    def __init__(self):
        self.title = None
        self.rows = []

    def set_title(self, text):
        self.title = text

    def set_rows(self, rows):
        self.rows = list(rows)

    def value(self, label):
        return dict(self.rows)[label]


def _status(**overrides):
    values = dict(
        name=NAME, kind="stepScan", folder=f"/export/{NAME}", csv_file=f"/export/{NAME}/{NAME}_aefi.csv",
        acquisition_file=f"/export/{NAME}/{NAME}.h5", state=TO_RECOMPUTE, reason="new",
        measured_object="bouteille_cristalline", schema_version="1.4",
        applied_rotation=AppliedRotationDTO(
            (34.9, 45.7, -5.3), "extrinsic", "ZYX", "sources_to_sensor", origin="calibrated", calibration_id="cal-2026-11-13",
        ),
    )
    values.update(overrides)
    return AcquisitionStatusDTO(**values)


def _presenter():
    view = FakeParametersView()
    return AcquisitionParametersPresenter(view), view


def test_the_panel_shows_the_object_the_angles_the_convention_and_the_schema_of_the_chosen_acquisition():
    presenter, view = _presenter()

    presenter.show(_status())

    assert view.title == NAME
    assert view.value("Objet mesuré") == "bouteille_cristalline"
    assert view.value("Angle θx appliqué") == "34.9 °"
    assert view.value("Angle θy appliqué") == "45.7 °"
    assert view.value("Angle θz appliqué") == "-5.3 °"
    assert view.value("Convention de rotation") == "extrinsic · ZYX · sources_to_sensor"
    assert view.value("Origine des angles") == "calibrated"
    assert view.value("Calibration appliquée") == "cal-2026-11-13"
    assert view.value("Version du schéma") == "1.4"
    assert view.value("Angles utilisés au traitement") == "ceux de l'acquisition"


def test_an_acquisition_whose_file_says_nothing_shows_not_said_and_the_ideal_angles_fallback():
    presenter, view = _presenter()

    presenter.show(_status(measured_object=None, schema_version=None, applied_rotation=None))

    assert view.value("Objet mesuré") == "non renseigné"
    assert view.value("Version du schéma") == "non renseigné"
    assert view.value("Angles appliqués") == "non renseignés"
    assert view.value("Angles utilisés au traitement") == "angles idéaux du gabarit"
    assert "Angle θx appliqué" not in dict(view.rows)


def test_a_rotation_the_application_refuses_shows_why_and_the_fallback():
    presenter, view = _presenter()

    presenter.show(_status(applied_rotation=None, rotation_problem="convention de rotation non prise en charge (intrinsic, ZYX, sources_to_sensor)"))

    assert "intrinsic" in view.value("Rotation inutilisable")
    assert view.value("Angles utilisés au traitement") == "angles idéaux du gabarit (repli)"


def test_a_missing_origin_or_calibration_is_not_shown_as_a_row():
    presenter, view = _presenter()

    presenter.show(_status(applied_rotation=AppliedRotationDTO((1.0, 2.0, 3.0), "extrinsic", "ZYX", "sources_to_sensor")))

    assert "Origine des angles" not in dict(view.rows) and "Calibration appliquée" not in dict(view.rows)


def test_without_selection_the_panel_says_so():
    presenter, view = _presenter()
    presenter.show(_status())

    presenter.clear()

    assert view.title == "Aucune acquisition sélectionnée" and view.rows == []


def test_showing_an_acquisition_writes_no_file(tmp_path):
    presenter, _view = _presenter()
    before = sorted(os.listdir(tmp_path))

    presenter.show(_status(folder=str(tmp_path)))

    assert sorted(os.listdir(tmp_path)) == before
