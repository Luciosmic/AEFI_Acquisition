"""
Lanceur Global des Tests Backend AD9106/ADS131A04

Usage:
    python run_all_tests.py --quick      # Niveaux 1-2 uniquement
    python run_all_tests.py --no-hardware # Niveaux 1-3 (sans hardware)
    python run_all_tests.py --all        # Tous niveaux
    python run_all_tests.py --verbose    # Mode verbose
"""

import sys
import argparse
import time
from pathlib import Path

# Import des modules de test
try:
    from test_1_imports import run_level1_tests
    from test_2_unit_mode_controller import run_mode_controller_tests
    from test_2_unit_data_buffer import run_data_buffer_tests
    # from test_2_unit_adc_converter import run_adc_converter_tests
    # from test_2_unit_csv_exporter import run_csv_exporter_tests
    TESTS_AVAILABLE = True
except ImportError as e:
    TESTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestRunner:
    """Gestionnaire d'exécution des tests"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {
            'level1': {'executed': False, 'success': False, 'duration': 0},
            'level2_mode': {'executed': False, 'success': False, 'duration': 0},
            'level2_buffer': {'executed': False, 'success': False, 'duration': 0},
            'level2_adc': {'executed': False, 'success': False, 'duration': 0},
            'level2_csv': {'executed': False, 'success': False, 'duration': 0},
        }
    
    def print_banner(self):
        """Affiche la bannière de démarrage"""
        print("=" * 60)
        print("🧪 SUITE DE TESTS BACKEND AD9106/ADS131A04")
        print("=" * 60)
        print("🎯 Objectif : Validation complète backend avant interface")
        print(f"⏱️  Heure de début : {time.strftime('%H:%M:%S')}")
        if self.verbose:
            print("🔍 Mode verbose activé")
        print("")
    
    def run_level1(self):
        """Exécute les tests niveau 1"""
        print("🔧 ======= NIVEAU 1 : IMPORTS ET SYNTAXE =======")
        
        if not TESTS_AVAILABLE:
            print(f"❌ Import tests impossible : {IMPORT_ERROR}")
            return False
        
        start_time = time.time()
        
        try:
            success = run_level1_tests()
            duration = time.time() - start_time
            
            self.results['level1'] = {
                'executed': True,
                'success': success,
                'duration': duration
            }
            
            if success:
                print(f"✅ NIVEAU 1 RÉUSSI en {duration:.1f}s")
            else:
                print(f"❌ NIVEAU 1 ÉCHOUÉ en {duration:.1f}s")
                print("🛑 Arrêt : corriger les imports avant de continuer")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"🚨 ERREUR NIVEAU 1 : {e}")
            self.results['level1'] = {
                'executed': True,
                'success': False,
                'duration': duration
            }
            return False
    
    def run_level2(self):
        """Exécute les tests niveau 2 (unitaires)"""
        print("\n⚡ ======= NIVEAU 2 : TESTS UNITAIRES =======")
        
        level2_tests = [
            ('mode', 'ModeController', run_mode_controller_tests),
            ('buffer', 'DataBuffer', run_data_buffer_tests),
        ]
        
        all_success = True
        
        for test_key, test_name, test_func in level2_tests:
            print(f"\n--- {test_name} ---")
            start_time = time.time()
            
            try:
                success = test_func()
                
                duration = time.time() - start_time
                
                self.results[f'level2_{test_key}'] = {
                    'executed': True,
                    'success': success,
                    'duration': duration
                }
                
                if success:
                    print(f"✅ {test_name} RÉUSSI en {duration:.1f}s")
                else:
                    print(f"❌ {test_name} ÉCHOUÉ en {duration:.1f}s")
                    all_success = False
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"🚨 ERREUR {test_name} : {e}")
                self.results[f'level2_{test_key}'] = {
                    'executed': True,
                    'success': False,
                    'duration': duration
                }
                all_success = False
        
        return all_success
    
    def run_quick_tests(self):
        """Exécute tests rapides (niveau 1-2)"""
        print("🚀 MODE RAPIDE : Tests Niveau 1-2 uniquement")
        print("⏱️  Durée estimée : 5-8 minutes\n")
        
        # Niveau 1
        level1_success = self.run_level1()
        if not level1_success:
            return False
        
        # Niveau 2
        level2_success = self.run_level2()
        
        return level1_success and level2_success
    
    def print_final_report(self):
        """Affiche le rapport final"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL")
        print("=" * 60)
        
        total_duration = sum(r['duration'] for r in self.results.values() if r['executed'])
        total_tests = sum(1 for r in self.results.values() if r['executed'])
        successful_tests = sum(1 for r in self.results.values() if r['executed'] and r['success'])
        
        print(f"⏱️  Durée totale : {total_duration:.1f}s")
        print(f"📈 Tests exécutés : {total_tests}")
        print(f"✅ Succès : {successful_tests}")
        print(f"❌ Échecs : {total_tests - successful_tests}")
        
        print("\nDétail par niveau :")
        
        for test_key, result in self.results.items():
            if result['executed']:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"  {test_key:15} : {status:8} ({result['duration']:.1f}s)")
        
        # Recommandations
        print("\n🎯 RECOMMANDATIONS :")
        
        if all(r['success'] for r in self.results.values() if r['executed']):
            print("🎉 TOUS LES TESTS PASSENT !")
            print("✅ Backend validé - Prêt pour développement interface")
        else:
            print("⚠️  ÉCHECS DÉTECTÉS")
            failed_tests = [k for k, r in self.results.items() if r['executed'] and not r['success']]
            print(f"🔧 Corriger : {', '.join(failed_tests)}")
            print("🛑 Ne pas continuer vers interface avant résolution")
        
        return all(r['success'] for r in self.results.values() if r['executed'])


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Tests Backend AD9106/ADS131A04",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'usage:
  python run_all_tests.py --quick      # Tests rapides (5 min)
  python run_all_tests.py --verbose    # Mode détaillé
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Tests rapides niveau 1-2 uniquement')
    parser.add_argument('--no-hardware', action='store_true',
                       help='Tests niveau 1-3 sans hardware')
    parser.add_argument('--all', action='store_true',
                       help='Tous les tests y compris hardware')
    parser.add_argument('--verbose', action='store_true',
                       help='Mode verbose avec détails')
    
    args = parser.parse_args()
    
    # Mode par défaut = quick si aucun spécifié
    if not (args.quick or args.no_hardware or args.all):
        args.quick = True
    
    # Création runner
    runner = TestRunner(verbose=args.verbose)
    runner.print_banner()
    
    # Exécution selon mode
    try:
        if args.quick:
            overall_success = runner.run_quick_tests()
        elif args.no_hardware:
            print("🔄 MODE COMPLET : Tests Niveau 1-3 (sans hardware)")
            print("⏱️  Durée estimée : 15-20 minutes")
            print("⚠️  Pas encore implémenté - utiliser --quick")
            overall_success = False
        elif args.all:
            print("🔌 MODE COMPLET + HARDWARE : Tous les tests")
            print("⏱️  Durée estimée : 25-30 minutes")
            print("⚠️  Pas encore implémenté - utiliser --quick")
            overall_success = False
        
        # Rapport final
        runner.print_final_report()
        
        # Code de sortie
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrompus par l'utilisateur")
        return 2
    except Exception as e:
        print(f"\n🚨 ERREUR INATTENDUE : {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main()) 