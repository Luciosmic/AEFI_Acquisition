"""
Dashboard Wiring

Responsibility:
- Connect Qt signals/slots between the Dashboard's panels (views) and the
  application's presenters. Pure plumbing, no business logic.

Rationale:
- Dashboard itself stays a generic view shell (panels + taskbar) with no
  knowledge of concrete presenters — this module is what couples the two,
  so main.py doesn't have to carry ~190 lines of .connect(...) calls inline.
"""

import logging

from interface.shell.dashboard import Dashboard
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.excitation_presenter import ExcitationPresenter
from interface.presenters.synchronous_detection_presenter import SynchronousDetectionPresenter
from interface.presenters.aefi_continuous_reading_presenter import AefiContinuousReadingPresenter
from interface.presenters.electric_field_probe_presenter import ElectricFieldProbePresenter
from interface.presenters.scan_presenter import ScanPresenter
from interface.presenters.hardware_advanced_config_presenter import HardwareAdvancedConfigPresenter

logger = logging.getLogger(__name__)


def wire_dashboard(
    dashboard: Dashboard,
    motion_presenter: MotionPresenter,
    excitation_presenter: ExcitationPresenter,
    synchronous_detection_presenter: SynchronousDetectionPresenter,
    aefi_continuous_reading_presenter: AefiContinuousReadingPresenter,
    electric_field_probe_presenter: ElectricFieldProbePresenter,
    scan_presenter: ScanPresenter,
    hardware_config_presenter: HardwareAdvancedConfigPresenter,
) -> None:
    """Connect every dashboard panel to its presenter. Called once from
    main.py right after the dashboard and presenters are constructed."""
    print("--- Wiring Presenters to Panels ---")

    # Motion Panel
    motion_panel = dashboard.panels["motion"]
    motion_panel.jog_requested.connect(motion_presenter.on_jog_requested)
    motion_panel.move_to_requested.connect(motion_presenter.on_move_to_requested)
    motion_panel.move_both_requested.connect(motion_presenter.on_move_both_requested)
    motion_panel.move_to_center_requested.connect(motion_presenter.on_move_to_center_requested)
    motion_panel.home_requested.connect(motion_presenter.on_home_requested)
    motion_panel.stop_requested.connect(motion_presenter.on_stop_requested)
    motion_panel.estop_requested.connect(motion_presenter.on_estop_requested)
    motion_panel.speed_mode_changed.connect(motion_presenter.on_speed_mode_requested)

    motion_presenter.position_updated.connect(motion_panel.update_position)
    motion_presenter.status_updated.connect(motion_panel.update_status)
    motion_presenter.jog_enabled_changed.connect(motion_panel.set_jog_enabled)
    motion_presenter.limits_updated.connect(motion_panel.set_axis_limits)

    # Settings Panel -> Motion Panel (referential mode: limit-switch raw vs. centered/4-quadrants)
    settings_panel = dashboard.panels["settings"]
    settings_panel.motion_referential_changed.connect(motion_panel.set_referential_mode)

    # Initialize presenter to fetch limits
    motion_presenter.initialize()
    logger.debug("Motion panel wired")

    # Excitation Panel
    excitation_panel = dashboard.panels["excitation"]
    logger.debug("Connecting signal: excitation_panel.excitation_changed -> excitation_presenter.on_excitation_changed")
    excitation_panel.excitation_changed.connect(excitation_presenter.on_excitation_changed)
    excitation_presenter.excitation_updated.connect(excitation_panel.set_state)
    excitation_panel.link_toggled.connect(excitation_presenter.on_link_toggled)
    excitation_presenter.link_state_changed.connect(excitation_panel.set_link_state)
    excitation_presenter.refresh_state()
    synchronous_detection_presenter.sphere_phases_updated.connect(excitation_panel.set_synchronous_detection_state)
    excitation_panel.lock_in_detection_toggled.connect(synchronous_detection_presenter.on_lock_in_detection_toggled)
    excitation_panel.compensation_toggle_requested.connect(synchronous_detection_presenter.on_compensation_toggle_requested)
    synchronous_detection_presenter.compensation_state_changed.connect(excitation_panel.set_compensation_state)
    excitation_panel.lock_in_phase_offset_changed.connect(synchronous_detection_presenter.on_lock_in_phase_offset_changed)
    excitation_panel.lock_in_phase_offset_reset_requested.connect(synchronous_detection_presenter.on_lock_in_phase_offset_reset_requested)
    # NOTE: synchronous_detection_presenter.refresh_state() is deliberately
    # NOT called here — compensation_state_changed isn't wired to
    # hardware_config_panel yet at this point (that happens further below,
    # in the Hardware Advanced Config Panel wiring block). Calling it here
    # would emit the real persisted compensation state to no listener, and
    # the panel's toggle button would keep Qt's default (unchecked) instead
    # of the actual persisted state. See the single refresh_state() call
    # after ALL synchronous-detection wiring is complete, below.
    logger.debug("Excitation panel wired")

    # Continuous Acquisition Panel
    aefi_continuous_reading_panel = dashboard.panels["aefi_continuous_reading"]
    aefi_continuous_reading_panel.acquisition_start_requested.connect(aefi_continuous_reading_presenter.on_acquisition_start_requested)
    aefi_continuous_reading_panel.acquisition_stop_requested.connect(aefi_continuous_reading_presenter.on_acquisition_stop_requested)

    # Calibration & Transformation Wiring
    aefi_continuous_reading_panel.calibrate_noise_requested.connect(aefi_continuous_reading_presenter.calibrate_noise)
    aefi_continuous_reading_panel.calibrate_phase_requested.connect(aefi_continuous_reading_presenter.calibrate_phase)
    aefi_continuous_reading_panel.calibrate_primary_requested.connect(aefi_continuous_reading_presenter.calibrate_primary)
    aefi_continuous_reading_panel.reset_calibration_requested.connect(aefi_continuous_reading_presenter.reset_calibration)

    # Correction toggles (panel -> presenter)
    aefi_continuous_reading_panel.noise_toggled.connect(aefi_continuous_reading_presenter.on_noise_toggled)
    aefi_continuous_reading_panel.phase_toggled.connect(aefi_continuous_reading_presenter.on_phase_toggled)
    aefi_continuous_reading_panel.primary_toggled.connect(aefi_continuous_reading_presenter.on_primary_toggled)

    # Correction state feedback (presenter -> panel)
    aefi_continuous_reading_presenter.correction_states_updated.connect(aefi_continuous_reading_panel.update_correction_states)

    aefi_continuous_reading_panel.apply_rotation_toggled.connect(aefi_continuous_reading_presenter.on_rotation_toggled)

    aefi_continuous_reading_presenter.acquisition_started.connect(aefi_continuous_reading_panel.on_acquisition_started)
    aefi_continuous_reading_presenter.acquisition_stopped.connect(aefi_continuous_reading_panel.on_acquisition_stopped)
    aefi_continuous_reading_presenter.sample_acquired.connect(aefi_continuous_reading_panel.on_sample_acquired)
    aefi_continuous_reading_presenter.angles_updated.connect(aefi_continuous_reading_panel.update_angles_display)
    logger.debug("Continuous acquisition panel wired")

    # Electric Field Probe Panel
    electric_field_probe_panel = dashboard.panels["electric_field_probe"]
    electric_field_probe_panel.connect_requested.connect(electric_field_probe_presenter.on_connect_requested)
    electric_field_probe_panel.disconnect_requested.connect(electric_field_probe_presenter.on_disconnect_requested)
    electric_field_probe_panel.refresh_battery_requested.connect(electric_field_probe_presenter.on_refresh_battery_requested)
    electric_field_probe_panel.acquisition_start_requested.connect(electric_field_probe_presenter.on_acquisition_start_requested)
    electric_field_probe_panel.acquisition_stop_requested.connect(electric_field_probe_presenter.on_acquisition_stop_requested)
    electric_field_probe_panel.calibrate_noise_requested.connect(electric_field_probe_presenter.calibrate_noise)
    electric_field_probe_panel.reset_calibration_requested.connect(electric_field_probe_presenter.reset_calibration)
    electric_field_probe_panel.noise_toggled.connect(electric_field_probe_presenter.on_noise_toggled)

    electric_field_probe_presenter.probe_connection_changed.connect(electric_field_probe_panel.on_probe_connection_changed)
    electric_field_probe_presenter.probe_axes_defined.connect(electric_field_probe_panel.on_probe_axes_defined)
    electric_field_probe_presenter.acquisition_started.connect(electric_field_probe_panel.on_acquisition_started)
    electric_field_probe_presenter.acquisition_stopped.connect(electric_field_probe_panel.on_acquisition_stopped)
    electric_field_probe_presenter.sample_acquired.connect(electric_field_probe_panel.on_sample_acquired)
    electric_field_probe_presenter.noise_state_updated.connect(electric_field_probe_panel.update_correction_states)
    electric_field_probe_presenter.frequency_correction_changed.connect(electric_field_probe_panel.on_frequency_correction_changed)
    logger.debug("Electric field probe panel wired")

    # Scan Panels Wiring
    scan_control_panel = dashboard.panels["scan_control"]
    aefi_voltage_map_panel = dashboard.panels["aefi_voltage_map"]
    electric_field_map_panel = dashboard.panels["electric_field_map"]

    # Control -> Presenter
    scan_control_panel.scan_start_requested.connect(scan_presenter.on_scan_start_requested)
    scan_control_panel.scan_stop_requested.connect(scan_presenter.on_scan_stop_requested)
    scan_control_panel.scan_pause_requested.connect(scan_presenter.on_scan_pause_requested)
    scan_control_panel.scan_resume_requested.connect(scan_presenter.on_scan_resume_requested)

    # Presenter -> Control
    scan_presenter.status_updated.connect(scan_control_panel.update_status)
    scan_presenter.scan_started.connect(lambda scan_id, _: scan_control_panel.on_scan_started(scan_id))
    scan_presenter.scan_completed.connect(scan_control_panel.on_scan_completed)
    scan_presenter.scan_failed.connect(scan_control_panel.on_scan_failed)
    scan_presenter.scan_cancelled.connect(scan_control_panel.on_scan_cancelled)
    scan_presenter.scan_paused.connect(scan_control_panel.on_scan_paused)
    scan_presenter.scan_resumed.connect(scan_control_panel.on_scan_resumed)

    # Presenter -> Visualization
    def on_scan_started_viz(scan_id, config):
        aefi_voltage_map_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"]
        )
        # Channel set depends on the connected probe (mono/bi/tri-axial),
        # so it's left empty here and populated lazily from the first point.
        electric_field_map_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"],
            channels=[]
        )

    def on_scan_progress_viz(current, total, data):
        # data has 'x', 'y', 'value'
        aefi_voltage_map_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    def on_field_scan_progress_viz(current, total, data):
        electric_field_map_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    scan_presenter.scan_started.connect(on_scan_started_viz)
    scan_presenter.scan_progress.connect(on_scan_progress_viz)
    scan_presenter.field_scan_progress.connect(on_field_scan_progress_viz)
    logger.debug("Scan panels wired")

    # Hardware Advanced Config Panel Wiring
    hardware_config_panel = dashboard.panels["hardware_config"]

    # Presenter -> Panel
    hardware_config_presenter.hardware_list_updated.connect(hardware_config_panel.set_hardware_list)
    hardware_config_presenter.specs_loaded.connect(hardware_config_panel.set_parameter_specs)
    hardware_config_presenter.status_message.connect(hardware_config_panel.set_status_message)
    hardware_config_presenter.config_applied.connect(lambda hw_id: hardware_config_panel.set_status_message(f"Configuration applied to {hw_id}"))

    # Panel -> Presenter
    hardware_config_panel.hardware_selected.connect(hardware_config_presenter.select_hardware)
    hardware_config_panel.apply_requested.connect(hardware_config_presenter.apply_configuration)
    hardware_config_panel.save_default_requested.connect(hardware_config_presenter.save_configuration_as_default)
    hardware_config_panel.reset_default_requested.connect(hardware_config_presenter.reset_configuration_to_default)

    # Synchronous Detection (calibration point + compensation toggle) — Panel -> Presenter
    hardware_config_panel.save_calibration_point_requested.connect(
        synchronous_detection_presenter.on_save_calibration_point_requested
    )
    hardware_config_panel.compensation_toggle_requested.connect(
        synchronous_detection_presenter.on_compensation_toggle_requested
    )
    # Synchronous Detection — Presenter -> Panel
    synchronous_detection_presenter.compensation_state_changed.connect(
        hardware_config_panel.set_compensation_enabled_state
    )
    synchronous_detection_presenter.status_message.connect(hardware_config_panel.set_status_message)

    # All synchronous-detection wiring (both panels, both directions) is now
    # complete — safe to push the real persisted state (sphere phases +
    # compensation-enabled) to both panels for the first time.
    synchronous_detection_presenter.refresh_state()

    # Initialize: refresh hardware list on startup
    hardware_config_presenter.refresh_hardware_list()

    logger.debug("Hardware config panel wired")

    logger.debug("Transformation panel wired (via constructor)")
