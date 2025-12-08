#!/usr/bin/env python3
"""
Acquisition Manager pour LSM9D - Modes EXPLORATION/EXPORT, structure compatible projet principal
"""

import time
import threading
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import sys, os

# Import modules LSM9D
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "instrument"))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from LSM9D_SerialCommunication import LSM9D_SerialCommunicator

comp_dir = os.path.dirname(os.path.abspath(__file__))
if comp_dir not in sys.path:
    sys.path.insert(0, comp_dir)
from LSM9D_ModeController_Module import AcquisitionMode
from LSM9D_DataBuffer_Module import AdaptiveDataBuffer
from LSM9D_CSVexporter_Module import CSVExporter, ExportConfig

class AcquisitionStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class LSM9D_AcquisitionManager(QObject):
    """
    Manager d'acquisition pour LSM9D, modes EXPLORATION/EXPORT, structure compatible projet principal
    """
    data_ready = pyqtSignal(object)  # dict de données LSM9D
    status_changed = pyqtSignal(str, str)  # AcquisitionStatus, message
    error_occurred = pyqtSignal(str)
    configuration_changed = pyqtSignal(dict)

    def __init__(self, port="COM5", buffer_size=1000):
        super().__init__()
        self._serial_communicator = LSM9D_SerialCommunicator(port=port)
        self._serial_communicator.add_status_callback(self._on_controller_status)
        self._acquisition_thread = None
        self._status = AcquisitionStatus.STOPPED
        self._running = False
        self._paused = False
        self._stop_requested = False
        self._thread_lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._buffer = AdaptiveDataBuffer()
        self._current_mode = AcquisitionMode.EXPLORATION
        self._samples_acquired = 0
        self._last_acquisition_time = None
        self._csv_exporter = None

    def _on_controller_status(self, status, message):
        print(f"[DEBUG] Manager relay status: {status}, {message}")
        self.status_changed.emit(status, message)

    def start_acquisition(self, mode: AcquisitionMode = AcquisitionMode.EXPLORATION) -> bool:
        with self._thread_lock:
            if self._status == AcquisitionStatus.RUNNING:
                return False
            self._running = True
            self._paused = False
            self._stop_requested = False
            self._pause_event.set()
            self._samples_acquired = 0
            self._current_mode = mode
            self._buffer.set_mode(mode)
            self._acquisition_thread = threading.Thread(target=self._acquisition_worker)
            self._acquisition_thread.start()
            self._set_status(AcquisitionStatus.RUNNING)
            self.configuration_changed.emit({'mode': mode.value})
            return True

    def stop_acquisition(self) -> bool:
        with self._thread_lock:
            if self._status == AcquisitionStatus.STOPPED:
                return True
            self._stop_requested = True
            self._running = False
            self._pause_event.set()
            if self._acquisition_thread:
                self._acquisition_thread.join(timeout=5.0)
            self._set_status(AcquisitionStatus.STOPPED)
            return True

    def pause_acquisition(self) -> bool:
        with self._thread_lock:
            if self._status != AcquisitionStatus.RUNNING:
                return False
            self._paused = True
            self._pause_event.clear()
            self._set_status(AcquisitionStatus.PAUSED)
            return True

    def resume_acquisition(self) -> bool:
        with self._thread_lock:
            if self._status != AcquisitionStatus.PAUSED:
                return False
            self._paused = False
            self._pause_event.set()
            self._set_status(AcquisitionStatus.RUNNING)
            return True

    def clear_buffer(self):
        self._buffer.clear_buffer()

    def start_export_csv(self, export_config: dict) -> bool:
        if self._csv_exporter and self._csv_exporter.is_exporting:
            return False
        config = ExportConfig(
            output_dir=export_config.get('output_dir', '.'),
            filename_base=export_config.get('filename_base', 'LSM9D_export'),
            duration_seconds=export_config.get('duration_seconds', None),
            metadata=export_config.get('metadata', {})
        )
        self._csv_exporter = CSVExporter()
        self._buffer.set_mode(AcquisitionMode.EXPORT)
        self._csv_exporter.start_export(config)
        # Callback pour flush du buffer vers l'export
        self._buffer.add_production_callback(self._csv_exporter.add_samples)
        self._current_mode = AcquisitionMode.EXPORT
        self._set_status(AcquisitionStatus.RUNNING)
        self.configuration_changed.emit({'mode': 'export'})
        return True

    def stop_export_csv(self):
        if self._csv_exporter and self._csv_exporter.is_exporting:
            self._csv_exporter.stop_export()
            self._buffer.set_mode(AcquisitionMode.EXPLORATION)
            self._current_mode = AcquisitionMode.EXPLORATION
            self._set_status(AcquisitionStatus.RUNNING)
            self.configuration_changed.emit({'mode': 'exploration'})
            return True
        return False

    @property
    def is_exporting_csv(self):
        return self._csv_exporter is not None and self._csv_exporter.is_exporting

    def _acquisition_worker(self):
        try:
            self._serial_communicator.connect()
            self._serial_communicator.initialize_sensor_mode('ALL_SENSORS')
            self._serial_communicator.start_streaming()
            while self._running and not self._stop_requested:
                self._pause_event.wait()
                if not self._running or self._stop_requested:
                    break
                data = self._serial_communicator.get_current_data()
                # On crée un dict compatible avec le buffer (timestamp inclus)
                data['timestamp'] = datetime.now()
                self._buffer.append_sample(data)
                self._samples_acquired += 1
                self._last_acquisition_time = data['timestamp']
                self.data_ready.emit(data)
                time.sleep(0.01)  # 100 Hz max, ajustable
            self._serial_communicator.stop_streaming()
            self._serial_communicator.disconnect()
        except Exception as e:
            self.error_occurred.emit(str(e))
            self._set_status(AcquisitionStatus.ERROR)

    def get_latest_data(self, count=1):
        return self._buffer.get_latest_samples(count)

    def get_buffer_status(self) -> Dict[str, Any]:
        return self._buffer.get_buffer_status()

    def get_acquisition_stats(self) -> Dict[str, Any]:
        return {
            'status': self._status.value,
            'mode': self._current_mode.value,
            'samples_acquired': self._samples_acquired,
            'last_acquisition': self._last_acquisition_time.isoformat() if self._last_acquisition_time else None,
            'buffer_status': self.get_buffer_status()
        }

    def _set_status(self, status: AcquisitionStatus):
        self._status = status
        self.status_changed.emit(status.value, "") # Assuming message is empty for now

    @property
    def status(self) -> AcquisitionStatus:
        return self._status

    @property
    def samples_acquired(self) -> int:
        return self._samples_acquired

    @property
    def is_connected(self):
        return getattr(self._serial_communicator, "is_connected", False)

    def close(self):
        self.stop_acquisition()
        if self._serial_communicator:
            try:
                self._serial_communicator.disconnect()
            except Exception as e:
                print(f"Warning: Erreur lors de la fermeture SerialCommunicator: {e}")
            finally:
                self._serial_communicator = None 

    def add_data_callback(self, callback):
        self.data_ready.connect(callback)

    def add_status_callback(self, callback):
        self.status_changed.connect(callback) 

    def connect(self):
        print("[DEBUG] manager.connect() appelé")
        return self._serial_communicator.connect()

    def disconnect(self):
        return self._serial_communicator.disconnect()

    def initialize_sensor_mode(self, mode):
        return self._serial_communicator.initialize_sensor_mode(mode)

    def start_streaming(self):
        return self._serial_communicator.start_streaming()

    def stop_streaming(self):
        return self._serial_communicator.stop_streaming()

    def clear_data(self):
        return self._serial_communicator.clear_data()

    def get_current_data(self):
        return self._serial_communicator.get_current_data()

    def get_status(self):
        return self._serial_communicator.get_status()

    @property
    def is_streaming(self):
        return getattr(self._serial_communicator, "is_streaming", False) 