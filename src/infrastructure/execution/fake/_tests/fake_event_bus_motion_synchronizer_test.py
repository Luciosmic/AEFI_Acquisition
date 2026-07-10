"""
Tests for FakeEventBusMotionSynchronizer.

One test per MotionSyncError variant (gate D of pre-pr-quality-check):
  - Success
  - MotionTimeout
  - MotionHardwareFailed
  - EmergencyStop
  - MotionStoppedExternally
"""

import unittest

from application.services.scan_application_service.errors.motion_sync_error import (
    EmergencyStop,
    MotionHardwareFailed,
    MotionStoppedExternally,
    MotionTimeout,
)
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.execution.fake.fake_event_bus_motion_synchronizer import (
    FakeEventBusMotionSynchronizer,
)


class TestFakeEventBusMotionSynchronizer(unittest.TestCase):
    # ------------------------------------------------------------------ #
    # Contract: success path
    # ------------------------------------------------------------------ #

    def test_returns_ok_when_programmed_with_success(self) -> None:
        sync = FakeEventBusMotionSynchronizer([OperationResult.ok(None)])
        result = sync.wait_for_motion("id-1", timeout_seconds=5.0)
        self.assertTrue(result.is_success)

    # ------------------------------------------------------------------ #
    # Contract: each MotionSyncError variant
    # ------------------------------------------------------------------ #

    def test_returns_motion_timeout_error(self) -> None:
        error = MotionTimeout(motion_id="id-1", timeout_seconds=30.0)
        sync = FakeEventBusMotionSynchronizer([OperationResult.fail(error)])
        result = sync.wait_for_motion("id-1", timeout_seconds=30.0)
        self.assertTrue(result.is_failure)
        self.assertIsInstance(result.error, MotionTimeout)
        self.assertEqual(result.error.motion_id, "id-1")

    def test_returns_motion_hardware_failed_error(self) -> None:
        error = MotionHardwareFailed(motion_id="id-2", error_detail="axis fault")
        sync = FakeEventBusMotionSynchronizer([OperationResult.fail(error)])
        result = sync.wait_for_motion("id-2", timeout_seconds=5.0)
        self.assertTrue(result.is_failure)
        self.assertIsInstance(result.error, MotionHardwareFailed)
        self.assertEqual(result.error.error_detail, "axis fault")

    def test_returns_emergency_stop_error(self) -> None:
        error = EmergencyStop()
        sync = FakeEventBusMotionSynchronizer([OperationResult.fail(error)])
        result = sync.wait_for_motion("id-3", timeout_seconds=5.0)
        self.assertTrue(result.is_failure)
        self.assertIsInstance(result.error, EmergencyStop)

    def test_returns_motion_stopped_externally_error(self) -> None:
        error = MotionStoppedExternally(motion_id="id-4", reason="scan_cancelled")
        sync = FakeEventBusMotionSynchronizer([OperationResult.fail(error)])
        result = sync.wait_for_motion("id-4", timeout_seconds=5.0)
        self.assertTrue(result.is_failure)
        self.assertIsInstance(result.error, MotionStoppedExternally)
        self.assertEqual(result.error.reason, "scan_cancelled")

    # ------------------------------------------------------------------ #
    # Contract: call tracking
    # ------------------------------------------------------------------ #

    def test_call_count_increments_per_call(self) -> None:
        sync = FakeEventBusMotionSynchronizer(
            [OperationResult.ok(None), OperationResult.ok(None)]
        )
        sync.wait_for_motion("a", 1.0)
        sync.wait_for_motion("b", 1.0)
        self.assertEqual(sync.call_count, 2)

    def test_received_motion_ids_records_all_calls(self) -> None:
        sync = FakeEventBusMotionSynchronizer(
            [OperationResult.ok(None), OperationResult.ok(None)]
        )
        sync.wait_for_motion("first", 1.0)
        sync.wait_for_motion("second", 1.0)
        self.assertEqual(sync.received_motion_ids, ["first", "second"])

    def test_raises_index_error_when_results_exhausted(self) -> None:
        sync = FakeEventBusMotionSynchronizer([OperationResult.ok(None)])
        sync.wait_for_motion("x", 1.0)
        with self.assertRaises(IndexError):
            sync.wait_for_motion("y", 1.0)

    def test_mixed_sequence_success_then_failure(self) -> None:
        sync = FakeEventBusMotionSynchronizer(
            [
                OperationResult.ok(None),
                OperationResult.fail(MotionTimeout(motion_id="id-2", timeout_seconds=5.0)),
            ]
        )
        r1 = sync.wait_for_motion("id-1", 5.0)
        r2 = sync.wait_for_motion("id-2", 5.0)
        self.assertTrue(r1.is_success)
        self.assertTrue(r2.is_failure)
        self.assertIsInstance(r2.error, MotionTimeout)


if __name__ == "__main__":
    unittest.main()
