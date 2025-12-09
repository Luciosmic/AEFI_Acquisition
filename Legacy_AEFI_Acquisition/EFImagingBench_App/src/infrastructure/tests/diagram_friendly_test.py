import unittest
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

class DiagramFriendlyTest(unittest.TestCase):
    """
    Base class for tests that generate diagram-friendly execution traces.
    Produces a JSON file with all interactions for sequence diagram generation.
    """
    
    def setUp(self):
        self.interactions = []
        self.test_start = datetime.now()
        # Call super setup if needed, though unittest.TestCase.setUp is empty
        super().setUp()
    
    def log_interaction(
        self, 
        actor: str, 
        action: str, 
        target: str, 
        message: str, 
        data: Optional[dict] = None, 
        expect: Any = None, 
        got: Any = None
    ):
        """
        Log an interaction for the sequence diagram.
        
        Args:
            actor: Who initiates the action (e.g., "Test", "ScanService")
            action: The type of action (CREATE, CALL, RETURN, PUBLISH, RECEIVE, ASSERT, etc.)
            target: Who receives the action (e.g., "EventBus", "MotionPort")
            message: Description of the interaction
            data: Optional dictionary with relevant data payload
            expect: Expected value (for assertions)
            got: Actual value (for assertions)
        """
        self.interactions.append({
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
            "message": message,
            "data": data,
            "expect": str(expect) if expect is not None else None,
            "got": str(got) if got is not None else None
        })
        
        # Also print to stdout for immediate feedback
        print(f"[{actor}] {action} -> [{target}] : {message}")
        if data:
            print(f"  Data: {data}")
        if expect is not None:
            print(f"  Expect: {expect} | Got: {got}")

    def tearDown(self):
        test_name = self._testMethodName
        # Save to the same directory as the test file
        # We use the module file path if available, otherwise fallback
        module_path = Path(__file__).parent # Default fallback
        
        # Try to get the actual test file path from the child class module
        try:
            import sys
            module = sys.modules[self.__class__.__module__]
            if hasattr(module, '__file__'):
                module_path = Path(module.__file__).parent
                filename_stem = Path(module.__file__).stem
            else:
                filename_stem = "unknown_test"
        except Exception:
            filename_stem = "unknown_test"
            
        # Clean up filename to avoid double "test"
        clean_stem = filename_stem.replace("test_", "").replace("_test", "")
        clean_method = test_name.replace("test_", "")
        
        result_file = module_path / f"{clean_stem}_{clean_method}_results.json"
        
        status = "PASSED"
        # Check if test failed using _outcome (Python 3.4+)
        if hasattr(self, '_outcome'):
            if not self._outcome.success:
                status = "FAILED"

        results = {
            "test_name": test_name,
            "timestamp": self.test_start.isoformat(),
            "status": status,
            "interactions": self.interactions,
            "summary": self._generate_summary()
        }
        
        try:
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n[DiagramFriendlyTest] Saved interaction trace to: {result_file}")
        except Exception as e:
            print(f"\n[DiagramFriendlyTest] Failed to save interaction trace: {e}")
            
        super().tearDown()
    
    def _generate_summary(self):
        actions = [i['action'] for i in self.interactions]
        return {
            "total_interactions": len(self.interactions),
            "subscriptions": actions.count('SUBSCRIBE'),
            "publications": actions.count('PUBLISH'),
            "assertions": actions.count('ASSERT')
        }
