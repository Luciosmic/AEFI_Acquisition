---
description: 'Scaffold a Qt presenter that implements an application service output port and exposes signals/slots to bridge the service and view so you can cleanly wire new UI panels while keeping business logic and UI event handling decoupled when adding features to the dashboard.'
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

## Steps

### 1. Create the presenter file

Create `src/interface/presenters/<name>_presenter.py`.

### 2. Implement the presenter class

```python
from PySide6.QtCore import QObject, Signal, Slot
from application.services.<name>_service.<name>_service import <Name>Service
from application.services.<name>_service.i_<name>_output_port import I<Name>OutputPort

class <Name>Presenter(QObject, I<Name>OutputPort):
    # Signals to update Views
    <event>_signal = Signal(<types>)

    def __init__(self, service: <Name>Service) -> None:
        super().__init__()
        self._service = service
        service.set_output_port(self)

    # I<Name>OutputPort implementation
    def present_<event>(self, ...) -> None:
        self.<event>_signal.emit(...)

    # User action handlers
    @Slot(<types>)
    def on_<action>_requested(self, ...) -> None:
        self._service.<action>(...)
```

### 3. Connect to the view panel

In the view panel (`src/interface/widgets/panels/<name>_panel.py`), connect signals from the presenter to view update methods, and connect view interactions to presenter slots.

### 4. Register in composition root

Instantiate the presenter in the composition root after the service, then pass it to the panel widget.
