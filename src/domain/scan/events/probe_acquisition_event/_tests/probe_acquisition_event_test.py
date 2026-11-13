from uuid import uuid4

from domain.scan.events.probe_acquisition_event.probe_acquisition_event import ProbeAcquisitionEvent


class _Event:
    scan_id = uuid4()
    source = "any"
    acquisition_id = uuid4()


def test_structural_conformance() -> None:
    assert isinstance(_Event(), ProbeAcquisitionEvent)
    assert not isinstance(object(), ProbeAcquisitionEvent)
