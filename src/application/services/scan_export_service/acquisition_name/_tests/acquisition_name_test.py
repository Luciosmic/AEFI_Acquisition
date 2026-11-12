from application.services.scan_export_service.acquisition_name.acquisition_name import acquisition_name


def test_measured_object_then_lift_off():
    assert acquisition_name("hexagone_metallique", 15.0) == "hexagone_metallique_liftoff-15mm"


def test_decimal_lift_off_keeps_its_point():
    assert acquisition_name("plaque", 2.5) == "plaque_liftoff-2.5mm"


def test_spaces_become_dashes_and_unsafe_characters_are_dropped():
    assert acquisition_name("  bouteille d'eau / 350 kΩ ", 8.0) == "bouteille-deau--350-kΩ_liftoff-8mm"


def test_values_not_entered_are_named_as_such():
    assert acquisition_name("", None) == "objet-non-saisi_liftoff-non-saisi"
    assert acquisition_name("   ", 0.0) == "objet-non-saisi_liftoff-0mm"
