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


# -- la rotation appliquée (rotation_applied), contrat client-fournisseur --------------------------------------

STANDARD = {"type": "extrinsic", "order": "ZYX", "direction": "sources_to_sensor"}


def _deployment(**overrides):
    rotation = {
        "theta_x": {"value": 34.9, "unit": "deg"},
        "theta_y": {"value": 45.7, "unit": "deg"},
        "theta_z": {"value": -5.3, "unit": "deg"},
        "convention": dict(STANDARD),
        "origin": "calibrated",
        "calibration_id": "cal-2026-11-13",
        "applies_to_data": False,
        "notes": "",
    }
    rotation.update(overrides)
    return {"measurement_chain": {"sensor": {"deployment": {"id": "m1", "rotation_applied": rotation}}}}


def test_la_rotation_appliquee_donne_les_angles_la_convention_et_leur_origine():
    rotation = describe(_deployment()).applied_rotation

    assert rotation.angles == (34.9, 45.7, -5.3)
    assert (rotation.convention_type, rotation.convention_order, rotation.convention_direction) == (
        "extrinsic", "ZYX", "sources_to_sensor",
    )
    assert (rotation.origin, rotation.calibration_id) == ("calibrated", "cal-2026-11-13")
    assert describe(_deployment()).rotation_problem is None


def test_sans_montage_du_capteur_aucune_rotation_et_aucun_probleme():
    for parameters in ({}, {"measurement_chain": {"sensor": {"deployment": None}}}, _parameters()):
        description = describe(parameters)
        assert description.applied_rotation is None and description.rotation_problem is None


def test_une_convention_que_l_application_ne_sait_pas_appliquer_est_refusee():
    description = describe(_deployment(convention={"type": "intrinsic", "order": "ZYX", "direction": "sources_to_sensor"}))

    assert description.applied_rotation is None
    assert "convention" in description.rotation_problem and "intrinsic" in description.rotation_problem


def test_une_convention_absente_est_refusee():
    description = describe(_deployment(convention=None))

    assert description.applied_rotation is None and "convention" in description.rotation_problem


def test_des_valeurs_deja_tournees_ne_sont_pas_tournees_une_seconde_fois():
    description = describe(_deployment(applies_to_data=True))

    assert description.applied_rotation is None
    assert "déjà tournées" in description.rotation_problem


def test_un_angle_dans_une_autre_unite_que_le_degre_est_refuse():
    description = describe(_deployment(theta_y={"value": 0.8, "unit": "rad"}))

    assert description.applied_rotation is None
    assert "theta_y" in description.rotation_problem and "rad" in description.rotation_problem


def test_un_angle_absent_est_refuse_en_le_nommant():
    description = describe(_deployment(theta_z=None))

    assert description.applied_rotation is None and "theta_z" in description.rotation_problem


def test_une_rotation_mal_formee_ne_leve_pas():
    assert describe({"measurement_chain": {"sensor": {"deployment": {"rotation_applied": "?"}}}}).applied_rotation is None
    assert describe(_deployment(theta_x={"value": "x", "unit": "deg"})).applied_rotation is None


def test_le_contrat_se_lit_de_la_meme_facon_avant_et_apres_le_retrait_du_h5_de_data_files():
    """1.6 liste le `.h5` de l'acquisition dans data.files, 1.7 ne le liste plus : le catalogue ne lit pas cette entrée."""
    ancien = _parameters(version="1.6", kind="fly_scan")
    ancien["data"] = {"files": [{"name": "a_aefi.csv", "format": "CSV"}, {"name": "a.h5", "format": "HDF5"}]}
    nouveau = _parameters(version="1.7", kind="fly_scan")
    nouveau["data"] = {"files": [{"name": "a_aefi.csv", "format": "CSV"}]}

    ancienne_lecture, nouvelle_lecture = describe(ancien), describe(nouveau)

    assert (ancienne_lecture.kind, ancienne_lecture.measured_object, ancienne_lecture.lift_off_mm) == (
        nouvelle_lecture.kind, nouvelle_lecture.measured_object, nouvelle_lecture.lift_off_mm)
    assert (ancienne_lecture.schema_version, nouvelle_lecture.schema_version) == ("1.6", "1.7")
