"""
Plot Service
Handles Matplotlib Figure generation.
Adapted from plot_scan.py
"""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

class FigureFactory:
    """
    Creates Figures for the Visualisation Presenter.
    Avoids GUI code (plt.show), returns Figure objects for embedding.
    """
    
    def create_figure(self, grids: dict, extent: list, metadata: dict, context_title: str) -> Figure:
        """
        Create a fast figure with 6 subplots or single plot.
        """
        # We always want the 6-channel view if possible, based on screenshot
        
        # Check if we have the 6 standard channels
        # If not, fallback to single?
        # Screenshot shows 6 panels.
        
        components = ['x', 'y', 'z']
        
        fig = Figure(figsize=(12, 8), dpi=100) # Adjust figsize as needed
        axes = fig.subplots(2, 3)
        
        # Ligne 0: Réelles (in_phase)
        for col_idx, component in enumerate(components):
            col_name = f'voltage_{component}_in_phase'
            ax = axes[0, col_idx]
            
            if col_name in grids:
                grid = grids[col_name]
                im = ax.imshow(
                    grid,
                    extent=extent,
                    origin='lower',
                    cmap='viridis',
                    interpolation='nearest',
                    aspect='auto'
                )
                ax.set_title(f'{component.upper()} In-Phase')
                fig.colorbar(im, ax=ax) # Standard colorbar
            else:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                
            ax.grid(True, alpha=0.3, linestyle='--')
            
        
        # Ligne 1: Imaginaires (quadrature)
        for col_idx, component in enumerate(components):
            col_name = f'voltage_{component}_quadrature'
            ax = axes[1, col_idx]
            
            if col_name in grids:
                grid = grids[col_name]
                im = ax.imshow(
                    grid,
                    extent=extent,
                    origin='lower',
                    cmap='viridis',
                    interpolation='nearest',
                    aspect='auto'
                )
                ax.set_title(f'{component.upper()} Quadrature')
                fig.colorbar(im, ax=ax)
            else:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center')
                
            ax.grid(True, alpha=0.3, linestyle='--')
            
        fig.suptitle(context_title, fontsize=10)
        fig.tight_layout()
        
        return fig
