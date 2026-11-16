import dataclasses

import pytest

from domain.shared_kernel.events.acquisition_export_closed.acquisition_export_closed import AcquisitionExportClosed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_l_export_ferme_nomme_l_acquisition_qu_il_ferme() -> None:
    event = AcquisitionExportClosed(acquisition_kind="frequency_sweep", acquisition_id="sweep-1")
    assert isinstance(event, DomainEvent)
    assert (event.acquisition_kind, event.acquisition_id) == ("frequency_sweep", "sweep-1")


def test_l_export_ferme_est_immuable() -> None:
    event = AcquisitionExportClosed(acquisition_kind="frequency_sweep", acquisition_id="sweep-1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.acquisition_id = "autre"  # type: ignore[misc]
