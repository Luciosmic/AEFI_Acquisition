import dataclasses

import pytest

from domain.shared_kernel.events.acquisition_export_opened.acquisition_export_opened import AcquisitionExportOpened
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_l_export_ouvert_nomme_l_acquisition_et_son_objet() -> None:
    event = AcquisitionExportOpened(acquisition_kind="step_scan", acquisition_id="scan-1", measured_object="plaque")
    assert isinstance(event, DomainEvent)
    assert (event.acquisition_kind, event.acquisition_id, event.measured_object) == ("step_scan", "scan-1", "plaque")


def test_l_export_ouvert_sans_objet_mesure_a_un_objet_vide() -> None:
    assert AcquisitionExportOpened(acquisition_kind="time_series", acquisition_id="a-1").measured_object == ""


def test_l_export_ouvert_est_immuable() -> None:
    event = AcquisitionExportOpened(acquisition_kind="step_scan", acquisition_id="scan-1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.acquisition_id = "autre"  # type: ignore[misc]
