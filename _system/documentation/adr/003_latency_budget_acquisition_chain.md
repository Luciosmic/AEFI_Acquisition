# ADR-003: Latency Budget of the Acquisition Chain

## Status
Accepted

## Context
The question investigated: **which stage of the acquisition chain dominates the timing uncertainty of a measurement?** The chain runs from the Python interpreter, through the dsPIC33FJ128GP microcontroller, over the USB-serial link, to the ADS131A04 ADC (known OSR). Without knowing which stage dominates, effort could be spent optimizing a stage that contributes negligibly, while the real bottleneck stays unaddressed.

## Decision

We establish the following latency budget for one acquisition sample, from measurement and bench data gathered 2026-10-02:

| Stage | Order of magnitude | Verdict |
|---|---|---|
| ADC (ADS131A04) — DRDY jitter | ~0.2 µs, measured on oscilloscope (see `fake_drdy_capture_port.py`) | Negligible |
| Serial transmission (1.5 Mbaud) | tens of µs | Negligible |
| USB-serial bridge (FTDI FT232R) — `LatencyTimer` driver delay | 7.6 ms at `LatencyTimer=1ms`, 23.6 ms at `LatencyTimer=16ms` | **Dominant** |
| Python `datetime.now()` timestamp, taken after the full round-trip | not isolated/quantified | Open — not yet measured in isolation |

Raw measurements are not duplicated here; see
[`ftdi_usb_latency_timer_reader_intention.md`](../../../src/infrastructure/hardware/serial_link/ftdi_usb_latency_timer_reader_intention.md)
and
[`i_usb_latency_timer_port_intention.md`](../../../src/application/shared/acquisition_parameters/i_usb_latency_timer_port_intention.md)
for the source of the T₀ figures above.

### Root cause: physical floor of the FT232R chip

The USB-serial bridge was identified as an **FT232R** via its USB PID, read
from the Windows hardware ID `FTDIBUS\COMPORT&VID_0403&PID_6001` (PID
`0403:6001`). The FT232R is a **USB Full-Speed only** chip — unlike the
Hi-Speed FT2232H/FT4232H/FT232H parts, it has no micro-frame support. USB
Full-Speed framing imposes a physical floor of 1 ms. Consequently,
`LatencyTimer=1ms` is already the minimum achievable value on this chip: it
is not a sub-optimal setting, it is a hardware limit of the component.

### Alternatives considered, not retained for now

These were discussed during the investigation and explicitly **not**
scheduled as work — listed here as alternatives considered, not as a plan:

- **(a) Amortize T₀ over more samples** by raising `n_avg` — reduces the
  effective point rate, does not reduce the per-point latency itself.
- **(b) Switch from a per-sample request/response protocol to a continuous
  MCU→PC stream** — requires a firmware protocol change plus an adapter
  change.
- **(c) Replace the FTDI chip with a Hi-Speed part (FT232H/FT2232H)** on a
  future board revision — the only hardware option that would bring the
  USB-serial floor below 1 ms.

## Consequences

### Positive
- The dominant source of timing uncertainty is identified and explained by a physical limit, not a misconfiguration — no further time is spent chasing a FTDI driver tuning that cannot improve beyond the current setting.
- The ADC and serial transmission stages are confirmed negligible and can be deprioritized in any future latency work.

### Negative / Open
- The contribution of the Python `datetime.now()` timestamp (taken after the full round-trip) to the overall budget remains unquantified in isolation — left open for a future investigation if the FTDI floor is ever lifted (e.g. after option (c)).
- No immediate action is taken: D2XX driver migration was evaluated as not providing a latency gain on this Full-Speed chip, so it is not planned.
