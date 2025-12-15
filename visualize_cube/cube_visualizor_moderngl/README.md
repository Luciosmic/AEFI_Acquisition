# Cube Visualizer - ModernGL (Non fonctionnel)

⚠️ **ATTENTION** : Cette implémentation ModernGL intégrée dans Qt ne fonctionne pas actuellement.

## Problème

Le cube ne s'affiche pas dans le widget Qt intégré, malgré :
- Le contexte OpenGL créé correctement
- Les VAOs créés
- Les appels de rendu effectués
- Le fond coloré visible

## Solution actuelle

Utiliser `cube_visualizor_emerging` avec PyVista en **fenêtre séparée**, qui fonctionne correctement.

## Structure

Le code est organisé en DDD pour référence future :
- `domain/` : Value objects, services de géométrie
- `application/` : Services, commandes (CQRS)
- `infrastructure/` : Messaging (CommandBus, EventBus), rendering (ModernGL)
- `interface/` : UI Qt

## Tests

Les tests unitaires passent, mais le rendu dans Qt ne fonctionne pas.

