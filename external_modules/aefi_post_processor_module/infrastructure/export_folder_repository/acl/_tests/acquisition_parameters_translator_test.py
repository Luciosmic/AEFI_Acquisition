from datetime import datetime, timedelta, timezone

from ..acquisition_parameters_translator import NOT_A_SCAN, describe

LIFT_OFF_15 = {"value": 15.0, "unit": "mm", "alias": "lift_off"}


def _parameters(version="1.4", kind="step_scan", started_at="2026-11-12T20:57:00.050+01:00", feature=None):
    return {
        "schema": {"name": "aefi-acquisition-parameters", "version": version},
        "provenance": {"activity": {"kind": kind, "started_at": started_at}},
        "feature_of_interest": feature if feature is not None else {
            "present": True, "description": "cylindre_base_hexagonale_metallique",
            "distance_between_lowest_point_of_sphere_and_highest_point_of_object_under_test": LIFT_OFF_15,
        },
    }


def test_le_contrat_donne_date_objet_lift_off_et_version():
    description = describe(_parameters())
    assert description.kind == "stepScan"
    assert description.acquired_at == datetime(2026, 11, 12, 20, 57, 0, 50000, tzinfo=timezone(timedelta(hours=1)))
    assert description.measured_object == "cylindre_base_hexagonale_metallique"
    assert description.lift_off_mm == 15.0
    assert description.schema_version == "1.4"


def test_un_scan_au_vol_est_reconnu_par_son_activite():
    assert describe(_parameters(kind="fly_scan")).kind == "flyScan"


def test_avant_le_schema_1_4_un_step_scan_ne_dit_pas_s_il_etait_au_vol():
    assert describe(_parameters(version="1.2")).kind is None


def test_une_autre_activite_n_est_pas_un_scan():
    assert describe(_parameters(kind="time_series")).kind == NOT_A_SCAN
    assert describe(_parameters(kind="frequency_sweep")).kind == NOT_A_SCAN


def test_un_lift_off_absent_ou_dans_une_autre_unite_est_inconnu():
    assert describe(_parameters(feature={"present": True, "description": "hexagone_metallique_15mm"})).lift_off_mm is None
    other_unit = {"present": True, "description": "x", "d": {"value": 1.5, "unit": "cm", "alias": "lift_off"}}
    assert describe(_parameters(feature=other_unit)).lift_off_mm is None


def test_un_fichier_sans_ces_champs_ne_leve_pas_et_rend_des_inconnus():
    description = describe({})
    assert (description.kind, description.acquired_at, description.measured_object,
            description.lift_off_mm, description.schema_version) == (None, None, None, None, None)
    assert describe({"provenance": {"activity": {"started_at": "pas une date"}}, "feature_of_interest": None}).acquired_at is None
