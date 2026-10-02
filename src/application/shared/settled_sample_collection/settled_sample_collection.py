"""
Settled Sample Collection

See settled_sample_collection_intention.md.
"""

import queue
import time
from datetime import datetime
from typing import List, Tuple

from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)


def collect_settled_samples(
    events: "queue.Queue", count: int, settled_at: datetime, timeout_s: float
) -> Tuple[List[AefiVoltageSampleAcquired], int]:
    """Up to `count` events whose acquisition started after `settled_at`
    (their predecessor ended after it), and the number rejected. Gives up
    after `timeout_s`, returning what was kept so far."""
    kept: List[AefiVoltageSampleAcquired] = []
    rejected = 0
    predecessor = None
    deadline = time.monotonic() + timeout_s
    while len(kept) < count:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            event = events.get(timeout=remaining)
        except queue.Empty:
            break
        if (
            predecessor is not None
            and event.acquisition_id == predecessor.acquisition_id
            and event.sample_index == predecessor.sample_index + 1
            and predecessor.sample.timestamp > settled_at
        ):
            kept.append(event)
        else:
            rejected += 1
        predecessor = event
    return kept, rejected
