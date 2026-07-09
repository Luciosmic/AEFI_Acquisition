# Tests E2E - Structure

## Organisation par Services Application

Les tests e2e sont organisés par **services application** (use cases) plutôt que par domain, car :
- Les services représentent les use cases métier
- Tests alignés avec l'utilisation réelle
- Facile de tester les interactions entre bounded contexts

## Structure

```
tests_e2e/
├── base/                          # Infrastructure commune
│   ├── test_base_agent.py        # Classe de base diagram-friendly
│   ├── e2e_test_environment.py   # Environnement de test complet
│   └── test_fixtures.py          # Fixtures réutilisables
│
├── scan_application_service/      # Tests ScanApplicationService
│   └── test_scan_executor_backend_mock_refinement.py
│
├── motion_control_service/        # Tests MotionControlService
│
├── continuous_acquisition_service/ # Tests ContinuousAcquisitionService
│
├── hardware_configuration_service/ # Tests HardwareConfigurationService
│
└── integration/                    # Tests multi-services
```

## Utilisation

```python
from tests_e2e.base import DiagramFriendlyTest, create_scan_config, create_mock_motion_port

class TestMyFeature(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.config = create_scan_config()
        self.motion_port = create_mock_motion_port()
```



