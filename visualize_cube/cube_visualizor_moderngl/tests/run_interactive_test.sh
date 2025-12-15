#!/bin/bash
# Script pour lancer le test interactif

cd "$(dirname "$0")/.."
python -m tests.test_interactive_rendering

