## Responsibility
Ensure that runtime config files exist in `.aefi_acquisition/configs/` before the application starts reading them.

## Rationale
Config files live in two places: `config_templates/` (git-tracked, default values) and `.aefi_acquisition/configs/` (gitignored, user-customized). On first run or on a new machine, the runtime directory is empty. The bootstrapper silently seeds it from the templates so the rest of the infrastructure can always find its config files — no dialog, no prompt.

## Design
Pure file-copy operation with no domain knowledge. Receives `templates_dir` and `runtime_dir` as constructor arguments for testability. Discovers all `.json` files in the templates directory automatically — no hardcoded filename list. Does not overwrite existing files, preserving user-edited values across restarts.
