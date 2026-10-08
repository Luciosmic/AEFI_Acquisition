import queue
import unittest
from datetime import datetime, timedelta
from uuid import uuid4

from application.shared.settled_sample_collection.settled_sample_collection import collect_settled_samples
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

T0 = datetime(2026, 10, 2, 12, 0, 0)


def sample_event(acquisition_id, index, ended_at_ms):
    measurement = AefiVoltageMeasurement(
        voltage_x_in_phase=float(index), voltage_x_quadrature=0.0,
        voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
        voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
        timestamp=T0 + timedelta(milliseconds=ended_at_ms),
    )
    return AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=index, sample=measurement)


def queue_of(events):
    q = queue.Queue()
    for event in events:
        q.put(event)
    return q


class TestCollectSettledSamples(unittest.TestCase):
    def test_keeps_only_samples_started_after_settling(self):
        """Samples end every 10 ms; settled at 25 ms: sample ending at 30 ms
        started at 20 ms (before) — the first clean one ends at 40 ms."""
        acquisition = uuid4()
        events = [sample_event(acquisition, i, 10 * i) for i in range(10)]

        kept, rejected = collect_settled_samples(
            queue_of(events), count=3, settled_at=T0 + timedelta(milliseconds=25), timeout_s=1.0
        )

        self.assertEqual([e.sample_index for e in kept], [4, 5, 6])
        self.assertEqual(rejected, 4)

    def test_first_event_is_rejected_without_a_known_predecessor(self):
        acquisition = uuid4()
        events = [sample_event(acquisition, i, 10 * i) for i in range(5, 8)]

        kept, rejected = collect_settled_samples(queue_of(events), count=5, settled_at=T0, timeout_s=0.05)

        self.assertEqual([e.sample_index for e in kept], [6, 7])
        self.assertEqual(rejected, 1)

    def test_a_restarted_stream_needs_a_new_predecessor(self):
        first, second = uuid4(), uuid4()
        events = [sample_event(first, 0, 10), sample_event(second, 0, 20), sample_event(second, 1, 30)]

        kept, _ = collect_settled_samples(queue_of(events), count=5, settled_at=T0, timeout_s=0.05)

        self.assertEqual([(e.acquisition_id, e.sample_index) for e in kept], [(second, 1)])

    def test_returns_a_short_collection_on_timeout(self):
        kept, rejected = collect_settled_samples(queue.Queue(), count=3, settled_at=T0, timeout_s=0.05)
        self.assertEqual((kept, rejected), ([], 0))


if __name__ == "__main__":
    unittest.main()
