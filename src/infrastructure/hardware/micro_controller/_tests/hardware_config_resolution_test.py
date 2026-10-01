import os
import sys
import unittest
from pathlib import Path

src_path = Path(__file__).resolve().parents[4]
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.micro_controller.hardware_config_resolution import (
    resolve_config,
    load_json_if_exists,
)


class TestResolveConfig(unittest.TestCase):
    def test_override_wins_on_flat_keys(self):
        result = resolve_config({"frequency_hz": 1000}, {"frequency_hz": 2000})
        self.assertEqual(result, {"frequency_hz": 2000})

    def test_untouched_nested_channel_keeps_default_value(self):
        default = {
            "channels": {
                "3": {"gain": 10000, "phase": 16384},
                "4": {"gain": 10000, "phase": 0},
            }
        }
        override = {"channels": {"1": {"gain": 1000, "phase": 16000}}}

        result = resolve_config(default, override)

        self.assertEqual(result["channels"]["3"], {"gain": 10000, "phase": 16384})
        self.assertEqual(result["channels"]["4"], {"gain": 10000, "phase": 0})
        self.assertEqual(result["channels"]["1"], {"gain": 1000, "phase": 16000})

    def test_none_override_returns_copy_of_default(self):
        default = {"n_avg": 1}
        result = resolve_config(default, None)
        self.assertEqual(result, default)
        self.assertIsNot(result, default)

    def test_does_not_mutate_arguments(self):
        default = {"channels": {"1": {"gain": 0}}}
        override = {"channels": {"1": {"gain": 1000}}}

        resolve_config(default, override)

        self.assertEqual(default["channels"]["1"]["gain"], 0)
        self.assertEqual(override["channels"]["1"]["gain"], 1000)

    def test_load_json_if_exists_returns_empty_dict_when_missing(self):
        self.assertEqual(load_json_if_exists("nonexistent_path.json"), {})


if __name__ == "__main__":
    unittest.main()
