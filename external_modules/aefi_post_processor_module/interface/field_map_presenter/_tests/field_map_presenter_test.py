"""Le presenter de la Carte avec une vue Fake, le vrai service de carte et un lecteur d'étapes Fake."""

import logging
from types import SimpleNamespace

import numpy as np

from ....application.field_map_service.field_map_service import FieldMapService
from ....infrastructure.hdf5_step_reader.fake.fake_hdf5_step_reader import FakeHdf5StepReader
from ..field_map_presenter import FieldMapPresenter

ACQUISITION_FILE = "/export/20261112_stepScan_a/20261112_stepScan_a.h5"
CHANNELS = ["voltage_x_in_phase", "voltage_x_quadrature", "voltage_y_in_phase", "voltage_y_quadrature",
            "voltage_z_in_phase", "voltage_z_quadrature"]


class _Signal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in self._slots:
            slot(*args)


class FakeFieldMapView:
    def __init__(self):
        self.step_selected = _Signal()
        self.cursor_moved = _Signal()
        self.steps = []
        self.selected = []
        self.cleared = 0
        self.figures = []
        self.frame_info = None
        self.cursor_text = None

    def set_steps(self, steps):
        self.steps = steps

    def select_step(self, display_name):
        self.selected.append(display_name)

    def clear_map(self):
        self.cleared += 1

    def show_figure(self, figure):
        self.figures.append(figure)

    def set_frame_info(self, rotation, reference_point):
        self.frame_info = (rotation, reference_point)

    def set_cursor_text(self, text):
        self.cursor_text = text


class FakeFigureFactory:
    def __init__(self):
        self.calls = []

    def create_figure(self, grids, extent, metadata, context_title):
        self.calls.append((dict(grids), list(extent), dict(metadata), context_title))
        return f"figure of {context_title}"


def _data(value):
    return np.full((4, 4, 6), float(value))


def _metadata(**extra):
    return {"channel_names": str(CHANNELS).replace("'", '"'), "extent": "[0.0, 30.0, 0.0, 20.0]", **extra}


def _parts(steps=("preprocessed", "phase_calibrated", "rotated_frame")):
    reader = FakeHdf5StepReader()
    for i, step in enumerate(steps):
        reader.add_step(ACQUISITION_FILE, step, _data(i), _metadata(rotation_angles=[1.0, 2.0, 3.0], reference_point="[0, 0]"))
    view, factory = FakeFieldMapView(), FakeFigureFactory()
    presenter = FieldMapPresenter(view, FieldMapService(reader), factory)
    return presenter, view, factory, reader


def test_choosing_an_acquisition_lists_its_steps_in_processing_order_and_draws_nothing():
    presenter, view, factory, _ = _parts(steps=("rotated_frame", "preprocessed", "phase_calibrated"))

    presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)

    assert view.steps == ["1 - preprocessed", "2 - phase_calibrated", "3 - rotated_frame"]
    assert view.figures == [] and factory.calls == []


def test_choosing_a_step_draws_the_map_of_that_step_with_its_extent_and_rotation():
    presenter, view, factory, _ = _parts()
    presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)

    view.step_selected.emit("3 - rotated_frame")

    grids, extent, _metadata_, title = factory.calls[0]
    assert title == "20261112_stepScan_a : rotated_frame" and extent == [0.0, 30.0, 0.0, 20.0]
    assert list(grids) == CHANNELS and np.all(grids["voltage_x_in_phase"] == 2.0)
    assert view.figures == ["figure of 20261112_stepScan_a : rotated_frame"]
    assert view.frame_info == ("[1.00, 2.00, 3.00]", "[0, 0]")


def test_a_step_read_twice_comes_from_memory_until_the_acquisition_is_refreshed():
    presenter, view, factory, reader = _parts()
    presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)
    view.step_selected.emit("1 - preprocessed")
    reader.add_step(ACQUISITION_FILE, "preprocessed", _data(99), _metadata())

    view.step_selected.emit("1 - preprocessed")
    assert np.all(factory.calls[1][0]["voltage_x_in_phase"] == 0.0)

    presenter.refresh()
    assert np.all(factory.calls[2][0]["voltage_x_in_phase"] == 99.0)
    assert view.selected == ["1 - preprocessed"]


def test_refreshing_lists_the_steps_a_processing_just_stored():
    presenter, view, _, reader = _parts(steps=())
    presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)
    assert view.steps == []

    for step in ("preprocessed", "phase_calibrated"):
        reader.add_step(ACQUISITION_FILE, step, _data(1), _metadata())
    presenter.refresh()

    assert view.steps == ["1 - preprocessed", "2 - phase_calibrated"]


def test_an_acquisition_without_steps_says_so_in_the_journal(caplog):
    presenter, view, _, _ = _parts(steps=())

    with caplog.at_level(logging.WARNING):
        presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)

    assert any(r.getMessage() == "scan.no_steps scan=20261112_stepScan_a" for r in caplog.records)


def test_a_step_that_cannot_be_read_is_logged_and_leaves_the_previous_map(caplog):
    presenter, view, _, _ = _parts()
    presenter.show_acquisition("20261112_stepScan_a", ACQUISITION_FILE)
    view.step_selected.emit("1 - preprocessed")

    with caplog.at_level(logging.ERROR):
        view.step_selected.emit("9 - never_stored")

    assert len(view.figures) == 1
    assert any(r.getMessage().startswith("step.load_failed scan=20261112_stepScan_a step=9 - never_stored") for r in caplog.records)


def test_the_value_under_the_mouse_is_written_with_its_position():
    presenter, view, _, _ = _parts()
    image = SimpleNamespace(get_cursor_data=lambda event: 3.14159)

    view.cursor_moved.emit(SimpleNamespace(inaxes=SimpleNamespace(images=[image]), xdata=1.26, ydata=2.0))
    assert view.cursor_text == "Cursor: x=1.3, y=2.0 | z=3.142"

    view.cursor_moved.emit(SimpleNamespace(inaxes=None, xdata=None, ydata=None))
    assert view.cursor_text == "Cursor: Out of axes"

    nan_image = SimpleNamespace(get_cursor_data=lambda event: float("nan"))
    view.cursor_moved.emit(SimpleNamespace(inaxes=SimpleNamespace(images=[nan_image]), xdata=0.0, ydata=0.0))
    assert view.cursor_text.endswith("z=NaN")
