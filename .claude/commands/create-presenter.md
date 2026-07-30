---
description: 'Create presenter'
---

# Create Presenter

Scaffold a new presenter that bridges an application service and a Qt view. The presenter implements the service's output port and exposes Qt signals for the view.

## When to Use

- Adding a new feature panel to the AEFI dashboard
- Wiring a new application service to the UI layer
- Separating UI event handling from a panel widget that has grown too large

## Checkpoints

- What is the name of the feature (e.g., `calibration`, `signal_processing`)?
- Which application service does this presenter drive?
- Which output port interface does it implement?
- For each variant of the service's Use Case error union, what UI reaction is expected?
- Does any Slot handler `raise` or silently drop the error branch of the `Result`? (Both are forbidden.)

## Steps

### 1. Create the presenter file

Create `src/interface/presenters/<name>_presenter.py`.

### 2. Implement the presenter class

```python
from PySide6.QtCore import QObject, Signal, Slot
from application.services.<name>_service.<name>_service import <Name>Service
from application.services.<name>_service.i_<name>_output_port import I<Name>OutputPort

class <Name>Presenter(QObject, I<Name>OutputPort):
    # Signals to update Views (success + one refusal signal per error variant)
    <event>_signal = Signal(<types>)
    refused_<variant>_signal = Signal(<types>)

    def __init__(self, service: <Name>Service) -> None:
        super().__init__()
        self._service = service
        service.set_output_port(self)

    # I<Name>OutputPort implementation
    def present_success_<event>(self, ...) -> None:
        self.<event>_signal.emit(...)

    def present_refused_<variant>(self, ...) -> None:
        self.refused_<variant>_signal.emit(...)
```

### 2.5. Handle the Result union in the Slot handler

The `on_<action>_requested` Slot must consume `OperationResult[T, <Name>UseCaseError]` returned by the service and dispatch to `present_success_<event>` or `present_refused_<variant>` output-port methods. Never `raise` from a Slot; never discard the error branch.

```python
    @Slot(<types>)
    def on_<action>_requested(self, ...) -> None:
        result = self._service.<action>(...)
        if result.is_success:
            self.present_success_<event>(result.value)
        else:
            self._dispatch_refusal(result.error)  # match on variant, call the right present_refused_*
```

### 2.6. Extend the output port with a refusal method per error variant

For each variant of `<Name>UseCaseError`, add a `present_refused_<variant>` method to `I<Name>OutputPort` so the view can react per business-refusal semantics — not per exception class. The presenter implements every variant explicitly; a missing branch is a static error.

### 3. Connect to the view panel

In the view panel (`src/interface/widgets/panels/<name>_panel.py`), connect signals from the presenter to view update methods, and connect view interactions to presenter slots.

### 4. Register in composition root

Instantiate the presenter in the composition root after the service, then pass it to the panel widget.
