#!/usr/bin/env python3
"""
Script pour synchroniser les fichiers CSV et .fig vers un répertoire cloud partagé.
"""

import os
import sys
from pathlib import Path
import shutil

# TUI avec rich (optionnel)
try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

def print_msg(msg: str, style: str = ""):
    """Affiche un message avec ou sans rich."""
    if HAS_RICH:
        console.print(msg, style=style)
    else:
        # Supprimer les tags rich pour affichage simple
        import re
        clean_msg = re.sub(r'\[.*?\]', '', msg)
        print(clean_msg)

def sync_files(source_dir: Path, dest_dir: Path, overwrite: bool = False):
    """
    Synchronise les fichiers CSV et .fig du répertoire source vers le répertoire de destination.
    
    Args:
        source_dir: Répertoire source
        dest_dir: Répertoire de destination
        overwrite: Si True, écrase les fichiers existants. Si False, ignore les fichiers existants.
    """
    # Créer le répertoire de destination s'il n'existe pas
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Lister les fichiers à copier
    csv_files = list(source_dir.glob("*.csv"))
    fig_files = list(source_dir.glob("*.fig"))
    all_files = csv_files + fig_files
    
    if not all_files:
        print_msg("[yellow]Aucun fichier CSV ou .fig trouvé dans le répertoire source.[/yellow]")
        return
    
    print_msg(f"\n[cyan]Fichiers trouvés:[/cyan] {len(csv_files)} CSV, {len(fig_files)} .fig")
    
    copied_count = 0
    skipped_count = 0
    error_count = 0
    
    if HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Copie en cours...", total=len(all_files))
            
            for file_path in all_files:
                dest_path = dest_dir / file_path.name
                
                # Vérifier si le fichier existe déjà
                if dest_path.exists() and not overwrite:
                    skipped_count += 1
                    progress.update(task, description=f"Ignore (existe): {file_path.name}")
                else:
                    try:
                        shutil.copy2(file_path, dest_path)
                        copied_count += 1
                        progress.update(task, description=f"Copie: {file_path.name}")
                    except Exception as e:
                        error_count += 1
                        progress.update(task, description=f"Erreur: {file_path.name}")
                        print_msg(f"[red]Erreur lors de la copie de {file_path.name}: {e}[/red]")
                
                progress.advance(task)
    else:
        for idx, file_path in enumerate(all_files, 1):
            dest_path = dest_dir / file_path.name
            
            # Vérifier si le fichier existe déjà
            if dest_path.exists() and not overwrite:
                print_msg(f"[{idx}/{len(all_files)}] Ignore (existe): {file_path.name}")
                skipped_count += 1
            else:
                try:
                    shutil.copy2(file_path, dest_path)
                    print_msg(f"[{idx}/{len(all_files)}] Copie: {file_path.name}")
                    copied_count += 1
                except Exception as e:
                    print_msg(f"[{idx}/{len(all_files)}] ERREUR: {file_path.name} - {e}")
                    error_count += 1
    
    # Résumé
    print_msg(f"\n[bold]Resume de la synchronisation:[/bold]")
    print_msg(f"[green]Copies: {copied_count}[/green]")
    if not overwrite:
        print_msg(f"[yellow]Ignores (existe deja): {skipped_count}[/yellow]")
    print_msg(f"[red]Erreurs: {error_count}[/red]")
    print_msg(f"[cyan]Total: {len(all_files)} fichier(s)[/cyan]")

def main():
    """Point d'entrée principal."""
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]AEFI Cloud Sync[/bold cyan]\n"
            "Synchronisation des fichiers CSV et .fig vers le répertoire cloud",
            border_style="cyan"
        ))
    else:
        print("\n" + "="*50)
        print("  AEFI Cloud Sync")
        print("  Synchronisation des fichiers CSV et .fig vers le répertoire cloud")
        print("="*50)
    
    # Déterminer les répertoires
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent  # sync_to_cloud/ -> post_processor_modules/ -> tools/ -> project root
    source_dir = project_root / ".aefi_acquisition" / "scans" / "raw_data"
    
    # Répertoire de destination (cloud)
    dest_dir = Path(r"C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\Ressources\ExperimentalData_ASSOCE\Scans XY\AEFI_Acquisition_data_repository\scans")
    
    # Vérifier que le répertoire source existe
    if not source_dir.exists():
        print_msg(f"[red]Repertoire source introuvable: {source_dir}[/red]")
        sys.exit(1)
    
    # Vérifier que le répertoire de destination est accessible
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print_msg(f"[red]Impossible d'acceder au repertoire de destination: {dest_dir}[/red]")
        print_msg(f"[red]Erreur: {e}[/red]")
        sys.exit(1)
    
    print_msg(f"\n[cyan]Repertoire source:[/cyan] {source_dir}")
    print_msg(f"[cyan]Repertoire destination:[/cyan] {dest_dir}")
    
    # Demander le mode de synchronisation
    print_msg("\n[bold]Mode de synchronisation:[/bold]")
    print_msg("  1. Ajouter et laisser l'existant (ne pas ecraser)")
    print_msg("  2. Tout ecraser")
    
    while True:
        try:
            if HAS_RICH:
                mode = Prompt.ask(
                    "\n[bold cyan]Selectionnez le mode (1-2)[/bold cyan]",
                    default="1"
                )
            else:
                mode = input("\nSelectionnez le mode (1-2) [1]: ").strip() or "1"
            
            if mode == "1":
                overwrite = False
                break
            elif mode == "2":
                overwrite = True
                # Confirmation pour le mode écrasement
                if HAS_RICH:
                    confirm = Prompt.ask(
                        "\n[bold red]ATTENTION: Tous les fichiers existants seront ecrases. Continuer ? (o/n)[/bold red]",
                        default="n"
                    )
                else:
                    confirm = input("\nATTENTION: Tous les fichiers existants seront ecrases. Continuer ? (o/n) [n]: ").strip().lower() or "n"
                
                if confirm.lower() in ['o', 'oui', 'y', 'yes']:
                    break
                else:
                    print_msg("[yellow]Operation annulee.[/yellow]")
                    sys.exit(0)
            else:
                print_msg("[red]Choix invalide.[/red]")
        except KeyboardInterrupt:
            print_msg("\n[yellow]Operation annulee par l'utilisateur.[/yellow]")
            sys.exit(0)
    
    # Effectuer la synchronisation
    sync_files(source_dir, dest_dir, overwrite)
    
    print_msg("\n[green]Synchronisation terminee![/green]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_msg("\n[yellow]Interrompu par l'utilisateur.[/yellow]")
        sys.exit(0)
    except Exception as e:
        print_msg(f"[red]Erreur: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
