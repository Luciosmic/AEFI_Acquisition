"""
FigureFactory - Draws a stored step as six colour maps (see figure_factory_intention.md).
Moved unchanged from the old window of the module.
"""

from matplotlib.figure import Figure


class FigureFactory:
    """
    Creates Figures for the field map presenter.
    Avoids GUI code (plt.show), returns Figure objects for embedding.
    """

    def create_figure(self, grids: dict, extent: list, metadata: dict, context_title: str) -> Figure:
        """Create a figure with the 6 standard channels (in-phase on top, quadrature below), "No Data" where one is missing."""
        components = ['x', 'y', 'z']

        fig = Figure(figsize=(12, 8), dpi=100)
        axes = fig.subplots(2, 3)

        for row_idx, (suffix, label) in enumerate((('in_phase', 'In-Phase'), ('quadrature', 'Quadrature'))):
            for col_idx, component in enumerate(components):
                col_name = f'voltage_{component}_{suffix}'
                ax = axes[row_idx, col_idx]

                if col_name in grids:
                    im = ax.imshow(
                        grids[col_name],
                        extent=extent,
                        origin='lower',
                        cmap='viridis',
                        interpolation='nearest',
                        aspect='auto',
                    )
                    ax.set_title(f'{component.upper()} {label}')
                    fig.colorbar(im, ax=ax)
                else:
                    ax.text(0.5, 0.5, "No Data", ha='center', va='center')

                ax.grid(True, alpha=0.3, linestyle='--')

        fig.suptitle(context_title, fontsize=10)
        fig.tight_layout()

        return fig
