# PyVista et Qt - Problèmes d'Intégration

## Problème Identifié

L'intégration de PyVista dans Qt via `pyvistaqt` pose des problèmes de rendu sur macOS :
- Le widget `QtInteractor` ne rend pas correctement
- Problèmes de contexte OpenGL/VTK avec Qt
- Le rendu ne s'affiche pas dans le widget intégré

## Solution Actuelle

**Utilisation d'une fenêtre séparée PyVista** (mode par défaut).

### Avantages
- ✅ Fonctionne correctement
- ✅ Rendu fiable
- ✅ Pas de problèmes de contexte OpenGL
- ✅ Compatible avec tous les systèmes

### Inconvénients
- ❌ Fenêtre séparée (pas intégrée dans l'UI Qt)
- ❌ Gestion de fenêtre supplémentaire

## Configuration

Dans `cube_visualizer_adapter_pyvista.py`, ligne ~79 :

```python
USE_STANDALONE_WINDOW = True  # Fenêtre séparée (recommandé)
USE_STANDALONE_WINDOW = False  # Intégration Qt (problématique)
```

## Alternatives Futures

Si l'intégration Qt est nécessaire, considérer :
1. **QVTKRenderWindowInteractor** : Intégration VTK directe avec Qt
2. **PyQtGraph** : Alternative à PyVista pour la visualisation 3D
3. **Matplotlib 3D** : Plus simple mais moins performant
4. **Open3D** : Bibliothèque 3D moderne avec support Qt

## Références

- [PyVista Qt Integration Issues](https://github.com/pyvista/pyvista/issues)
- [VTK Qt macOS Rendering](https://discourse.vtk.org/t/vtk-9-pyqt-macos-no-rendering/3358)


