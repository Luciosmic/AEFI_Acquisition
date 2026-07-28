# AEFI Acquisition — VIBE.md

## Projet

Système d'acquisition pour l'AEFI (Électromagnétisme par Fluorescence d'Impédance). Pilote un banc de scan 2D avec excitation DDS (AD9106), ADC (ADS131A04), capteur électromagnétique, et post-traitement synchrone. Produit des cartographies 2D de mesures pour un problème direct 4 sphères.

## Stack

- Python ≥ 3.10, géré par **uv** (`uv run python`, `uv run pytest`)
- UI : **PySide6**
- Architecture : **DDD** (domain / application / infrastructure / interface)
- Tests : pytest (`src/_tests/`)
- Agent : **Mistral Vibe** (remplace Claude Code)

## Structure

```
src/
  domain/          # entités, value objects, services domaine, ports (interfaces)
  application/     # use-cases, services applicatifs, DTOs
  infrastructure/  # adaptateurs hardware (serial, AD9106, ADS131A04, moteurs Arcus)
  interface/       # UI PySide6, controllers, panneau hardware
  _tests/          # tests unitaires et intégration

.vibe/             # Configuration Mistral Vibe (remplace .claude/)
  config.toml      # Configuration principale
  hooks.toml       # Hooks expérimentaux
  hooks/           # Scripts de hooks
    session-start.sh
    track-touched-files.sh
    inject-session-id.sh

_system/           # référence agents — lire en premier
_docs/             # ADR, analyses architecturales, datasheets hardware
external_modules/  # modules tiers (cube_visualizer 3D, post_processor_module)
.aefi_acquisition/ # données runtime (configs, scans, calibrations, logs) — gitignored
```

## Configuration Vibe

### Prérequis

1. Installer Mistral Vibe:
   ```bash
   uv tool install mistral-vibe
   ```

2. Configurer votre clé API Mistral:
   ```bash
   echo "MISTRAL_API_KEY=votre_cle_api" >> ~/.vibe/.env
   ```

3. Faire confiance au dossier du projet:
   ```bash
   cd /chemin/vers/AEFI_Acquisition
   vibe --trust
   ```

### Configuration spécifique au projet

La configuration Vibe est dans `.vibe/config.toml`:

- **Modèle par défaut**: `mistral-medium-3.5`
- **Outils activés**: bash, read, write_file, edit, grep, todo, task
- **Hooks expérimentaux**: activés pour le suivi des fichiers modifiés
- **Signature des commits**: activée (Co-Authored-By: Mistral Vibe)

### Hooks Vibe

Les hooks suivants sont configurés:

| Hook | Type | Description |
|------|------|-------------|
| `session-start-cleanup` | `post_agent_turn` | Nettoie les fichiers de suivi au démarrage |
| `track-touched-files` | `after_tool` | Suivi des fichiers modifiés par `write_file` |
| `track-edited-files` | `after_tool` | Suivi des fichiers modifiés par `edit` |
| `inject-session-id` | `before_tool` | Injection de l'ID de session pour le suivi |

Les fichiers de suivi sont stockés dans `.vibe/session_touched_files_<session_id>`.

## Migration depuis Claude Code

### Modifications apportées

1. **Création de `.vibe/`** :
   - `config.toml` - Configuration principale Vibe
   - `hooks.toml` - Définition des hooks expérimentaux
   - `hooks/` - Scripts bash adaptés de `.claude/hooks/`

2. **Adaptation des hooks**:
   - Conversion du format Claude Code vers le format Vibe
   - Changement des variables d'environnement (`CLAUDE_CONVERSATION_ID` → `VIBE_SESSION_ID`)
   - Adaptation du schéma JSON des payloads

3. **Conservation des fonctionnalités**:
   - Suivi des fichiers modifiés
   - Nettoyage automatique des fichiers de session anciens (> 7 jours)
   - Injection de l'ID de session dans le contexte

### Compatibilité

- ✅ Tous les outils nécessaires sont activés
- ✅ Les hooks de suivi des fichiers sont fonctionnels
- ✅ La configuration DDD/SolidAI est préservée
- ⚠️ Le dossier `.claude/` peut être supprimé ou archivé

## Commandes utiles

```bash
# Démarrer une session Vibe
vibe

# Démarrer avec un agent spécifique
vibe --agent plan

# Mode programmatique (sans interaction)
vibe -p "Votre prompt ici"

# Mode programmatique avec approval automatique
vibe -p "Votre prompt ici" --auto-approve

# Continuer la session précédente
vibe --continue

# Lister les sessions récentes
vibe --resume

# Recharger la configuration
/reload

# Voir les logs
/log
```

## Référence agents

Lire `_system/` avant toute décision architecturale :

- [`_system/self/goals.md`](_system/self/goals.md) — objectifs et features en cours
- [`_system/ops/tasks.md`](_system/ops/tasks.md) — tâches actives

## Branches

| Branche | Rôle |
|---------|------|
| `main` | Stable = release/v1.0.1 |
| `develop` | Intégration — base pour les nouvelles features |
| `feature/*` | Feature branch depuis develop |
| `release/v1.0.1` | Worktree `AEFI_Acquisition/` — utilisé pour les acquisitions |
| `release/v1.0.0` | Archive historique |
| `archive/ddd-refactoring` | Refactoring DDD gelé — documentation uniquement, ne pas merger |

## Conventions

- Style de commit : conventionnel (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`)
- Tout nouveau développement part de `develop`
- Les configs hardware utilisateur vivent dans `.aefi_acquisition/configs/` (hors git)
- La référence des schémas de config est dans `_system/self/goals.md`
- Les modifications Vibe sont signées avec `Co-Authored-By: Mistral Vibe <vibe@mistral.ai>`
