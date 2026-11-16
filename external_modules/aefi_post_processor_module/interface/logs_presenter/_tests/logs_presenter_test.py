"""Le presenter des Logs avec une vue Fake : lignes colorées et ouverture du fichier journal."""

import logging

from ..logs_presenter import LogsPresenter


class _Signal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in self._slots:
            slot(*args)


class FakeLogsView:
    def __init__(self):
        self.open_log_requested = _Signal()
        self.location = None
        self.lines = []
        self.opened = []

    def set_location(self, text):
        self.location = text

    def append_line(self, text, color):
        self.lines.append((text, color))

    def open_file(self, path):
        self.opened.append(path)


def test_the_view_is_told_where_the_journal_file_is():
    view = FakeLogsView()

    LogsPresenter(view, "/logs/post_processor.log")

    assert "/logs/post_processor.log" in view.location


def test_each_message_becomes_a_line_coloured_by_its_severity():
    view = FakeLogsView()
    presenter = LogsPresenter(view, "/logs/post_processor.log")

    presenter.append_feedback(logging.INFO, "sync.started scans_found=2")
    presenter.append_feedback(logging.WARNING, "sync.finished failed=1")
    presenter.append_feedback(logging.ERROR, "pipeline.failed step=preprocess")

    texts = [text for text, _ in view.lines]
    colors = [color for _, color in view.lines]
    assert texts == ["INFO sync.started scans_found=2", "WARNING sync.finished failed=1", "ERROR pipeline.failed step=preprocess"]
    assert colors[2] != colors[1] != colors[0]


def test_asking_to_open_the_journal_opens_its_file_and_says_so_in_the_journal(caplog):
    view = FakeLogsView()
    LogsPresenter(view, "/logs/post_processor.log")

    with caplog.at_level(logging.INFO):
        view.open_log_requested.emit()

    assert view.opened == ["/logs/post_processor.log"]
    assert any(m.startswith("logs.open_requested file=/logs/post_processor.log") for m in [r.getMessage() for r in caplog.records])
