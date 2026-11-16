import numpy as np

from ..figure_factory import FigureFactory

CHANNELS = [f"voltage_{c}_{p}" for c in "xyz" for p in ("in_phase", "quadrature")]


def test_a_full_step_gives_six_maps_with_their_titles():
    grids = {name: np.arange(16.0).reshape(4, 4) for name in CHANNELS}

    figure = FigureFactory().create_figure(grids, [0, 3, 0, 3], {}, "scan : preprocessed")

    titles = sorted(ax.get_title() for ax in figure.axes if ax.get_title())
    assert titles == ["X In-Phase", "X Quadrature", "Y In-Phase", "Y Quadrature", "Z In-Phase", "Z Quadrature"]
    assert figure.texts[0].get_text() == "scan : preprocessed"


def test_a_missing_channel_is_written_as_no_data():
    grids = {"voltage_x_in_phase": np.ones((3, 3))}

    figure = FigureFactory().create_figure(grids, [0, 2, 0, 2], {}, "partial")

    no_data = [t for ax in figure.axes for t in ax.texts if t.get_text() == "No Data"]
    assert len(no_data) == 5
