"""
Script de compilation pour le module Cython ultra-optimisé
Usage: python setup_cython.py build_ext --inplace
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

# Configuration avec optimisations maximales
extensions = [
    Extension(
        "ultra_serial",
        ["ultra_serial.pyx"],
        include_dirs=[],
        libraries=[],
        library_dirs=[],
        # Optimisations de compilation
        extra_compile_args=[
            "/O2",          # Optimisation maximale (Windows MSVC)
            "/favor:INTEL64", # Optimisation pour processeurs 64-bit
            "/GL",          # Optimisation globale
        ] if "win" in str(setup.__module__) else [
            "-O3",          # Optimisation maximale (GCC/Clang)
            "-march=native", # Optimisation pour l'architecture locale
            "-ffast-math",  # Optimisations mathématiques agressives
            "-flto",        # Link Time Optimization
        ],
        extra_link_args=[
            "/LTCG"         # Link Time Code Generation (Windows)
        ] if "win" in str(setup.__module__) else [
            "-flto"         # Link Time Optimization (GCC/Clang)
        ],
        language="c"
    )
]

setup(
    name="UltraSerial",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,     # Désactiver la vérification des limites
            'wraparound': False,      # Désactiver l'indexation négative
            'cdivision': True,        # Division C native (plus rapide)
            'profile': False,         # Désactiver le profiling
            'linetrace': False,       # Désactiver le line tracing
            'binding': False,         # Désactiver le binding Python
        },
        annotate=True  # Génère un fichier HTML d'analyse
    ),
    zip_safe=False,
) 