#!/usr/bin/env python3
"""Test simple pour vérifier que PyVista fonctionne."""

print("=== Test PyVista ===")
import pyvista as pv
print(f"PyVista version: {pv.__version__}")

print("Création d'un plotter...")
plotter = pv.Plotter()
print("Ajout d'une sphère...")
plotter.add_mesh(pv.Sphere())
print("Ouverture de la fenêtre (fermez-la pour continuer)...")
plotter.show()
print("Fenêtre fermée. Test terminé.")

