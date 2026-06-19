import json
import unittest
from datetime import datetime
from pathlib import Path

class DiagramFriendlyTest(unittest.TestCase):
    """
    Base class for tests that generate structured JSON logs for sequence diagrams.
    Follows .cursor/rules/agent_test_designer.mdc Guidelines.
    """
    def setUp(self):
        self.interactions = []
        self.test_start = datetime.now()
    
    def log_interaction(self, actor, action, target, message, data=None, expect=None, got=None):
        """
        Log a single interaction for the sequence diagram.
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
            "message": message,
        }
        if data is not None:
            interaction["data"] = data
        if expect is not None:
            interaction["expect"] = str(expect)
        if got is not None:
            interaction["got"] = str(got)
            
        self.interactions.append(interaction)
    
    def log_divider(self, title: str):
        """
        Log a visual divider for the sequence diagram.
        
        Args:
            title: The text to display in the divider (e.g., "Setup", "Execution")
        """
        self.interactions.append({
            "timestamp": datetime.now().isoformat(),
            "actor": "System",
            "action": "DIVIDER",
            "target": "System",
            "message": title,
            "data": None,
            "expect": None,
            "got": None
        })
        print(f"\n=== {title} ===\n")
    
    def tearDown(self):
        test_name = self._testMethodName
        # Get the filename of the actual test class being run
        test_file = Path(self.__class__.__module__.replace('.', '/') + '.py')
        # We need the absolute path to write next to the test file
        # This is a bit tricky with unittest discovery, so we'll use the inspections
        import inspect
        test_file_path = Path(inspect.getfile(self.__class__))
        
        result_file = test_file_path.parent / f"{test_file_path.stem}_results.json"
        
        # Merge with existing results if file exists (for multiple tests in one file)
        existing_results = {}
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    existing_results = json.load(f)
            except json.JSONDecodeError:
                pass

        # Structure for this specific test
        test_result = {
            "test_name": test_name,
            "timestamp": self.test_start.isoformat(),
            "status": "PASSED" if self._result_passed() else "FAILED",
            "interactions": self.interactions,
            "summary": self._generate_summary()
        }
        
        # If the file format is a list of tests, append. If it was single object (from rule example), make it a list or dict.
        # The rule shows a single object structure, but for multiple tests in a class, we need a way to store them.
        # However, to strictly follow the rule output requirements:
        # "Format: Valid JSON with the following schema: { ... }" -> seemingly one object per file?
        # But a test file has multiple methods. 
        # I will augment the schema slightly to wrap results in a map Key=TestName, or just Overwrite for now if running single test.
        # Let's stick to the schema from the rule for the *structure of the object*, but maybe store a list of them if we run multiple?
        # The rule says: "Result File Structure ... {test_filename}_results.json"
        # If we run multiple tests, we shouldn't overwrite.
        # Let's use a dictionary keyed by test name for practical storage, but the INNER structure matches the schema.
        
        if "tests" not in existing_results:
             # Initialize as a collection of test results
             existing_results = {"tests": []}

        # Remove old run of this test if exists
        existing_results["tests"] = [t for t in existing_results.get("tests", []) if t["test_name"] != test_name]
        existing_results["tests"].append(test_result)
        
        with open(result_file, 'w') as f:
            json.dump(existing_results, f, indent=2)

    def _result_passed(self):
        # A hack to check if the current test passed in standard unittest
        # This depends on how the runner is called. 
        # For simplicity, we assume passed unless an exception was raised during execution.
        # In `tearDown`, `sys.exc_info()` returns information about the exception being handled.
        import sys
        return sys.exc_info() == (None, None, None)

    def _generate_summary(self):
        actions = [i['action'] for i in self.interactions]
        return {
            "total_interactions": len(self.interactions),
            "subscriptions": actions.count('SUBSCRIBE'),
            "publications": actions.count('PUBLISH'),
            "assertions": actions.count('ASSERT')
        }
