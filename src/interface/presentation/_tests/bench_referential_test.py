from interface.presentation.bench_referential import BenchReferential


def test_limit_switch_leaves_coordinates_untouched():
    referential = BenchReferential("limit_switch", 1200.0, 1160.0)

    assert (referential.to_raw_x(600.0), referential.to_display_y(300.0)) == (600.0, 300.0)


def test_centered_puts_zero_at_the_middle_of_each_axis():
    referential = BenchReferential("centered", 1200.0, 1160.0)

    assert (referential.to_raw_x(0.0), referential.to_raw_y(0.0)) == (600.0, 580.0)
    assert (referential.to_display_x(600.0), referential.to_display_y(1160.0)) == (0.0, 580.0)


def test_raw_and_display_round_trip():
    referential = BenchReferential("centered", 1200.7, 1161.8)

    assert abs(referential.to_display_x(referential.to_raw_x(-123.4)) + 123.4) < 1e-9


def test_the_middle_follows_the_travel_in_mm():
    centered = BenchReferential("centered", 1200.0, 1200.0)

    assert centered.with_limits(1250.0, 1200.0).to_raw_x(0.0) == 625.0


def test_an_unknown_mode_falls_back_to_the_limit_switches():
    assert not BenchReferential().with_mode("spiral").is_centered
