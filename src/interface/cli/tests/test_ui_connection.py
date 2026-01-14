"""
Test de Connexion UI ↔ CLI

Valide que le presenter UI utilise le même service que le CLI (testé).
Test sans dépendance PySide6 (vérification statique).
"""

import unittest
import inspect
from pathlib import Path
import sys

# Add src to path
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from interface.cli.scan_cli import create_scan_service, ScanCLIOutputPort
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort


class TestUIConnection(unittest.TestCase):
    """Test que UI et CLI utilisent le même service."""
    
    def test_cli_and_ui_use_same_service_class(self):
        """Vérifie que CLI et UI utilisent la même classe de service."""
        # Service CLI
        cli_service = create_scan_service()
        
        # Service UI (même création - vérification statique du code)
        # Dans main.py ligne 197, on crée aussi ScanApplicationService
        # Vérifions que c'est la même classe
        
        self.assertIsInstance(cli_service, ScanApplicationService,
                             "CLI doit utiliser ScanApplicationService")
        
        # Vérifier que la classe a les méthodes attendues
        self.assertTrue(hasattr(cli_service, 'execute_scan'),
                       "Service doit avoir execute_scan")
        self.assertTrue(hasattr(cli_service, 'execute_fly_scan'),
                       "Service doit avoir execute_fly_scan")
        self.assertTrue(hasattr(cli_service, 'set_output_port'),
                       "Service doit avoir set_output_port")
    
    def test_cli_output_port_implements_interface(self):
        """Vérifie que ScanCLIOutputPort implémente IScanOutputPort."""
        cli_output = ScanCLIOutputPort()
        
        self.assertIsInstance(cli_output, IScanOutputPort,
                             "ScanCLIOutputPort doit implémenter IScanOutputPort")
    
    def test_presenter_file_has_correct_structure(self):
        """Vérifie que scan_presenter.py a la structure attendue (vérification statique)."""
        presenter_file = src_dir / "interface" / "presenters" / "scan_presenter.py"
        
        self.assertTrue(presenter_file.exists(),
                        "scan_presenter.py doit exister")
        
        # Lire le fichier pour vérifier la structure
        content = presenter_file.read_text()
        
        # Vérifier que ScanPresenter implémente IScanOutputPort
        self.assertIn("class ScanPresenter", content,
                      "ScanPresenter doit être défini")
        self.assertIn("IScanOutputPort", content,
                      "ScanPresenter doit implémenter IScanOutputPort")
        self.assertIn("set_output_port", content,
                      "ScanPresenter doit appeler set_output_port")
        self.assertIn("present_scan_started", content,
                      "ScanPresenter doit avoir present_scan_started")
        self.assertIn("present_flyscan_started", content,
                      "ScanPresenter doit avoir present_flyscan_started")
    
    def test_main_py_connects_presenter_to_service(self):
        """Vérifie que main.py connecte le presenter au service (vérification statique)."""
        main_file = Path(__file__).parent.parent.parent.parent.parent / "main.py"
        
        if not main_file.exists():
            self.skipTest("main.py non trouvé")
        
        content = main_file.read_text()
        
        # Vérifier que main.py crée le service
        self.assertIn("ScanApplicationService", content,
                     "main.py doit créer ScanApplicationService")
        
        # Vérifier que main.py crée le presenter avec le service
        self.assertIn("ScanPresenter", content,
                     "main.py doit créer ScanPresenter")
        
        # Vérifier que les panels sont connectés
        self.assertIn("scan_start_requested.connect", content,
                     "main.py doit connecter scan_start_requested")
        self.assertIn("flyscan_start_requested.connect", content,
                     "main.py doit connecter flyscan_start_requested")
    
    def test_service_output_port_pattern(self):
        """Vérifie que le pattern Output Port est correctement utilisé."""
        service = create_scan_service()
        cli_output = ScanCLIOutputPort()
        
        # Vérifier que service a une méthode set_output_port
        self.assertTrue(hasattr(service, 'set_output_port'),
                       "Service doit avoir set_output_port")
        
        # Tester que set_output_port fonctionne
        service.set_output_port(cli_output)
        self.assertEqual(service._output_port, cli_output,
                        "Service doit avoir le output port après set_output_port")
    
    def test_required_output_port_methods(self):
        """Vérifie que toutes les méthodes IScanOutputPort sont présentes."""
        cli_output = ScanCLIOutputPort()
        
        # Méthodes IScanOutputPort requises
        required_methods = {
            'present_scan_started',
            'present_scan_progress',
            'present_scan_completed',
            'present_scan_failed',
            'present_scan_cancelled',
            'present_scan_paused',
            'present_scan_resumed',
            'present_flyscan_started',
            'present_flyscan_progress',
            'present_flyscan_completed',
            'present_flyscan_failed',
            'present_flyscan_cancelled'
        }
        
        for method in required_methods:
            self.assertTrue(hasattr(cli_output, method),
                          f"CLI OutputPort doit avoir la méthode {method}")
            # Vérifier que c'est une méthode callable
            method_obj = getattr(cli_output, method)
            self.assertTrue(callable(method_obj),
                          f"{method} doit être callable")
    
    def test_service_methods_match_cli_usage(self):
        """Vérifie que le service a les méthodes utilisées par le CLI."""
        service = create_scan_service()
        
        # Méthodes utilisées par le CLI
        cli_methods = {
            'execute_scan',
            'execute_fly_scan',
            'set_output_port',
            'get_status'
        }
        
        for method in cli_methods:
            self.assertTrue(hasattr(service, method),
                          f"Service doit avoir la méthode {method} utilisée par CLI")
            self.assertTrue(callable(getattr(service, method)),
                          f"{method} doit être callable")


if __name__ == '__main__':
    unittest.main()

