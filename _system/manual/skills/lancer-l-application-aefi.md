---
type: mcp.skill::au-mcp-sdk
name: lancer-l-application-aefi
description: "Lance l'application AEFI Acquisition Software (UI PySide6) depuis le worktree courant, sur le matériel réel ou tout en simulation, dans une fenêtre à part. À utiliser quand l'humain demande de lancer, démarrer ou relancer l'application AEFI, le logiciel d'acquisition ou l'app, ou de la voir tourner."
---

# Lancer l'application AEFI

1. **Choisis le mode.**
   - Matériel réel : le point d'entrée est `src/interface/main.py`. Prends-le quand l'humain parle du banc, d'une mesure ou du matériel branché.
   - Simulation : le point d'entrée est `src/main_mock.py`. Prends-le pour vérifier un changement d'UI sans matériel.
   - Si la demande ne tranche pas, prends le matériel réel sur l'ordinateur du laboratoire et dis-le en une ligne.

2. **Lance dans une fenêtre à part**, depuis la racine du worktree courant, pour que la session continue :

   ```powershell
   Start-Process powershell -ArgumentList "-NoProfile -NoExit -Command `"cd '<racine du worktree>'; uv run python <point d'entrée>`""
   ```

   uv crée ou met à jour `.venv` au premier lancement.

3. **Vérifie que la fenêtre est là** : un processus Python porte le titre « AEFI Acquisition Software ».

   ```powershell
   Get-Process | Where-Object { $_.MainWindowTitle -match "AEFI" } | Select-Object Id, MainWindowTitle
   ```

   Laisse quelques secondes au démarrage.
   Sans fenêtre, relance au premier plan (`uv run python <point d'entrée>`) pour lire l'erreur.

4. **Dis à l'humain** le mode lancé et le worktree.

## Pannes connues

- `uv` introuvable : uv n'est pas dans le PATH.
- `ModuleNotFoundError` : lance `uv sync`, puis relance.
- En mode réel sans matériel branché, les adaptateurs signalent des erreurs de connexion : c'est attendu, la simulation est l'autre point d'entrée.
