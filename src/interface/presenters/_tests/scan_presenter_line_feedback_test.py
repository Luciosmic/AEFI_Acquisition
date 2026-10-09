"""ScanPresenter relays the fly line preview and abandonment as simple Qt signals / status messages."""
from interface.presenters._tests.scan_presenter_line_request_test import _presenter


def test_line_abandoned_is_shown_as_a_status_message_and_a_signal():
    presenter, _ = _presenter()
    messages, signals = [], []
    presenter.status_updated.connect(messages.append)
    presenter.scan_line_abandoned.connect(lambda i, r: signals.append((i, r)))

    presenter.present_scan_line_abandoned(1, "paused")

    assert signals == [(1, "paused")]
    assert len(messages) == 1 and "Line 2" in messages[0] and "paused" in messages[0]


def test_line_preview_is_forwarded_as_a_signal():
    presenter, _ = _presenter()
    seen = []
    presenter.scan_line_preview.connect(lambda i, k, d: seen.append((i, k, d)))

    presenter.present_scan_line_preview(0, 2, {"x": 1.0, "y": 2.0, "value": {}})

    assert seen == [(0, 2, {"x": 1.0, "y": 2.0, "value": {}})]
