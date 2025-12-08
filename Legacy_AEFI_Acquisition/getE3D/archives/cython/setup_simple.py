"""
Script de compilation simplifié pour le module Cython ultra-optimisé
Usage: python setup_simple.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize

# Configuration simplifiée
extensions = [
    Extension(
        "ultra_serial_simple",
        ["ultra_serial_simple.pyx"],
        language="c"
    )
]

setup(
    name="UltraSerialSimple",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
        }
    ),
    zip_safe=False,
) 