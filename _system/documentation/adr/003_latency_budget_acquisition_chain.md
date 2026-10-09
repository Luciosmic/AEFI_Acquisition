# ADR-003: Latency Budget of the Acquisition Chain

## Status
Accepted

## Context
The question investigated: **which stage of the acquisition chain dominates the timing uncertainty of a measurement?** The chain runs from the Python interpreter, through the dsPIC33FJ128GP microcontroller, over the USB-serial link, to the ADS131A04 ADC (known OSR). Without knowing which stage dominates, effort could be spent optimizing a stage that contributes negligibly, while the real bottleneck stays unaddressed.

**Latency vs. jitter — a distinction the original version of this ADR conflated.** "Timing uncertainty" was the original question, but the Decision below (2026-10-02 data) establishes a **latency** budget — the mean fixed delay per stage. It does not, by itself, answer the uncertainty question, which is about **jitter** — the sample-to-sample dispersion (standard deviation) of that delay, not its average. A stage can have high mean latency and low jitter (predictable, compensable), or low mean latency and high jitter (unpredictable, corrupts synchronous post-processing). The two require different measurements. The jitter side of the question was left open in this ADR's first version (see the now-resolved entry in Consequences / Negative-Open) and is answered by the host-runtime jitter benchmark added below.

## Decision

We establish the following latency budget for one acquisition sample, from measurement and bench data gathered 2026-10-02:

| Stage | Order of magnitude | Verdict |
|---|---|---|
| ADC (ADS131A04) — DRDY jitter | ~0.2 µs, measured on oscilloscope (see `fake_drdy_capture_port.py`) | Negligible |
| Serial transmission (1.5 Mbaud) | tens of µs | Negligible |
| USB-serial bridge (FTDI FT232R) — `LatencyTimer` driver delay | 7.6 ms at `LatencyTimer=1ms`, 23.6 ms at `LatencyTimer=16ms` | **Dominant** |
| Python `datetime.now()` timestamp, taken after the full round-trip | mean contribution not isolated/quantified | Open (latency) — not yet measured in isolation |
| Python runtime jitter (GIL, GC pauses, interpreter overhead) — host-side contribution to timing **dispersion** | stdev 0.465 ms (Python) vs 0.513 ms (C, no managed runtime) — same order of magnitude, Python slightly *lower* | **Resolved, negligible** — see jitter measurement below (2026-10-09) |

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

### Jitter measurement: does the Python host runtime contribute to timing dispersion? (2026-10-09)

The latency budget above left the host runtime's contribution to **jitter** unmeasured. The hypothesis under test: the Python runtime (GIL contention, garbage-collector pauses, interpreter dispatch overhead) could itself be a source of timing dispersion on the host side, independent of the FTDI/MCU chain — which, if true, would justify externalizing the acquisition loop to a lower-level language.

**Method.** Two disposable, throwaway benchmark programs (scratchpad only — not committed to the repo) were run against the real hardware under a strictly identical protocol: `m1*` command, 1,500,000 baud, `LatencyTimer=1ms` (confirmed in the Windows registry for the device), real COM10 port, `n_avg=1`, 5000 iterations each:

- **C**, using the raw Win32 serial API directly (`CreateFile`/`ReadFile`/`WriteFile`) — no managed runtime of any kind.
- **Python**, using `pyserial` over the same API surface.

**Results.**

| Metric | C (raw Win32) | Python (pyserial) |
|---|---|---|
| mean | 4.353 ms | 4.586 ms |
| stdev | 0.513 ms | 0.465 ms |
| min | 3.107 ms | 3.506 ms |
| max | 17.801 ms | 5.637 ms |
| p50 | 4.109 ms | 4.697 ms |
| p95 | 5.101 ms | 5.236 ms |
| p99 | 5.292 ms | 5.386 ms |

**Interpretation.** The jitter (stdev) is of the same order of magnitude for both implementations, and Python's is slightly *lower* than C's (0.465 ms vs 0.513 ms) — if anything, favoring Python, though the difference is not meaningful at this sample size. This directly answers the original "what creates the most timing uncertainty" question: the ~0.5 ms of jitter observed here is carried by the FTDI/MCU chain, which is identical across both benchmarks, not by the host language or runtime. For scale, this is roughly three orders of magnitude above the ADC's own jitter (~0.2 µs, DRDY jitter row above) — the FTDI/MCU chain dominates the ADC by a wide margin, and the host runtime does not add a measurable contribution on top of it.

**Decision resulting from this measurement.** Externalizing the acquisition loop to a lower-level language (C or otherwise) to reduce timing jitter is explicitly **not pursued** — not as a default architectural preference, but because this measurement shows there is no jitter to recover by doing so. The option remains on the table only if a future change (e.g. a different FTDI chip, option (c) above) exposes host-side jitter that is currently masked by the larger FTDI/MCU contribution.

## Consequences

### Positive
- The dominant source of timing uncertainty is identified and explained by a physical limit, not a misconfiguration — no further time is spent chasing a FTDI driver tuning that cannot improve beyond the current setting.
- The ADC and serial transmission stages are confirmed negligible and can be deprioritized in any future latency work.

### Negative / Open
- The contribution of the Python `datetime.now()` timestamp (taken after the full round-trip) to the overall **latency** budget (mean delay) remains unquantified in isolation — left open for a future investigation if the FTDI floor is ever lifted (e.g. after option (c)).
- No immediate action is taken: D2XX driver migration was evaluated as not providing a latency gain on this Full-Speed chip, so it is not planned.

### Resolved (2026-10-09)
- The host runtime's contribution to **jitter** (timing dispersion, as opposed to mean latency above) — previously an open question in this ADR — is now resolved: the Python runtime is not a significant contributor (see "Jitter measurement" section above). Externalizing acquisition to another language on jitter grounds is explicitly ruled out on this basis, not left as a default choice.
